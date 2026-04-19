# LifePlanner 项目规范

## 沟通语言

**与用户沟通时请使用中文。**

## 项目结构

```
LifePlanner/
├── frontend/        # Vue 3 + Vite，端口 3000
├── backend/         # Flask Python，端口 5001
├── locales/         # i18n 翻译文件（zh.json / en.json）
└── CLAUDE.md
```

## 启动方式

```bash
# 后端（开发）
cd backend && .venv/bin/python3 run.py

# 前端（开发）
cd frontend && npm run dev

# Electron 开发窗口（先启动上面两个，再运行）
npm run electron:dev   # 根目录

# 打包分发（macOS）
npm run dist:mac

# 打包分发（Windows，需在 Windows 环境）
npm run dist:win
```

## Electron 打包说明

```
LifePlanner/
├── electron/
│   ├── main.js         # Electron 主进程
│   ├── preload.js      # 预加载脚本（最小权限）
│   └── loading.html    # 启动等待画面
├── lifeplanner.spec    # PyInstaller 打包规格
├── package.json        # 根目录：Electron + electron-builder
└── dist-bin/           # PyInstaller 输出（.gitignore）
    └── lifeplanner[.exe]
```

**打包流程：**
1. `npm run build:frontend` → Vite 构建到 `frontend/dist/`
2. `npm run build:backend` → PyInstaller 将 Flask + `frontend/dist/` + `locales/` 打包为单一可执行文件 `dist-bin/lifeplanner`
3. `electron-builder` 将 Electron 壳 + Flask 二进制 → `.dmg` / `.exe`

**数据目录（生产模式）：**
- macOS：`~/Library/Application Support/LifePlanner/`
- Windows：`%APPDATA%\LifePlanner\`
- 通过 `LIFEPLANNER_DATA_DIR` 环境变量覆盖

## 技术栈

- **前端**：Vue 3 + Vite + Vue Router + D3.js + Axios
- **后端**：Flask + SQLite（WAL 模式）+ OpenAI 兼容 LLM 接口
- **样式**：Claude 设计系统（parchment 背景、Georgia serif、terracotta 强调色）

## 设计规范

- 背景色：`--c-parchment: #f5f4ed`
- 强调色：`--c-terracotta: #c96442`
- 标题字体：Georgia / Noto Serif SC（serif）
- 正文字体：Inter / Noto Sans SC（sans）
- 设计 token 统一定义在 `frontend/src/styles/design.css`
- 图标规范：禁用 emoji 作 UI 图标，统一内联 SVG（`avatar_emoji` 等用户数据字段除外）

### 桌面 App UX 规范

**页面应遵循「打开即工作」原则，不使用 Web 落地页思维。**

主界面（有数据）条件渲染模式：

```
加载态  →  loading === true           → 居中加载动画，不渲染其他内容
空态    →  !loading && data.length === 0  → 简洁欢迎屏，单一主操作
主界面  →  !loading && data.length > 0   → 数据内容为主，导航提供快捷入口
```

- 导航栏的「主操作」按钮（如「+ 新决策」）仅在有历史数据时显示
- Hero section / 使用说明步骤 / 营销文案在有数据后不再渲染
- 与三态正交的全局提示（如未配置 banner）独立渲染，不干扰三态切换

## 内容安全红线

**内置历史人物库严禁收录以下类别，违者触发法律风险：**
- 近现代政治人物（无论哪国、无论立场）
- 军事/战争主导者
- 宗教领袖
- 任何在世的人

**内置库只收录：** 商业创业者、科学家、艺术家/作家、哲学家（古代）、运动员等非政治性人物。
有争议的统一不放，宁缺毋滥。用户可自由创建自定义角色（风险自担）。

## 功能开发流程

**开始实现新功能之前，必须先用 EnterPlanMode（superpowers）制定实现计划，与用户确认后再动手编码。**

**每个新功能完成后，必须执行六人专家团审视（`/lp-review`），再交付给用户。**

### 六人专家团

Agent 定义存放在 `.claude/agents/`，按场景灵活组合：

| 场景 | Agent 组合 |
|------|-----------|
| 全栈功能 | 全部 6 个（产品 + 交互设计 + 视觉设计 + 架构 + 前端 + 后端）|
| 页面视觉 | 视觉设计 + 交互设计 + 前端 |
| 纯前端逻辑 | 交互设计 + 前端 |
| 后端 API | 架构 + 后端 |
| 新功能评审 | 产品 + 交互设计 |
| 设计方案 | 产品 + 交互设计 + 视觉设计 |
| 安全/性能审计 | 架构 + 后端 + 前端 |

用户也可直接指定任意组合（如 `/lp-review 架构+视觉`）。

审视发现的严重和重要问题，必须在交付前修复。建议类问题列出供用户决策。

## 开发约定

- LLM 调用统一通过 `backend/app/utils/llm_client.py`
- 数据库操作统一通过 `backend/app/models/` 下的 Repository 类
- 后台任务（模拟推演、档案合成）使用 `TaskManager` 单例 + 线程池
- SSE 流式输出用于报告生成和 Step 5 对话
- 轮询用于后台任务进度查询

### 前端状态管理约定

**异步检查的布尔状态初始值用 `null`，不用 `true` 或 `false`。**

```js
// 正确：null = 未知/加载中
const llmConfigured = ref(null)   // null | true | false
const profileComplete = ref(null) // null | true | false

// 错误：初始值预设结论，catch 静默时状态不正确
const llmConfigured = ref(true)
```

- UI 条件判断用严格比较（`=== false`），不用 `!`，避免 `null` 被当作 falsy 误渲染
- `catch` 保守降级：检查请求失败时，视为「未配置/未完善」而非「已配置/已完善」
- 异步加载后才渲染的区域用 `v-if="status !== null"` 延迟挂载，避免布局跳变（CLS）

```html
<!-- 正确：状态未知时不渲染，避免内容跳变 -->
<div v-if="profileStatus !== null" class="status-strip">...</div>

<!-- 错误：先渲染加载占位再替换，导致 CLS -->
<div v-if="profileStatus === null">检查中...</div>
<div v-else>{{ actualContent }}</div>
```

### HTML 语义约定

**禁止在 `<button>` 内嵌套交互式元素。**

折叠区域与其内部的独立操作（如「清空」）必须拆分为各自独立的 `<button>`，用外层 `<div>` 承载布局：

```html
<!-- 正确 -->
<div class="section-header">
  <button class="toggle-btn" @click="open = !open">标题 ▼</button>
  <button class="action-btn" @click="doAction">操作</button>
</div>

<!-- 禁止：button 内嵌 role="button" 或另一个 button -->
<button @click="open = !open">
  标题
  <span role="button" @click.stop="doAction">操作</span>
</button>
```

### 美术素材约定

使用 `/art-pipeline` 执行完整流水线。**生成前必须确定集成方案，不可先生成再找位置。**

| 用途 | 实现方式 | opacity |
|------|---------|---------|
| 主视觉（空态插画、品牌横幅） | `<img>` 标签 | 100%（原图） |
| 装饰纹理（卡片 header、面板角落） | `::before/::after` + `mask-image` 渐变淡出 | 15-25% |
| 全屏背景（YearFlip 覆盖层） | 多层 CSS `background`（暗色渐变 + 图像叠加） | 按设计 |

- 禁止 opacity < 10%（不可见等于没做）
- 装饰纹理必须加 `mask-image` 渐变，禁止硬边
- 素材文件放 `frontend/public/art/`，CSS 变量 `--img-*` 定义在 `design.css`

**文生图 API 凭据**（`ARK_API_KEY` 等）：
- 项目级 env 文件：`.env.art`（已 gitignore；模板见 `.env.art.example`）
- 生成前执行：`set -a && source .env.art && set +a`

**三国立绘规范**（canonical 画风 / 构图 / 势力色 / prompt 模板）：
- 见 `backend/prompts/image-anchors/_SANGUO-PORTRAIT-STYLE.md`
- Batch 模板：`backend/prompts/image-anchors/batch-sanguo-portraits.json`
- 新增三国角色立绘必须按此规范，不得回退工笔重彩/silhouette 等旧风格

### Composable 标准库

| Composable | 用途 | 替代 |
|-----------|------|------|
| `useEventStream` | SSE 连接（自动清理、超时） | 手动 `new EventSource` |
| `useApiRequest` | API 请求（loading/error/data + toast） | try/catch/finally 模板 |
| `useToast` | 全局通知 | 各组件自行实现 |

新增 SSE 或 API 请求时，必须使用对应 Composable，禁止手动管理 EventSource 生命周期。

### 后端韧性约定

- **JSON 解析**：统一 `safe_json_loads()`，禁止裸 `json.loads()`
- **LLM 调用**：统一 `llm_client.py` 的 `chat_with_retry()`
- **SQLite 连接**：`threading.local()` 线程独立，禁止 `check_same_thread=False`
- **多表操作**：同一事务内完成，失败回滚

### 项目级 Hooks

`.claude/settings.json` 定义了 4 个 PostToolUse 自动守卫：

| Hook | 检查 | 触发文件 |
|------|------|---------|
| `lint-hardcoded-colors` | 禁止硬编码颜色（`#xxxxxx`），必须用 Token | `.vue` / `.css` |
| `lint-json-loads` | 禁止裸 `json.loads()`，必须用 `safe_json_loads` | `.py` |
| `lint-eventsource` | `new EventSource` 必须有 `onBeforeUnmount` 清理 | `.vue` |
| `lint-component-size` | 组件超 400 行警告 | `.vue` |
