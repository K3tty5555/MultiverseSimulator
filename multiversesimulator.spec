# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for 多元宇宙模拟器 backend
# 运行方式：cd MultiverseSimulator && pyinstaller multiversesimulator.spec --clean

import sys
import os

block_cipher = None

a = Analysis(
    ['backend/run.py'],
    pathex=[os.path.abspath('backend')],
    binaries=[],
    datas=[
        # 将构建好的前端静态文件打入包中
        ('frontend/dist', 'frontend'),
        # 国际化文件
        ('locales', 'locales'),
    ],
    hiddenimports=[
        # Flask 应用模块
        'app',
        'app.api',
        'app.api.persona',
        'app.api.profile',
        'app.api.settings',
        'app.api.universe',
        'app.api.world',
        'app.models',
        'app.models.canonical_event',
        'app.models.persona',
        'app.models.profile',
        'app.models.settings',
        'app.models.task',
        'app.models.universe',
        'app.services',
        'app.services.agent_factory',
        'app.services.npc_preloader',
        'app.services.personal_universe_init',
        'app.services.profile_builder',
        'app.services.universe_engine',
        'app.utils',
        'app.utils.ai_assist',
        'app.utils.claude_reader',
        'app.utils.file_parser',
        'app.utils.llm_client',
        'app.utils.locale',
        'app.utils.logger',
        'app.utils.persona_context',
        'app.utils.safe_json',
        # 第三方库
        'flask',
        'flask_cors',
        'openai',
        'fitz',          # PyMuPDF
        'dotenv',
        'python_dotenv',
        'charset_normalizer',
        'sqlalchemy',
        'werkzeug',
        'werkzeug.utils',
        'werkzeug.serving',
        'click',
        'jinja2',
        'itsdangerous',
        'httpx',
        'httpcore',
        'anyio',
        'sniffio',
        'certifi',
        'idna',
        'h11',
        'distutils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='multiversesimulator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,          # 可替换为 'build/icons/icon.icns'
)
