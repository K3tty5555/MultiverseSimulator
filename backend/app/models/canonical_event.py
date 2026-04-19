"""角色史实节点（canonical events）的数据访问层。

按 (character_name, universe_type, world_label) 分组存储，每组 5-8 个节点。
LLM 首次生成时 bulk_create，用户可 update/delete 单条（置 is_edited=1）。
"""

from datetime import datetime, timezone
from typing import Optional, Dict, List
from ..database import get_db


class CanonicalEventRepository:

    @staticmethod
    def list_for(character_name: str, universe_type: str,
                 world_label: Optional[str] = None) -> List[Dict]:
        """按角色 + 类型 + 世界标签查询史实节点，按 sort_order, year 升序。"""
        with get_db() as conn:
            if world_label:
                rows = conn.execute(
                    """SELECT * FROM character_canonical_events
                       WHERE character_name=? AND universe_type=? AND world_label=?
                       ORDER BY sort_order ASC, COALESCE(year, 9999) ASC, id ASC""",
                    (character_name, universe_type, world_label)
                ).fetchall()
            else:
                # 空 world_label：匹配 NULL 或空字符串
                rows = conn.execute(
                    """SELECT * FROM character_canonical_events
                       WHERE character_name=? AND universe_type=?
                         AND (world_label IS NULL OR world_label='')
                       ORDER BY sort_order ASC, COALESCE(year, 9999) ASC, id ASC""",
                    (character_name, universe_type)
                ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get(event_id: int) -> Optional[Dict]:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM character_canonical_events WHERE id=?", (event_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def bulk_create(character_name: str, universe_type: str,
                    world_label: Optional[str], events: List[Dict]) -> List[Dict]:
        """批量插入。events=[{year, title, description, sort_order}]。"""
        now = datetime.now(timezone.utc).isoformat()
        inserted_ids = []
        with get_db() as conn:
            for idx, e in enumerate(events):
                cur = conn.execute(
                    """INSERT INTO character_canonical_events
                       (character_name, universe_type, world_label,
                        year, sort_order, title, description, is_edited,
                        created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
                    (
                        character_name,
                        universe_type,
                        world_label or None,
                        e.get('year'),
                        int(e.get('sort_order') or (idx + 1)),
                        str(e.get('title') or '')[:200],
                        str(e.get('description') or '')[:1000],
                        now, now,
                    )
                )
                inserted_ids.append(cur.lastrowid)
            conn.commit()
        # 返回刚插入的
        with get_db() as conn:
            placeholders = ','.join('?' * len(inserted_ids))
            rows = conn.execute(
                f"SELECT * FROM character_canonical_events WHERE id IN ({placeholders}) "
                "ORDER BY sort_order ASC",
                inserted_ids
            ).fetchall() if inserted_ids else []
        return [dict(r) for r in rows]

    @staticmethod
    def update(event_id: int, *, title=None, description=None,
               year=None, sort_order=None) -> Optional[Dict]:
        """用户编辑：更新指定字段 + 自动置 is_edited=1 + updated_at。"""
        fields, values = [], []
        if title is not None:
            fields.append('title=?')
            values.append(str(title)[:200])
        if description is not None:
            fields.append('description=?')
            values.append(str(description)[:1000])
        if year is not None:
            fields.append('year=?')
            values.append(year)
        if sort_order is not None:
            fields.append('sort_order=?')
            values.append(int(sort_order))
        if not fields:
            return CanonicalEventRepository.get(event_id)

        now = datetime.now(timezone.utc).isoformat()
        fields.append('is_edited=1')
        fields.append('updated_at=?')
        values.append(now)
        values.append(event_id)

        with get_db() as conn:
            conn.execute(
                f"UPDATE character_canonical_events SET {', '.join(fields)} WHERE id=?",
                values
            )
            conn.commit()
        return CanonicalEventRepository.get(event_id)

    @staticmethod
    def delete(event_id: int) -> bool:
        with get_db() as conn:
            cur = conn.execute(
                "DELETE FROM character_canonical_events WHERE id=?", (event_id,)
            )
            conn.commit()
        return cur.rowcount > 0
