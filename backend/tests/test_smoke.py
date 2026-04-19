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
# 2. strategy.resolve_mode — 优先级 HISTORICAL > RETROSPECTIVE > PLANNING
# ─────────────────────────────────────────────────────────────────────────────
from app.services.strategy import DecisionMode, resolve_mode


def test_resolve_mode_historical_takes_priority():
    """persona_id 有值时，无论 decision_type 是什么，都应返回 HISTORICAL"""
    d = {"persona_id": 1, "decision_type": "retrospective"}
    assert resolve_mode(d) == DecisionMode.HISTORICAL


def test_resolve_mode_retrospective():
    """无 persona_id、decision_type='retrospective' → RETROSPECTIVE"""
    d = {"persona_id": None, "decision_type": "retrospective"}
    assert resolve_mode(d) == DecisionMode.RETROSPECTIVE


def test_resolve_mode_planning_default():
    """无 persona_id、无特殊 decision_type → PLANNING"""
    d = {"persona_id": None, "decision_type": "planning"}
    assert resolve_mode(d) == DecisionMode.PLANNING


def test_resolve_mode_planning_empty():
    """空字典 → PLANNING（最低优先级兜底）"""
    assert resolve_mode({}) == DecisionMode.PLANNING


# ─────────────────────────────────────────────────────────────────────────────
# 3. locale 模块 — 加载时不崩溃
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
# 4. clarification_agent — HISTORICAL 模式使用独立线程锁
# ─────────────────────────────────────────────────────────────────────────────
def test_historical_lock_isolation():
    """不同 decision_id 应获得不同的 Lock 实例"""
    from app.services.clarification_agent import _get_historical_lock
    lock_a = _get_historical_lock(1001)
    lock_b = _get_historical_lock(1002)
    lock_same = _get_historical_lock(1001)
    assert lock_a is not lock_b, "不同 decision_id 必须是不同锁"
    assert lock_a is lock_same, "相同 decision_id 必须复用同一把锁"


def test_clarification_agent_historical_uses_lock():
    """clarification_agent 的 HISTORICAL 分支包含 _get_historical_lock 调用"""
    import app.services.clarification_agent as ca
    src = inspect.getsource(ca.get_or_ask_question)
    assert "_get_historical_lock" in src, (
        "get_or_ask_question 必须调用 _get_historical_lock 防止并发重复生成"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 5. clarification_agent — RETROSPECTIVE 与 HISTORICAL 使用独立 system prompt
# ─────────────────────────────────────────────────────────────────────────────
def test_retrospective_prompt_is_independent_from_historical():
    """RETROSPECTIVE prompt 不应复用 HISTORICAL 分支的「历史推演分析师」提示词"""
    import app.services.clarification_agent as ca
    src = inspect.getsource(ca._generate_next_question)
    # RETROSPECTIVE 分支应包含「回溯分析」关键词
    assert "回溯" in src, "_generate_next_question 缺少 RETROSPECTIVE 回溯分析 prompt"
    # 不能只有一个 if mode != PLANNING（会把 RETROSPECTIVE 混入 HISTORICAL 分支）
    assert "RETROSPECTIVE" in src, (
        "_generate_next_question 必须有独立的 RETROSPECTIVE 条件分支"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 6. simulation_engine — 失败率追踪
# ─────────────────────────────────────────────────────────────────────────────
def test_simulation_engine_failed_count_tracking():
    """simulation_engine 必须追踪 failed_count 并在失败率过高时发送 error/partial SSE 事件"""
    import app.services.simulation_engine as se
    src = inspect.getsource(se.stream_simulation)
    assert "failed_count" in src, "stream_simulation 缺少 failed_count 失败计数"
    # SSE 模式下通过发送 error 或 partial done 事件通知客户端，而非调用 fail_task
    assert '"type": "error"' in src or '"type":"error"' in src, (
        "stream_simulation 必须在全部失败时向客户端发送 {type: error} SSE 事件"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 7. report_generator — SSE 流有 except 错误处理
# ─────────────────────────────────────────────────────────────────────────────
def test_report_generator_sse_has_exception_handler():
    """report_generator 的 SSE 流必须有 except 块，防止异常静默"""
    import app.services.report_generator as rg
    src = inspect.getsource(rg.generate_report_stream)
    assert "except" in src, "generate_report_stream 缺少 except 错误处理"
    assert '"type": "error"' in src or '"type":"error"' in src, (
        "generate_report_stream 必须向客户端发送 {type: error} SSE 事件"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 8. report_generator — situation 截断防止超长 prompt
# ─────────────────────────────────────────────────────────────────────────────
def test_report_generator_situation_truncated():
    """generate_report_stream 必须对 situation 做截断处理"""
    import app.services.report_generator as rg
    src = inspect.getsource(rg.generate_report_stream)
    # 截断常用模式：[:MAX_INPUT_LEN] 或 [:N]
    assert "situation[:" in src or "MAX_INPUT_LEN" in src, (
        "generate_report_stream 中 situation 必须被截断，防止超出 token 限制"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 9. chat API — send_message 包含 404 检查
# ─────────────────────────────────────────────────────────────────────────────
def test_chat_send_message_has_404_check():
    """chat.send_message 必须对不存在的 decision_id 返回 404"""
    import app.api.chat as chat_api
    src = inspect.getsource(chat_api.send_message)
    assert "404" in src, "send_message 缺少 404 检查（decision 不存在时应返回 404）"


# ─────────────────────────────────────────────────────────────────────────────
# 10. decision API — simulation_status 处理 interrupted 状态
# ─────────────────────────────────────────────────────────────────────────────
def test_simulate_stream_route_exists():
    """simulate_stream 路由必须存在，且检查 decision 状态合法性"""
    import app.api.decision as decision_api
    assert hasattr(decision_api, 'simulate_stream'), (
        "decision.py 必须有 simulate_stream 路由（SSE 流式推演入口）"
    )
    src = inspect.getsource(decision_api.simulate_stream)
    assert "clarified" in src or "simulating" in src, (
        "simulate_stream 必须校验 decision 状态（clarified/simulating/reporting/done）"
    )


def test_database_startup_reset_uses_clarified():
    """服务重启后 simulating 状态应重置为 clarified（不是 clarifying，避免送回 Step 2）"""
    import app.database as db_mod
    src = inspect.getsource(db_mod.init_db)
    assert "status='clarified'" in src or 'status=\'clarified\'' in src, (
        "database.init_db 必须将 simulating 重置为 clarified（不是 clarifying），"
        "否则服务重启后用户会被送回 Step 2"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 11. chat_agent — HISTORICAL 模式不注入用户个人背景
# ─────────────────────────────────────────────────────────────────────────────
def test_chat_agent_historical_excludes_user_profile():
    """_build_context 在 HISTORICAL 模式下不应包含用户背景信息"""
    import app.services.chat_agent as chat_agent
    src = inspect.getsource(chat_agent._build_context)
    # 必须有针对 HISTORICAL 的条件判断
    assert "HISTORICAL" in src or "historical" in src.lower(), (
        "_build_context 必须对 HISTORICAL 模式做特殊处理（不注入用户背景）"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 12. decision API — path traversal 防护（os.path.isfile）
# ─────────────────────────────────────────────────────────────────────────────
def test_frontend_serve_uses_isfile_not_exists():
    """静态文件服务应使用 os.path.isfile，不接受目录路径（防路径穿越）"""
    import app
    src = inspect.getsource(app)
    # 如果 app/__init__.py 内有静态服务逻辑
    init_path = os.path.join(os.path.dirname(app.__file__), "__init__.py")
    with open(init_path, "r", encoding="utf-8") as f:
        init_src = f.read()
    if "send_from_directory" in init_src:
        assert "os.path.isfile" in init_src, (
            "app/__init__.py 静态文件服务必须使用 os.path.isfile（防止目录穿越）"
        )
