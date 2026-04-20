"""平行宇宙 API Blueprint"""

import json
import logging
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, Response
from ..models.universe import UniverseRepository
from ..services.universe_engine import stream_turn, generate_perspective_alt
from ..services.personal_universe_init import generate_root_narration
from ..database import get_db
from ..utils.locale import get_locale
from ..utils.safe_json import safe_json_loads
from ..extensions import limiter

universe_bp = Blueprint('universe', __name__)
logger = logging.getLogger('lifeplanner.universe_api')

MAX_TITLE_LEN = 200
MAX_PREMISE_LEN = 2000
MAX_NAME_LEN = 50
MAX_ACTION_LEN = 1000

# Short-lived in-memory token store for SSE turn actions (avoids long URLs)
_pending_turns: dict = {}
_pending_turns_lock = threading.Lock()
TURN_TOKEN_TTL = 300  # 5 minutes


def _mark_npc_ready(universe_id: int) -> None:
    """后台 NPC 预生成结束后回写状态。失败时记 warn，但不抛出（已在后台线程内）。"""
    try:
        with get_db() as conn:
            conn.execute(
                "UPDATE parallel_universes SET npc_ready=1 WHERE id=?",
                (universe_id,)
            )
            conn.commit()
    except Exception as e:
        logger.warning("NPC ready 标记失败 [universe=%s]: %s", universe_id, e)


def _cleanup_tokens():
    """Remove expired tokens (must be called with _pending_turns_lock held)."""
    now = time.time()
    stale = [k for k, v in _pending_turns.items() if v['expires_at'] < now]
    for k in stale:
        del _pending_turns[k]


def _add_tree_labels(node: dict) -> dict:
    """Recursively add D3 display labels to tree nodes (keeps Repository layer clean)."""
    if node is None:
        return node
    action = node.get('protagonist_action') or ''
    node['label'] = f"第{node['turn_number']}回" + (f"：{action[:20]}" if action else '')
    node['type'] = 'node'
    for child in node.get('children', []):
        _add_tree_labels(child)
    return node


@universe_bp.route('', methods=['GET'])
def list_universes():
    universes = UniverseRepository.list_all()
    return jsonify({'universes': universes})


@universe_bp.route('/with-agents', methods=['GET'])
def list_universes_with_agents():
    """跨宇宙 NPC 总览：一次请求返回所有活跃（非个人主宇宙）宇宙及其活跃 agents。
    供 /agents 前端页面使用。"""
    universes = UniverseRepository.list_all()
    result = []
    for u in universes:
        agents = UniverseRepository.list_agents(u['id'])
        result.append({
            'universe_id':         u['id'],
            'title':               u['title'],
            'protagonist_name':    u.get('protagonist_name') or '',
            'protagonist_role':    u.get('protagonist_role') or '',
            'universe_type':       u.get('universe_type') or 'historical',
            'era_label':           u.get('era_label') or '',
            'world_label':         u.get('world_label') or '',
            'canonical_event_id':  u.get('canonical_event_id'),
            'node_count':          u.get('node_count') or 0,
            'updated_at':          u.get('updated_at'),
            'agents':              [{
                'id':     a.get('id'),
                'name':   a.get('name'),
                'role':   a.get('role') or '',
                'stance': a.get('stance') or 'neutral',
            } for a in agents],
        })
    return jsonify({'universes': result})


@universe_bp.route('/canonical/events', methods=['GET'])
def list_canonical_events():
    """查询某角色的史实年表。不自动触发生成——客户端需显式调 /generate。
    query: ?name=X&type=historical&world_label=Y
    注：type 允许 historical / fictional / personal（personal 仅查询，不支持 generate）
    returns: {events: [...], generated: bool}
    """
    from ..models.canonical_event import CanonicalEventRepository
    name = (request.args.get('name') or '').strip()
    utype = request.args.get('type') or 'historical'
    world_label = (request.args.get('world_label') or '').strip() or None
    if not name:
        return jsonify({'error': '请提供角色名字'}), 400
    if utype not in ('historical', 'fictional', 'personal'):
        return jsonify({'error': 'type 必须为 historical / fictional / personal'}), 400
    events = CanonicalEventRepository.list_for(name, utype, world_label)
    return jsonify({'events': events, 'generated': len(events) > 0})


@universe_bp.route('/canonical/events/generate', methods=['POST'])
@limiter.limit("5/minute")
def generate_canonical_events_route():
    """触发 LLM 生成该角色的史实年表，存库并返回。
    body: {name, universe_type, world_label}
    注：universe_type 只支持 historical / fictional；personal 类型无外部史实，不走此端点。
    """
    from ..utils.ai_assist import generate_canonical_events
    from ..models.canonical_event import CanonicalEventRepository
    from ..models.settings import SettingsRepository
    from openai import APITimeoutError

    if not SettingsRepository.is_configured():
        return jsonify({'error': 'LLM 未配置，请先在设置中填写 API 信息'}), 503

    data = request.get_json() or {}
    name = str(data.get('name') or '').strip()[:MAX_NAME_LEN]
    utype = data.get('universe_type') or 'historical'
    world_label = str(data.get('world_label') or '').strip() or None

    if not name:
        return jsonify({'error': '请提供角色名字'}), 400
    if utype not in ('historical', 'fictional'):
        return jsonify({'error': 'universe_type 必须为 historical 或 fictional（personal 类型不支持自动生成）'}), 400

    # 幂等：若已生成过，直接返回现有（用户可手动触发重生成时需先删除）
    existing = CanonicalEventRepository.list_for(name, utype, world_label)
    if existing:
        return jsonify({'events': existing, 'generated': True, 'from_cache': True})

    try:
        raw_events = generate_canonical_events(name, utype, world_label or '')
        if not raw_events:
            return jsonify({'events': [], 'generated': False,
                            'reason': '该角色没有可考证的史实/原著节点'}), 200
        saved = CanonicalEventRepository.bulk_create(name, utype, world_label, raw_events)
        return jsonify({'events': saved, 'generated': True, 'from_cache': False})
    except ValueError as e:
        return jsonify({'error': f'AI 返回格式异常，请重试：{str(e)[:160]}'}), 422
    except (APITimeoutError, TimeoutError):
        return jsonify({'error': 'AI 服务超时，请稍后重试'}), 504
    except Exception:
        logger.exception("generate_canonical_events 失败: type=%s name=%s", utype, name)
        return jsonify({'error': 'AI 生成失败，请稍后重试'}), 500


@universe_bp.route('/canonical/events/<int:event_id>', methods=['PUT'])
def update_canonical_event(event_id):
    """编辑单条史实节点。"""
    from ..models.canonical_event import CanonicalEventRepository
    existing = CanonicalEventRepository.get(event_id)
    if not existing:
        return jsonify({'error': '节点不存在'}), 404
    data = request.get_json() or {}
    kwargs = {}
    if 'title' in data:
        t = str(data.get('title') or '').strip()
        if not t:
            return jsonify({'error': 'title 不能为空'}), 400
        kwargs['title'] = t
    if 'description' in data:
        kwargs['description'] = str(data.get('description') or '')
    if 'year' in data:
        y = data.get('year')
        if y is None or y == '':
            kwargs['year'] = None
        else:
            try:
                kwargs['year'] = int(y)
            except (TypeError, ValueError):
                return jsonify({'error': 'year 必须为整数或留空'}), 400
    if 'sort_order' in data:
        try:
            kwargs['sort_order'] = int(data.get('sort_order'))
        except (TypeError, ValueError):
            return jsonify({'error': 'sort_order 必须为整数'}), 400
    updated = CanonicalEventRepository.update(event_id, **kwargs)
    return jsonify({'event': updated})


@universe_bp.route('/canonical/events/<int:event_id>', methods=['DELETE'])
def delete_canonical_event(event_id):
    """删除单条史实节点。UPDATE 外键清空 + DELETE 在同一事务内完成，避免 crash 导致不一致。"""
    from ..models.canonical_event import CanonicalEventRepository
    existing = CanonicalEventRepository.get(event_id)
    if not existing:
        return jsonify({'error': '节点不存在'}), 404
    with get_db() as conn:
        conn.execute(
            "UPDATE parallel_universes SET canonical_event_id=NULL WHERE canonical_event_id=?",
            (event_id,)
        )
        conn.execute(
            "DELETE FROM character_canonical_events WHERE id=?",
            (event_id,)
        )
        conn.commit()
    return jsonify({'success': True})


@universe_bp.route('/canonical/events/bulk-delete', methods=['POST'])
def bulk_delete_canonical_events():
    """批量删除指定角色下未被用户编辑过的史实节点（用于重新梳理流程）。
    body: {name, universe_type, world_label}
    在单个事务内原子完成，避免串行 HTTP 调用中途失败导致部分删除。
    returns: {deleted_count: int}
    """
    from ..models.canonical_event import CanonicalEventRepository
    data = request.get_json() or {}
    name = str(data.get('name') or '').strip()[:MAX_NAME_LEN]
    utype = data.get('universe_type') or 'historical'
    world_label = str(data.get('world_label') or '').strip() or None
    if not name:
        return jsonify({'error': '请提供角色名字'}), 400

    events = CanonicalEventRepository.list_for(name, utype, world_label)
    to_delete = [e['id'] for e in events if not e.get('is_edited')]
    if not to_delete:
        return jsonify({'deleted_count': 0})

    with get_db() as conn:
        placeholders = ','.join('?' * len(to_delete))
        conn.execute(
            "UPDATE parallel_universes SET canonical_event_id=NULL "
            f"WHERE canonical_event_id IN ({placeholders})",
            to_delete
        )
        conn.execute(
            f"DELETE FROM character_canonical_events WHERE id IN ({placeholders})",
            to_delete
        )
        conn.commit()
    return jsonify({'deleted_count': len(to_delete)})


@universe_bp.route('/agent-timeline', methods=['GET'])
def agent_timeline():
    """返回某角色（name + universe_type）参与的所有节点，跨宇宙合流按 created_at 升序。
    参与规则：
      1. 作为主角（protagonist_name=name）所在宇宙的所有 nodes
      2. 作为 agent（universe_agents.name=name）在该宇宙的 nodes 里 agent_reactions 提及他的
    query: ?name=X&type=historical
    returns: {items: [{node_id, universe_id, universe_title, world_label, universe_type,
                        turn_number, node_type, protagonist_action, narrator_preview, created_at}]}
    """
    name = (request.args.get('name') or '').strip()
    universe_type = request.args.get('type') or 'historical'
    if not name:
        return jsonify({'error': '请提供角色名字'}), 400
    if universe_type not in ('historical', 'fictional', 'personal'):
        return jsonify({'error': 'type 必须为 historical / fictional / personal'}), 400

    items_by_node_id = {}

    with get_db() as conn:
        # 1. 作为主角：找所有该类型且 protagonist_name=name 的活跃宇宙的所有节点
        proto_rows = conn.execute(
            """SELECT n.id AS node_id, n.universe_id, n.turn_number, n.node_type,
                      n.protagonist_action, n.narrator_content, n.created_at,
                      u.title AS universe_title, u.world_label, u.universe_type
               FROM universe_nodes n
               JOIN parallel_universes u ON u.id = n.universe_id
               WHERE u.status='active'
                 AND u.is_personal_main=0
                 AND u.universe_type=?
                 AND u.protagonist_name=?
               ORDER BY n.created_at ASC""",
            (universe_type, name)
        ).fetchall()

        for r in proto_rows:
            items_by_node_id[r['node_id']] = dict(r)

        # 2. 作为 NPC：先找该 name + type 的所有 agent 所在 universe_id
        agent_rows = conn.execute(
            """SELECT a.universe_id
               FROM universe_agents a
               JOIN parallel_universes u ON u.id = a.universe_id
               WHERE a.deleted_at IS NULL
                 AND a.name=?
                 AND u.status='active'
                 AND u.is_personal_main=0
                 AND u.universe_type=?""",
            (name, universe_type)
        ).fetchall()

        if agent_rows:
            universe_ids = tuple({r['universe_id'] for r in agent_rows})
            placeholders = ','.join('?' * len(universe_ids))
            # agent_reactions JSON 里 "name":"xxx" 用 LIKE 模糊匹配
            like_pattern = f'%"name": "{name}"%'
            like_pattern_alt = f'%"name":"{name}"%'   # 紧凑格式也覆盖
            node_rows = conn.execute(
                f"""SELECT n.id AS node_id, n.universe_id, n.turn_number, n.node_type,
                           n.protagonist_action, n.narrator_content, n.created_at,
                           u.title AS universe_title, u.world_label, u.universe_type
                    FROM universe_nodes n
                    JOIN parallel_universes u ON u.id = n.universe_id
                    WHERE n.universe_id IN ({placeholders})
                      AND (n.agent_reactions LIKE ? OR n.agent_reactions LIKE ?)
                    ORDER BY n.created_at ASC""",
                (*universe_ids, like_pattern, like_pattern_alt)
            ).fetchall()
            for r in node_rows:
                items_by_node_id.setdefault(r['node_id'], dict(r))

    # 合并、按 created_at 升序
    items = sorted(items_by_node_id.values(), key=lambda x: x.get('created_at') or '')

    # 裁剪 narrator_content 为 preview（100 字）
    result = []
    for r in items:
        narrator = (r.get('narrator_content') or '')
        result.append({
            'node_id':           r['node_id'],
            'universe_id':       r['universe_id'],
            'universe_title':    r.get('universe_title') or '',
            'world_label':       r.get('world_label') or '',
            'universe_type':     r.get('universe_type') or 'historical',
            'turn_number':       r.get('turn_number') or 0,
            'node_type':         r.get('node_type') or 'narrative',
            'protagonist_action': r.get('protagonist_action') or '',
            'narrator_preview':  narrator[:100] + ('…' if len(narrator) > 100 else ''),
            'created_at':        r.get('created_at'),
        })

    return jsonify({'items': result})


@universe_bp.route('', methods=['POST'])
def create_universe():
    """创建自定义宇宙。
    新建流程允许 protagonist_name='' —— 表示主角延迟指定（进入宇宙后通过
    PUT /universe/<id>/protagonist 设定，届时触发 NPC preload）。
    body: {title, premise, protagonist_name?='', protagonist_role?, protagonist_bio?,
           perspective?='god', universe_type?='historical', era_label?}
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    title = str(data.get('title') or '').strip()
    premise = str(data.get('premise') or '').strip()
    protagonist_name = str(data.get('protagonist_name') or '').strip()
    protagonist_role = str(data.get('protagonist_role') or '').strip() or None
    protagonist_bio = str(data.get('protagonist_bio') or '').strip() or None
    perspective = data.get('perspective', 'god')
    universe_type = data.get('universe_type', 'historical')
    era_label = str(data.get('era_label') or '').strip() or None
    world_label = str(data.get('world_label') or '').strip() or None
    if world_label and len(world_label) > 40:
        world_label = world_label[:40]
    canonical_event_id = data.get('canonical_event_id')
    if canonical_event_id is not None:
        try:
            canonical_event_id = int(canonical_event_id)
        except (TypeError, ValueError):
            canonical_event_id = None

    if not title:
        return jsonify({'error': '标题不能为空'}), 400
    if len(title) > MAX_TITLE_LEN:
        return jsonify({'error': f'标题不能超过 {MAX_TITLE_LEN} 字'}), 400
    if not premise:
        return jsonify({'error': '世界背景不能为空'}), 400
    if len(premise) > MAX_PREMISE_LEN:
        return jsonify({'error': f'世界背景不能超过 {MAX_PREMISE_LEN} 字'}), 400
    if protagonist_name and len(protagonist_name) > MAX_NAME_LEN:
        return jsonify({'error': f'主角名字不能超过 {MAX_NAME_LEN} 字'}), 400
    if perspective not in ('god', 'first_person'):
        perspective = 'god'
    if universe_type not in ('historical', 'fictional'):
        return jsonify({'error': 'universe_type 必须为 historical 或 fictional'}), 400
    if era_label and len(era_label) > 100:
        era_label = era_label[:100]

    universe = UniverseRepository.create(
        title=title[:MAX_TITLE_LEN],
        premise=premise[:MAX_PREMISE_LEN],
        protagonist_name=protagonist_name[:MAX_NAME_LEN],   # 允许空字符串
        protagonist_role=protagonist_role[:MAX_NAME_LEN] if protagonist_role else None,
        protagonist_bio=protagonist_bio[:MAX_PREMISE_LEN] if protagonist_bio else None,
        perspective=perspective,
        universe_type=universe_type,
        era_label=era_label,
        world_label=world_label,
        canonical_event_id=canonical_event_id,
    )
    return jsonify({'universe': universe}), 201


@universe_bp.route('/scaffold', methods=['POST'])
@limiter.limit("10/minute")
def scaffold_universe():
    """AI 生成新宇宙骨架（不持久化），供前端弹层预填。
    body: {universe_type, keywords}
    returns: {result: {title, premise, era_label}}
    """
    from ..utils.ai_assist import generate_universe_scaffold
    from ..models.settings import SettingsRepository

    if not SettingsRepository.is_configured():
        return jsonify({'error': 'LLM 未配置，请先在设置中填写 API 信息'}), 503

    data = request.get_json() or {}
    universe_type = data.get('universe_type', 'historical')
    keywords = str(data.get('keywords') or '').strip()

    if universe_type not in ('historical', 'fictional'):
        return jsonify({'error': 'universe_type 必须为 historical 或 fictional'}), 400
    if not keywords:
        return jsonify({'error': '请提供关键词描述想要的宇宙'}), 400
    if len(keywords) > 200:
        return jsonify({'error': '关键词不能超过 200 字'}), 400

    try:
        import json as _json
        result = generate_universe_scaffold(universe_type, keywords)
        return jsonify({'result': result})
    except (ValueError, _json.JSONDecodeError) as e:
        return jsonify({'error': f'AI 返回格式异常，请重试：{str(e)[:160]}'}), 422
    except TimeoutError as e:
        return jsonify({'error': f'AI 服务超时，请稍后重试：{str(e)[:160]}'}), 504
    except Exception as e:
        return jsonify({'error': f'AI 生成失败：{str(e)[:200]}'}), 500


@universe_bp.route('/<int:universe_id>/protagonist', methods=['PUT'])
def set_universe_protagonist(universe_id):
    """设定/更新宇宙主角。首次设定时触发后台 NPC 预生成。
    body: {name, role?, bio?}
    """
    universe = UniverseRepository.get(universe_id)
    if not universe:
        return jsonify({'error': '宇宙不存在'}), 404

    data = request.get_json() or {}
    name = str(data.get('name') or '').strip()
    role = str(data.get('role') or '').strip() or None
    bio = str(data.get('bio') or '').strip() or None

    if not name:
        return jsonify({'error': '主角名字不能为空'}), 400
    if len(name) > MAX_NAME_LEN:
        return jsonify({'error': f'主角名字不能超过 {MAX_NAME_LEN} 字'}), 400

    was_empty = not (universe.get('protagonist_name') or '').strip()

    updated = UniverseRepository.set_protagonist(
        universe_id,
        name=name[:MAX_NAME_LEN],
        role=role[:MAX_NAME_LEN] if role else None,
        bio=bio[:MAX_PREMISE_LEN] if bio else None,
    )

    # 首次设定：触发后台 NPC 预生成
    if was_empty:
        from ..services.npc_preloader import preload_npcs_for_universe

        def _bg_preload():
            try:
                preload_npcs_for_universe(
                    universe_id=universe_id,
                    protagonist_name=name,
                    premise=universe.get('premise') or '',
                    event_context='',
                    count=3,
                )
            except Exception as e:
                logger.warning("后台 NPC 预生成失败 (new universe %s): %s", universe_id, e)
            finally:
                _mark_npc_ready(universe_id)

        threading.Thread(target=_bg_preload, daemon=True).start()

    return jsonify({'universe': updated})


@universe_bp.route('/<int:universe_id>/protagonist/assist', methods=['POST'])
@limiter.limit("10/minute")
def assist_universe_protagonist(universe_id):
    """根据宇宙背景 + 主角姓名，AI 生成 {role, bio} 供前端表单预填。"""
    from ..utils.ai_assist import assist_protagonist
    from ..models.settings import SettingsRepository

    if not SettingsRepository.is_configured():
        return jsonify({'error': 'LLM 未配置，请先在设置中填写 API 信息'}), 503

    universe = UniverseRepository.get(universe_id)
    if not universe:
        return jsonify({'error': '宇宙不存在'}), 404

    data = request.get_json() or {}
    name = str(data.get('name') or '').strip()[:MAX_NAME_LEN]
    if not name:
        return jsonify({'error': '请提供主角名字'}), 400

    try:
        import json as _json
        result = assist_protagonist(
            name=name,
            premise=universe.get('premise') or '',
            era_label=universe.get('era_label') or '',
        )
        return jsonify({'result': result})
    except (ValueError, _json.JSONDecodeError) as e:
        return jsonify({'error': f'AI 返回格式异常，请重试：{str(e)[:160]}'}), 422
    except TimeoutError as e:
        return jsonify({'error': f'AI 服务超时，请稍后重试：{str(e)[:160]}'}), 504
    except Exception as e:
        return jsonify({'error': f'AI 生成失败：{str(e)[:200]}'}), 500


@universe_bp.route('/personal', methods=['GET'])
def get_personal_universe_api():
    """返回「我的宇宙」及其时间线节点。"""
    personal = UniverseRepository.get_personal_universe()
    if not personal:
        return jsonify({'universe': None, 'nodes': [], 'initialized': False, 'last_node': None})
    nodes = UniverseRepository.get_personal_timeline()
    initialized = any(n.get('node_type') == 'root' for n in nodes)
    # 取 id 最大的非 root 节点作为「最近推演」（不依赖 timeline 排序顺序）
    non_root = [n for n in nodes if n.get('node_type') != 'root']
    last_node = max(non_root, key=lambda n: n.get('id', 0)) if non_root else None
    return jsonify({'universe': personal, 'nodes': nodes, 'initialized': initialized, 'last_node': last_node})


@universe_bp.route('/personal/init', methods=['POST'])
def init_personal_universe():
    """引导初始化：接收问答答案 → LLM 生成根节点叙事 → 创建根节点。"""
    data    = request.get_json(silent=True) or {}
    answers = data.get('answers', {})
    if not isinstance(answers, dict):
        answers = {}

    personal = UniverseRepository.get_personal_universe()
    if not personal:
        return jsonify({'error': '宇宙未创建，请重启应用'}), 500

    # 幂等：已有 root 节点则直接返回（不重复初始化）
    with get_db() as conn:
        existing_root_row = conn.execute(
            "SELECT * FROM universe_nodes WHERE universe_id=? AND node_type='root' LIMIT 1",
            (personal['id'],)
        ).fetchone()
    if existing_root_row:
        root = dict(existing_root_row)
        root['agent_reactions'] = safe_json_loads(root.get('agent_reactions'), default=[])
        root['branch_options']  = safe_json_loads(root.get('branch_options'),  default=[])
        return jsonify({'node': root, 'universe': personal}), 200

    # 获取 Profile 数据（可选，失败不阻断）
    profile = {}
    try:
        from ..models.profile import ProfileRepository
        profile = ProfileRepository.get() or {}
    except Exception:
        pass

    narration = generate_root_narration(answers, profile)

    try:
        node = UniverseRepository.create_node(
            universe_id=personal['id'],
            parent_id=None,
            perspective='god',
            protagonist_action=None,
            narrator_content=narration,
            node_type='root',
        )
    except sqlite3.IntegrityError:
        # 并发竞态：另一个请求刚刚创建了根节点，直接返回已有节点
        with get_db() as conn:
            existing = conn.execute(
                "SELECT * FROM universe_nodes WHERE universe_id=? AND node_type='root' LIMIT 1",
                (personal['id'],)
            ).fetchone()
        node = dict(existing)
        node['agent_reactions'] = safe_json_loads(node.get('agent_reactions'), default=[])
        node['branch_options']  = safe_json_loads(node.get('branch_options'),  default=[])
        return jsonify({'node': node, 'universe': UniverseRepository.get_personal_universe()}), 200

    # 更新宇宙主角名（若仍是占位符）——SQL-层条件保障幂等
    name = (answers.get('name') or '').strip() or profile.get('display_name', '')
    if name:
        with get_db() as conn:
            conn.execute(
                "UPDATE parallel_universes SET protagonist_name=?, updated_at=? "
                "WHERE id=? AND protagonist_name IN ('', '我')",
                (name[:80], datetime.now(timezone.utc).isoformat(), personal['id'])
            )
            conn.commit()

    return jsonify({'node': node, 'universe': UniverseRepository.get_personal_universe()}), 201


@universe_bp.route('/personal/reinit', methods=['POST'])
def reinit_personal_universe():
    """用最新档案重新生成「我的宇宙」根节点叙事。
    删除现有根节点及所有后代，然后根据当前 Profile 重新生成根节点。
    无根节点时等同 init（幂等）。
    """
    personal = UniverseRepository.get_personal_universe()
    if not personal:
        return jsonify({'error': '宇宙未创建，请重启应用'}), 500

    try:
        existing_root = UniverseRepository.get_root_node(personal['id'])
        if existing_root:
            UniverseRepository.delete_node_cascade(existing_root['id'])

        profile = {}
        try:
            from ..models.profile import ProfileRepository
            profile = ProfileRepository.get() or {}
        except Exception:
            pass

        narration = generate_root_narration({}, profile)

        node = UniverseRepository.create_node(
            universe_id=personal['id'],
            parent_id=None,
            perspective='god',
            protagonist_action=None,
            narrator_content=narration,
            node_type='root',
        )
        UniverseRepository.touch(personal['id'])
        return jsonify({'node': node, 'universe': UniverseRepository.get_personal_universe()}), 200

    except Exception as e:
        logger.exception('reinit_personal_universe failed')
        return jsonify({'error': '重新初始化失败，请稍后重试'}), 500


@universe_bp.route('/from-persona', methods=['POST'])
def create_from_persona():
    """从历史/内置角色快速创建平行宇宙，NPC 在后台异步预生成。"""
    from ..models.persona import PersonaRepository
    from ..services.npc_preloader import preload_npcs_for_universe

    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    # 安全转换整数 ID
    try:
        persona_id = int(data.get('persona_id'))
    except (TypeError, ValueError):
        return jsonify({'error': 'persona_id 必须为整数'}), 400

    perspective = data.get('perspective', 'god')
    if perspective not in ('god', 'first_person'):
        perspective = 'god'

    persona = PersonaRepository.get(persona_id)
    if not persona:
        return jsonify({'error': '角色不存在'}), 404
    if persona.get('persona_type') not in ('historical', 'builtin'):
        return jsonify({'error': '只有历史人物或内置角色可以快速创建宇宙'}), 400

    # B2: 没有 bio 的角色无法构造有意义的 premise，拦截避免生成空壳宇宙
    bio = (persona.get('bio') or '').strip()
    if not bio:
        return jsonify({'error': '角色背景为空，请先在角色管理中完善简介'}), 400

    # 拼装宇宙字段
    name = persona['name']
    meta = persona.get('meta') if isinstance(persona.get('meta'), dict) else {}
    era_year = meta.get('era_year')
    era_str = f'（{era_year}年）' if era_year else ''
    protagonist_role = str(meta.get('role') or '')[:MAX_NAME_LEN] or None

    title = f'{name}的平行宇宙'
    premise = f'{name}{era_str}：{bio[:500]}'[:MAX_PREMISE_LEN]

    universe = UniverseRepository.create(
        title=title[:MAX_TITLE_LEN],
        premise=premise,
        protagonist_name=name[:MAX_NAME_LEN],
        protagonist_role=protagonist_role,
        perspective=perspective,
        persona_id=persona_id,
    )
    universe_id = universe['id']

    # NPC 预生成在后台线程中运行，不阻塞 HTTP 响应（约 5-8 秒）
    def _bg_preload():
        try:
            preload_npcs_for_universe(
                universe_id=universe_id,
                protagonist_name=name,
                premise=premise,
                event_context='',
                count=3,
            )
        except Exception as e:
            logger.warning("后台 NPC 预生成失败: %s", e)
        finally:
            # B1: 无论成败都标记 ready，避免前端永远显示"生成中"
            _mark_npc_ready(universe_id)

    threading.Thread(target=_bg_preload, daemon=True).start()

    return jsonify({'universe': universe}), 201


@universe_bp.route('/from-checkpoint', methods=['POST'])
def create_from_checkpoint():
    """从世界节点（checkpoint）+ 角色名称快速创建平行宇宙，NPC 在后台异步预生成。
    POST body: { checkpoint_id, persona_name, perspective='god' }
    """
    from ..models.persona import PersonaRepository
    from ..services.npc_preloader import preload_npcs_for_universe

    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    try:
        checkpoint_id = int(data.get('checkpoint_id'))
    except (TypeError, ValueError):
        return jsonify({'error': 'checkpoint_id 必须为整数'}), 400

    persona_name = str(data.get('persona_name') or '').strip()
    if not persona_name:
        return jsonify({'error': 'persona_name 不能为空'}), 400

    perspective = data.get('perspective', 'god')
    if perspective not in ('god', 'first_person'):
        perspective = 'god'

    # 查询 checkpoint + 关联世界
    with get_db() as conn:
        cp_row = conn.execute(
            """SELECT c.*, w.name AS world_name, w.description AS world_description
               FROM world_checkpoints c
               JOIN universe_worlds w ON w.id = c.world_id
               WHERE c.id=?""",
            (checkpoint_id,)
        ).fetchone()

    if not cp_row:
        return jsonify({'error': '节点不存在'}), 404
    cp = dict(cp_row)

    # 校验 persona_name 在允许列表内
    available = safe_json_loads(cp.get('available_persona_names'), default=[])
    if persona_name not in available:
        return jsonify({'error': f'该节点不支持角色「{persona_name}」，可选角色：{available}'}), 400

    # 查找角色（builtin/historical）
    with get_db() as conn:
        persona_row = conn.execute(
            """SELECT * FROM personas
               WHERE name=? AND persona_type IN ('builtin', 'historical')
               LIMIT 1""",
            (persona_name,)
        ).fetchone()
    if not persona_row:
        return jsonify({'error': f'角色「{persona_name}」不存在，请先在角色库中创建'}), 404
    persona = dict(persona_row)
    meta = safe_json_loads(persona.get('meta'), default={})

    # 拼装宇宙字段
    era_year = meta.get('era_year')
    bio = (persona.get('bio') or '').strip()
    protagonist_role = str(meta.get('role') or '')[:MAX_NAME_LEN] or None

    world_desc = (cp.get('world_description') or '').strip()
    cp_premise = (cp.get('premise') or '').strip()
    # 世界通史前 200 字 + 节点专属背景
    premise = (world_desc[:200] + '\n\n' + cp_premise if world_desc else cp_premise)[:MAX_PREMISE_LEN]

    title = f"{cp['title']}：{persona_name}的抉择"[:MAX_TITLE_LEN]

    # 预制入门行动（按节点 + 角色索引，帮助新手快速开始）
    _STARTER_ACTIONS = {
        ('赤壁前夕', '诸葛亮'): [
            '舌战群儒，说服东吴主战派联合抗曹',
            '分析曹操水军弱点，向孙权献借东风之计',
            '暗中联络周瑜，共商火攻破敌方略',
        ],
        ('赤壁前夕', '曹操'): [
            '传令水军加紧操练，择日渡江一举灭吴',
            '派细作入吴，打探孙刘联合动向',
            '约见蔡瑁张允，确认荆州水军指挥权',
        ],
        ('赤壁前夕', '周瑜'): [
            '公开表态主战，压制东吴降派声音',
            '勘察曹军水寨布局，制定火攻方案',
            '暗中试探诸葛亮深浅，摸清蜀汉底牌',
        ],
        ('赤壁前夕', '孙权'): [
            '召集文武廷议，拍板孙刘联合的决策',
            '密遣使者赴刘备营地，商讨结盟条件',
            '巡视长江防线，亲自鼓舞将士士气',
        ],
        ('隆中对', '刘备'): [
            '虚心请教诸葛亮对天下大势的判断',
            '提出取荆州之策，听取诸葛亮的意见',
            '询问如何在曹操、孙权夹缝中求存图强',
        ],
        ('隆中对', '诸葛亮'): [
            '展开《隆中对》，向刘备详述三分天下战略',
            '分析曹操、孙权优劣，指出荆益之地的价值',
            '向刘备表明出山辅佐的决心与条件',
        ],
        ('官渡之战', '曹操'): [
            '接纳许攸，听取乌巢屯粮的绝密情报',
            '亲率精锐轻骑奇袭乌巢，烧毁袁绍粮仓',
            '稳住正面防线，防止袁绍趁机反扑大营',
        ],
        ('官渡之战', '袁绍'): [
            '否决许攸的建议，坚守正面大阵不动',
            '分兵驰援乌巢，与曹操争夺粮仓控制权',
            '亲率大军猛攻曹操大营，以攻代守',
        ],
    }
    # 用 checkpoint 标题前缀匹配（不依赖 id 硬编码）
    cp_title = cp.get('title', '')
    starter_key = None
    for (t_prefix, p_name) in _STARTER_ACTIONS:
        if t_prefix in cp_title and p_name == persona_name:
            starter_key = (t_prefix, p_name)
            break
    starter_actions = _STARTER_ACTIONS.get(starter_key, [])

    universe = UniverseRepository.create(
        title=title,
        premise=premise,
        protagonist_name=persona_name[:MAX_NAME_LEN],
        protagonist_role=protagonist_role,
        perspective=perspective,
        persona_id=persona['id'],
    )
    universe_id = universe['id']

    # 记录 checkpoint_id 和 starter_actions
    with get_db() as conn:
        conn.execute(
            "UPDATE parallel_universes SET checkpoint_id=?, starter_actions=? WHERE id=?",
            (checkpoint_id, json.dumps(starter_actions, ensure_ascii=False), universe_id)
        )
        conn.commit()
    universe['checkpoint_id'] = checkpoint_id
    universe['starter_actions'] = starter_actions

    # NPC 预生成在后台线程中运行，不阻塞 HTTP 响应
    def _bg_preload():
        try:
            preload_npcs_for_universe(
                universe_id=universe_id,
                protagonist_name=persona_name,
                premise=premise,
                event_context=cp_premise,
                count=3,
            )
        except Exception as e:
            logger.warning("后台 NPC 预生成失败 (checkpoint universe): %s", e)
        finally:
            _mark_npc_ready(universe_id)

    threading.Thread(target=_bg_preload, daemon=True).start()

    return jsonify({'universe': universe}), 201


@universe_bp.route('/personal/insights', methods=['GET'])
def get_personal_insights():
    """获取个人宇宙洞察数据"""
    personal = UniverseRepository.get_personal_universe()
    if not personal:
        return jsonify({'insights': None}), 200

    nodes = UniverseRepository.get_personal_timeline()

    # 按年份统计决策数量
    year_counts = {}
    type_counts = {'career': 0, 'relationship': 0, 'finance': 0, 'health': 0, 'other': 0}

    for node in nodes:
        if node.get('node_type') == 'root':
            continue
        year = node.get('node_year') or 'unknown'
        year_counts[year] = year_counts.get(year, 0) + 1

        # 简单关键词分类
        action = (node.get('protagonist_action') or '') + (node.get('narrator_content') or '')
        action_lower = action.lower()
        if any(k in action_lower for k in ['工作', '职业', '升职', '创业', '离职', '跳槽']):
            type_counts['career'] += 1
        elif any(k in action_lower for k in ['恋爱', '结婚', '离婚', '友情', '家庭']):
            type_counts['relationship'] += 1
        elif any(k in action_lower for k in ['投资', '理财', '购房', '贷款', '存款']):
            type_counts['finance'] += 1
        elif any(k in action_lower for k in ['健康', '运动', '医疗', '减肥', '锻炼']):
            type_counts['health'] += 1
        else:
            type_counts['other'] += 1

    total = len([n for n in nodes if n.get('node_type') != 'root'])

    type_labels = {'career': '职业', 'relationship': '关系', 'finance': '财务',
                   'health': '健康', 'other': '其他'}
    type_dist = sorted(
        [{'type': t, 'count': c, 'label': type_labels[t]}
         for t, c in type_counts.items() if c > 0],
        key=lambda x: -x['count']
    )

    return jsonify({
        'insights': {
            'total_decisions': total,
            'year_distribution': [{'year': y, 'count': c} for y, c in sorted(year_counts.items())],
            'type_distribution': type_dist,
        }
    }), 200


@universe_bp.route('/<int:universe_id>', methods=['GET'])
def get_universe(universe_id):
    universe = UniverseRepository.get(universe_id)
    if not universe:
        return jsonify({'error': '宇宙不存在'}), 404
    return jsonify({'universe': universe})


@universe_bp.route('/<int:universe_id>', methods=['DELETE'])
def archive_universe(universe_id):
    universe = UniverseRepository.get(universe_id)
    if not universe:
        return jsonify({'error': '宇宙不存在'}), 404
    if universe.get('is_personal_main'):
        return jsonify({'error': '个人宇宙不可通过此接口操作'}), 403
    UniverseRepository.archive(universe_id)
    return jsonify({'success': True})


@universe_bp.route('/<int:universe_id>/agents', methods=['GET'])
def list_agents(universe_id):
    universe = UniverseRepository.get(universe_id)
    if not universe:
        return jsonify({'error': '宇宙不存在'}), 404
    agents = UniverseRepository.list_agents(universe_id)
    return jsonify({'agents': agents})


@universe_bp.route('/<int:universe_id>/agents', methods=['POST'])
def add_agent(universe_id):
    universe = UniverseRepository.get(universe_id)
    if not universe:
        return jsonify({'error': '宇宙不存在'}), 404
    data = request.get_json() or {}
    name = str(data.get('name') or '').strip()
    if not name:
        return jsonify({'error': '角色名字不能为空'}), 400
    agent = UniverseRepository.upsert_agent(
        universe_id=universe_id,
        name=name[:MAX_NAME_LEN],
        role=str(data.get('role') or '')[:100] or None,
        bio=str(data.get('bio') or '')[:500] or None,
        persona=str(data.get('persona') or '')[:500] or None,
        mbti=str(data.get('mbti') or '')[:10] or None,
        stance=data.get('stance', 'neutral') if data.get('stance') in ('ally', 'neutral', 'adversary') else 'neutral',
    )
    return jsonify({'agent': agent}), 201


def _ensure_agent_in_universe(universe_id, agent_id):
    """校验 agent 属于该 universe，返回 (agent, error_response)。"""
    agent = UniverseRepository.get_agent(agent_id)
    if not agent:
        return None, (jsonify({'error': '角色不存在'}), 404)
    if agent.get('universe_id') != universe_id:
        return None, (jsonify({'error': '角色不属于该宇宙'}), 404)
    return agent, None


@universe_bp.route('/<int:universe_id>/agents/<int:agent_id>', methods=['PUT'])
def update_agent(universe_id, agent_id):
    _agent, err = _ensure_agent_in_universe(universe_id, agent_id)
    if err:
        return err
    data = request.get_json() or {}
    # 字段白名单 + 长度截断，None/缺失不更新
    kwargs = {}
    if 'role' in data:
        kwargs['role'] = str(data.get('role') or '')[:100] or None
    if 'bio' in data:
        kwargs['bio'] = str(data.get('bio') or '')[:500] or None
    if 'persona' in data:
        kwargs['persona'] = str(data.get('persona') or '')[:500] or None
    if 'mbti' in data:
        kwargs['mbti'] = str(data.get('mbti') or '')[:10] or None
    if 'stance' in data:
        s = data.get('stance')
        if s not in ('ally', 'neutral', 'adversary'):
            return jsonify({'error': 'stance 必须为 ally / neutral / adversary'}), 400
        kwargs['stance'] = s
    updated = UniverseRepository.update_agent(agent_id, **kwargs)
    UniverseRepository.touch(universe_id)  # 宇宙 updated_at 同步，保证列表页排序正确
    return jsonify({'agent': updated})


@universe_bp.route('/<int:universe_id>/agents/<int:agent_id>', methods=['DELETE'])
def delete_agent(universe_id, agent_id):
    _agent, err = _ensure_agent_in_universe(universe_id, agent_id)
    if err:
        return err
    UniverseRepository.delete_agent(agent_id)
    UniverseRepository.touch(universe_id)
    return jsonify({'success': True})


@universe_bp.route('/<int:universe_id>/agents/rename', methods=['POST'])
def rename_agent(universe_id):
    """重命名 NPC（保留 id/memory/last_node_id/agent_reactions 历史引用）。
    body: {agent_id, new_name}
    失败条件：新名已被同宇宙其他 agent 占用。
    """
    data = request.get_json() or {}
    try:
        agent_id = int(data.get('agent_id'))
    except (TypeError, ValueError):
        return jsonify({'error': 'agent_id 必须为整数'}), 400
    new_name = str(data.get('new_name') or '').strip()[:MAX_NAME_LEN]
    if not new_name:
        return jsonify({'error': '新名字不能为空'}), 400

    _agent, err = _ensure_agent_in_universe(universe_id, agent_id)
    if err:
        return err

    # 检查同宇宙下是否重名
    clash = UniverseRepository.find_agent_by_name(universe_id, new_name)
    if clash and clash['id'] != agent_id:
        return jsonify({'error': f'名字「{new_name}」已被占用'}), 409

    updated = UniverseRepository.rename_agent(agent_id, new_name)
    UniverseRepository.touch(universe_id)
    return jsonify({'agent': updated})


@universe_bp.route('/<int:universe_id>/agents/assist', methods=['POST'])
@limiter.limit("10/minute")
def assist_agent_route(universe_id):
    """根据宇宙背景 + 主角 + NPC 姓名，AI 生成 NPC 档案供前端表单预填。"""
    from ..utils.ai_assist import assist_agent
    from ..models.settings import SettingsRepository

    if not SettingsRepository.is_configured():
        return jsonify({'error': 'LLM 未配置，请先在设置中填写 API 信息'}), 503

    universe = UniverseRepository.get(universe_id)
    if not universe:
        return jsonify({'error': '宇宙不存在'}), 404

    data = request.get_json() or {}
    name = str(data.get('name') or '').strip()[:MAX_NAME_LEN]
    if not name:
        return jsonify({'error': '请提供 NPC 名字'}), 400

    try:
        import json as _json
        result = assist_agent(
            name=name,
            premise=universe.get('premise') or '',
            protagonist=universe.get('protagonist_name') or '',
        )
        return jsonify({'result': result})
    except (ValueError, _json.JSONDecodeError) as e:
        # LLM 返回无法解析为 JSON
        return jsonify({'error': f'AI 返回格式异常，请重试：{str(e)[:160]}'}), 422
    except TimeoutError as e:
        return jsonify({'error': f'AI 服务超时，请稍后重试：{str(e)[:160]}'}), 504
    except Exception as e:
        return jsonify({'error': f'AI 生成失败：{str(e)[:200]}'}), 500


@universe_bp.route('/<int:universe_id>/tree', methods=['GET'])
def get_tree(universe_id):
    universe = UniverseRepository.get(universe_id)
    if not universe:
        return jsonify({'error': '宇宙不存在'}), 404
    tree = UniverseRepository.get_tree(universe_id)
    if tree:
        _add_tree_labels(tree)
    return jsonify({'tree': tree})


@universe_bp.route('/<int:universe_id>/thread', methods=['GET'])
def get_thread(universe_id):
    """返回指定节点到根的完整线程（含节点数据）。
    query param: node_id (int, optional)"""
    universe = UniverseRepository.get(universe_id)
    if not universe:
        return jsonify({'error': '宇宙不存在'}), 404

    node_id = request.args.get('node_id', type=int)
    if node_id:
        node = UniverseRepository.get_node(node_id)
        if not node or node['universe_id'] != universe_id:
            return jsonify({'error': '节点不存在'}), 404
        thread = UniverseRepository.get_thread(node_id)
    else:
        # 默认返回最新节点的线程
        latest = UniverseRepository.get_latest_node(universe_id)
        if latest:
            thread = UniverseRepository.get_thread(latest['id'])
        else:
            thread = []

    return jsonify({'thread': thread})


@universe_bp.route('/<int:universe_id>/perspective', methods=['PUT'])
def switch_perspective(universe_id):
    universe = UniverseRepository.get(universe_id)
    if not universe:
        return jsonify({'error': '宇宙不存在'}), 404
    if universe.get('is_personal_main'):
        return jsonify({'error': '个人宇宙不可通过此接口操作'}), 403
    data = request.get_json() or {}
    perspective = data.get('perspective')
    if perspective not in ('god', 'first_person'):
        return jsonify({'error': 'perspective 必须是 god 或 first_person'}), 400
    UniverseRepository.update_perspective(universe_id, perspective)
    return jsonify({'success': True, 'perspective': perspective})


@universe_bp.route('/<int:universe_id>/retrospect/stream', methods=['GET'])
def retrospect_stream(universe_id):
    """为历史节点生成新视角回溯叙事（SSE）。
    query: node_ids (comma-separated), perspective"""
    universe = UniverseRepository.get(universe_id)
    if not universe:
        return jsonify({'error': '宇宙不存在'}), 404

    node_ids_str = request.args.get('node_ids', '')
    node_ids = []
    for s in node_ids_str.split(','):
        try:
            node_ids.append(int(s.strip()))
        except ValueError:
            pass
    if not node_ids:
        return jsonify({'error': '需要提供 node_ids 参数'}), 400

    perspective = request.args.get('perspective', universe['perspective'])
    if perspective not in ('god', 'first_person'):
        perspective = 'god'

    def generate():
        try:
            yield from generate_perspective_alt(universe_id, node_ids, perspective)
        except GeneratorExit:
            pass
        except Exception:
            logger.exception("retrospect stream error universe=%s", universe_id)
            yield f'data: {json.dumps({"type": "error", "message": "回溯叙事服务异常"}, ensure_ascii=False)}\n\n'

    return Response(
        generate(),
        mimetype='text/event-stream; charset=utf-8',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        }
    )


@universe_bp.route('/<int:universe_id>/entity_states', methods=['GET'])
def get_entity_states(universe_id):
    """获取宇宙当前实体世界状态列表。"""
    universe = UniverseRepository.get(universe_id)
    if not universe:
        return jsonify({'error': '宇宙不存在'}), 404
    states = UniverseRepository.get_entity_states(universe_id)
    return jsonify({'states': states})


@universe_bp.route('/<int:universe_id>/turn/prepare', methods=['POST'])
def prepare_turn(universe_id):
    """存储行动到服务端 session，返回短期 token，供 SSE 端点消费。
    避免将长行动文本放入 URL 查询参数。"""
    universe = UniverseRepository.get(universe_id)
    if not universe:
        return jsonify({'error': '宇宙不存在'}), 404
    if universe.get('status') != 'active':
        return jsonify({'error': '该宇宙已归档'}), 400

    data = request.get_json() or {}
    action = str(data.get('action') or '').strip()
    if not action:
        return jsonify({'error': '行动描述不能为空'}), 400
    if len(action) > MAX_ACTION_LEN:
        return jsonify({'error': f'行动描述不能超过 {MAX_ACTION_LEN} 字'}), 400

    parent_node_id = data.get('parent_node_id')
    if parent_node_id is not None:
        parent_node_id = int(parent_node_id)
        parent_node = UniverseRepository.get_node(parent_node_id)
        if not parent_node or parent_node['universe_id'] != universe_id:
            return jsonify({'error': '父节点不存在'}), 404

    locale = str(data.get('lang') or get_locale())

    token = str(uuid.uuid4())
    with _pending_turns_lock:
        _cleanup_tokens()
        _pending_turns[token] = {
            'action': action,
            'parent_node_id': parent_node_id,
            'universe_id': universe_id,
            'locale': locale,
            'expires_at': time.time() + TURN_TOKEN_TTL,
        }
    return jsonify({'token': token})


@universe_bp.route('/<int:universe_id>/turn/stream', methods=['GET'])
def turn_stream(universe_id):
    """推演一轮（SSE）。query: token (str) — 由 /turn/prepare 获取"""
    token = request.args.get('token', '').strip()
    with _pending_turns_lock:
        if not token or token not in _pending_turns:
            return jsonify({'error': '无效或已过期的 token，请重新发送行动'}), 400
        turn_data = _pending_turns.pop(token)  # 单次消费
    if turn_data['universe_id'] != universe_id:
        return jsonify({'error': '宇宙不匹配'}), 400
    if turn_data['expires_at'] < time.time():
        return jsonify({'error': 'token 已过期，请重新发送行动'}), 400

    universe = UniverseRepository.get(universe_id)
    if not universe:
        return jsonify({'error': '宇宙不存在'}), 404
    if universe.get('status') != 'active':
        return jsonify({'error': '该宇宙已归档'}), 400

    action = turn_data['action']
    parent_node_id = turn_data['parent_node_id']
    locale = turn_data['locale']

    def generate():
        try:
            yield from stream_turn(universe_id, parent_node_id, action, locale)
        except GeneratorExit:
            pass
        except Exception:
            logger.exception("turn stream error universe=%s", universe_id)
            yield f'data: {json.dumps({"type": "error", "message": "推演服务异常，请重试"}, ensure_ascii=False)}\n\n'

    return Response(
        generate(),
        mimetype='text/event-stream; charset=utf-8',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        }
    )


@universe_bp.route('/<int:universe_id>/nodes/<int:node_id>', methods=['DELETE'])
def delete_node(universe_id, node_id):
    """删除节点及其所有后代。叶节点直接删；有子节点时级联删（前端已二次确认）。
    根节点也可删除，宇宙变为空状态后用户可重新初始化。"""
    universe = UniverseRepository.get(universe_id)
    if not universe:
        return jsonify({'error': '宇宙不存在'}), 404
    node = UniverseRepository.get_node(node_id)
    if not node or node['universe_id'] != universe_id:
        return jsonify({'error': '节点不存在'}), 404
    UniverseRepository.delete_node_cascade(node_id)
    UniverseRepository.touch(universe_id)  # 更新宇宙 updated_at，保证列表页排序正确
    return jsonify({'success': True, 'deleted_node_id': node_id})
