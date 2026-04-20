"""SQLite 数据库初始化与连接管理"""

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone

_db_path = None
_thread_local = threading.local()


def _make_connection() -> sqlite3.Connection:
    """创建线程私有 SQLite 连接，启用 WAL 模式和外键约束。"""
    conn = sqlite3.connect(
        _db_path,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")  # WAL 模式下 NORMAL 安全且更快
    return conn


def _get_thread_conn() -> sqlite3.Connection:
    """返回当前线程的专属连接，不存在则创建。"""
    if not getattr(_thread_local, 'conn', None):
        _thread_local.conn = _make_connection()
    return _thread_local.conn


def init_db(db_path: str):
    global _db_path
    _db_path = db_path
    with get_db() as conn:
        conn.executescript(_SCHEMA)

        # 确保默认 self persona 存在（INSERT OR IGNORE 防并发重复）
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """INSERT OR IGNORE INTO personas (id, name, persona_type, bio, avatar_emoji, meta, created_at, updated_at)
               SELECT 1, '我自己', 'self', '', '🪞', '{}', ?, ?
               WHERE NOT EXISTS (SELECT 1 FROM personas WHERE persona_type='self')""",
            (now, now)
        )

        # 确保内置示例角色「诸葛亮」存在（幂等 seed）
        _meta_228 = json.dumps({"era_year": 228}, ensure_ascii=False)
        conn.execute(
            """INSERT OR IGNORE INTO personas (name, persona_type, bio, avatar_emoji, meta, created_at, updated_at)
               SELECT '诸葛亮', 'builtin',
                      '三国蜀汉丞相，字孔明，号卧龙。以《隆中对》三分天下之策辅佐刘备，鞠躬尽瘁。长于战略筹谋与内政治理，善用「谋定而后动」，在资源有限、对手强大的困境下尤见智慧。北伐中原以弱抗强，其决策思维极具参考价值。',
                      '📜', ?, ?, ?
               WHERE NOT EXISTS (
                   SELECT 1 FROM personas WHERE persona_type='builtin' AND name='诸葛亮'
               )""",
            (_meta_228, now, now)
        )

        # 内置三国角色 seed（幂等，INSERT OR IGNORE + WHERE NOT EXISTS）
        _THREE_KINGDOMS_PERSONAS = [
            ('曹操', 155, '东汉末年政治家、军事家，字孟德，挟天子以令诸侯统一北方，善用人才，兼具雄才大略与权谋心术。'),
            ('刘备', 161, '汉末枭雄，字玄德，以仁义著称，三顾茅庐求贤若渴，从织席贩履起家，历经颠沛终建蜀汉。'),
            ('周瑜', 175, '东吴名将，字公瑾，文武双全，年少得志，主导赤壁之战大破曹军，用兵如神。'),
            ('孙权', 182, '东吴主公，字仲谋，善于守成与用人，曹操叹称"生子当如孙仲谋"，赤壁之战做出联刘抗曹的关键决断。'),
            ('袁绍', 153, '东汉末年军阀，四世三公，占据冀青幽并四州，官渡之战前实力最强，然优柔寡断，不善纳谏，败于曹操。'),
        ]
        for _pname, _era_year, _pbio in _THREE_KINGDOMS_PERSONAS:
            _pmeta = json.dumps({"era_year": _era_year}, ensure_ascii=False)
            conn.execute(
                """INSERT OR IGNORE INTO personas (name, persona_type, bio, avatar_emoji, meta, created_at, updated_at)
                   SELECT ?, 'builtin', ?, '📜', ?, ?, ?
                   WHERE NOT EXISTS (
                       SELECT 1 FROM personas WHERE persona_type='builtin' AND name=?
                   )""",
                (_pname, _pbio, _pmeta, now, now, _pname)
            )

        # 三国世界与节点 seed（幂等）
        _world_row = conn.execute(
            "SELECT id FROM universe_worlds WHERE name='三国乱世' AND is_builtin=1 LIMIT 1"
        ).fetchone()
        if not _world_row:
            _world_desc = (
                '汉末天下大乱，灵帝崩后宦官与外戚争权，董卓入京废帝弑君，引发诸侯讨伐。'
                '官渡之战后曹操统一北方，赤壁之战奠定三分格局，蜀汉、东吴、曹魏鼎立。'
                '英雄豪杰各展所长，谋臣武将各出奇谋，上演中国历史上最波澜壮阔的乱世图卷。'
            )
            _world_cur = conn.execute(
                """INSERT INTO universe_worlds (name, era, description, is_builtin, created_at)
                   VALUES ('三国乱世', '汉末三国（184-280 AD）', ?, 1, ?)""",
                (_world_desc, now)
            )
            _wid = _world_cur.lastrowid
            _CHECKPOINTS = [
                {
                    'title': '赤壁前夕：曹操八十万大军压境',
                    'year_label': '建安十三年 · 208 AD',
                    'premise': (
                        '建安十三年秋，曹操平定北方后挥师南下荆州。刘表新丧，刘琮降曹，刘备仓皇南逃。'
                        '曹操自称率军八十万，战船铁锁横江，意在一举吞并江东统一天下。'
                        '刘备派诸葛亮出使东吴，孙刘是否联合、周瑜是否主战、诸葛亮能否说服孙权——'
                        '历史的天平悬而未决，一念之差将决定天下三分或归一。'
                    ),
                    'available': ['诸葛亮', '曹操', '周瑜', '孙权'],
                    'difficulty': 'hard',
                    'sort_order': 0,
                },
                {
                    'title': '隆中对：三分天下的抉择',
                    'year_label': '建安十二年 · 207 AD',
                    'premise': (
                        '建安十二年，刘备三顾茅庐，终于请出隐居隆中的诸葛亮。'
                        '此时曹操已占中原，孙权据有江东，刘备仅有新野小县、麾下数千之众。'
                        '诸葛亮提出"三分天下"之策，建议先取荆州、益州，再图北伐。'
                        '刘备是否应信任这位年仅二十七岁的布衣谋士？荆州应当如何取得？'
                        '这次对话将决定蜀汉王朝的命运。'
                    ),
                    'available': ['刘备', '诸葛亮'],
                    'difficulty': 'easy',
                    'sort_order': 1,
                },
                {
                    'title': '官渡之战：北方霸主的决战',
                    'year_label': '建安五年 · 200 AD',
                    'premise': (
                        '建安五年，曹操与袁绍在官渡对峙。袁绍坐拥四州、兵力十倍于曹操，粮草充裕；'
                        '曹操兵少粮乏，内部不稳，许多部将暗通袁绍。'
                        '战争相持阶段，曹操面临粮草告急的危机。'
                        '此时袁绍谋士许攸叛逃，带来了袁绍屯粮乌巢的秘报。'
                        '是否奇袭乌巢？如何在兵力悬殊下扭转战局？这是改变北方格局的关键时刻。'
                    ),
                    'available': ['曹操', '袁绍'],
                    'difficulty': 'medium',
                    'sort_order': 2,
                },
            ]
            for _cp in _CHECKPOINTS:
                conn.execute(
                    """INSERT INTO world_checkpoints
                       (world_id, title, year_label, premise, available_persona_names, difficulty, sort_order)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (_wid, _cp['title'], _cp['year_label'], _cp['premise'],
                     json.dumps(_cp['available'], ensure_ascii=False),
                     _cp['difficulty'], _cp['sort_order'])
                )

        # 迁移：移除已废弃的 historical_events 表（功能已被世界入口取代）
        conn.execute("DROP TABLE IF EXISTS historical_events")
        conn.execute("DROP INDEX IF EXISTS idx_historical_events_persona")

        # 迁移：parallel_universes 补加 persona_id / universe_type / is_personal_main 列
        pu_cols = {row[1] for row in conn.execute("PRAGMA table_info(parallel_universes)")}
        if 'persona_id' not in pu_cols and pu_cols:
            conn.execute(
                "ALTER TABLE parallel_universes ADD COLUMN persona_id INTEGER REFERENCES personas(id) ON DELETE SET NULL"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_parallel_universes_persona ON parallel_universes(persona_id)"
            )
        if 'universe_type' not in pu_cols and pu_cols:
            conn.execute(
                "ALTER TABLE parallel_universes ADD COLUMN universe_type TEXT NOT NULL DEFAULT 'historical'"
            )
        if 'is_personal_main' not in pu_cols and pu_cols:
            conn.execute(
                "ALTER TABLE parallel_universes ADD COLUMN is_personal_main INTEGER NOT NULL DEFAULT 0"
            )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_universes_personal "
                "ON parallel_universes(is_personal_main) WHERE is_personal_main=1"
            )
        if 'npc_ready' not in pu_cols and pu_cols:
            # 老宇宙一律视为 ready（不回去重跑预生成）
            conn.execute(
                "ALTER TABLE parallel_universes ADD COLUMN npc_ready INTEGER NOT NULL DEFAULT 1"
            )
        if 'era_label' not in pu_cols and pu_cols:
            conn.execute("ALTER TABLE parallel_universes ADD COLUMN era_label TEXT")
        if 'protagonist_bio' not in pu_cols and pu_cols:
            conn.execute("ALTER TABLE parallel_universes ADD COLUMN protagonist_bio TEXT")
        if 'world_label' not in pu_cols and pu_cols:
            conn.execute("ALTER TABLE parallel_universes ADD COLUMN world_label TEXT")
            conn.execute("""
                UPDATE parallel_universes
                SET world_label = (
                    SELECT w.name FROM world_checkpoints c
                    JOIN universe_worlds w ON w.id = c.world_id
                    WHERE c.id = parallel_universes.checkpoint_id
                )
                WHERE checkpoint_id IS NOT NULL AND world_label IS NULL
            """)
        if 'canonical_event_id' not in pu_cols and pu_cols:
            conn.execute(
                "ALTER TABLE parallel_universes ADD COLUMN canonical_event_id INTEGER "
                "REFERENCES character_canonical_events(id) ON DELETE SET NULL"
            )

        # 迁移：universe_agents 加 deleted_at（软删除，保留历史 agent_reactions 引用）
        ua_cols = {row[1] for row in conn.execute("PRAGMA table_info(universe_agents)")}
        if 'deleted_at' not in ua_cols and ua_cols:
            conn.execute("ALTER TABLE universe_agents ADD COLUMN deleted_at TEXT")

        # 迁移：universe_nodes 补加 node_type / node_year / decision_id 列
        un_cols = {row[1] for row in conn.execute("PRAGMA table_info(universe_nodes)")}
        if 'node_type' not in un_cols and un_cols:
            conn.execute(
                "ALTER TABLE universe_nodes ADD COLUMN node_type TEXT NOT NULL DEFAULT 'narrative'"
            )
        if 'node_year' not in un_cols and un_cols:
            conn.execute("ALTER TABLE universe_nodes ADD COLUMN node_year INTEGER")
        if 'decision_id' not in un_cols and un_cols:
            conn.execute(
                "ALTER TABLE universe_nodes ADD COLUMN decision_id INTEGER REFERENCES decisions(id) ON DELETE SET NULL"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_nodes_decision ON universe_nodes(decision_id)"
            )
        # 确保根节点唯一约束索引存在（防并发重复初始化）
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_nodes_root "
            "ON universe_nodes(universe_id) WHERE node_type='root'"
        )

        # 迁移：parallel_universes 补加 checkpoint_id 列
        if 'checkpoint_id' not in pu_cols:
            conn.execute(
                "ALTER TABLE parallel_universes ADD COLUMN checkpoint_id INTEGER "
                "REFERENCES world_checkpoints(id) ON DELETE SET NULL"
            )

        # 迁移：parallel_universes 补加 starter_actions 列（JSON 数组，来自 checkpoint 的预制行动）
        if 'starter_actions' not in pu_cols:
            conn.execute(
                "ALTER TABLE parallel_universes ADD COLUMN starter_actions TEXT"
            )

        # 迁移：新增实体世界状态表（CREATE TABLE IF NOT EXISTS 本身幂等）
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS universe_entity_states (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                universe_id  INTEGER NOT NULL REFERENCES parallel_universes(id) ON DELETE CASCADE,
                entity_name  TEXT NOT NULL,
                category     TEXT NOT NULL DEFAULT 'person',
                summary      TEXT NOT NULL,
                stance       TEXT NOT NULL DEFAULT 'unknown',
                stance_score REAL NOT NULL DEFAULT 0.0,
                updated_turn INTEGER NOT NULL DEFAULT 0,
                UNIQUE(universe_id, entity_name)
            );
            CREATE INDEX IF NOT EXISTS idx_entity_states_universe
                ON universe_entity_states(universe_id);
            CREATE TABLE IF NOT EXISTS universe_entity_history (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                universe_id  INTEGER NOT NULL REFERENCES parallel_universes(id) ON DELETE CASCADE,
                entity_name  TEXT NOT NULL,
                category     TEXT NOT NULL DEFAULT 'person',
                summary      TEXT NOT NULL,
                stance       TEXT NOT NULL DEFAULT 'unknown',
                stance_score REAL NOT NULL DEFAULT 0.0,
                turn_number  INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_entity_history_universe
                ON universe_entity_history(universe_id, entity_name);
        """)

        # 创建「我的宇宙」（唯一 is_personal_main=1，幂等）
        personal_row = conn.execute(
            "SELECT id FROM parallel_universes WHERE is_personal_main=1 LIMIT 1"
        ).fetchone()
        if not personal_row:
            self_persona = conn.execute(
                "SELECT id, name FROM personas WHERE persona_type='self' LIMIT 1"
            ).fetchone()
            protagonist = self_persona['name'] if self_persona else '我'
            persona_id_val = self_persona['id'] if self_persona else None
            conn.execute(
                """INSERT INTO parallel_universes
                   (title, premise, protagonist_name, protagonist_role,
                    perspective, persona_id, universe_type, is_personal_main,
                    status, created_at, updated_at)
                   VALUES (?, '', ?, NULL, 'god', ?, 'personal', 1, 'active', ?, ?)""",
                ('我的宇宙', protagonist, persona_id_val, now, now)
            )

        conn.commit()


@contextmanager
def get_db():
    """返回当前线程的专属连接。异常时自动 rollback，保证连接状态干净。"""
    conn = _get_thread_conn()
    try:
        yield conn
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise


_SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
    id          INTEGER PRIMARY KEY,
    display_name TEXT,
    age         INTEGER,
    structured  TEXT NOT NULL DEFAULT '{}',
    summary     TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS profile_files (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id  INTEGER NOT NULL REFERENCES profiles(id),
    filename    TEXT NOT NULL,
    file_type   TEXT NOT NULL,
    source      TEXT NOT NULL,
    content     TEXT,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS profile_versions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id   INTEGER NOT NULL,
    display_name TEXT,
    age          INTEGER,
    structured   TEXT,
    summary      TEXT,
    saved_at     TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (profile_id) REFERENCES profiles(id)
);

CREATE TABLE IF NOT EXISTS personas (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    persona_type TEXT NOT NULL DEFAULT 'custom',
    bio          TEXT,
    avatar_emoji TEXT DEFAULT '👤',
    meta         TEXT NOT NULL DEFAULT '{}',
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decisions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    title            TEXT NOT NULL,
    situation        TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'draft',
    decision_type    TEXT NOT NULL DEFAULT 'planning',
    persona_id       INTEGER REFERENCES personas(id),
    actual_choice_id INTEGER,
    actual_outcome   TEXT,
    time_period      TEXT,
    occurrence_year  INTEGER,
    clarification_qa TEXT,
    recommendation   TEXT,
    universe_node_id INTEGER REFERENCES universe_nodes(id) ON DELETE SET NULL,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL,
    deleted_at       TEXT
);

CREATE TABLE IF NOT EXISTS decision_options (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id INTEGER NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    label       TEXT NOT NULL,
    description TEXT,
    sort_order  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS simulation_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id     INTEGER NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    option_id       INTEGER NOT NULL REFERENCES decision_options(id) ON DELETE CASCADE,
    dimension       TEXT NOT NULL,
    time_horizon    TEXT NOT NULL,
    content         TEXT NOT NULL,
    score           REAL,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id INTEGER NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    phase       TEXT NOT NULL,
    role        TEXT NOT NULL,
    content     TEXT NOT NULL,
    metadata    TEXT,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS parallel_universes (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    title              TEXT NOT NULL,
    premise            TEXT NOT NULL,
    protagonist_name   TEXT NOT NULL,
    protagonist_role   TEXT,
    protagonist_bio    TEXT,
    perspective        TEXT NOT NULL DEFAULT 'god',
    persona_id         INTEGER REFERENCES personas(id) ON DELETE SET NULL,
    universe_type      TEXT NOT NULL DEFAULT 'historical',
    is_personal_main   INTEGER NOT NULL DEFAULT 0,
    npc_ready          INTEGER NOT NULL DEFAULT 0,
    era_label          TEXT,
    world_label        TEXT,
    canonical_event_id INTEGER REFERENCES character_canonical_events(id) ON DELETE SET NULL,
    status             TEXT NOT NULL DEFAULT 'active',
    created_at         TEXT NOT NULL,
    updated_at         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS character_canonical_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    character_name  TEXT NOT NULL,
    universe_type   TEXT NOT NULL,
    world_label     TEXT,
    year            INTEGER,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    title           TEXT NOT NULL,
    description     TEXT,
    is_edited       INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_canonical_character
    ON character_canonical_events(character_name, universe_type, world_label);

CREATE INDEX IF NOT EXISTS idx_parallel_universes_persona
    ON parallel_universes(persona_id);

CREATE TABLE IF NOT EXISTS universe_agents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    universe_id     INTEGER NOT NULL REFERENCES parallel_universes(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    role            TEXT,
    bio             TEXT,
    persona         TEXT,
    mbti            TEXT,
    stance          TEXT NOT NULL DEFAULT 'neutral',
    memory_summary  TEXT,
    last_node_id    INTEGER,
    created_at      TEXT NOT NULL,
    deleted_at      TEXT
);

CREATE TABLE IF NOT EXISTS universe_nodes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    universe_id         INTEGER NOT NULL REFERENCES parallel_universes(id) ON DELETE CASCADE,
    parent_id           INTEGER REFERENCES universe_nodes(id),
    turn_number         INTEGER NOT NULL DEFAULT 0,
    perspective         TEXT NOT NULL DEFAULT 'god',
    protagonist_action  TEXT,
    narrator_content    TEXT,
    perspective_alt     TEXT,
    agent_reactions     TEXT NOT NULL DEFAULT '[]',
    branch_prompt       TEXT,
    branch_options      TEXT,
    node_type           TEXT NOT NULL DEFAULT 'narrative',
    node_year           INTEGER,
    decision_id         INTEGER REFERENCES decisions(id) ON DELETE SET NULL,
    created_at          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_decisions_status    ON decisions(status);
CREATE INDEX IF NOT EXISTS idx_simulation_decision ON simulation_results(decision_id, option_id);
CREATE INDEX IF NOT EXISTS idx_chat_decision_phase ON chat_messages(decision_id, phase);
CREATE UNIQUE INDEX IF NOT EXISTS idx_personas_self        ON personas(persona_type) WHERE persona_type='self';
CREATE UNIQUE INDEX IF NOT EXISTS idx_personas_builtin_name ON personas(name)        WHERE persona_type='builtin';
CREATE INDEX IF NOT EXISTS idx_universe_nodes_universe ON universe_nodes(universe_id, turn_number);
CREATE INDEX IF NOT EXISTS idx_universe_agents_universe ON universe_agents(universe_id);

CREATE TABLE IF NOT EXISTS universe_entity_states (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    universe_id  INTEGER NOT NULL REFERENCES parallel_universes(id) ON DELETE CASCADE,
    entity_name  TEXT NOT NULL,
    category     TEXT NOT NULL DEFAULT 'person',
    summary      TEXT NOT NULL,
    stance       TEXT NOT NULL DEFAULT 'unknown',
    stance_score REAL NOT NULL DEFAULT 0.0,
    updated_turn INTEGER NOT NULL DEFAULT 0,
    UNIQUE(universe_id, entity_name)
);
CREATE INDEX IF NOT EXISTS idx_entity_states_universe
    ON universe_entity_states(universe_id);

CREATE TABLE IF NOT EXISTS universe_entity_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    universe_id  INTEGER NOT NULL REFERENCES parallel_universes(id) ON DELETE CASCADE,
    entity_name  TEXT NOT NULL,
    category     TEXT NOT NULL DEFAULT 'person',
    summary      TEXT NOT NULL,
    stance       TEXT NOT NULL DEFAULT 'unknown',
    stance_score REAL NOT NULL DEFAULT 0.0,
    turn_number  INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_entity_history_universe
    ON universe_entity_history(universe_id, entity_name);

CREATE TABLE IF NOT EXISTS universe_worlds (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL,
    era                 TEXT NOT NULL,
    description         TEXT NOT NULL,
    is_builtin          INTEGER NOT NULL DEFAULT 0,
    generation_keywords TEXT,
    created_at          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS world_checkpoints (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    world_id                INTEGER NOT NULL REFERENCES universe_worlds(id) ON DELETE CASCADE,
    title                   TEXT NOT NULL,
    year_label              TEXT NOT NULL,
    premise                 TEXT NOT NULL,
    available_persona_names TEXT NOT NULL DEFAULT '[]',
    difficulty              TEXT NOT NULL DEFAULT 'medium',
    sort_order              INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_world_checkpoints_world
    ON world_checkpoints(world_id, sort_order);
"""
