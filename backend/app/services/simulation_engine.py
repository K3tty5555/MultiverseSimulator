"""多路径模拟引擎 - Step 3"""

import json
import queue
import threading
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Generator, List
from ..models.profile import ProfileRepository
from ..models.decision import DecisionRepository
from ..utils.llm_client import LLMClient
from ..utils.locale import get_language_instruction, set_locale
from ..utils.persona_context import build_persona_context
from .strategy import resolve_mode, DecisionMode

logger = logging.getLogger('lifeplanner.simulation')

# 取消令牌：新 SSE 连接建立时通知旧连接的 worker 停止写入 DB
_active_stop_events: Dict[int, threading.Event] = {}
_active_stop_events_lock = threading.Lock()

DIMENSIONS = ['career', 'finance', 'relationships', 'wellbeing']
TIME_HORIZONS = ['short_term', 'mid_term', 'long_term']

DIMENSION_LABELS_ZH = {
    'career': '事业发展',
    'finance': '财务影响',
    'relationships': '人际关系',
    'wellbeing': '身心健康'
}

TIME_LABELS_ZH = {
    'short_term': '短期（1年内）',
    'mid_term': '中期（3-5年）',
    'long_term': '长期（10年以上）'
}

MAX_INPUT_LEN = 5000  # 情境/选项最大字符数


def simulate_option(
    option: Dict,
    situation: str,
    clarification_context: str,
    profile_summary: str,
    locale: str,
    mode: DecisionMode = DecisionMode.PLANNING,
    is_actual_choice: bool = False,
    actual_outcome: str = '',
    time_period: str = '',
    persona_context: str = ''
) -> List[Dict]:
    """对单个选项进行 LLM 推演，返回 4x3 个结果"""
    set_locale(locale)
    lang = get_language_instruction()
    llm = LLMClient(timeout=120)

    dim_list = '\n'.join([f"- {DIMENSION_LABELS_ZH[d]}（{d}）" for d in DIMENSIONS])
    time_list = '\n'.join([f"- {TIME_LABELS_ZH[t]}（{t}）" for t in TIME_HORIZONS])

    if mode == DecisionMode.RETROSPECTIVE:
        time_label = f"（发生于{time_period}）" if time_period else ''
        if is_actual_choice:
            system_content = f"""你是一位擅长回溯分析的人生顾问，帮助用户深刻理解自己过去做出的选择及其影响。
请基于用户提供的实际结果，对该选择在各维度上的影响进行结构化分析。
分析要有深度，挖掘表面结果背后的深层影响，每个单元格给出 50-100 字。
{lang}{persona_context}"""
            option_context = f"""【这是用户实际选择的路径】
已知实际结果：
{actual_outcome[:1000] if actual_outcome else '（未提供具体结果）'}

请基于已知结果，对该选择在以下维度的影响进行深化分析："""
        else:
            system_content = f"""你是一位擅长历史假设推演的分析师，专注于「如果当初选择不同……」的思想实验。
你的任务是推演：如果当时走了这条路，会发生什么？
推演要合乎情理、有因果依据，允许有一定的叙事感。每个单元格给出 50-100 字。
{lang}{persona_context}"""
            option_context = f"""【这是用户当时未选择的路径】
用户实际选择后的结果：{actual_outcome[:500] if actual_outcome else '（未提供）'}

请推演：如果用户当时选择了这条路，情况会如何不同？"""

        clarification_section = f"\n澄清信息：\n{clarification_context[:2000]}" if clarification_context else ''
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": f"""用户背景：
{profile_summary[:1500] if profile_summary else '未提供'}

决策情境{time_label}：
{situation[:MAX_INPUT_LEN]}{clarification_section}

{option_context}

选项：
{option['label'][:200]}
{option.get('description', '')[:500]}

推演维度：
{dim_list}

时间段（相对于决策发生时）：
{time_list}

返回格式（JSON）：
{{
  "results": [
    {{
      "dimension": "career",
      "time_horizon": "short_term",
      "content": "具体描述...",
      "score": 7.5
    }},
    ... （共12个，4维度×3时间段）
  ]
}}"""}
        ]
    elif mode == DecisionMode.HISTORICAL:
        system_content = f"""你是一位专业的架空历史推演分析师，专注于「如果历史人物做出不同选择，历史将如何演变」的思想实验。
请根据历史背景、决策情境和具体选项，对以下4个维度 × 3个时间段进行推演分析。
每个单元格给出 50-100 字的具体描述，要有历史依据、符合时代约束，具有叙事感。
{lang}{persona_context}"""
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": f"""决策情境：
{situation[:MAX_INPUT_LEN]}

澄清信息：
{clarification_context[:2000] if clarification_context else '无'}

需要推演的选项：
{option['label'][:200]}
{option.get('description', '')[:500]}

请对以下维度和时间段进行推演：
维度：
{dim_list}

时间段：
{time_list}

返回格式（JSON）：
{{
  "results": [
    {{
      "dimension": "career",
      "time_horizon": "short_term",
      "content": "具体描述...",
      "score": 7.5
    }},
    ... （共12个，4维度×3时间段）
  ]
}}"""}
        ]
    else:  # PLANNING
        system_content = f"""你是一位专业的人生规划顾问，负责对人生决策选项进行系统性推演。
请根据用户背景、决策情境和具体选项，对以下4个维度 × 3个时间段进行预测分析。
每个单元格给出 50-100 字的具体描述，要有依据、贴近现实，避免空话。
{lang}"""
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": f"""用户背景：
{profile_summary[:1500] if profile_summary else '未提供'}

决策情境：
{situation[:MAX_INPUT_LEN]}

澄清信息：
{clarification_context[:2000] if clarification_context else '无'}

需要推演的选项：
{option['label'][:200]}
{option.get('description', '')[:500]}

请对以下维度和时间段进行推演：
维度：
{dim_list}

时间段：
{time_list}

返回格式（JSON）：
{{
  "results": [
    {{
      "dimension": "career",
      "time_horizon": "short_term",
      "content": "具体描述...",
      "score": 7.5
    }},
    ... （共12个，4维度×3时间段）
  ]
}}"""}
        ]

    response = llm.chat_json(messages=messages, temperature=0.6, max_tokens=3000)

    results = []
    for item in response.get('results', []):
        dim = item.get('dimension')
        th = item.get('time_horizon')
        if dim not in DIMENSIONS or th not in TIME_HORIZONS:
            logger.warning(f"LLM 返回了非法的 dimension/time_horizon: {dim}/{th}，已跳过")
            continue
        results.append({
            'option_id': option['id'],
            'dimension': dim,
            'time_horizon': th,
            'content': item.get('content', ''),
            'score': item.get('score')
        })
    return results


def stream_simulation(decision_id: int, locale: str = 'zh') -> Generator[str, None, None]:
    """SSE 生成器：并发推演所有未完成选项，每个选项完成即时推送并持久化。
    支持断线重连：已完成选项通过 replay 事件回放，未完成的继续推演。
    心跳：queue.get(timeout=15) 超时时自动发送 SSE comment 保活连接。
    GeneratorExit（客户端断线）：finally 块设置 stop_event，确保 worker 线程停止写 DB。"""
    set_locale(locale)

    decision = DecisionRepository.get(decision_id)
    if not decision:
        yield f'data: {json.dumps({"type": "error", "message": "决策不存在"}, ensure_ascii=False)}\n\n'
        return

    options = decision.get('options', [])
    total = len(options)
    if not options:
        yield f'data: {json.dumps({"type": "error", "message": "没有可用的选项"}, ensure_ascii=False)}\n\n'
        return

    # ── 1. 恢复已完成结果（断线重连时回放）──────────────────────
    completed_ids = set(DecisionRepository.get_completed_option_ids(decision_id))
    pending_options = [o for o in options if o['id'] not in completed_ids]

    completed_count = 0
    existing_results = decision.get('simulation_results', [])
    for opt in options:
        if opt['id'] in completed_ids:
            completed_count += 1
            opt_results = [r for r in existing_results if r['option_id'] == opt['id']]
            yield f'data: {json.dumps({"type": "replay", "option_id": opt["id"], "option_label": opt["label"], "results": opt_results, "completed": completed_count, "total": total}, ensure_ascii=False)}\n\n'

    # ── 2. 全部已完成：立即结束 ──────────────────────────────
    if not pending_options:
        if decision.get('status') not in ('reporting', 'done'):
            DecisionRepository.update_status(decision_id, 'reporting')
        yield f'data: {json.dumps({"type": "done"}, ensure_ascii=False)}\n\n'
        return

    # ── 3. 注册取消令牌，通知旧连接的 worker 停止 ─────────────
    stop_event = threading.Event()
    with _active_stop_events_lock:
        old_event = _active_stop_events.get(decision_id)
        if old_event:
            old_event.set()
        _active_stop_events[decision_id] = stop_event

    try:
        # ── 4. 准备推演上下文 ────────────────────────────────────
        mode = resolve_mode(decision)
        if mode == DecisionMode.HISTORICAL:
            profile_summary = ''
        else:
            profile = ProfileRepository.get()
            profile_summary = profile.get('summary', '') if profile else ''

        qa_list = decision.get('clarification_qa') or []
        clarification_context = '\n'.join(
            [f"Q: {qa['question']}\nA: {qa['answer']}" for qa in qa_list]
        )
        actual_choice_id = decision.get('actual_choice_id')
        actual_outcome = decision.get('actual_outcome') or ''
        time_period = decision.get('time_period') or ''
        persona_context = build_persona_context(decision) if mode == DecisionMode.HISTORICAL else ''

        DecisionRepository.update_status(decision_id, 'simulating')

        # ── 5. 启动线程池（非阻塞，不等待所有 Future 完成）──────────
        result_queue: queue.Queue = queue.Queue()

        def worker(opt: Dict):
            if stop_event.is_set():
                result_queue.put((opt, None, 'cancelled'))
                return
            try:
                is_actual = mode == DecisionMode.RETROSPECTIVE and opt['id'] == actual_choice_id
                results = simulate_option(
                    opt,
                    decision['situation'],
                    clarification_context,
                    profile_summary,
                    locale,
                    mode,
                    is_actual,
                    actual_outcome,
                    time_period,
                    persona_context,
                )
                if stop_event.is_set():
                    result_queue.put((opt, None, 'cancelled'))
                    return
                if results:
                    DecisionRepository.upsert_option_results(decision_id, opt['id'], results)
                result_queue.put((opt, results or None, 'ok'))
            except Exception as e:
                logger.exception(f"选项推演失败 [{opt.get('label', '')}]: {e}")
                result_queue.put((opt, None, str(e)))

        executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix=f'sim-{decision_id}')
        for opt in pending_options:
            executor.submit(worker, opt)
        executor.shutdown(wait=False)  # 不阻塞 SSE 生成器线程

        # 立即刷新 HTTP 响应头——不发此注释 headers 会等到第一个真实事件（最多 15s）才到达
        yield ': sim-start\n\n'

        # ── 6. SSE 消费循环（queue.get timeout=15 自动产生心跳）──────
        received = 0
        failed_count = 0
        pending_total = len(pending_options)
        MAX_TOTAL_SECONDS = 20 * 60  # 整体最长等待 20 分钟，防止 LLM 无响应时永久挂起
        deadline = time.monotonic() + MAX_TOTAL_SECONDS

        while received < pending_total:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                logger.error(f"推演总超时（>{MAX_TOTAL_SECONDS}s），已收到 {received}/{pending_total}")
                yield f'data: {json.dumps({"type": "error", "message": "推演超时，请检查 API 配置后重试"}, ensure_ascii=False)}\n\n'
                return
            try:
                opt, results, status = result_queue.get(timeout=min(15.0, remaining))
                received += 1
                if status == 'ok':
                    if results:
                        completed_count += 1
                        yield f'data: {json.dumps({"type": "option_done", "option_id": opt["id"], "option_label": opt["label"], "results": results, "completed": completed_count, "total": total}, ensure_ascii=False)}\n\n'
                    else:
                        logger.warning(f"选项推演返回空结果 [{opt.get('label', '')}]")
                        failed_count += 1
                elif status == 'cancelled':
                    # 被新连接抢占，退出循环（stop_event 已由新连接设置）
                    break
                else:
                    failed_count += 1
            except queue.Empty:
                # 15 秒无结果，发送心跳保持连接
                yield ': heartbeat\n\n'

        # ── 7. 发送最终事件（仅在未被抢占时）────────────────────
        if not stop_event.is_set():
            if completed_count == 0 and total > 0:
                DecisionRepository.update_status(decision_id, 'clarified')
                yield f'data: {json.dumps({"type": "error", "message": "所有选项推演均失败，请检查 API 配置后重试"}, ensure_ascii=False)}\n\n'
            elif failed_count > 0 and failed_count >= (total + 1) // 2:
                # 过半失败（相对于总选项数），结果质量不可信
                logger.warning(f"推演失败率过高：{failed_count}/{total}")
                DecisionRepository.update_status(decision_id, 'reporting')
                yield f'data: {json.dumps({"type": "done", "partial": True}, ensure_ascii=False)}\n\n'
            else:
                if failed_count > 0:
                    logger.warning(f"推演部分失败：{failed_count}/{total} 个选项")
                DecisionRepository.update_status(decision_id, 'reporting')
                yield f'data: {json.dumps({"type": "done"}, ensure_ascii=False)}\n\n'

    finally:
        # 无论何种退出（正常完成、被抢占、客户端断线 GeneratorExit），均通知 worker 停止
        stop_event.set()
        with _active_stop_events_lock:
            if _active_stop_events.get(decision_id) is stop_event:
                del _active_stop_events[decision_id]
