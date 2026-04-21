"""设置 API"""

from flask import Blueprint, request, jsonify
from openai import OpenAI
from ..models.settings import SettingsRepository

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('', methods=['GET'])
def get_settings():
    cfg = SettingsRepository.get_llm_config()
    api_key = cfg['api_key'] or ''
    # 脱敏：只显示前 8 位
    masked = (api_key[:8] + '****') if len(api_key) > 8 else ('****' if api_key else '')
    return jsonify({
        'configured': SettingsRepository.is_configured(),
        'llm_api_key': masked,
        'llm_base_url': cfg['base_url'] or '',
        'llm_model_name': cfg['model'] or '',
    })


@settings_bp.route('', methods=['PUT'])
def update_settings():
    data = request.get_json() or {}
    if 'llm_api_key' in data and data['llm_api_key'] and '****' not in data['llm_api_key']:
        SettingsRepository.set('llm_api_key', data['llm_api_key'].strip())
    if 'llm_base_url' in data:
        SettingsRepository.set('llm_base_url', data['llm_base_url'].strip())
    if 'llm_model_name' in data:
        SettingsRepository.set('llm_model_name', data['llm_model_name'].strip())
    return jsonify({'success': True, 'configured': SettingsRepository.is_configured()})


@settings_bp.route('/test', methods=['POST'])
def test_connection():
    """测试 LLM 连接是否可用"""
    data = request.get_json() or {}
    api_key = (data.get('llm_api_key') or '').strip()
    base_url = (data.get('llm_base_url') or '').strip()
    model = (data.get('llm_model_name') or '').strip()

    if not api_key or '****' in api_key:
        # 用已保存的 key
        cfg = SettingsRepository.get_llm_config()
        api_key = cfg['api_key']
        base_url = base_url or cfg['base_url']
        model = model or cfg['model']

    if not api_key:
        return jsonify({'success': False, 'error': '未填写 API Key'}), 400

    try:
        client = OpenAI(api_key=api_key, base_url=base_url or None, timeout=15)
        resp = client.chat.completions.create(
            model=model or 'gpt-4o-mini',
            messages=[{'role': 'user', 'content': '回复"ok"'}],
            max_tokens=10,
        )
        reply = resp.choices[0].message.content or ''
        return jsonify({'success': True, 'reply': reply.strip()})
    except Exception as e:
        # 只返回通用错误，避免泄露 API Key 或请求细节
        import logging
        logging.getLogger('lifeplanner').warning(f"LLM 连接测试失败: {e}")
        msg = str(e)
        # 脱敏：移除可能含 key 的部分
        if api_key and api_key in msg:
            msg = msg.replace(api_key, '***')
        return jsonify({'success': False, 'error': msg[:200]}), 400
