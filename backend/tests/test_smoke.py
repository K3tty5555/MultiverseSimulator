"""
冒烟测试套件 — 无 LLM 依赖，纯逻辑 + 源码结构验证
在 backend/ 目录下执行：pytest tests/test_smoke.py -v
"""
import ast
import inspect
import sys
import os

# 确保 backend/ 在 sys.path 中（pyproject.toml 已配置 pythonpath）
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ─────────────────────────────────────────────────────────────────────────────
# 1. Python 语法检查 — 全部后端模块
# ─────────────────────────────────────────────────────────────────────────────
import glob

BACKEND_ROOT = os.path.dirname(os.path.dirname(__file__))
PYTHON_FILES = glob.glob(os.path.join(BACKEND_ROOT, "app", "**", "*.py"), recursive=True)


def test_python_syntax_all_files():
    """所有后端 .py 文件均能被 ast.parse，无语法错误"""
    errors = []
    for path in PYTHON_FILES:
        rel = os.path.relpath(path, BACKEND_ROOT)
        try:
            with open(path, "r", encoding="utf-8") as f:
                source = f.read()
            ast.parse(source, filename=path)
        except SyntaxError as e:
            errors.append(f"{rel}: {e}")
    assert not errors, "语法错误：\n" + "\n".join(errors)


# ─────────────────────────────────────────────────────────────────────────────
# 2. locale 模块 — 加载时不崩溃
# ─────────────────────────────────────────────────────────────────────────────
def test_locale_loads_without_crash():
    """locale 模块可以安全导入，即使文件缺失也不抛异常"""
    import importlib
    try:
        import app.utils.locale as loc_mod
        importlib.reload(loc_mod)
    except Exception as e:
        raise AssertionError(f"locale 模块加载崩溃: {e}")


def test_locale_get_instruction_returns_string():
    """get_language_instruction 始终返回字符串（不返回 None）"""
    from app.utils.locale import get_language_instruction
    result = get_language_instruction()
    assert isinstance(result, str)


# ─────────────────────────────────────────────────────────────────────────────
# 3. 前端静态服务 — path traversal 防护（os.path.isfile）
# ─────────────────────────────────────────────────────────────────────────────
def test_frontend_serve_uses_isfile_not_exists():
    """静态文件服务应使用 os.path.isfile，不接受目录路径（防路径穿越）"""
    import app
    init_path = os.path.join(os.path.dirname(app.__file__), "__init__.py")
    with open(init_path, "r", encoding="utf-8") as f:
        init_src = f.read()
    if "send_from_directory" in init_src:
        assert "os.path.isfile" in init_src, (
            "app/__init__.py 静态文件服务必须使用 os.path.isfile（防止目录穿越）"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 4. Blueprint 注册 — 核心路由蓝图完整
# ─────────────────────────────────────────────────────────────────────────────
def test_all_blueprints_registered():
    """app/__init__.py 必须注册所有存活蓝图（profile/settings/universe/world）"""
    import app
    init_path = os.path.join(os.path.dirname(app.__file__), "__init__.py")
    with open(init_path, "r", encoding="utf-8") as f:
        init_src = f.read()
    for bp in ['profile_bp', 'settings_bp', 'universe_bp', 'world_bp']:
        assert bp in init_src, f"蓝图 {bp} 未在 app/__init__.py 中注册"


# ─────────────────────────────────────────────────────────────────────────────
# 5. safe_json_loads — 统一 JSON 解析入口
# ─────────────────────────────────────────────────────────────────────────────
def test_safe_json_loads_returns_none_on_invalid():
    """safe_json_loads 对无效 JSON 返回 None（不抛异常）"""
    from app.utils.safe_json import safe_json_loads
    assert safe_json_loads("") is None
    assert safe_json_loads("not json") is None
    assert safe_json_loads("{invalid") is None
    assert safe_json_loads('{"ok": 1}') == {"ok": 1}
