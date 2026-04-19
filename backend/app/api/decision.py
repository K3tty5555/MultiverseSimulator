"""Decision API Blueprint"""

import json
import logging
from flask import Blueprint, request, jsonify, Response
from ..models.decision import DecisionRepository
from ..database import get_db
from ..services.clarification_agent import get_or_ask_question
from ..services.simulation_engine import stream_simulation
from ..utils.locale import get_locale
from ..extensions import limiter

decision_bp = Blueprint('decision', __name__)
logger = logging.getLogger('lifeplanner.decision')

MAX_TITLE_LEN = 200
MAX_SITUATION_LEN = 5000
MAX_OPTION_LABEL_LEN = 200
MAX_OPTIONS = 8


@decision_bp.route('', methods=['GET'])
def list_decisions():
    decisions = DecisionRepository.list_all()
    return jsonify({'decisions': decisions})


@decision_bp.route('', methods=['POST'])
@limiter.limit("10/minute")
def create_decision():
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    title = data.get('title', '').strip()
    situation = data.get('situation', '').strip()
    options = data.get('options', [])

    if not title:
        return jsonify({'error': '标题不能为空'}), 400
    if len(title) > MAX_TITLE_LEN:
        return jsonify({'error': f'标题不能超过 {MAX_TITLE_LEN} 字'}), 400
    if not situation:
        return jsonify({'error': '情境描述不能为空'}), 400
    if len(situation) > MAX_SITUATION_LEN:
        return jsonify({'error': f'情境描述不能超过 {MAX_SITUATION_LEN} 字'}), 400
    if len(options) < 2:
        return jsonify({'error': '至少需要两个选项'}), 400
    if len(options) > MAX_OPTIONS:
        return jsonify({'error': f'最多支持 {MAX_OPTIONS} 个选项'}), 400

    # 截断过长的选项标签
    safe_options = []
    for opt in options:
        safe_options.append({
            'label': str(opt.get('label', ''))[:MAX_OPTION_LABEL_LEN],
            'description': str(opt.get('description', ''))[:500],
        })

    decision_type = data.get('decision_type', 'planning')
    if decision_type not in ('planning', 'retrospective'):
        decision_type = 'planning'

    persona_id = data.get('persona_id')
    if persona_id is not None:
        try:
            persona_id = int(persona_id)
        except (TypeError, ValueError):
            persona_id = None
        if persona_id is not None:
            from ..models.persona import PersonaRepository
            if not PersonaRepository.get(persona_id):
                return jsonify({'error': '角色不存在'}), 400

    actual_choice_index = data.get('actual_choice_index')
    if actual_choice_index is not None:
        try:
            actual_choice_index = int(actual_choice_index)
        except (TypeError, ValueError):
            actual_choice_index = None
        if actual_choice_index is not None and not (0 <= actual_choice_index < len(safe_options)):
            return jsonify({'error': '实际选择索引超出范围'}), 400

    actual_outcome = str(data.get('actual_outcome', '') or '')[:2000]
    time_period = str(data.get('time_period', '') or '')[:100]

    occurrence_year = None
    raw_year = data.get('occurrence_year')
    if raw_year is not None:
        try:
            occurrence_year = int(raw_year)
        except (TypeError, ValueError):
            return jsonify({'error': '发生年份必须是整数'}), 400
        if not (1 <= occurrence_year <= 2100):
            return jsonify({'error': '发生年份须在 1～2100 年之间'}), 400

    decision = DecisionRepository.create(
        title, situation, safe_options,
        decision_type=decision_type,
        persona_id=persona_id,
        actual_choice_index=actual_choice_index,
        actual_outcome=actual_outcome or None,
        time_period=time_period or None,
        occurrence_year=occurrence_year,
    )

    # 同步到「我的宇宙」—— 失败不阻塞主流程
    try:
        from ..models.universe import UniverseRepository
        personal = UniverseRepository.get_personal_universe()
        if personal:
            root = UniverseRepository.get_root_node(personal['id'])
            sync_node = UniverseRepository.create_node(
                universe_id=personal['id'],
                parent_id=root['id'] if root else None,
                perspective='god',
                protagonist_action=decision['title'],
                narrator_content='',
                node_type='decision',
                node_year=decision.get('occurrence_year'),
                decision_id=decision['id'],
            )
            DecisionRepository.set_universe_node_id(decision['id'], sync_node['id'])
    except Exception as e:
        logger.warning('sync decision to personal universe failed: %s', e)

    return jsonify({'decision': decision}), 201


@decision_bp.route('/<int:decision_id>', methods=['GET'])
def get_decision(decision_id):
    decision = DecisionRepository.get(decision_id)
    if not decision:
        return jsonify({'error': '决策不存在'}), 404
    return jsonify({'decision': decision})


@decision_bp.route('/<int:decision_id>', methods=['PUT'])
def update_decision(decision_id):
    return jsonify({'error': '暂不支持修改决策'}), 501


@decision_bp.route('/<int:decision_id>', methods=['DELETE'])
def delete_decision(decision_id):
    """软删除：移入回收站。"""
    decision = DecisionRepository.get(decision_id)
    if not decision:
        return jsonify({'error': '决策不存在'}), 404
    DecisionRepository.soft_delete(decision_id)
    return jsonify({'success': True})


@decision_bp.route('/trash', methods=['GET'])
def list_trash():
    decisions = DecisionRepository.list_trash()
    return jsonify({'decisions': decisions})


@decision_bp.route('/trash', methods=['DELETE'])
def empty_trash():
    DecisionRepository.empty_trash()
    return jsonify({'success': True})


@decision_bp.route('/<int:decision_id>/restore', methods=['POST'])
def restore_decision(decision_id):
    with get_db() as conn:
        row = conn.execute("SELECT id FROM decisions WHERE id=?", (decision_id,)).fetchone()
    if not row:
        return jsonify({'error': '决策不存在'}), 404
    DecisionRepository.restore(decision_id)
    return jsonify({'success': True})


@decision_bp.route('/<int:decision_id>/permanent', methods=['DELETE'])
def permanent_delete(decision_id):
    with get_db() as conn:
        row = conn.execute("SELECT id FROM decisions WHERE id=?", (decision_id,)).fetchone()
    if not row:
        return jsonify({'error': '决策不存在'}), 404
    DecisionRepository.delete(decision_id)
    return jsonify({'success': True})


@decision_bp.route('/<int:decision_id>/clarify', methods=['POST'])
def clarify(decision_id):
    data = request.get_json() or {}
    user_answer = data.get('answer')

    # 限制回答长度
    if user_answer and len(user_answer) > MAX_SITUATION_LEN:
        user_answer = user_answer[:MAX_SITUATION_LEN]

    decision = DecisionRepository.get(decision_id)
    if not decision:
        return jsonify({'error': '决策不存在'}), 404

    if decision['status'] == 'draft':
        DecisionRepository.update_status(decision_id, 'clarifying')

    try:
        question, all_answered = get_or_ask_question(decision_id, user_answer)
    except Exception as e:
        logger.exception("clarify LLM error for decision %s", decision_id)
        return jsonify({'error': 'AI 服务暂时不可用，请稍后重试'}), 503

    # 澄清完成：将状态推进到 clarified，让 simulate_stream 路由能接受该决策
    if all_answered and decision.get('status') not in ('clarified', 'simulating', 'reporting', 'done'):
        DecisionRepository.update_status(decision_id, 'clarified')

    return jsonify({
        'question': question,
        'all_answered': all_answered
    })


@decision_bp.route('/<int:decision_id>/simulate/stream', methods=['GET'])
@limiter.limit("20/minute")
def simulate_stream(decision_id):
    decision = DecisionRepository.get(decision_id)
    if not decision:
        return jsonify({'error': '决策不存在'}), 404
    if decision.get('status') not in ('clarified', 'simulating', 'reporting', 'done'):
        return jsonify({'error': '决策尚未完成澄清阶段'}), 400

    locale = request.args.get('lang', get_locale())

    def generate():
        try:
            yield from stream_simulation(decision_id, locale)
        except GeneratorExit:
            pass
        except Exception:
            logger.exception("simulate stream error decision=%s", decision_id)
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


@decision_bp.route('/<int:decision_id>/tree', methods=['GET'])
def get_tree(decision_id):
    decision = DecisionRepository.get(decision_id)
    if not decision:
        return jsonify({'error': '决策不存在'}), 404

    tree = {
        'id': f'decision-{decision_id}',
        'type': 'decision',
        'label': decision['title'],
        'children': []
    }

    for opt in decision.get('options', []):
        opt_node = {
            'id': f'option-{opt["id"]}',
            'type': 'option',
            'label': opt['label'],
            'children': []
        }
        results = decision.get('simulation_results', [])
        for dim in ['career', 'finance', 'relationships', 'wellbeing']:
            dim_results = [r for r in results if r['option_id'] == opt['id'] and r['dimension'] == dim]
            if dim_results:
                opt_node['children'].append({
                    'id': f'outcome-{opt["id"]}-{dim}',
                    'type': 'outcome',
                    'label': {'career': '事业', 'finance': '财务', 'relationships': '关系', 'wellbeing': '健康'}[dim],
                    'children': []
                })
        tree['children'].append(opt_node)

    return jsonify({'tree': tree})


@decision_bp.route('/<int:decision_id>/export', methods=['GET'])
def export_decision(decision_id):
    """导出决策报告为 Markdown"""
    d = DecisionRepository.get(decision_id)
    if not d:
        return jsonify({'error': '决策不存在'}), 404

    lines = [f"# {d.get('situation', '决策报告')}", ""]

    # 基本信息
    mode_labels = {'planning': '规划推演', 'retrospective': '回溯分析', 'historical': '历史推演'}
    lines.append(f"**决策模式：** {mode_labels.get(d.get('decision_mode', ''), '未知')}")
    lines.append(f"**创建时间：** {str(d.get('created_at', ''))[:10]}")
    lines.append("")

    # 选项
    options = d.get('options', [])
    actual_choice_id = d.get('actual_choice_id')
    if options:
        lines.append("## 决策选项")
        for i, opt in enumerate(options, 1):
            actual = " ✓（实际选择）" if (actual_choice_id and opt.get('id') == actual_choice_id) else ""
            lines.append(f"{i}. {opt.get('label', '')}{actual}")
        lines.append("")

    # 澄清 QA
    qa_list = d.get('clarification_qa', [])
    if qa_list:
        lines.append("## 澄清追问")
        for qa in qa_list:
            lines.append(f"**Q：** {qa.get('question', '')}")
            lines.append(f"**A：** {qa.get('answer', '')}")
            lines.append("")

    # 报告正文
    report = d.get('recommendation', '')
    if report:
        lines.append("## AI 分析报告")
        lines.append(report)
        lines.append("")

    content = "\n".join(lines)
    return content, 200, {
        'Content-Type': 'text/markdown; charset=utf-8',
        'Content-Disposition': f'attachment; filename="decision-{decision_id}.md"'
    }
