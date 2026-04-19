"""一次性为所有角色生成史实年表（绕 HTTP rate limit，直接用函数调用）。
跑法：cd backend && .venv/bin/python3 scripts/bulk_generate_canonical.py
"""

import sys
import os
import time
import traceback

# 禁用 buffering，让后台日志实时可见
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db, init_db
from app.config import Config
from app.models.canonical_event import CanonicalEventRepository
from app.utils.ai_assist import generate_canonical_events

# 初始化 DB 连接配置（复用 app 的 DB_PATH）
init_db(Config.DB_PATH)


def collect_characters():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT DISTINCT name, universe_type, COALESCE(world_label, '') AS world_label FROM (
              SELECT protagonist_name as name, universe_type, world_label
              FROM parallel_universes
              WHERE status='active' AND is_personal_main=0 AND protagonist_name != ''
              UNION
              SELECT a.name, u.universe_type, u.world_label
              FROM universe_agents a JOIN parallel_universes u ON u.id=a.universe_id
              WHERE a.deleted_at IS NULL AND u.status='active' AND u.is_personal_main=0
            ) ORDER BY name
        """).fetchall()
    return [(r['name'], r['universe_type'], r['world_label'] or None) for r in rows]


def main():
    chars = collect_characters()
    print(f"共 {len(chars)} 个角色待生成\n")

    for idx, (name, utype, world_label) in enumerate(chars, 1):
        existing = CanonicalEventRepository.list_for(name, utype, world_label)
        if existing:
            print(f"[{idx}/{len(chars)}] {name} ({utype}·{world_label}) — 已有 {len(existing)} 条，跳过")
            continue

        print(f"[{idx}/{len(chars)}] {name} ({utype}·{world_label}) — 生成中...", end=' ', flush=True)
        t0 = time.time()
        try:
            events = generate_canonical_events(name, utype, world_label or '')
            dur = time.time() - t0
            if events:
                saved = CanonicalEventRepository.bulk_create(name, utype, world_label, events)
                print(f"✓ {len(saved)} 条 ({dur:.1f}s)")
            else:
                print(f"— 空结果 ({dur:.1f}s)")
        except Exception as e:
            print(f"✗ 失败：{type(e).__name__}: {str(e)[:200]}")
            traceback.print_exc()

        time.sleep(1)   # 稍微缓一下避免 LLM provider 抖动

    print("\n全部完成。")


if __name__ == '__main__':
    main()
