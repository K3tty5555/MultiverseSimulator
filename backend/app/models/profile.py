"""用户档案数据访问层"""

import json
from datetime import datetime, timezone
from typing import Optional, Dict, List
from ..database import get_db
from ..utils.safe_json import safe_json_loads


class ProfileRepository:

    @staticmethod
    def get() -> Optional[Dict]:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM profiles ORDER BY id LIMIT 1"
            ).fetchone()
            if not row:
                return None
            profile = dict(row)
            profile['structured'] = safe_json_loads(profile.get('structured'), {}, 'profile_structured')
            files = conn.execute(
                "SELECT * FROM profile_files WHERE profile_id = ?", (profile['id'],)
            ).fetchall()
            profile['files'] = [dict(f) for f in files]
            return profile

    @staticmethod
    def upsert(display_name: str = None, age: int = None, structured: Dict = None) -> Dict:
        now = datetime.now(timezone.utc).isoformat()
        structured_json = json.dumps(structured or {}, ensure_ascii=False)
        with get_db() as conn:
            existing = conn.execute("SELECT id FROM profiles LIMIT 1").fetchone()
            if existing:
                # 保存当前版本到历史记录（在更新前快照）
                conn.execute("""
                    INSERT INTO profile_versions (profile_id, display_name, age, structured, summary)
                    SELECT id, display_name, age, structured, summary FROM profiles WHERE id = ?
                """, (existing['id'],))
                # 只保留最近 5 个版本
                conn.execute("""
                    DELETE FROM profile_versions
                    WHERE profile_id = ? AND id NOT IN (
                        SELECT id FROM profile_versions WHERE profile_id = ?
                        ORDER BY id DESC LIMIT 5
                    )
                """, (existing['id'], existing['id']))
                conn.execute(
                    """UPDATE profiles SET display_name=?, age=?, structured=?, updated_at=?
                       WHERE id=?""",
                    (display_name, age, structured_json, now, existing['id'])
                )
                conn.commit()
                return ProfileRepository.get()
            else:
                conn.execute(
                    """INSERT INTO profiles (display_name, age, structured, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (display_name, age, structured_json, now, now)
                )
                conn.commit()
                return ProfileRepository.get()

    @staticmethod
    def get_versions() -> list:
        """获取档案版本列表（最近 5 个）"""
        with get_db() as conn:
            rows = conn.execute("""
                SELECT id, display_name, age, saved_at FROM profile_versions
                ORDER BY id DESC LIMIT 5
            """).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_version(version_id: int) -> Optional[Dict]:
        """获取特定版本的完整档案数据"""
        with get_db() as conn:
            row = conn.execute("""
                SELECT * FROM profile_versions WHERE id = ?
            """, (version_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def update_summary(summary: str):
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            conn.execute(
                "UPDATE profiles SET summary=?, updated_at=? WHERE id=(SELECT id FROM profiles LIMIT 1)",
                (summary, now)
            )
            conn.commit()

    @staticmethod
    def add_file(filename: str, file_type: str, source: str, content: str = None) -> Dict:
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            profile = conn.execute("SELECT id FROM profiles LIMIT 1").fetchone()
            if not profile:
                ProfileRepository.upsert()
                profile = conn.execute("SELECT id FROM profiles LIMIT 1").fetchone()
            conn.execute(
                """INSERT INTO profile_files (profile_id, filename, file_type, source, content, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (profile['id'], filename, file_type, source, content, now)
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM profile_files WHERE profile_id=? ORDER BY id DESC LIMIT 1",
                (profile['id'],)
            ).fetchone()
            return dict(row)

    @staticmethod
    def delete_file(file_id: int):
        with get_db() as conn:
            conn.execute("DELETE FROM profile_files WHERE id=?", (file_id,))
            conn.commit()

    @staticmethod
    def get_all_files() -> List[Dict]:
        with get_db() as conn:
            profile = conn.execute("SELECT id FROM profiles LIMIT 1").fetchone()
            if not profile:
                return []
            rows = conn.execute(
                "SELECT * FROM profile_files WHERE profile_id=?", (profile['id'],)
            ).fetchall()
            return [dict(r) for r in rows]
