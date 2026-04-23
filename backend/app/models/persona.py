"""人格角色数据访问层"""

from typing import Optional, Dict, List
from ..database import get_db
from ..utils.safe_json import safe_json_loads


class PersonaRepository:

    @staticmethod
    def list_all() -> List[Dict]:
        with get_db() as conn:
            # self 排在最前，其余按创建时间升序
            rows = conn.execute(
                """SELECT * FROM personas
                   ORDER BY (persona_type = 'self') DESC,
                            (persona_type = 'builtin') DESC,
                            created_at ASC"""
            ).fetchall()
            return [PersonaRepository._to_dict(r) for r in rows]

    @staticmethod
    def get(persona_id: int) -> Optional[Dict]:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM personas WHERE id=?", (persona_id,)
            ).fetchone()
            return PersonaRepository._to_dict(row) if row else None

    @staticmethod
    def get_self() -> Optional[Dict]:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM personas WHERE persona_type='self' LIMIT 1"
            ).fetchone()
            return PersonaRepository._to_dict(row) if row else None

    @staticmethod
    def _to_dict(row) -> Dict:
        p = dict(row)
        p['meta'] = safe_json_loads(p.get('meta'), {}, 'persona_meta')
        return p
