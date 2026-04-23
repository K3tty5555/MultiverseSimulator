"""世界探索 API Blueprint — GET /worlds, GET /worlds/<id>"""

import logging
from flask import Blueprint, jsonify
from ..database import get_db
from ..utils.safe_json import safe_json_loads

world_bp = Blueprint('world', __name__)
logger = logging.getLogger('lifeplanner.world_api')


@world_bp.route('', methods=['GET'])
def list_worlds():
    """GET /worlds — 返回所有世界（含 checkpoint 数量）。"""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT w.id, w.name, w.era, w.description, w.is_builtin,
                      w.generation_keywords, w.created_at,
                      COUNT(c.id) AS checkpoint_count
               FROM universe_worlds w
               LEFT JOIN world_checkpoints c ON c.world_id = w.id
               GROUP BY w.id
               ORDER BY w.is_builtin DESC, w.id ASC"""
        ).fetchall()
    worlds = [dict(r) for r in rows]
    return jsonify({'worlds': worlds})


@world_bp.route('/<int:world_id>', methods=['GET'])
def get_world(world_id):
    """GET /worlds/<id> — 返回世界详情 + checkpoints + 可选角色摘要。"""
    with get_db() as conn:
        world_row = conn.execute(
            "SELECT * FROM universe_worlds WHERE id=?", (world_id,)
        ).fetchone()
        if not world_row:
            return jsonify({'error': '世界不存在'}), 404
        world = dict(world_row)

        cp_rows = conn.execute(
            """SELECT id, world_id, title, year_label, premise,
                      available_persona_names, difficulty, sort_order
               FROM world_checkpoints
               WHERE world_id=?
               ORDER BY sort_order ASC""",
            (world_id,)
        ).fetchall()

    # 一次性收集所有 checkpoint 中出现的角色名，批量查询
    all_names = set()
    cp_name_lists = []
    for cp_row in cp_rows:
        try:
            names = safe_json_loads(cp_row['available_persona_names'], [], 'cp_persona_names')
        except (json.JSONDecodeError, TypeError):
            names = []
        cp_name_lists.append(names)
        all_names.update(names)

    persona_map = {}
    if all_names:
        placeholders = ','.join('?' * len(all_names))
        with get_db() as conn2:
            p_rows = conn2.execute(
                f"""SELECT id, name, bio, avatar_emoji, meta
                    FROM personas
                    WHERE name IN ({placeholders})
                      AND persona_type IN ('builtin', 'historical')""",
                list(all_names)
            ).fetchall()
        for p_row in p_rows:
            p = dict(p_row)
            try:
                p['meta'] = safe_json_loads(p.get('meta'), {}, 'persona_meta')
            except (json.JSONDecodeError, TypeError):
                p['meta'] = {}
            persona_map[p['name']] = p

    checkpoints = []
    for cp_row, names in zip(cp_rows, cp_name_lists):
        cp = dict(cp_row)
        cp['available_persona_names'] = names
        cp['personas'] = [
            persona_map.get(n, {'name': n, 'bio': '', 'avatar_emoji': '📜', 'meta': {}})
            for n in names
        ]
        checkpoints.append(cp)

    world['checkpoints'] = checkpoints
    return jsonify({'world': world})


@world_bp.route('/personas', methods=['GET'])
def list_builtin_personas():
    """GET /worlds/personas — 返回内置角色列表（供角色长廊展示）。"""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, name, bio, avatar_emoji, persona_type, meta
               FROM personas
               WHERE persona_type IN ('builtin', 'historical')
               ORDER BY created_at ASC"""
        ).fetchall()
    personas = []
    for r in rows:
        p = dict(r)
        try:
            p['meta'] = safe_json_loads(p.get('meta'), {}, 'persona_meta')
        except (json.JSONDecodeError, TypeError):
            p['meta'] = {}
        personas.append(p)
    return jsonify({'personas': personas})
