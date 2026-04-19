"""NPC Agent 按需生成服务"""

import logging
from typing import List
from ..utils.llm_client import LLMClient
from ..models.universe import UniverseRepository

logger = logging.getLogger('lifeplanner.agent_factory')


def detect_new_agents(text: str, known_names: set) -> List[str]:
    """使用轻量 LLM 调用从文本中识别尚未创建档案的具名角色。
    只在 text 非空且 known_names 较少时调用，减少不必要的 LLM 请求。"""
    if not text or not text.strip():
        return []
    try:
        llm = LLMClient(timeout=30)
        known_list = '、'.join(list(known_names)[:20]) if known_names else '无'
        msgs = [
            {
                "role": "system",
                "content": "你是角色识别器。找出文本中被提及的具名人物（人名/角色名），排除已知角色。只返回JSON。"
            },
            {
                "role": "user",
                "content": (
                    f"已知角色：{known_list}\n\n"
                    f"文本：{text[:800]}\n\n"
                    "返回格式：{\"new_names\": [\"姓名1\", \"姓名2\"]}，无新角色则返回 {\"new_names\": []}"
                )
            }
        ]
        result = llm.chat_json(msgs, temperature=0.1, max_tokens=200)
        names = result.get('new_names', [])
        # 过滤掉 known_names（不区分大小写）
        known_lower = {n.lower() for n in known_names}
        return [n for n in names if isinstance(n, str) and n.strip()
                and n.lower() not in known_lower][:3]  # 每轮最多生成3个新角色
    except Exception as e:
        logger.warning(f"NPC检测失败（已忽略）: {e}")
        return []


def generate_agent_profile(universe_id: int, name: str, premise: str,
                            protagonist_name: str, context_excerpt: str) -> dict:
    """为新出现的角色生成档案并持久化到 DB。
    返回已持久化的 agent dict。"""
    llm = LLMClient(timeout=60)
    msgs = [
        {
            "role": "system",
            "content": (
                "你是角色档案生成器。根据世界背景和角色出场语境，生成该角色的简要档案。"
                "档案要符合世界观设定，人物性格鲜明。"
            )
        },
        {
            "role": "user",
            "content": (
                f"宇宙背景：{premise[:800]}\n"
                f"主角：{protagonist_name}\n"
                f"角色名字：{name}\n"
                f"出场语境：{context_excerpt[:500]}\n\n"
                "请生成角色档案（JSON）：\n"
                "{\n"
                "  \"role\": \"角色职位或身份（简短）\",\n"
                "  \"bio\": \"50字以内背景简介\",\n"
                "  \"persona\": \"性格特征与行为风格（50字以内）\",\n"
                "  \"mbti\": \"MBTI类型或null\",\n"
                "  \"stance\": \"ally或neutral或adversary（对主角的初始立场）\"\n"
                "}"
            )
        }
    ]
    result = llm.chat_json(msgs, temperature=0.4, max_tokens=400)

    agent = UniverseRepository.upsert_agent(
        universe_id=universe_id,
        name=name,
        role=str(result.get('role') or '')[:100],
        bio=str(result.get('bio') or '')[:500],
        persona=str(result.get('persona') or '')[:500],
        mbti=str(result.get('mbti') or '')[:10] if result.get('mbti') else None,
        stance=result.get('stance', 'neutral') if result.get('stance') in ('ally', 'neutral', 'adversary') else 'neutral',
    )
    logger.info(f"新 NPC 生成：{name} (universe={universe_id})")
    return agent
