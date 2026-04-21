"""我的宇宙引导初始化 — 根据用户问答生成根节点开篇叙事"""

import logging
from typing import Dict, Optional
from ..utils.llm_client import LLMClient

logger = logging.getLogger('lifeplanner.personal_init')


def generate_root_narration(answers: Dict, profile: Dict = None) -> str:
    """
    根据初始化问答 + Profile 数据，生成「我的宇宙」根节点的开篇叙事。
    第三人称，诗意风格，150 字以内。
    LLM 失败时返回降级默认文本，不抛异常。
    """
    name       = (answers.get('name') or (profile or {}).get('display_name') or '这个人')[:50]
    phase      = answers.get('phase', '')[:200]
    theme      = answers.get('theme', '')[:200]
    aspiration = answers.get('aspiration', '')[:200]

    profile_summary = ((profile or {}).get('summary') or '')[:300]

    system = (
        "你是一位叙事作家，为用户撰写「人生宇宙」的开篇叙事。"
        "风格：第三人称，诗意但不浮夸，150字以内。"
        "不加标题，直接是叙事正文，以当前处境和核心张力收尾。"
    )

    user_parts = [
        f"姓名/称呼：{name}",
        f"当前阶段：{phase}" if phase else None,
        f"最重要的主题：{theme}" if theme else None,
        f"一直想做但还没做到：{aspiration}" if aspiration else None,
        f"补充背景：{profile_summary}" if profile_summary else None,
    ]
    user = '\n'.join(p for p in user_parts if p) + '\n\n请写开篇叙事：'

    try:
        return LLMClient(timeout=30).chat(
            messages=[
                {'role': 'system', 'content': system},
                {'role': 'user',   'content': user},
            ],
            temperature=0.8,
        )
    except Exception as e:
        logger.warning('generate_root_narration failed: %s', e)
        return f"{name}的宇宙在此刻启动。每一个选择，都是一条新的时间线。"
