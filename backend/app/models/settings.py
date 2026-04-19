"""设置存储 - LLM 配置持久化"""

from datetime import datetime, timezone
from ..database import get_db
from ..config import Config


def _now():
    return datetime.now(timezone.utc).isoformat()


class SettingsRepository:
    @staticmethod
    def get(key: str, default=None):
        with get_db() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
            return row['value'] if row else default

    @staticmethod
    def set(key: str, value: str):
        with get_db() as conn:
            conn.execute(
                """INSERT INTO settings (key, value, updated_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
                (key, value, _now())
            )
            conn.commit()

    @staticmethod
    def get_llm_config() -> dict:
        """读取 LLM 配置，DB 优先，fallback 到 .env"""
        return {
            'api_key': SettingsRepository.get('llm_api_key') or Config.LLM_API_KEY,
            'base_url': SettingsRepository.get('llm_base_url') or Config.LLM_BASE_URL,
            'model': SettingsRepository.get('llm_model_name') or Config.LLM_MODEL_NAME,
        }

    @staticmethod
    def is_configured() -> bool:
        key = SettingsRepository.get('llm_api_key') or Config.LLM_API_KEY
        return bool(key and key not in ('your_api_key_here', 'placeholder', ''))
