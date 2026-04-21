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
            ('关羽', 160, '蜀汉五虎上将之首，字云长，刮骨疗毒、过五关斩六将，义薄云天，后败走麦城遇难，被尊为武圣。'),
            ('张飞', 167, '蜀汉猛将，字翼德，声如雷霆、勇猛无双，长坂坡一人喝退曹军数万，性烈如火。'),
            ('赵云', 168, '蜀汉五虎将，字子龙，长坂坡单骑救主，义薄云天，终身忠勇，白袍将军之名震天下。'),
            ('鲁肃', 172, '东吴战略家，字子敬，提出榻上策构建孙刘联盟，宽厚持重，是维系三方平衡的关键人物。'),
            ('曹丕', 187, '曹操嫡长子，字子桓，建立曹魏，迫汉献帝禅让，结束四百年大汉，工诗词善文章，有文帝之号。'),
            ('荀彧', 163, '曹操首席谋士，字文若，被称王佐之才，深谋远虑助曹操统一北方，然忠于汉室，最终与曹操决裂。'),
            ('郭嘉', 170, '曹操最信任的谋士，字奉孝，智谋奇绝，连提十胜论，英年早逝，曹操痛称惜哉奉孝，天丧孤也。'),
            ('司马懿', 179, '三国后期最终赢家，字仲达，深藏不露、隐忍数十年，以高平陵之变夺魏国实权，子孙建立晋朝统一天下。'),
            ('陆逊', 183, '东吴军事家，字伯言，夷陵之战火烧刘备连营，化解蜀汉报仇之兵，后官至丞相，却因卷入立嗣争议而郁郁而终。'),
            ('吕布', 169, '三国第一猛将，字奉先，曾戟刺丁原、弑杀董卓，骁勇无双却反复无常，白门楼被曹操处决，留下人中吕布马中赤兔之名。'),
            ('董卓', 139, '东汉末年军阀，应何进之召入京，废少帝立献帝，倒行逆施引天下共讨，最终死于义子吕布之手。'),
            ('貂蝉', 169, '中国古代四大美人之一，司徒王允义女，以美人计离间董卓与吕布，成功促成吕布弑杀董卓，为东汉除一大害。'),
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
        _CHECKPOINTS = [
                {
                    'title': '黄巾之乱：苍天已死，黄天当立',
                    'year_label': '中平元年 · 184 AD',
                    'premise': (
                        '中平元年，太平道张角以"苍天已死，黄天当立"为号召，率三十六方黄巾军同时起义，天下震动。'
                        '汉灵帝急诏各地州郡招募义兵镇压。刘备、关羽、张飞桃园结义，投身讨贼；'
                        '曹操受命讨黄巾，初露军事才华；袁绍等世家子弟亦乘乱扩充势力。'
                        '乱世序幕在此刻骤然揭开，你将以何种身份，踏入这场改变中国四百年的历史漩涡？'
                    ),
                    'available': ['曹操', '刘备', '袁绍'],
                    'difficulty': 'easy',
                    'sort_order': 0,
                },
                {
                    'title': '何进之变：宦官与外戚的最后博弈',
                    'year_label': '中平六年 · 189 AD',
                    'premise': (
                        '汉灵帝驾崩，大将军何进辅佐少帝即位，宦官十常侍把持宫廷。'
                        '何进欲诛十常侍，却被说服召凉州军阀董卓入京为援，袁绍力谏不听。'
                        '宦官抢先动手，何进身死，袁绍率兵杀入宫中大肆屠戮宦官，皇帝出奔城外。'
                        '此时董卓铁骑已逼近洛阳城下。这场政变的每一个决策，都将重塑汉帝国的命运。'
                    ),
                    'available': ['袁绍', '曹操'],
                    'difficulty': 'medium',
                    'sort_order': 1,
                },
                {
                    'title': '关东讨董：十八路诸侯聚义',
                    'year_label': '初平元年 · 190 AD',
                    'premise': (
                        '董卓把持朝政、废帝另立、迁都长安，倒行逆施激起天下公愤。'
                        '关东诸侯以袁绍为盟主，曹操、孙坚、刘备等十八路义军聚于虎牢关下，会盟讨董。'
                        '然而诸侯各怀私心：有人想借机扩充地盘，有人首鼠两端，真正出力的寥寥无几。'
                        '历史的十字路口：联盟能否突破虎牢、真正消灭董卓，还是就此分裂、各自割据？'
                    ),
                    'available': ['袁绍', '曹操', '孙权'],
                    'difficulty': 'medium',
                    'sort_order': 2,
                },
                {
                    'title': '计除董卓：一曲凤仪亭',
                    'year_label': '初平三年 · 192 AD',
                    'premise': (
                        '董卓专权三年，天下怨恨沸腾。司徒王允设下连环计：将义女貂蝉同时许嫁董卓与吕布，'
                        '挑拨这对干父子反目。凤仪亭中，吕布与貂蝉私会被董卓撞破，戟掷吕布，嫌隙由此种下。'
                        '吕布骁勇冠绝天下，却为美色所迷；董卓权倾朝野，却被义子所弑。'
                        '你将扮演这场密谋中的哪个角色？历史的棋局，落子无悔。'
                    ),
                    'available': ['貂蝉', '吕布', '董卓'],
                    'difficulty': 'hard',
                    'sort_order': 3,
                },
                {
                    'title': '迎奉天子：曹操的战略抉择',
                    'year_label': '建安元年 · 195 AD',
                    'premise': (
                        '汉献帝辗转逃回洛阳，宫室残破、百官饥困。曹操谋士荀彧力主迎天子至许都，'
                        '"奉天子以令不臣"，此乃千载难逢之机；另一派则顾虑迎天子等于引火烧身。'
                        '袁绍曾有此机会却错失，如今曹操面临同样的抉择。'
                        '是否迎奉天子？迎了之后如何处置君臣关系、如何防止旧臣干政？这一步将奠定曹魏霸业的根基。'
                    ),
                    'available': ['曹操', '荀彧'],
                    'difficulty': 'medium',
                    'sort_order': 4,
                },
                {
                    'title': '袁术称帝：第一个僭越者的命运',
                    'year_label': '建安二年 · 197 AD',
                    'premise': (
                        '袁术得传国玉玺，自恃汝南袁氏四世三公、兵力雄厚，在寿春僭号称帝，建号仲氏。'
                        '此举立刻使他成为天下公敌：曹操、袁绍、吕布、孙策四路大军相继讨伐。'
                        '袁术粮草断绝、众叛亲离，欲将玉玺传给袁绍以求援，却已回天乏术。'
                        '以袁绍或曹操的视角：面对这个乱世中第一个冒险称帝的人，应如何布局获取最大利益？'
                    ),
                    'available': ['袁绍', '曹操'],
                    'difficulty': 'easy',
                    'sort_order': 5,
                },
                {
                    'title': '下邳之战：飞将吕布的覆灭',
                    'year_label': '建安三年 · 198 AD',
                    'premise': (
                        '吕布占据徐州，三姓家奴之名令人不齿，却凭无匹武力令诸侯忌惮。'
                        '曹操与刘备联军围困下邳，决水灌城。吕布高顺、陈宫力战不敌，城中粮尽援绝。'
                        '部将侯成、宋宪、魏续临阵倒戈，吕布被缚送至曹操面前。'
                        '此刻：吕布苦求刘备求情，刘备却一言定吕布生死；曹操亦在除掉威胁与收揽猛将之间权衡。'
                    ),
                    'available': ['吕布', '曹操', '刘备'],
                    'difficulty': 'hard',
                    'sort_order': 6,
                },
                {
                    'title': '衣带诏：汉室的最后抵抗',
                    'year_label': '建安五年 · 200 AD',
                    'premise': (
                        '汉献帝不甘傀儡，秘密将诏书藏于衣带之中，授予国舅董承，命其联络刘备等密谋诛杀曹操。'
                        '刘备身在曹营心在汉，借出兵截击袁术之机出逃，举兵徐州反曹。'
                        '然而事机不密，董承等人被曹操所杀，刘备在徐州兵败，关羽被俘降曹，张飞各自逃散。'
                        '在曹操权力最盛之时，忠于汉室的人们还能做什么？这场密谋是否有成功的可能？'
                    ),
                    'available': ['刘备', '曹操'],
                    'difficulty': 'hard',
                    'sort_order': 7,
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
                    'sort_order': 8,
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
                    'sort_order': 9,
                },
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
                    'sort_order': 10,
                },
                {
                    'title': '张松献图：益州易主的序幕',
                    'year_label': '建安十六年 · 211 AD',
                    'premise': (
                        '益州牧刘璋懦弱，张松出使曹操遭冷遇后转投刘备，献上益州地图并力邀刘备入川为援。'
                        '刘备得诸葛亮、庞统辅佐，以帮助刘璋抵御张鲁为名，率军西进入川。'
                        '庞统献上、中、下三策：上策奇袭成都；中策诈斩张松拉拢的将领；下策退回荆州再图徐图。'
                        '以客军身份入益州，进退之间皆是凶险，刘备该如何在道义与现实之间抉择？'
                    ),
                    'available': ['刘备', '诸葛亮'],
                    'difficulty': 'medium',
                    'sort_order': 11,
                },
                {
                    'title': '成都之战：益州归刘，三分初成',
                    'year_label': '建安十九年 · 214 AD',
                    'premise': (
                        '庞统阵亡落凤坡后，诸葛亮、张飞、赵云分兵入川增援。刘备重兵围困成都，'
                        '刘璋粮草充足却军心动摇，谋士劝降者众。'
                        '城中百姓不欲再战，刘璋最终开城投降，刘备得益州。'
                        '此刻：投降是否是刘璋唯一的选择？若坚守，结局会否不同？'
                        '益州既得，刘备如何安抚旧臣、整合新旧势力、为下一步争汉中做准备？'
                    ),
                    'available': ['刘备', '诸葛亮'],
                    'difficulty': 'easy',
                    'sort_order': 12,
                },
                {
                    'title': '汉中之战：称王前夕的豪赌',
                    'year_label': '建安二十四年 · 219 AD',
                    'premise': (
                        '刘备与曹操争夺战略要地汉中，双方在定军山一带激战。'
                        '黄忠阵斩曹操大将夏侯渊，曹操亲率大军来援，刘备坚守不出，以赵云奇袭断其粮道。'
                        '曹操无功而返，刘备得汉中，随即自立汉中王。'
                        '同一时间，关羽在荆州发动北伐，威震华夏，却引来吴魏联合夹击——'
                        '汉中大胜与荆州危机在同一年爆发，蜀汉的命运走向了怎样的分叉？'
                    ),
                    'available': ['刘备', '曹操', '赵云'],
                    'difficulty': 'hard',
                    'sort_order': 13,
                },
                {
                    'title': '关羽北伐：威震华夏与走麦城',
                    'year_label': '建安二十四年 · 219 AD',
                    'premise': (
                        '关羽率荆州军北伐，水淹七军、擒于禁、斩庞德，威震华夏，曹操一度欲迁都避锋。'
                        '然而东吴吕蒙白衣渡江，偷袭荆州；关羽进退失据，后方失守，军心涣散。'
                        '关羽败走麦城，兵败被擒，拒降而死。荆州从此永失，蜀汉两路北伐的战略构想成为泡影。'
                        '若关羽当时选择与东吴维持同盟，结局是否会不同？这场悲剧是否有另一种可能？'
                    ),
                    'available': ['关羽', '曹操', '孙权'],
                    'difficulty': 'hard',
                    'sort_order': 14,
                },
                {
                    'title': '曹丕篡汉：四百年大汉的终章',
                    'year_label': '黄初元年 · 220 AD',
                    'premise': (
                        '曹操薨逝，曹丕继魏王之位。汉献帝在群臣"劝进"压力下，颁下禅让诏书，'
                        '将帝位让于曹丕，延续四百年的大汉王朝宣告终结。'
                        '曹丕精心策划了这场禅让仪式，以示"顺应天命"而非武力篡夺。'
                        '汉室忠臣们的最后抵抗是什么？曹丕如何处置既想利用又要防范的荀彧旧部？'
                        '一个王朝的落幕，是历史的必然还是人心向背的结果？'
                    ),
                    'available': ['曹丕', '曹操'],
                    'difficulty': 'medium',
                    'sort_order': 15,
                },
                {
                    'title': '夷陵之战：陆逊火烧连营',
                    'year_label': '黄初三年 · 222 AD',
                    'premise': (
                        '关羽之死令刘备悲怒交加，不顾诸葛亮、赵云劝阻，倾举国之力伐吴报仇。'
                        '吴主孙权任命年轻的陆逊为大都督，以避锋芒、坚守不出应对蜀军。'
                        '刘备连营七百里，却在盛夏扎营于山林密集之处。陆逊抓住时机，火烧连营。'
                        '蜀军溃败，刘备狼狈逃至白帝城，蜀汉元气大伤，从此再无主动进攻东吴的实力。'
                    ),
                    'available': ['刘备', '陆逊', '孙权'],
                    'difficulty': 'hard',
                    'sort_order': 16,
                },
                {
                    'title': '白帝城托孤：诸葛亮的天下重任',
                    'year_label': '章武三年 · 223 AD',
                    'premise': (
                        '夷陵惨败后刘备病重于白帝城，自知时日无多，将幼子刘禅及蜀汉江山托付于诸葛亮。'
                        '"若嗣子可辅，辅之；如其不才，君可自取。"这句话让诸葛亮泪流满面，誓死效忠。'
                        '面对百废待兴的蜀汉、强大的曹魏、不稳的东吴联盟、平息的南方蛮族——'
                        '诸葛亮接下这份千钧重担，他的下一步战略是什么？如何在内忧外患中重振汉室？'
                    ),
                    'available': ['刘备', '诸葛亮', '赵云'],
                    'difficulty': 'medium',
                    'sort_order': 17,
                },
                {
                    'title': '北伐第一战：街亭得失与马谡之争',
                    'year_label': '建兴六年 · 228 AD',
                    'premise': (
                        '诸葛亮稳定后方后，举兵北伐，声东击西令曹魏三郡望风而降，天水获姜维。'
                        '然而关键一役，诸葛亮派马谡守街亭——此人熟读兵法却无实战经验。'
                        '马谡违背诸葛亮部署，自作主张弃城据山，被张郃切断水源，街亭失守，北伐功亏一篑。'
                        '诸葛亮挥泪斩马谡，自贬三级。此战若马谡守住街亭，历史会否不同？司马懿如何应对？'
                    ),
                    'available': ['诸葛亮', '司马懿'],
                    'difficulty': 'medium',
                    'sort_order': 18,
                },
                {
                    'title': '五丈原：星落秋风五丈原',
                    'year_label': '青龙二年 · 234 AD',
                    'premise': (
                        '诸葛亮第六次北伐，与司马懿在渭水相持百余日。诸葛亮频繁挑战，甚至送去女人衣服羞辱，'
                        '司马懿坚守不出，以逸待劳。蜀军粮草补给困难，诸葛亮积劳成疾，病重卧榻。'
                        '秋风起时，诸葛亮于五丈原中军帐中辞世，临终部署退军、将兵符传于姜维。'
                        '蜀军秘不发丧，有序撤退，司马懿追击不及，叹曰"死诸葛走生仲达"。一颗星就此陨落。'
                    ),
                    'available': ['诸葛亮', '司马懿'],
                    'difficulty': 'hard',
                    'sort_order': 19,
                },
                {
                    'title': '高平陵之变：司马懿的最终棋局',
                    'year_label': '正始十年 · 249 AD',
                    'premise': (
                        '曹爽专权，带着魏帝曹芳去高平陵祭祀。司马懿等待了多年的时机终于到来——'
                        '洛阳空虚，他奉郭太后诏令，以迅雷之势关闭城门、占据武库、控制要道。'
                        '曹爽听信司马懿"只免官爵不伤性命"之诺，放弃抵抗投降。'
                        '随后曹爽三族被夷。这场不流血的政变，让曹魏实权彻底落入司马氏之手。'
                        '这一天是司马懿隐忍数十年后的总爆发，棋局已定，天下归司马。'
                    ),
                    'available': ['司马懿'],
                    'difficulty': 'hard',
                    'sort_order': 20,
                },
                {
                    'title': '阴平奇袭：蜀汉的最后防线',
                    'year_label': '景元四年 · 263 AD',
                    'premise': (
                        '司马昭遣钟会率十万大军伐蜀，姜维扼守剑阁天险，魏军久攻不下。'
                        '邓艾率三万奇兵，凿山开路、穿越阴平七百里无人区，"攀木缘磴、鱼贯而进"，'
                        '出现在成都西面的江油、绵竹，蜀汉腹地毫无防备。'
                        '诸葛亮之子诸葛瞻战死绵竹，后主刘禅出城投降，蜀汉至此灭亡。'
                        '姜维在剑阁得知，设计令钟会反叛，却在兵变中身死。乱世终章，何以至此？'
                    ),
                    'available': ['司马懿', '诸葛亮'],
                    'difficulty': 'hard',
                    'sort_order': 21,
                },
        ]
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
            for _cp in _CHECKPOINTS:
                conn.execute(
                    """INSERT INTO world_checkpoints
                       (world_id, title, year_label, premise, available_persona_names, difficulty, sort_order)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (_wid, _cp['title'], _cp['year_label'], _cp['premise'],
                     json.dumps(_cp['available'], ensure_ascii=False),
                     _cp['difficulty'], _cp['sort_order'])
                )
        else:
            # 迁移：三国乱世扩充节点（3 → 22）及 sort_order 同步
            _wid = _world_row[0]
            _existing_cp = {r[0] for r in conn.execute(
                "SELECT title FROM world_checkpoints WHERE world_id=?", (_wid,)
            )}
            for _cp in _CHECKPOINTS:
                if _cp['title'] not in _existing_cp:
                    conn.execute(
                        """INSERT INTO world_checkpoints
                           (world_id, title, year_label, premise, available_persona_names, difficulty, sort_order)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (_wid, _cp['title'], _cp['year_label'], _cp['premise'],
                         json.dumps(_cp['available'], ensure_ascii=False),
                         _cp['difficulty'], _cp['sort_order'])
                    )
                conn.execute(
                    "UPDATE world_checkpoints SET sort_order=? WHERE world_id=? AND title=?",
                    (_cp['sort_order'], _wid, _cp['title'])
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
