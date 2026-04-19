"""配置管理"""

import os
import sys
import platform
from dotenv import load_dotenv

project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')
if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
else:
    load_dotenv(override=True)


def _resolve_data_dir() -> str:
    """解析数据目录：优先使用环境变量，其次根据运行模式自动判断。"""
    env_dir = os.environ.get('MULTIVERSESIMULATOR_DATA_DIR')
    if env_dir:
        return env_dir
    # PyInstaller 打包模式 — 使用系统用户数据目录
    if getattr(sys, 'frozen', False):
        if platform.system() == 'Darwin':
            return os.path.expanduser('~/Library/Application Support/MultiverseSimulator')
        if platform.system() == 'Windows':
            return os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'MultiverseSimulator')
        return os.path.expanduser('~/.config/MultiverseSimulator')
    # 开发模式
    return os.path.join(os.path.dirname(__file__), '../data')


_DATA_DIR = _resolve_data_dir()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'multiversesimulator-secret-key')

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # 生产环境强制校验 SECRET_KEY
        if os.environ.get('FLASK_ENV') == 'production' and \
                cls.SECRET_KEY == 'multiversesimulator-secret-key':
            raise RuntimeError("生产环境必须通过 SECRET_KEY 环境变量设置密钥，禁止使用默认值")
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    JSON_AS_ASCII = False

    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1')
    LLM_MODEL_NAME = os.environ.get('LLM_MODEL_NAME', 'gpt-4o-mini')

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(_DATA_DIR, 'uploads')
    DB_PATH = os.path.join(_DATA_DIR, 'multiversesimulator.db')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}

    CLAUDE_HOME = os.path.expanduser('~/.claude')

    SIMULATION_MAX_WORKERS = 3
    SIMULATION_TIMEOUT = 120

    REPORT_TEMPERATURE = 0.7
    CHAT_TEMPERATURE = 0.8

    @classmethod
    def validate(cls):
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY 未配置")
        return errors
