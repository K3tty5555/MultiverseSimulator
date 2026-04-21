# 三国立绘规范（canonical · v3）

2026-04-19 确立。新增三国角色立绘**必须**按此规范生成，不得回退到工笔重彩 / 档案照片 / Art Deco frame 等旧风格。

---

## 一、画风锁定

**Chinese heroic character CG illustration**（中国古风商业游戏人设）：
- Semi-realistic painterly CG rendering
- 商业游戏人设质感（类《阴阳师》《王者荣耀》早期风）
- Fine painterly detail on face, fabric, armor
- 精致写实五官 + 戏剧化表情

**禁止**：工笔重彩 / 水墨 / 水彩 / 动漫 / 3D 渲染 / 档案照片 silhouette。

## 二、构图锁定

**严格 bust / close-up 半身像**：
- 只到胸/肩（mid-chest 裁切），人物占画面 65-75%
- 3/4 侧身视角，头微偏，眼神方向有意图
- **禁全身**：NO 腿 / NO 脚 / NO 腰以下 / NO 地面 / NO 蹲姿
- 武器（刀/矛/枪/扇/旗）只露部分，从画面上下边缘进入
- 2:3 比例（配合前端 AgentCard）

**禁止**：标准站立全身 / 卡牌边框 / 装饰侧边 / 顶部标题 / 底部 rules text。

## 三、势力色 × 场景映射表

| 势力 | 色调基调 | 场景氛围 | 例证角色 |
|------|---------|----------|---------|
| **蜀** SHU | 深血红 / oxblood crimson | 战场烟尘 + 火光 + 蜀军旗 | 刘备 / 诸葛亮 / 关羽 / 张飞 / 赵云 / 马超 / 黄忠 / 姜维 |
| **魏** WEI | 钢蓝 / 青灰 / midnight indigo + 金 | 宫殿内部 + 王座 + 冷侧光 + 红披风对比 | 曹操 / 司马懿 / 夏侯惇 / 张辽 / 许褚 |
| **吴** WU | 翠绿 / deep teal + 金 | 江南 / 江上战船 / 金秋帷幕 / 赤壁火焰 | 孙权 / 周瑜 / 鲁肃 / 黄盖 / 甘宁 / 太史慈 |
| **群雄** QUN | 土褐 / ochre + 琥珀灯光 | 郡城 / 边塞 / 衙门 / 驿馆 / 孤城 | 董卓 / 袁绍 / 刘表 / 刘度 / 金旋 / 吕布 |

**每张必须**：
- 背景色调与势力色一致
- 气氛写意、不具象（不是山水画）
- 人物占主体，背景虚化 blur
- 强侧/背 rim light + 戏剧 chiaroscuro

## 四、Prompt 模板

参考 `portrait-guanyu.md` / `portrait-caocao.md` 等。每个 md 必须包含 6 节：

```md
# Character Portrait · {name} (三国杀 CG 风 · {faction})

Paint {name} ({pinyin}), {faction} Kingdom {role}, in the painting style of the provided reference images.

## CRITICAL — reference usage
仅学画风技法，IGNORE 卡牌边框/文字/faction 代码。Output: full-bleed illustration only.

## CRITICAL — FRAMING (strict)
CLOSE-UP BUST PORTRAIT, head + shoulders + upper chest only, mid-chest cutoff.
NO legs, NO feet, NO waist below ribcage, NO full-body stance, NO ground.

## Style lock
(见「一、画风锁定」)

## Subject · ACTION POSE
一个戏剧瞬间的动作 + 服饰 + 武器 + 面部特写。
例：关羽挥刀瞬间 / 张飞咆哮瞬间 / 周瑜挥旗瞬间 / 鲁肃疾指地图瞬间。
**禁静态站立**。

## Background · {faction} faction
按上表势力色 + 场景氛围，always dark atmospheric, not scenic landscape.

## Mood
角色标志典故（"一身是胆" / "义薄云天" / "运筹帷幄" 等）。

## Strict negative
NO card layout / NO frame / NO side caption / NO rules-text / NO faction codes (WEI/SHU/WU) / NO name labels / NO text overlay.
NO ink/gongbi/watercolor / NO flat color-fill / NO 山水 / NO 祥云 / NO 印章 / NO anime / NO 3D render.
NO full body / NO legs / NO feet / NO ground / NO standing stance.
```

## 五、Reference 图用法

**当前 canonical references**（v3 已生成立绘，仅用于学画风）：
```
/Users/xiaowu/workplace/LifePlanner/frontend/public/art/portrait-caocao.png  # 曹操（魏·武将）
/Users/xiaowu/workplace/LifePlanner/frontend/public/art/portrait-sunquan.png  # 孙权（吴·君主）
```

**传法**：`--ref {cao-cao-card.png} {sun-quan-card.png}`
**不传诸葛亮卡 (1.png)** —— 避免 ID 复刻。
**日后**：如果 cache 路径失效，任选两张高质量三国杀官方卡图（文武各一）。

**常见副作用**：参考图是卡牌 → 模型会学整个卡牌结构（侧边文字 / 底部 rules / 势力代码）。**必须在 prompt 首段明确**：`Match ONLY the painting technique, IGNORE card frame/text/borders. Output must be a full-bleed illustration.`

若仍污染：把角色动作改为**动态瞬间**（挥刀 / 举旗 / 疾读），打破"静立肖像"的卡牌定势。

## 六、势力色选型经验

- **动态武将（蜀/魏战将）**：红/蓝背景 + 火光 + 军旗剪影 —— 最易出好图
- **儒将 / 文官（周瑜 / 鲁肃 / 孙权）**：吴绿 + 金色高光 —— 画面偏"优雅"，需动作打破静态
- **老将（黄盖）**：火船 / 战陨 —— 苦肉计瞬间、带绷带
- **群雄地方**：土褐 + 灯笼暖光 —— 夜衙读诏 / 孤城持戟

## 七、批量生成命令

```bash
set -a && source ~/.baoyu-skills/.env && set +a
# 或用项目 env：
# set -a && source .env.art && set +a

cd backend/prompts/image-anchors
bun /Users/xiaowu/.claude/skills/baoyu-imagine/scripts/main.ts \
  --batchfile batch-sanguo-portraits.json
```

Batch JSON 结构见 `batch-sanguo-portraits.json`。每个任务用：
- `promptFiles`: 相对路径 `portrait-{name}.md`
- `image`: `../../../frontend/public/art/portrait-{name}.png`
- `ar`: `2:3`
- `quality`: `2k`
- `provider`: `seedream`
- `ref`: 参考图绝对路径数组

concurrency 建议 2-3（避免 Seedream API 限流）。

## 八、集成

生成完成后把 `{name}: '/art/portrait-{name}.png'` 加入 `frontend/src/views/AgentsView.vue` 的 `portraitMap`。

卡片布局在 `AgentCard.vue`，比例 `aspect-ratio: 2/3`，`object-position: center top`。

## 九、经验沉淀

- v1（早期）：vintage archival silhouette + Art Deco oval frame → 与项目风格不符，弃
- v2（2026-04 中）：工笔重彩 / gongbi heavy color → 画风平淡，缺戏剧张力，弃
- v3（2026-04-19 本轮）：Chinese heroic CG + 势力色 + reference image + bust framing → **当前标准**

若 Seedream 对中文人物强训练偏置导致"回退到国画"：
1. 强化 negative 写更多 `NO ink/gongbi/watercolor`
2. 传参考图（必须是 CG 画风卡）
3. prompt 明确 "painterly semi-realistic CG rendering, NOT traditional Chinese painting"
4. 换动态动作描述打破静态
