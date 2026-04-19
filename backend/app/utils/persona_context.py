"""历史人物视角注入工具 - 供各 service 模块共享"""

from typing import Dict


def build_persona_context(decision: Dict) -> str:
    """
    若决策关联历史人物（historical/builtin），返回视角注入字符串；
    否则返回空字符串。
    """
    persona_id = decision.get('persona_id')
    if not persona_id:
        return ''

    # 延迟导入避免循环依赖
    from ..models.persona import PersonaRepository
    persona = PersonaRepository.get(persona_id)
    if not persona or persona.get('persona_type') not in ('historical', 'builtin'):
        return ''

    name = persona.get('name', '')
    bio = persona.get('bio', '')[:400]
    return (
        f"\n\n【架空历史推演背景】"
        f"本次推演的主体是历史人物「{name}」。"
        f"历史背景：{bio}。"
        f"你的角色是第三方历史推演分析师：基于{name}所处时代的政治、军事、经济等真实约束，"
        f"推演{name}做出各选项后历史将如何演变。"
        f"以现代历史分析语言陈述，不要以{name}的第一人称发言，不要模仿古文语气。"
    )
