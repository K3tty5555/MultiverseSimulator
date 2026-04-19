"""Flask 扩展单例（在 create_app 中通过 init_app 初始化）"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["300/day", "60/hour"],
    storage_uri="memory://",
)
