"""报告生成服务 - Step 4，SSE 流式输出"""

import logging
from typing import Generator
from ..models.profile import ProfileRepository

logger = logging.getLogger('lifeplanner.report_generator')
from ..models.decision import DecisionRepository
from ..utils.llm_client import LLMClient
from ..utils.locale import get_language_instruction
from ..utils.persona_context import build_persona_context
from .strategy import resolve_mode, DecisionMode

MAX_INPUT_LEN = 5000   # 与 simulation_engine 保持一致
MAX_CLARIFICATION_LEN = 2000

DIMENSION_LABELS = {
    'career': '事业发展',
    'finance': '财务影响',
    'relationships': '人际关系',
    'wellbeing': '身心健康'
}

TIME_LABELS = {
    'short_term': '短期（1年内）',
    'mid_term': '中期（3-5年）',
    'long_term': '长期（10年以上）'
}


def _build_top_values_text(profile: dict | None) -> str:
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


def _build_simulation_summary(decision: dict) -> str:
    options = {o['id']: o['label'] for o in decision.get('options', [])}
    results = decision.get('simulation_results', [])
    lines = []
    for opt_id, opt_label in options.items():
        lines.append(f"\n### {opt_label}")
        for dim in ['career', 'finance', 'relationships', 'wellbeing']:
            for th in ['short_term', 'mid_term', 'long_term']:
                cell = next(
                    (r for r in results if r['option_id'] == opt_id
                     and r['dimension'] == dim and r['time_horizon'] == th),
                    None
                )
                if cell:
                    lines.append(
                        f"- {DIMENSION_LABELS[dim]} / {TIME_LABELS[th]}: {cell['content']}"
                    )
    return '\n'.join(lines)


def generate_report_stream(decision_id: int) -> Generator[str, None, None]:
    """SSE 流式生成建议报告"""
    decision = DecisionRepository.get(decision_id)
    if not decision:
        yield 'data: {"type": "error", "content": "决策不存在"}\n\n'
        return

    mode = resolve_mode(decision)
    # HISTORICAL 模式不使用用户档案
    if mode == DecisionMode.PLANNING or mode == DecisionMode.RETROSPECTIVE:
        profile = ProfileRepository.get()
        profile_summary = profile.get('summary', '') if profile else ''
        # 提取价值观权重 top 5，用于个性化报告
        top_values_text = _build_top_values_text(profile)
    else:
        profile_summary = ''
        top_values_text = ''

    qa_list = decision.get('clarification_qa') or []
    clarification_context = '\n'.join(
        [f"Q: {qa['question']}\nA: {qa['answer']}" for qa in qa_list]
    )[:MAX_CLARIFICATION_LEN] if qa_list else '无'

    simulation_summary = _build_simulation_summary(decision)
    lang = get_language_instruction()

    actual_outcome = decision.get('actual_outcome') or ''
    time_period = decision.get('time_period') or ''
    actual_choice_id = decision.get('actual_choice_id')

    actual_choice_label = ''
    if actual_choice_id:
        for opt in decision.get('options', []):
            if opt['id'] == actual_choice_id:
                actual_choice_label = opt['label']
                break

    if mode == DecisionMode.RETROSPECTIVE:
        time_label = f"（{time_period}）" if time_period else ''
        messages = [
            {
                "role": "system",
                "content": f"""你是一位擅长回溯分析的人生顾问，帮助用户深度理解和反思过去的决策。
报告应使用叙事性风格，有温度、有洞察，围绕「当时的选择」与「如果走另一条路」展开。
避免说教，重在启发用户从历史中汲取智慧。使用 Markdown 格式。
{lang}"""
            },
            {
                "role": "user",
                "content": f"""请基于以下信息生成回溯分析报告：

## 用户背景
{profile_summary[:1500] if profile_summary else '未提供'}

## 决策情境{time_label}
{decision['situation'][:MAX_INPUT_LEN]}

## 澄清信息
{clarification_context}

## 当时的实际选择
{actual_choice_label or '（未标记）'}

## 实际发生的结果
{actual_outcome or '（未提供）'}

## 各选项推演分析
{simulation_summary[:6000]}

请生成包含以下部分的回溯分析报告：
1. **情境还原**——那个时刻的全貌与压力
2. **你做出的选择及其实际影响**（深度分析已知结果，挖掘深层影响）
3. **未选之路**——如果走了其他选项，会发生什么（对每条路径进行叙事性推演）
4. **关键转折点分析**——哪些因素最终决定了走向
5. **从这段经历中，你可以带走什么**"""
            }
        ]
    elif mode == DecisionMode.HISTORICAL:
        persona_context = build_persona_context(decision)
        messages = [
            {
                "role": "system",
                "content": f"""你是一位专业的架空历史推演分析师，擅长撰写「平行宇宙」历史叙事报告。
报告应以现代历史分析语言撰写，有叙事感、有因果推断，呈现各选项下历史的不同走向。
不要以历史人物第一人称发言，不模仿古文语气。使用 Markdown 格式。
{lang}{persona_context}"""
            },
            {
                "role": "user",
                "content": f"""请基于以下信息生成架空历史推演报告：

## 决策情境
{decision['situation'][:MAX_INPUT_LEN]}

## 澄清背景
{clarification_context}

## 各选项推演结果
{simulation_summary[:6000]}

请生成包含以下部分的报告：
1. **历史节点还原**——该决策在历史上的真实背景与压力
2. **各路径的历史走向**——每个选项如果被采纳，历史将如何演变（逐一叙述）
3. **关键转折因素**——哪些变量决定了不同路径的分野
4. **历史启示**——这段架空历史对今天的决策者有何借鉴"""
            }
        ]
    else:
        # 动态拼接价值观契合分析段落（有数据才追加）
        values_section = (
            f"\n6. **价值观契合分析**：根据用户价值观权重（{top_values_text}），"
            f"分析各选项对高权重价值观的保护和牺牲情况，以及推荐选项与其价值取向的吻合程度"
            if top_values_text else ''
        )
        messages = [
            {
                "role": "system",
                "content": f"""你是一位经验丰富的人生规划顾问，正在为用户撰写决策建议报告。
报告应结构清晰、有理有据，给出明确的推荐意见，并解释理由。
避免空话套话，要具体、有说服力。使用 Markdown 格式。
{lang}"""
            },
            {
                "role": "user",
                "content": f"""请基于以下信息生成决策建议报告：

## 用户背景
{profile_summary[:1500] if profile_summary else '未提供'}

## 决策情境
{decision['situation'][:MAX_INPUT_LEN]}

## 澄清信息
{clarification_context}

## 各选项推演结果
{simulation_summary[:6000]}

请生成包含以下部分的报告：
1. 情境分析与关键要素
2. 各选项综合评估（优势、劣势、风险）
3. **推荐选项及核心理由**（这是最重要的部分）
4. 无论选择哪个选项的注意事项
5. 行动建议清单{values_section}"""
            }
        ]

    import json
    full_content = ''
    llm = LLMClient(timeout=120)
    try:
        for delta in llm.stream(messages, temperature=0.7, max_tokens=2000):
            full_content += delta
            yield f'data: {json.dumps({"type": "delta", "content": delta}, ensure_ascii=False)}\n\n'
    except Exception:
        # 流中断：向客户端发送错误事件，保存已积累内容避免状态不一致
        yield f'data: {json.dumps({"type": "error", "content": "报告生成中断，请重试"}, ensure_ascii=False)}\n\n'
        if full_content:
            DecisionRepository.save_recommendation(decision_id, full_content)
        return

    # Save the complete report
    DecisionRepository.save_recommendation(decision_id, full_content)

    # 同步更新「我的宇宙」对应节点的摘要内容
    try:
        dec = DecisionRepository.get(decision_id)
        if dec and dec.get('universe_node_id'):
            from ..models.universe import UniverseRepository
            UniverseRepository.update_node_content(
                dec['universe_node_id'], full_content
            )
    except Exception as e:
        logger.warning('update universe node content failed for decision %s: %s', decision_id, e)

    yield f'data: {json.dumps({"type": "done"}, ensure_ascii=False)}\n\n'
