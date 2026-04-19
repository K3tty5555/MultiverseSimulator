"""JSON 解析容错工具"""

import json
import logging

logger = logging.getLogger('lifeplanner.safe_json')


def safe_json_loads(data, default=None, label: str = ''):
    """安全解析 JSON 字符串，失败时返回 default 并记录日志。

    Args:
        data: 待解析的字符串或 None
        default: 解析失败时的默认值（通常为 [] 或 {}）
        label: 日志中标识字段来源，便于排查
    """
    if not data:
        return default
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(
            "JSON 解析失败 [%s]: %s | data[:100]=%r",
            label, e, str(data)[:100]
        )
        return default
