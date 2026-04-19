"""Chat API Blueprint - SSE 流式对话"""

import json
import logging
from flask import Blueprint, request, jsonify, Response
from ..models.decision import ChatRepository, DecisionRepository
from ..services.chat_agent import stream_chat_response
from ..utils.locale import get_locale

chat_bp = Blueprint('chat', __name__)
logger = logging.getLogger('lifeplanner.chat')

MAX_CONTENT_LEN = 5000


@chat_bp.route('/<int:decision_id>/history', methods=['GET'])
def get_history(decision_id):
    if not DecisionRepository.get(decision_id):
        return jsonify({'error': '决策不存在'}), 404
    phase = request.args.get('phase', 'interaction')
    messages = ChatRepository.get_messages(decision_id, phase)
    return jsonify({'messages': messages})


@chat_bp.route('/<int:decision_id>/send', methods=['POST'])
def send_message(decision_id):
    if not DecisionRepository.get(decision_id):
        return jsonify({'error': '决策不存在'}), 404
    data = request.get_json() or {}
    content = data.get('content', '').strip()
    phase = data.get('phase', 'interaction')

    if not content:
        return jsonify({'error': '内容不能为空'}), 400
    if len(content) > MAX_CONTENT_LEN:
        return jsonify({'error': f'消息长度不能超过 {MAX_CONTENT_LEN} 字'}), 400

    msg = ChatRepository.add_message(decision_id, phase, 'user', content)
    return jsonify({'message': msg}), 201


@chat_bp.route('/<int:decision_id>/stream', methods=['GET'])
def stream(decision_id):
    locale = request.args.get('lang', get_locale())

    def generate():
        try:
            yield from stream_chat_response(decision_id)
        except GeneratorExit:
            pass  # 客户端断连，静默退出
        except Exception:
            logger.exception("SSE chat stream error for decision %s", decision_id)
            yield f'data: {json.dumps({"type": "error", "content": "AI 服务异常，请刷新后重试"}, ensure_ascii=False)}\n\n'

    return Response(
        generate(),
        mimetype='text/event-stream; charset=utf-8',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )
