"""决策模式策略层 - 单一入口确定推演模式"""

from enum import Enum
from typing import Dict


class DecisionMode(Enum):
    HISTORICAL    = 'historical'     # persona_id 有值 → 历史人物推演（最高优先级）
    RETROSPECTIVE = 'retrospective'  # decision_type='retrospective'，无 persona → 个人回溯
    PLANNING      = 'planning'       # 其余 → 个人规划（默认）


def resolve_mode(decision: Dict) -> DecisionMode:
    """
    从 decision dict 解析决策模式。
    优先级：HISTORICAL > RETROSPECTIVE > PLANNING
    """
    if decision.get('persona_id'):
        return DecisionMode.HISTORICAL
    if decision.get('decision_type') == 'retrospective':
        return DecisionMode.RETROSPECTIVE
    return DecisionMode.PLANNING
