"""平行宇宙数据访问层"""

import json
from datetime import datetime, timezone
from typing import Optional, Dict, List
from ..database import get_db
from ..utils.safe_json import safe_json_loads


class UniverseRepository:

    # ── 宇宙 CRUD ───────────────────────────────────────────────────────────

    @staticmethod
    def create(title: str, premise: str, protagonist_name: str,
               protagonist_role: str = None, perspective: str = 'god',
               persona_id: int = None, universe_type: str = 'historical',
               era_label: str = None, protagonist_bio: str = None,
               world_label: str = None, canonical_event_id: int = None) -> Dict:
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            cur = conn.execute(
                """INSERT INTO parallel_universes
                   (title, premise, protagonist_name, protagonist_role, protagonist_bio,
                    perspective, persona_id, universe_type, era_label, world_label,
                    canonical_event_id, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)""",
                (title, premise, protagonist_name, protagonist_role, protagonist_bio,
                 perspective, persona_id, universe_type, era_label, world_label,
                 canonical_event_id, now, now)
            )
            universe_id = cur.lastrowid
            conn.commit()
        return UniverseRepository.get(universe_id)

    @staticmethod
    def get(universe_id: int) -> Optional[Dict]:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM parallel_universes WHERE id=?", (universe_id,)
            ).fetchone()
            if not row:
                return None
            universe = dict(row)
            agents = conn.execute(
                """SELECT * FROM universe_agents
                   WHERE universe_id=? AND deleted_at IS NULL
                   ORDER BY id""",
                (universe_id,)
            ).fetchall()
            universe['agents'] = [dict(a) for a in agents]
        # 解析 starter_actions JSON → list
        universe['starter_actions'] = safe_json_loads(universe.get('starter_actions'), [], 'starter_actions')
        return universe

    @staticmethod
    def list_all() -> List[Dict]:
        with get_db() as conn:
            rows = conn.execute(
                """SELECT u.*, COUNT(n.id) AS node_count,
                          p.name AS persona_name,
                          c.title AS checkpoint_title
                   FROM parallel_universes u
                   LEFT JOIN universe_nodes n ON n.universe_id = u.id
                   LEFT JOIN personas p ON p.id = u.persona_id
                   LEFT JOIN world_checkpoints c ON c.id = u.checkpoint_id
                   WHERE u.status = 'active' AND u.is_personal_main = 0
                   GROUP BY u.id
                   ORDER BY u.updated_at DESC"""
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_personal_universe() -> Optional[Dict]:
        """获取「我的宇宙」（is_personal_main=1）。"""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM parallel_universes WHERE is_personal_main=1 LIMIT 1"
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_personal_timeline() -> List[Dict]:
        """返回「我的宇宙」所有节点（软删除的决策节点除外），单次查询，按 node_year ASC, id ASC。"""
        with get_db() as conn:
            universe_row = conn.execute(
                "SELECT id FROM parallel_universes WHERE is_personal_main=1 LIMIT 1"
            ).fetchone()
            if not universe_row:
                return []
            rows = conn.execute(
                """SELECT n.*, d.decision_type FROM universe_nodes n
                   LEFT JOIN decisions d ON d.id = n.decision_id
                   WHERE n.universe_id=?
                     AND (n.node_type != 'decision' OR d.deleted_at IS NULL)
                   ORDER BY COALESCE(n.node_year, 9999) ASC, n.id ASC""",
                (universe_row['id'],)
            ).fetchall()
        result = []
        for row in rows:
            node = dict(row)
            node['agent_reactions'] = safe_json_loads(node.get('agent_reactions'), [], 'agent_reactions')
            node['branch_options']  = safe_json_loads(node.get('branch_options'),  [], 'branch_options')
            result.append(node)
        return result

    MAX_NODE_CONTENT = 2000  # narrator_content 摘要字符上限

    @staticmethod
    def update_node_content(node_id: int, narrator_content: str):
        """分析完成后填充节点叙事内容，最多保存 MAX_NODE_CONTENT 字。"""
        with get_db() as conn:
            conn.execute(
                "UPDATE universe_nodes SET narrator_content=? WHERE id=?",
                (narrator_content[:UniverseRepository.MAX_NODE_CONTENT], node_id)
            )
            conn.commit()

    @staticmethod
    def list_by_persona(persona_id: int, limit: int = 100) -> List[Dict]:
        """Return active universes linked to the given persona, with node counts."""
        with get_db() as conn:
            rows = conn.execute(
                """SELECT u.*, COUNT(n.id) AS node_count
                   FROM parallel_universes u
                   LEFT JOIN universe_nodes n ON n.universe_id = u.id
                   WHERE u.persona_id=? AND u.status='active'
                   GROUP BY u.id
                   ORDER BY u.updated_at DESC
                   LIMIT ?""",
                (persona_id, limit)
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def update_perspective(universe_id: int, perspective: str):
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            conn.execute(
                "UPDATE parallel_universes SET perspective=?, updated_at=? WHERE id=?",
                (perspective, now, universe_id)
            )
            conn.commit()

    @staticmethod
    def archive(universe_id: int):
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            conn.execute(
                "UPDATE parallel_universes SET status='archived', updated_at=? WHERE id=?",
                (now, universe_id)
            )
            conn.commit()

    @staticmethod
    def touch(universe_id: int):
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            conn.execute(
                "UPDATE parallel_universes SET updated_at=? WHERE id=?",
                (now, universe_id)
            )
            conn.commit()

    @staticmethod
    def set_protagonist(universe_id: int, name: str,
                        role: str = None, bio: str = None) -> Optional[Dict]:
        """设定/更新宇宙主角。新建宇宙流程：先建宇宙（空 protagonist_name），
        进入后调用此方法设定主角 → 触发 NPC preload。"""
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            conn.execute(
                """UPDATE parallel_universes
                   SET protagonist_name=?, protagonist_role=?, protagonist_bio=?, updated_at=?
                   WHERE id=?""",
                (name, role, bio, now, universe_id)
            )
            conn.commit()
        return UniverseRepository.get(universe_id)

    # ── Agent 操作 ──────────────────────────────────────────────────────────

    @staticmethod
    def upsert_agent(universe_id: int, name: str, role: str = None,
                     bio: str = None, persona: str = None,
                     mbti: str = None, stance: str = 'neutral') -> Dict:
        """按 (universe_id, name) 唯一键 upsert；若命中软删除的记录则恢复 + 更新。"""
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            existing = conn.execute(
                "SELECT id FROM universe_agents WHERE universe_id=? AND name=?",
                (universe_id, name)
            ).fetchone()
            if existing:
                conn.execute(
                    """UPDATE universe_agents
                       SET role=?, bio=?, persona=?, mbti=?, stance=?, deleted_at=NULL
                       WHERE id=?""",
                    (role, bio, persona, mbti, stance, existing['id'])
                )
                agent_id = existing['id']
            else:
                cur = conn.execute(
                    """INSERT INTO universe_agents
                       (universe_id, name, role, bio, persona, mbti, stance, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (universe_id, name, role, bio, persona, mbti, stance, now)
                )
                agent_id = cur.lastrowid
            conn.commit()
            row = conn.execute(
                "SELECT * FROM universe_agents WHERE id=?", (agent_id,)
            ).fetchone()
        return dict(row)

    @staticmethod
    def get_agent(agent_id: int) -> Optional[Dict]:
        """获取 agent（排除软删除）。"""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM universe_agents WHERE id=? AND deleted_at IS NULL",
                (agent_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def find_agent_by_name(universe_id: int, name: str) -> Optional[Dict]:
        """在同宇宙下按 name 查活跃 agent（排除软删除）。用于重命名重名校验。"""
        with get_db() as conn:
            row = conn.execute(
                """SELECT * FROM universe_agents
                   WHERE universe_id=? AND name=? AND deleted_at IS NULL
                   LIMIT 1""",
                (universe_id, name)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def list_agents(universe_id: int) -> List[Dict]:
        """列出活跃 agent（排除软删除）。"""
        with get_db() as conn:
            rows = conn.execute(
                """SELECT * FROM universe_agents
                   WHERE universe_id=? AND deleted_at IS NULL
                   ORDER BY id""",
                (universe_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def update_agent_memory(agent_id: int, memory_summary: str, last_node_id: int = None):
        with get_db() as conn:
            conn.execute(
                "UPDATE universe_agents SET memory_summary=?, last_node_id=? WHERE id=?",
                (memory_summary, last_node_id, agent_id)
            )
            conn.commit()

    @staticmethod
    def update_agent(agent_id: int, *, role=None, bio=None, persona=None,
                     mbti=None, stance=None) -> Optional[Dict]:
        """PATCH 风格更新 agent 档案；None 字段不触碰。返回更新后的行。"""
        fields, values = [], []
        for col, val in (('role', role), ('bio', bio), ('persona', persona),
                         ('mbti', mbti), ('stance', stance)):
            if val is not None:
                fields.append(f"{col}=?")
                values.append(val)
        if not fields:
            return UniverseRepository.get_agent(agent_id)
        values.append(agent_id)
        with get_db() as conn:
            conn.execute(
                f"UPDATE universe_agents SET {', '.join(fields)} WHERE id=?",
                values
            )
            conn.commit()
        return UniverseRepository.get_agent(agent_id)

    @staticmethod
    def delete_agent(agent_id: int) -> bool:
        """软删除 agent（保留历史 agent_reactions 快照里的引用可追溯）。返回是否命中。"""
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            cur = conn.execute(
                "UPDATE universe_agents SET deleted_at=? WHERE id=? AND deleted_at IS NULL",
                (now, agent_id)
            )
            conn.commit()
        return cur.rowcount > 0

    @staticmethod
    def rename_agent(agent_id: int, new_name: str) -> Optional[Dict]:
        """仅改 name，保留 memory_summary / last_node_id / agent_reactions 历史引用。"""
        with get_db() as conn:
            conn.execute(
                "UPDATE universe_agents SET name=? WHERE id=?",
                (new_name, agent_id)
            )
            conn.commit()
        return UniverseRepository.get_agent(agent_id)

    # ── 节点操作 ────────────────────────────────────────────────────────────

    @staticmethod
    def create_node(universe_id: int, parent_id: Optional[int],
                    perspective: str, protagonist_action: Optional[str],
                    narrator_content: Optional[str], agent_reactions: str = '[]',
                    branch_prompt: Optional[str] = None,
                    branch_options: Optional[str] = None,
                    node_type: str = 'narrative',
                    node_year: Optional[int] = None,
                    decision_id: Optional[int] = None) -> Dict:
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            # Compute turn_number atomically in DB to avoid race conditions
            cur = conn.execute(
                """INSERT INTO universe_nodes
                   (universe_id, parent_id, turn_number, perspective,
                    protagonist_action, narrator_content, agent_reactions,
                    branch_prompt, branch_options,
                    node_type, node_year, decision_id, created_at)
                   VALUES (?, ?,
                     (SELECT COALESCE(MAX(turn_number), 0) + 1 FROM universe_nodes WHERE universe_id=?),
                     ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (universe_id, parent_id, universe_id, perspective,
                 protagonist_action, narrator_content, agent_reactions,
                 branch_prompt, branch_options,
                 node_type, node_year, decision_id, now)
            )
            node_id = cur.lastrowid
            conn.commit()
            row = conn.execute(
                "SELECT * FROM universe_nodes WHERE id=?", (node_id,)
            ).fetchone()
        node = dict(row)
        node['agent_reactions'] = safe_json_loads(node.get('agent_reactions'), [], 'agent_reactions')
        node['branch_options']  = safe_json_loads(node.get('branch_options'),  [], 'branch_options')
        return node

    @staticmethod
    def count_descendants(node_id: int) -> int:
        """返回节点的后代总数（不含自身），用于确认弹层提示。"""
        with get_db() as conn:
            row = conn.execute("""
                WITH RECURSIVE sub AS (
                  SELECT id FROM universe_nodes WHERE parent_id=?
                  UNION ALL
                  SELECT n.id FROM universe_nodes n JOIN sub s ON n.parent_id=s.id
                )
                SELECT COUNT(*) FROM sub
            """, (node_id,)).fetchone()
        return row[0] if row else 0

    @staticmethod
    def delete_node_cascade(node_id: int):
        """删除节点及其所有后代（递归 CTE，硬删除）。"""
        with get_db() as conn:
            conn.execute("""
                WITH RECURSIVE to_del AS (
                  SELECT id FROM universe_nodes WHERE id=?
                  UNION ALL
                  SELECT n.id FROM universe_nodes n JOIN to_del d ON n.parent_id=d.id
                )
                DELETE FROM universe_nodes WHERE id IN (SELECT id FROM to_del)
            """, (node_id,))
            conn.commit()

    @staticmethod
    def update_node_alt(node_id: int, perspective_alt: str):
        """Store alternative perspective narration."""
        with get_db() as conn:
            conn.execute(
                "UPDATE universe_nodes SET perspective_alt=? WHERE id=?",
                (perspective_alt, node_id)
            )
            conn.commit()

    @staticmethod
    def get_node(node_id: int) -> Optional[Dict]:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM universe_nodes WHERE id=?", (node_id,)
            ).fetchone()
        if not row:
            return None
        node = dict(row)
        node['agent_reactions'] = safe_json_loads(node.get('agent_reactions'), [], 'agent_reactions')
        node['branch_options']  = safe_json_loads(node.get('branch_options'),  [], 'branch_options')
        return node

    @staticmethod
    def get_thread(node_id: int) -> List[Dict]:
        """Return all nodes from root to node_id (inclusive), ordered by turn_number.
        Uses a single recursive CTE query instead of N individual lookups."""
        with get_db() as conn:
            rows = conn.execute(
                """WITH RECURSIVE thread AS (
                     SELECT id, universe_id, parent_id, turn_number, perspective,
                            protagonist_action, narrator_content, perspective_alt,
                            agent_reactions, branch_prompt, branch_options, created_at
                     FROM universe_nodes WHERE id = ?
                     UNION ALL
                     SELECT n.id, n.universe_id, n.parent_id, n.turn_number, n.perspective,
                            n.protagonist_action, n.narrator_content, n.perspective_alt,
                            n.agent_reactions, n.branch_prompt, n.branch_options, n.created_at
                     FROM universe_nodes n
                     JOIN thread t ON n.id = t.parent_id
                   )
                   SELECT * FROM thread ORDER BY turn_number ASC""",
                (node_id,)
            ).fetchall()
        result = []
        for row in rows:
            node = dict(row)
            node['agent_reactions'] = safe_json_loads(node.get('agent_reactions'), [], 'agent_reactions')
            node['branch_options']  = safe_json_loads(node.get('branch_options'),  [], 'branch_options')
            result.append(node)
        return result

    @staticmethod
    def get_children(node_id: int) -> List[Dict]:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM universe_nodes WHERE parent_id=? ORDER BY turn_number",
                (node_id,)
            ).fetchall()
        result = []
        for row in rows:
            node = dict(row)
            node['agent_reactions'] = safe_json_loads(node.get('agent_reactions'), [], 'agent_reactions')
            node['branch_options']  = safe_json_loads(node.get('branch_options'),  [], 'branch_options')
            result.append(node)
        return result

    @staticmethod
    def get_root_node(universe_id: int) -> Optional[Dict]:
        """Return the root node (node_type='root') for this universe."""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM universe_nodes WHERE universe_id=? AND node_type='root' LIMIT 1",
                (universe_id,)
            ).fetchone()
        if not row:
            return None
        node = dict(row)
        node['agent_reactions'] = safe_json_loads(node.get('agent_reactions'), [], 'agent_reactions')
        node['branch_options']  = safe_json_loads(node.get('branch_options'),  [], 'branch_options')
        return node

    @staticmethod
    def get_latest_node(universe_id: int) -> Optional[Dict]:
        """Return the most recently created node for this universe."""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM universe_nodes WHERE universe_id=? ORDER BY id DESC LIMIT 1",
                (universe_id,)
            ).fetchone()
        if not row:
            return None
        node = dict(row)
        node['agent_reactions'] = safe_json_loads(node.get('agent_reactions'), [], 'agent_reactions')
        node['branch_options']  = safe_json_loads(node.get('branch_options'),  [], 'branch_options')
        return node

    @staticmethod
    def get_tree(universe_id: int) -> Optional[Dict]:
        """Build full D3-compatible tree structure for a universe."""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM universe_nodes WHERE universe_id=? ORDER BY turn_number, id",
                (universe_id,)
            ).fetchall()
        if not rows:
            return None

        # Build node dict
        node_map = {}
        for row in rows:
            n = dict(row)
            n['children'] = []
            node_map[n['id']] = n

        root = None
        for n in node_map.values():
            parent_id = n.get('parent_id')
            if parent_id is None:
                root = n
            elif parent_id in node_map:
                node_map[parent_id]['children'].append(n)

        return root

    @staticmethod
    def get_last_n_nodes(universe_id: int, n: int) -> List[Dict]:
        """Return the last n nodes ordered by id (most recent last)."""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM universe_nodes WHERE universe_id=? ORDER BY id DESC LIMIT ?",
                (universe_id, n)
            ).fetchall()
        result = []
        for row in rows:
            node = dict(row)
            node['agent_reactions'] = safe_json_loads(node.get('agent_reactions'), [], 'agent_reactions')
            node['branch_options']  = safe_json_loads(node.get('branch_options'),  [], 'branch_options')
            result.append(node)
        result.reverse()
        return result

    # ── 实体世界状态 ────────────────────────────────────────────────────────

    @staticmethod
    def get_entity_states(universe_id: int) -> List[Dict]:
        """获取宇宙当前所有实体状态，按 updated_turn DESC 排序。"""
        with get_db() as conn:
            rows = conn.execute(
                """SELECT id, universe_id, entity_name, category, summary,
                          stance, stance_score, updated_turn
                   FROM universe_entity_states
                   WHERE universe_id=?
                   ORDER BY updated_turn DESC""",
                (universe_id,)
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def upsert_entity_state(universe_id: int, entity_name: str, category: str,
                            summary: str, stance: str, stance_score: float,
                            updated_turn: int) -> int:
        """INSERT OR REPLACE 实体当前状态（UNIQUE 约束保证 upsert 语义）。"""
        with get_db() as conn:
            cur = conn.execute(
                """INSERT INTO universe_entity_states
                   (universe_id, entity_name, category, summary, stance, stance_score, updated_turn)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(universe_id, entity_name) DO UPDATE SET
                       category     = excluded.category,
                       summary      = excluded.summary,
                       stance       = excluded.stance,
                       stance_score = excluded.stance_score,
                       updated_turn = excluded.updated_turn""",
                (universe_id, entity_name, category, summary, stance, stance_score, updated_turn)
            )
            conn.commit()
        return cur.lastrowid

    @staticmethod
    def add_entity_history(universe_id: int, entity_name: str, category: str,
                           summary: str, stance: str, stance_score: float,
                           turn_number: int) -> int:
        """追加实体状态历史快照（append-only）。"""
        with get_db() as conn:
            cur = conn.execute(
                """INSERT INTO universe_entity_history
                   (universe_id, entity_name, category, summary, stance, stance_score, turn_number)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (universe_id, entity_name, category, summary, stance, stance_score, turn_number)
            )
            conn.commit()
        return cur.lastrowid
