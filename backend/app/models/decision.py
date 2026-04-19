"""决策数据访问层"""

import json
from datetime import datetime, timezone
from typing import Optional, Dict, List
from ..database import get_db
from ..utils.safe_json import safe_json_loads


class DecisionRepository:

    @staticmethod
    def list_all() -> List[Dict]:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM decisions WHERE deleted_at IS NULL ORDER BY created_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def list_trash() -> List[Dict]:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM decisions WHERE deleted_at IS NOT NULL ORDER BY deleted_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get(decision_id: int) -> Optional[Dict]:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM decisions WHERE id=?", (decision_id,)
            ).fetchone()
            if not row:
                return None
            decision = dict(row)
            decision['clarification_qa'] = safe_json_loads(decision.get('clarification_qa'), [], 'clarification_qa')

            options = conn.execute(
                "SELECT * FROM decision_options WHERE decision_id=? ORDER BY sort_order",
                (decision_id,)
            ).fetchall()
            decision['options'] = [dict(o) for o in options]

            results = conn.execute(
                "SELECT * FROM simulation_results WHERE decision_id=?",
                (decision_id,)
            ).fetchall()
            decision['simulation_results'] = [dict(r) for r in results]

            return decision

    @staticmethod
    def create(title: str, situation: str, options: List[Dict],
               decision_type: str = 'planning', persona_id: int = None,
               actual_choice_index: int = None, actual_outcome: str = None,
               time_period: str = None, occurrence_year: int = None) -> Dict:
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            cur = conn.execute(
                """INSERT INTO decisions
                   (title, situation, status, decision_type, persona_id,
                    actual_outcome, time_period, occurrence_year, created_at, updated_at)
                   VALUES (?, ?, 'draft', ?, ?, ?, ?, ?, ?, ?)""",
                (title, situation, decision_type, persona_id, actual_outcome,
                 time_period, occurrence_year, now, now)
            )
            decision_id = cur.lastrowid
            option_ids = []
            for i, opt in enumerate(options):
                cur2 = conn.execute(
                    """INSERT INTO decision_options (decision_id, label, description, sort_order)
                       VALUES (?, ?, ?, ?)""",
                    (decision_id, opt.get('label', f'选项{i+1}'), opt.get('description', ''), i)
                )
                option_ids.append(cur2.lastrowid)

            # 回溯模式：记录实际选择的选项 ID
            if actual_choice_index is not None and 0 <= actual_choice_index < len(option_ids):
                conn.execute(
                    "UPDATE decisions SET actual_choice_id=? WHERE id=?",
                    (option_ids[actual_choice_index], decision_id)
                )

            conn.commit()
            return DecisionRepository.get(decision_id)

    @staticmethod
    def update_status(decision_id: int, status: str):
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            conn.execute(
                "UPDATE decisions SET status=?, updated_at=? WHERE id=?",
                (status, now, decision_id)
            )
            conn.commit()

    @staticmethod
    def update_clarification_qa(decision_id: int, qa_list: List[Dict]):
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            conn.execute(
                "UPDATE decisions SET clarification_qa=?, updated_at=? WHERE id=?",
                (json.dumps(qa_list, ensure_ascii=False), now, decision_id)
            )
            conn.commit()

    @staticmethod
    def save_simulation_results(decision_id: int, results: List[Dict]):
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            conn.execute(
                "DELETE FROM simulation_results WHERE decision_id=?", (decision_id,)
            )
            for r in results:
                conn.execute(
                    """INSERT INTO simulation_results
                       (decision_id, option_id, dimension, time_horizon, content, score, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (decision_id, r['option_id'], r['dimension'], r['time_horizon'],
                     r['content'], r.get('score'), now)
                )
            conn.commit()

    @staticmethod
    def upsert_option_results(decision_id: int, option_id: int, results: List[Dict]):
        """按选项增量保存推演结果（原子事务：先删该 option 旧结果，再插入新结果）。
        用于 SSE 流式推演中每完成一个选项立即持久化，支持断线重连后恢复进度。"""
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            conn.execute(
                "DELETE FROM simulation_results WHERE decision_id=? AND option_id=?",
                (decision_id, option_id)
            )
            conn.executemany(
                """INSERT INTO simulation_results
                   (decision_id, option_id, dimension, time_horizon, content, score, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                [(decision_id, option_id, r['dimension'], r['time_horizon'],
                  r['content'], r.get('score'), now)
                 for r in results]
            )
            conn.commit()

    @staticmethod
    def get_completed_option_ids(decision_id: int) -> List[int]:
        """返回已有推演结果的 option_id 列表（用于断线重连时判断哪些选项已完成）。"""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT DISTINCT option_id FROM simulation_results WHERE decision_id=?",
                (decision_id,)
            ).fetchall()
        return [r[0] for r in rows]

    @staticmethod
    def set_universe_node_id(decision_id: int, node_id: int):
        """记录该决策对应的宇宙节点 ID（双向关联）。"""
        with get_db() as conn:
            conn.execute(
                "UPDATE decisions SET universe_node_id=? WHERE id=?",
                (node_id, decision_id)
            )
            conn.commit()

    @staticmethod
    def save_recommendation(decision_id: int, recommendation: str):
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            conn.execute(
                "UPDATE decisions SET recommendation=?, status='done', updated_at=? WHERE id=?",
                (recommendation, now, decision_id)
            )
            conn.commit()

    @staticmethod
    def soft_delete(decision_id: int):
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            conn.execute(
                "UPDATE decisions SET deleted_at=? WHERE id=?", (now, decision_id)
            )
            # 清除宇宙节点的 decision_id 引用，防止形成幽灵关联（E-1 孤岛清理）
            conn.execute(
                "UPDATE universe_nodes SET decision_id=NULL WHERE decision_id=?",
                (decision_id,)
            )
            conn.commit()

    @staticmethod
    def restore(decision_id: int):
        with get_db() as conn:
            conn.execute(
                "UPDATE decisions SET deleted_at=NULL WHERE id=?", (decision_id,)
            )
            conn.commit()

    @staticmethod
    def delete(decision_id: int):
        """永久删除（级联删除关联数据）。"""
        with get_db() as conn:
            conn.execute("DELETE FROM decisions WHERE id=?", (decision_id,))
            conn.commit()

    @staticmethod
    def empty_trash():
        with get_db() as conn:
            conn.execute("DELETE FROM decisions WHERE deleted_at IS NOT NULL")
            conn.commit()


class ChatRepository:

    @staticmethod
    def get_messages(decision_id: int, phase: str) -> List[Dict]:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM chat_messages WHERE decision_id=? AND phase=? ORDER BY id",
                (decision_id, phase)
            ).fetchall()
            result = []
            for r in rows:
                msg = dict(r)
                msg['metadata'] = safe_json_loads(msg.get('metadata'), {}, 'chat_metadata')
                result.append(msg)
            return result

    @staticmethod
    def add_message(decision_id: int, phase: str, role: str, content: str, metadata: Dict = None) -> Dict:
        now = datetime.now(timezone.utc).isoformat()
        metadata_json = json.dumps(metadata or {}, ensure_ascii=False)
        with get_db() as conn:
            cur = conn.execute(
                """INSERT INTO chat_messages (decision_id, phase, role, content, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (decision_id, phase, role, content, metadata_json, now)
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM chat_messages WHERE id=?", (cur.lastrowid,)
            ).fetchone()
            msg = dict(row)
            msg['metadata'] = safe_json_loads(msg.get('metadata'), {}, 'chat_metadata')
            return msg

    @staticmethod
    def get_last_user_message(decision_id: int, phase: str) -> Optional[Dict]:
        with get_db() as conn:
            row = conn.execute(
                """SELECT * FROM chat_messages
                   WHERE decision_id=? AND phase=? AND role='user'
                   ORDER BY id DESC LIMIT 1""",
                (decision_id, phase)
            ).fetchone()
            if not row:
                return None
            msg = dict(row)
            msg['metadata'] = safe_json_loads(msg.get('metadata'), {}, 'chat_metadata')
            return msg
