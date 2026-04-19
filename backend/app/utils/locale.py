"""多语言支持"""

import json
import os
import threading
from flask import request, has_request_context

_thread_local = threading.local()
_locales_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'locales')

_languages: dict = {}
_translations: dict = {}


def _load_locales() -> None:
    """加载翻译文件；失败时降级为空中文翻译，不阻塞应用启动。"""
    global _languages, _translations
    try:
        with open(os.path.join(_locales_dir, 'languages.json'), 'r', encoding='utf-8') as f:
            _languages = json.load(f)
        for filename in os.listdir(_locales_dir):
            if filename.endswith('.json') and filename != 'languages.json':
                locale_name = filename[:-5]
                with open(os.path.join(_locales_dir, filename), 'r', encoding='utf-8') as f:
                    _translations[locale_name] = json.load(f)
    except Exception as exc:
        import logging as _logging
        _logging.getLogger('lifeplanner.locale').warning(
            "locale 文件加载失败，使用默认中文降级: %s", exc
        )
        _languages = {'zh': {'llmInstruction': '请使用中文回答。'}}
        _translations = {'zh': {}}


_load_locales()


def set_locale(locale: str):
    _thread_local.locale = locale


def get_locale() -> str:
    if has_request_context():
        raw = request.headers.get('Accept-Language', 'zh')
        return raw if raw in _translations else 'zh'
    return getattr(_thread_local, 'locale', 'zh')


def t(key: str, **kwargs) -> str:
    locale = get_locale()
    messages = _translations.get(locale, _translations.get('zh', {}))
    value = messages
    for part in key.split('.'):
        value = value.get(part) if isinstance(value, dict) else None
        if value is None:
            break
    if value is None:
        value = _translations.get('zh', {})
        for part in key.split('.'):
            value = value.get(part) if isinstance(value, dict) else None
            if value is None:
                break
    if value is None:
        return key
    if kwargs:
        for k, v in kwargs.items():
            value = value.replace(f'{{{k}}}', str(v))
    return value


def get_language_instruction() -> str:
    locale = get_locale()
    lang_config = _languages.get(locale, _languages.get('zh', {}))
    return lang_config.get('llmInstruction', '请使用中文回答。')
