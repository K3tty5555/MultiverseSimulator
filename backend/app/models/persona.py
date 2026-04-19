"""人格角色数据访问层"""

import json
from datetime import datetime, timezone
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
    def create(name: str, persona_type: str = 'custom', bio: str = '',
               avatar_emoji: str = '👤', meta: Dict = None) -> Dict:
        now = datetime.now(timezone.utc).isoformat()
        meta_json = json.dumps(meta or {}, ensure_ascii=False)
        with get_db() as conn:
            cur = conn.execute(
                """INSERT INTO personas (name, persona_type, bio, avatar_emoji, meta, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (name, persona_type, bio, avatar_emoji, meta_json, now, now)
            )
            persona_id = cur.lastrowid
            conn.commit()
        return PersonaRepository.get(persona_id)

    # 可更新的列白名单，防止 f-string 拼接引入 SQL 注入
    _UPDATABLE_COLS = frozenset({'name', 'bio', 'avatar_emoji', 'meta', 'persona_type', 'updated_at'})

    @staticmethod
    def update(persona_id: int, name: str = None, bio: str = None,
               avatar_emoji: str = None, meta: Dict = None,
               persona_type: str = None) -> Optional[Dict]:
        if not PersonaRepository.get(persona_id):
            return None
        now = datetime.now(timezone.utc).isoformat()
        updates = {'updated_at': now}
        if name is not None:
            updates['name'] = name
        if bio is not None:
            updates['bio'] = bio
        if avatar_emoji is not None:
            updates['avatar_emoji'] = avatar_emoji
        if meta is not None:
            updates['meta'] = json.dumps(meta, ensure_ascii=False)
        if persona_type is not None:
            updates['persona_type'] = persona_type

        # 白名单校验列名，防止动态拼接引入 SQL 注入
        invalid = set(updates) - PersonaRepository._UPDATABLE_COLS
        if invalid:
            raise ValueError(f"非法列名: {invalid}")

        set_clause = ', '.join(f"{k}=?" for k in updates)
        values = list(updates.values()) + [persona_id]
        with get_db() as conn:
            conn.execute(f"UPDATE personas SET {set_clause} WHERE id=?", values)
            conn.commit()
        return PersonaRepository.get(persona_id)

    @staticmethod
    def has_active_decisions(persona_id: int) -> bool:
        """检查该角色是否有未删除的关联决策。"""
        with get_db() as conn:
            row = conn.execute(
                "SELECT id FROM decisions WHERE persona_id=? AND deleted_at IS NULL LIMIT 1",
                (persona_id,)
            ).fetchone()
            return row is not None

    @staticmethod
    def delete(persona_id: int):
        """删除角色（self 类型不可删除）。"""
        with get_db() as conn:
            conn.execute(
                "DELETE FROM personas WHERE id=? AND persona_type NOT IN ('self', 'builtin')",
                (persona_id,)
            )
            conn.commit()

    @staticmethod
    def _to_dict(row) -> Dict:
        p = dict(row)
        p['meta'] = safe_json_loads(p.get('meta'), {}, 'persona_meta')
        return p
