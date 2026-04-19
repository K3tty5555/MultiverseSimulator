"""深度交互对话服务 - Step 5，SSE 流式输出"""

import json
from typing import Generator
from ..models.profile import ProfileRepository
from ..models.decision import DecisionRepository, ChatRepository
from ..utils.llm_client import LLMClient
from ..utils.locale import get_language_instruction
from ..utils.persona_context import build_persona_context
from .strategy import resolve_mode, DecisionMode


def _build_context(decision: dict, profile_summary: str, mode: 'DecisionMode' = None) -> str:
    from .strategy import DecisionMode as _DM
    situation = decision['situation']
    options_text = '\n'.join(f"- {o['label']}" for o in decision.get('options', []))
    recommendation = decision.get('recommendation', '')
    ctx = f"""决策情境：{situation}

选项：
{options_text}

推演建议摘要：
{recommendation[:1000] if recommendation else '尚未生成'}"""
    # HISTORICAL 模式使用历史人物视角，不注入用户个人背景
    if mode != _DM.HISTORICAL:
        ctx += f"""

用户背景：
{profile_summary[:800] if profile_summary else '未提供'}"""
    return ctx


def stream_chat_response(decision_id: int) -> Generator[str, None, None]:
    """SSE 流式回复用户最新问题"""
    decision = DecisionRepository.get(decision_id)
    if not decision:
        yield f'data: {json.dumps({"type": "error", "content": "决策不存在"}, ensure_ascii=False)}\n\n'
        return

    mode = resolve_mode(decision)
    # HISTORICAL 模式不使用用户档案
    if mode == DecisionMode.HISTORICAL:
        profile_summary = ''
    else:
        profile = ProfileRepository.get()
        profile_summary = profile.get('summary', '') if profile else ''

    context = _build_context(decision, profile_summary, mode)
    lang = get_language_instruction()

    # 获取对话历史
    history = ChatRepository.get_messages(decision_id, 'interaction')
    if mode == DecisionMode.HISTORICAL:
        persona_context = build_persona_context(decision)
        system_prompt = f"""你是一位专业的架空历史推演分析师，刚刚完成了一次历史平行宇宙推演。
用户正在与你探讨推演结果：各选项下历史人物的不同命运走向、关键转折点与历史影响。
回答要有历史依据、有叙事感，以现代分析语言陈述，不要以历史人物第一人称发言。
{lang}{persona_context}

本次推演上下文：
{context}"""
    elif mode == DecisionMode.RETROSPECTIVE:
        system_prompt = f"""你是一位擅长回溯分析的人生顾问，正在帮助用户深入理解一个过去决策的推演结果。
用户当时面临的情境已经过去，你的角色是帮助他们从历史选择中汲取洞见与智慧。
回答要有温度、有洞察，引用推演数据来支持观点，避免说教。
{lang}

本次回溯上下文：
{context}"""
    else:  # PLANNING
        system_prompt = f"""你是一位专业的人生规划顾问，正在帮助用户深入理解一个重要决策的推演结果。
你了解用户的背景和决策情境，可以回答关于推演结果、选项比较、风险分析等方面的问题。
回答要具体、有见地，引用推演数据来支持你的观点。
{lang}

当前决策上下文：
{context}"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    # 加入历史对话（最近20条）
    for msg in history[-20:]:
        messages.append({
            "role": msg['role'],
            "content": msg['content']
        })

    full_content = ''
    llm = LLMClient(timeout=120)
    for delta in llm.stream(messages, temperature=0.8, max_tokens=1000):
        full_content += delta
        yield f'data: {json.dumps({"type": "delta", "content": delta}, ensure_ascii=False)}\n\n'

    # Save assistant response
    ChatRepository.add_message(decision_id, 'interaction', 'assistant', full_content)
    yield f'data: {json.dumps({"type": "done"}, ensure_ascii=False)}\n\n'
