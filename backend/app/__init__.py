"""人生规划器 Backend - Flask 应用工厂"""

import os
import sys
from flask import Flask, request, send_from_directory
from flask_cors import CORS


def _get_frontend_dist() -> str | None:
    """定位前端 dist 目录（兼容 PyInstaller 打包和开发模式）。"""
    # PyInstaller onefile: sys._MEIPASS 为解压临时目录
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'frontend')
    # 开发 / 部署模式：相对路径
    dev_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../frontend/dist'))
    return dev_path if os.path.isdir(dev_path) else None

from .config import Config
from .utils.logger import setup_logger, get_logger
from .database import init_db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False

    logger = setup_logger('lifeplanner')

    is_reloader = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log = not debug_mode or is_reloader

    if should_log:
        logger.info("=" * 50)
        logger.info("人生规划器 Backend 启动中...")
        logger.info("=" * 50)

    # 确保数据目录存在
    os.makedirs(os.path.dirname(config_class.DB_PATH), exist_ok=True)
    os.makedirs(config_class.UPLOAD_FOLDER, exist_ok=True)

    # 初始化数据库
    init_db(config_class.DB_PATH)
    if should_log:
        logger.info("数据库初始化完成")

    allowed_origins = os.environ.get(
        'ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:3001'
    ).split(',')
    CORS(app, resources={r"/api/*": {"origins": [o.strip() for o in allowed_origins]}})

    # 速率限制：防止 API 滥用
    from .extensions import limiter
    limiter.init_app(app)

    @app.before_request
    def log_request():
        get_logger('lifeplanner.request').debug(f"{request.method} {request.path}")

    @app.after_request
    def log_response(response):
        get_logger('lifeplanner.request').debug(f"→ {response.status_code}")
        return response

    from flask import jsonify as _jsonify

    @app.errorhandler(500)
    def internal_error(e):
        get_logger('lifeplanner').error(f"未处理的 500 错误: {e}")
        return _jsonify({'error': '服务器内部错误，请稍后重试'}), 500

    @app.errorhandler(415)
    def unsupported_media(e):
        return _jsonify({'error': '请求格式错误，请使用 JSON'}), 415

    from .api import profile_bp, settings_bp, universe_bp, world_bp
    app.register_blueprint(profile_bp, url_prefix='/api/profile')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(universe_bp, url_prefix='/api/universe')
    app.register_blueprint(world_bp, url_prefix='/api/worlds')

    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': '人生规划器 Backend'}

    # 服务前端静态文件（生产模式 / Electron 打包）
    frontend_dist = _get_frontend_dist()
    if frontend_dist:
        if should_log:
            logger.info(f"服务前端静态文件：{frontend_dist}")

        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def serve_frontend(path):
            if path:
                # 防止路径穿越：确保目标路径仍在 frontend_dist 下
                safe_path = os.path.normpath(os.path.join(frontend_dist, path))
                if safe_path.startswith(os.path.normpath(frontend_dist) + os.sep) \
                        and os.path.isfile(safe_path):
                    return send_from_directory(frontend_dist, path)
            return send_from_directory(frontend_dist, 'index.html')

    if should_log:
        logger.info("人生规划器 Backend 启动完成")

    return app
