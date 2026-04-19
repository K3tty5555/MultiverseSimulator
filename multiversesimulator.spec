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
        'app.api.chat',
        'app.api.decision',
        'app.api.profile',
        'app.api.report',
        'app.api.settings',
        'app.models',
        'app.models.decision',
        'app.models.profile',
        'app.models.settings',
        'app.models.task',
        'app.services',
        'app.services.chat_agent',
        'app.services.clarification_agent',
        'app.services.profile_builder',
        'app.services.report_generator',
        'app.services.simulation_engine',
        'app.utils',
        'app.utils.claude_reader',
        'app.utils.file_parser',
        'app.utils.llm_client',
        'app.utils.locale',
        'app.utils.logger',
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
