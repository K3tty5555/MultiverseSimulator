#!/usr/bin/env python3
"""
一次性脚本：为三国乱世 18 个角色批量生成并写入 canonical events。

运行方式：
    cd backend
    .venv/bin/python3 tools/seed_canonical_events.py

幂等：该角色已有 >0 条记录则跳过，不覆盖用户编辑过的数据。
预计耗时：5-10 分钟（每角色约 5-8 个 events × 18）。
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.config import Config
from app.database import init_db
from app.models.canonical_event import CanonicalEventRepository
from app.utils.ai_assist import generate_canonical_events

# 对 LLM 拒绝生成的传说性角色，直接硬编码史实年表
HARDCODED_EVENTS = {
    '貂蝉': [
        {'year': 189, 'title': '入王允府，学歌舞伎艺',
         'description': '貂蝉幼年被收养于司徒王允府中，习歌舞、学礼仪，成为府中歌姬。王允视其为义女，悉心培养，貂蝉容色绝世，倾国倾城，在乱世中成为王允手中一枚潜伏的政治棋子。', 'sort_order': 1},
        {'year': 192, 'title': '王允设连环计，貂蝉受命',
         'description': '汉献帝初平三年，王允欲除董卓，苦无良策，见貂蝉后设下"连环美人计"——先将貂蝉许嫁吕布，再献于董卓为妾，借两人情义制造嫌隙。貂蝉明知险境，慷慨应允，甘冒性命之危为汉室赴死。', 'sort_order': 2},
        {'year': 192, 'title': '凤仪亭相会，离间吕董',
         'description': '貂蝉在凤仪亭与吕布私会，被董卓撞破，董卓怒掷方天画戟，险伤吕布。貂蝉借机哭诉董卓欺凌，挑拨义父子二人反目。此后吕布对董卓积怨日深，连环计初见成效，成为汉末最著名的美人离间之局。', 'sort_order': 3},
        {'year': 192, 'title': '吕布诛董卓，连环计功成',
         'description': '王允与吕布里应外合，设伏于北掖门。吕布亲手刺杀董卓，汉末第一大奸雄就此覆灭。貂蝉的美人计是整个刺董行动的核心，她以一己之身搅动了两个枭雄的关系，使连环计成功。此后貂蝉随吕布，史书中关于其下落记载极少。', 'sort_order': 4},
        {'year': 198, 'title': '下邳城破，貂蝉命运成谜',
         'description': '建安三年，曹操、刘备联军围困下邳，吕布兵败被擒，在白门楼被杀。关于貂蝉此后命运，史书全无记载，民间流传多种版本：或随吕布同死，或被关羽保护归隐，或流落他处。貂蝉因此成为三国中最神秘的历史人物之一。', 'sort_order': 5},
    ],
}

CHARACTERS = [
    {'name': '曹操',   'universe_type': 'historical', 'world_label': '三国乱世'},
    {'name': '刘备',   'universe_type': 'historical', 'world_label': '三国乱世'},
    {'name': '周瑜',   'universe_type': 'historical', 'world_label': '三国乱世'},
    {'name': '孙权',   'universe_type': 'historical', 'world_label': '三国乱世'},
    {'name': '袁绍',   'universe_type': 'historical', 'world_label': '三国乱世'},
    {'name': '关羽',   'universe_type': 'historical', 'world_label': '三国乱世'},
    {'name': '张飞',   'universe_type': 'historical', 'world_label': '三国乱世'},
    {'name': '赵云',   'universe_type': 'historical', 'world_label': '三国乱世'},
    {'name': '鲁肃',   'universe_type': 'historical', 'world_label': '三国乱世'},
    {'name': '曹丕',   'universe_type': 'historical', 'world_label': '三国乱世'},
    {'name': '荀彧',   'universe_type': 'historical', 'world_label': '三国乱世'},
    {'name': '郭嘉',   'universe_type': 'historical', 'world_label': '三国乱世'},
    {'name': '司马懿', 'universe_type': 'historical', 'world_label': '三国乱世'},
    {'name': '陆逊',   'universe_type': 'historical', 'world_label': '三国乱世'},
    {'name': '吕布',   'universe_type': 'historical', 'world_label': '三国乱世'},
    {'name': '董卓',   'universe_type': 'historical', 'world_label': '三国乱世'},
    {'name': '诸葛亮', 'universe_type': 'historical', 'world_label': '三国乱世'},
    {'name': '貂蝉',   'universe_type': 'historical', 'world_label': '三国乱世'},
]


def main():
    init_db(Config.DB_PATH)
    total = len(CHARACTERS)
    success, skipped, failed = 0, 0, 0

    for i, char in enumerate(CHARACTERS, 1):
        name = char['name']
        utype = char['universe_type']
        wlabel = char['world_label']

        existing = CanonicalEventRepository.list_for(name, utype, wlabel)
        if existing:
            print(f'[{i}/{total}] {name} — 已有 {len(existing)} 条记录，跳过')
            skipped += 1
            continue

        hardcoded = HARDCODED_EVENTS.get(name)
        if hardcoded:
            print(f'[{i}/{total}] 正在写入 {name} 的硬编码年表...', end='', flush=True)
            try:
                created = CanonicalEventRepository.bulk_create(name, utype, wlabel, hardcoded)
                print(f' ✓ 写入 {len(created)} 条')
                success += 1
            except Exception as e:
                print(f' ✗ 失败：{e}')
                failed += 1
            continue

        print(f'[{i}/{total}] 正在生成 {name} 的史实年表...', end='', flush=True)
        try:
            events = generate_canonical_events(name, utype, wlabel)
            if not events:
                print(f' ✗ LLM 返回空列表，跳过')
                failed += 1
                continue
            created = CanonicalEventRepository.bulk_create(name, utype, wlabel, events)
            print(f' ✓ 生成 {len(created)} 条')
            success += 1
        except Exception as e:
            print(f' ✗ 失败：{e}')
            failed += 1

    print(f'\n完成：成功 {success} / 跳过 {skipped} / 失败 {failed}（共 {total} 个角色）')
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
