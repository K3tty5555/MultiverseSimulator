"""NPC 预生成服务：为新建宇宙批量生成同时代关键人物"""

import json
import logging
import re
from typing import List, Dict, Optional

logger = logging.getLogger('lifeplanner.npc_preloader')


def preload_npcs_for_universe(
    universe_id: int,
    protagonist_name: str,
    premise: str,
    event_context: str = '',
    count: int = 3
) -> List[Dict]:
    """
    调用 LLM 生成 count 个与主角关系密切的 NPC 档案，串行持久化后返回。
    失败时 best-effort——整体失败返回空列表，单个 NPC 出错不中止其他。
    """
    from ..utils.llm_client import LLMClient
    from ..models.universe import UniverseRepository

    system_prompt = (
        "你是历史/叙事 NPC 档案生成器。根据宇宙背景和主角信息，"
        "生成若干个对故事最关键的 NPC 角色档案。"
        "返回 JSON 数组（非对象），每个元素包含以下字段：\n"
        '{ "name": "姓名", "role": "身份/职位", "bio": "背景简介（不超过50字）", '
        '"persona": "性格风格描述", "stance": "ally|neutral|adversary" }'
    )

    event_part = f'\n当前场景：{event_context[:300]}' if event_context else ''
    user_prompt = (
        f'宇宙背景：{premise[:600]}\n'
        f'主角：{protagonist_name}'
        f'{event_part}\n'
        f'请生成 {count} 个与主角关系最密切、对故事最关键的 NPC：'
        '\n\n请以 JSON 数组格式返回结果。'
    )

    try:
        client = LLMClient(timeout=60)
        raw = client.chat(
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            temperature=0.7,
            max_tokens=1200,
        )
        # Strip markdown code fences if present
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', raw.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned).strip()
        # Extract first [...] array
        match = re.search(r'\[[\s\S]*\]', cleaned)
        if match:
            cleaned = match.group(0)
        npc_list = json.loads(cleaned)
        if not isinstance(npc_list, list):
            raise ValueError("LLM 未返回数组")
    except Exception as e:
        logger.warning("NPC 预生成 LLM 调用失败: %s", e)
        return []

    if not npc_list:
        return []

    def persist_npc(npc: dict) -> Optional[Dict]:
        try:
            name = str(npc.get('name') or '').strip()
            if not name:
                return None
            stance = npc.get('stance', 'neutral')
            if stance not in ('ally', 'neutral', 'adversary'):
                stance = 'neutral'
            return UniverseRepository.upsert_agent(
                universe_id=universe_id,
                name=name,
                role=str(npc.get('role') or '')[:100] or None,
                bio=str(npc.get('bio') or '')[:200] or None,
                persona=str(npc.get('persona') or '')[:200] or None,
                stance=stance,
            )
        except Exception as exc:
            logger.warning("持久化 NPC '%s' 失败: %s", npc.get('name'), exc)
            return None

    agents: List[Dict] = []
    for npc in npc_list[:count]:
        result = persist_npc(npc)
        if result:
            agents.append(result)

    return agents
