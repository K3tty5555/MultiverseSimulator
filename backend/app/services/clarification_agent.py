"""AI 澄清追问服务 - Step 2"""

import json
import threading
from typing import Dict, List, Optional, Tuple
from ..models.profile import ProfileRepository
from ..models.decision import DecisionRepository, ChatRepository
from ..utils.llm_client import LLMClient
from ..utils.locale import get_language_instruction
from .strategy import resolve_mode, DecisionMode

MAX_QUESTIONS = 5

# 防止 HISTORICAL 模式并发重复生成摘要
_historical_locks: Dict[int, threading.Lock] = {}
_historical_locks_mutex = threading.Lock()


def _get_historical_lock(decision_id: int) -> threading.Lock:
    with _historical_locks_mutex:
        if decision_id not in _historical_locks:
            _historical_locks[decision_id] = threading.Lock()
        return _historical_locks[decision_id]


def get_or_ask_question(decision_id: int, user_answer: Optional[str]) -> Tuple[Optional[str], bool]:
    """
    处理澄清对话逻辑。
    - user_answer=None 表示第一次请求（生成第一个问题）
    - 返回 (summary_or_question, all_answered)
    - HISTORICAL 模式：首次调用自动生成历史背景研究摘要，直接返回 (summary, True)
    """
    decision = DecisionRepository.get(decision_id)
    if not decision:
        raise ValueError("决策不存在")

    mode = resolve_mode(decision)

    # ── HISTORICAL 自研模式 ────────────────────────────────────────────────
    if mode == DecisionMode.HISTORICAL:
        lock = _get_historical_lock(decision_id)
        with lock:
            # 加锁后重新读取，防止并发重复生成
            decision = DecisionRepository.get(decision_id)
            qa_list = decision.get('clarification_qa') or []
            if qa_list:
                return None, True
            # 首次：AI 自主研究历史背景，不向用户追问
            summary = _generate_historical_summary(decision)
            DecisionRepository.update_clarification_qa(
                decision_id, [{'question': '历史背景研究', 'answer': summary}]
            )
            ChatRepository.add_message(
                decision_id, 'clarification', 'assistant', summary,
                metadata={'type': 'summary', 'all_answered': True}
            )
            return summary, True

    # ── PLANNING / RETROSPECTIVE 追问模式 ──────────────────────────────────
    if mode == DecisionMode.HISTORICAL:
        profile_summary = ''  # unreachable, but keeps linter happy
    else:
        profile = ProfileRepository.get()
        profile_summary = profile.get('summary', '') if profile else ''

    qa_list = decision.get('clarification_qa') or []

    # 如果有用户回答，保存到 QA 列表
    if user_answer is not None:
        msgs = ChatRepository.get_messages(decision_id, 'clarification')
        last_question = ''
        for m in reversed(msgs):
            if m['role'] == 'assistant':
                last_question = m['content']
                break
        qa_list.append({'question': last_question, 'answer': user_answer})
        DecisionRepository.update_clarification_qa(decision_id, qa_list)
        ChatRepository.add_message(decision_id, 'clarification', 'user', user_answer)

    # 判断是否已收集足够信息
    if len(qa_list) >= MAX_QUESTIONS:
        return None, True

    # 生成下一个问题
    question = _generate_next_question(decision, profile_summary, qa_list)
    if question is None:
        return None, True

    ChatRepository.add_message(decision_id, 'clarification', 'assistant', question)
    return question, False


def _generate_historical_summary(decision: Dict) -> str:
    """HISTORICAL 模式专用：AI 自主研究历史背景，返回结构化摘要文本。"""
    lang = get_language_instruction()
    situation = decision['situation']
    options = [o['label'] for o in decision.get('options', [])]
    options_text = '\n'.join(f"- {o}" for o in options)

    llm = LLMClient(timeout=120)
    content = llm.chat(
        messages=[
            {
                "role": "system",
                "content": f"""你是一位专业的架空历史推演分析师。
在开始推演之前，请先对本次决策节点进行历史背景研究，整合你所掌握的历史知识。
输出一段结构清晰的历史背景摘要，涵盖：当时的整体局势与各方力量、决策人所受的约束与压力、各选项可能触发的关键历史变量。
不要以第一人称（历史人物视角）叙述，用现代历史分析语言。字数控制在 300-500 字。
{lang}"""
            },
            {
                "role": "user",
                "content": f"""历史决策情境：
{situation}

可选路径：
{options_text}

请输出历史背景研究摘要。"""
            }
        ],
        temperature=0.5,
        max_tokens=800
    )
    return content


def _build_top_values_text(profile: Optional[Dict]) -> str:
    """从档案中提取价值观权重，返回 top 5 格式文本，无数据则返回空字符串。"""
    if not profile:
        return ''
    values = profile.get('structured', {}).get('values', {})
    if not values:
        return ''
    sorted_values = sorted(values.items(), key=lambda x: x[1], reverse=True)[:5]
    label_map = {
        'career': '事业发展', 'finance': '财务安全',
        'relationships': '人际关系', 'wellbeing': '身心健康', 'freedom': '自由度'
    }
    parts = [f"{label_map.get(k, k)}({v}/10)" for k, v in sorted_values]
    return '、'.join(parts)


def _generate_next_question(decision: Dict, profile_summary: str, qa_list: List[Dict]) -> Optional[str]:
    lang = get_language_instruction()
    situation = decision['situation']
    options = [o['label'] for o in decision.get('options', [])]
    options_text = '\n'.join(f"- {o}" for o in options)
    mode = resolve_mode(decision)

    # 获取价值观权重文本
    profile = ProfileRepository.get()
    top_values_text = _build_top_values_text(profile)

    qa_text = ''
    if qa_list:
        qa_text = '\n'.join([f"Q: {qa['question']}\nA: {qa['answer']}" for qa in qa_list])

    values_hint = f"\n用户最看重的价值维度（权重高到低）：{top_values_text}" if top_values_text else ''

    if mode == DecisionMode.RETROSPECTIVE:
        system_prompt = f"""你是一位擅长回溯分析的人生顾问，正在帮助用户重建一个过去决策的情境。
你需要通过追问，了解当时的时代背景、用户的处境、内心状态与可用信息。
每次只提出一个最关键的问题，帮助用户重新想起当时的完整感受与约束。
问题应与用户个人经历紧密相关，而非抽象问题。
已问过的问题不要重复。如果已有足够信息（{MAX_QUESTIONS}个问题后），返回 {{"done": true}}。
{lang}"""
        user_content = f"""回溯决策情境：
{situation}

可选路径：
{options_text}

用户背景：
{profile_summary[:1000] if profile_summary else '未知'}{values_hint}

已有问答记录：
{qa_text if qa_text else '（无）'}

请提出下一个最重要的情境追问，或者如果信息已足够则返回 done。
返回格式：{{"question": "问题内容"}} 或 {{"done": true}}"""
    else:  # PLANNING
        system_prompt = f"""你是一位经验丰富的人生规划顾问，正在帮助用户分析一个重要决策。
你需要通过追问来收集足够的信息，以便进行精准的路径推演。
每次只提出一个最关键的问题。问题应该简洁、具体，帮助揭示用户的真实约束、优先级和期望。
已问过的问题不要重复。如果已有足够信息（{MAX_QUESTIONS}个问题后），返回 {{"done": true}}。
{lang}"""
        user_content = f"""决策情境：
{situation}

可选路径：
{options_text}

用户背景：
{profile_summary[:1000] if profile_summary else '未知'}{values_hint}

已有问答记录：
{qa_text if qa_text else '（无）'}

请提出下一个最重要的追问，或者如果信息已足够则返回 done。
返回格式：{{"question": "问题内容"}} 或 {{"done": true}}"""

    llm = LLMClient(timeout=120)
    response = llm.chat_json(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=0.6
    )

    if response.get('done'):
        return None
    return response.get('question')
