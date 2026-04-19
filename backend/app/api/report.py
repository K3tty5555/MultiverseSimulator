"""Report API Blueprint - SSE 流式报告生成"""

import json
import logging
from flask import Blueprint, request, jsonify, Response
from ..models.decision import DecisionRepository
from ..services.report_generator import generate_report_stream
from ..utils.locale import get_locale

report_bp = Blueprint('report', __name__)
logger = logging.getLogger('lifeplanner.report')


@report_bp.route('/<int:decision_id>', methods=['GET'])
def get_report(decision_id):
    decision = DecisionRepository.get(decision_id)
    if not decision:
        return jsonify({'error': '决策不存在'}), 404
    return jsonify({'report': decision.get('recommendation', '')})


@report_bp.route('/<int:decision_id>/stream', methods=['GET'])
def stream_report(decision_id):
    locale = request.args.get('lang', get_locale())

    def generate():
        try:
            yield from generate_report_stream(decision_id)
        except GeneratorExit:
            pass  # 客户端断连，静默退出
        except Exception:
            logger.exception("SSE report stream error for decision %s", decision_id)
            yield f'data: {json.dumps({"type": "error", "content": "报告生成异常，请重试"}, ensure_ascii=False)}\n\n'

    return Response(
        generate(),
        mimetype='text/event-stream; charset=utf-8',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )
