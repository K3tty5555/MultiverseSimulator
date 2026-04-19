---
name: lp-ui-iterate
description: 基于 playwright 截图的 UI 自动化迭代流程。在大幅度 UI 修改后调用；playwright 截图 → 视觉/交互/产品 agent 并行评审 → 按共识修复代码 → 再截图再评审，最多 3 轮收敛后交付。和 lp-review 配套：lp-review 审代码文档，lp-ui-iterate 审实际渲染界面。
---

# LifePlanner UI 自动化迭代 Loop

## 适用场景

- 用户描述了 UI 层面的大幅改动（首页重做、子页面重构、视觉重构）并完成了初版
- 用户说"你改完自己截图给几个 agent 看一下，吵几轮再给我看"
- 视觉范式切换（如项目内从旧风格迁移到新风格锚）

不适用：小 bug 修复、纯后端改动、代码层面的 code review（那是 `/lp-review` 的职责）。

## 参数

通过 `$ARGUMENTS` 传递。支持以下（都可选）：

- `url` —— 要截图的页面 URL，默认 `http://localhost:3003/`
- `rounds` —— 最大迭代轮数，默认 `3`
- `viewport` —— 视口尺寸，默认 `1440x900`
- `agents` —— 参与评审的 agent 组合，默认 `visual-design,interaction-design,product`

示例调用：
```
/lp-ui-iterate                                  # 默认跑首页 3 轮
/lp-ui-iterate /agents 2                        # 角色长廊页跑 2 轮
/lp-ui-iterate rounds=4 agents=visual-design    # 只跑视觉师 4 轮
```

## 执行流程

### 阶段 0 · 环境准备

**0.1 解析参数** —— 应用默认值。

**0.2 清理僵尸 playwright chrome**（常见问题：上一次 session 没关干净）：
```bash
pkill -f "ms-playwright/mcp-chrome" 2>/dev/null
```

**0.3 用 ToolSearch 加载 playwright MCP 工具**（这些是 deferred tools）：
```
select:mcp__plugin_playwright_playwright__browser_navigate,mcp__plugin_playwright_playwright__browser_take_screenshot,mcp__plugin_playwright_playwright__browser_resize,mcp__plugin_playwright_playwright__browser_wait_for,mcp__plugin_playwright_playwright__browser_close
```

**0.4 检查 dev server**：
- 默认前端 dev 跑在 `http://localhost:3003/`，后端 `http://localhost:5001/`
- 如果 navigate 失败，提示用户「前端未启动，请在项目根 `cd frontend && npm run dev`」

### 阶段 1 · 基线截图（v0）

1. `browser_resize` 到 viewport 尺寸
2. `browser_navigate` 到 URL
3. `browser_wait_for` 2-3 秒（确保首次加载完成）
4. `browser_take_screenshot` 到工作区根 `<page-name>-v0.png`（例：`home-v0.png`, `agents-v0.png`）

文件命名约定：**`{页面名}-v{轮数}.png`**，放在项目根目录（`/Users/xiaowu/workplace/LifePlanner/`），便于多轮对比。

### 阶段 2 · 迭代循环（Round 1 → Round max_rounds）

每轮执行：

#### 2.1 并行派发评审 Agent

使用 `Agent` 工具并行派发。每个 agent 的 prompt **必须包含**：

1. **截图绝对路径**（通过 Read 图片直接看）
2. **项目定位**（从 `~/.claude/projects/-Users-xiaowu-workplace-LifePlanner/memory/project_multiverse_pivot.md` 摘取关键立意）
3. **该 agent 的评审视角**（从 `.claude/agents/{name}.md` 读取）
4. **上轮共识**（Round 2+ 时，附上 Round N-1 agent 共指的问题摘要）
5. **输出要求**：
   - 判断上轮问题修复度（每条一句话：修到位 / 部分修 / 没改善）
   - 列出本轮仍存在或新引入的问题
   - 给出 Top 3 最优先修复项（严重 > 重要 > 建议）
   - 字数 ≤ 250-350 字

**Agent 角色分工**（默认三人团）：
| Agent | 文件 | 视角 |
|---|---|---|
| `visual-design` | `.claude/agents/visual-design.md` | 视觉层次、留白、色彩协调、美术素材集成 |
| `interaction-design` | `.claude/agents/interaction-design.md` | CTA 焦点、动线、键盘可达、状态反馈 |
| `product` | `.claude/agents/product.md` | 叙事传达、价值感知、冷启动、入口发现性 |

#### 2.2 汇总共识

把 3 方返回的 Top 3 合并：
- 按 **严重度**（严重 > 重要 > 建议）排序
- 多方共指的问题优先级上升一档
- 排除视角分歧大的点（不同角色看法对立时先按用户意愿）
- 输出"Round N 应修清单"(3-5 条)

#### 2.3 按共识修代码

根据"Round N 应修清单"直接 Edit / Write 相关文件。每处改动简短 commit message 风格的 inline 注释。

**原则**：
- 每轮只修 Top 3-5 条，不一口气改所有
- 保留可 rollback 的简洁改动
- 不引入新抽象（等本 loop 结束后再重构）

#### 2.4 重新截图（vN）

- `browser_navigate`（重新加载，确保 HMR 完成）
- `browser_wait_for` 2-3 秒
- `browser_take_screenshot` 到 `<page-name>-v{N}.png`

#### 2.5 收敛判断

停止条件（任一满足）：
- 3 agent 的 Top 问题中「严重 + 重要」总数 ≤ 2 条
- 已达到 `max_rounds`
- 出现循环震荡（Round N 和 Round N-2 的改动互斥）—— 此时停止并交给用户决策

**日志**：每轮结束记录「Round N 修了什么 / 还剩什么」到主上下文（便于后续汇报）。

### 阶段 3 · 交付用户

不再询问，直接给结果：

```
## 迭代完成 · N 轮收敛

[附最终截图]

### 每轮改动摘要
- Round 1 → 2: [修了什么]
- Round 2 → 3: [修了什么]

### 残余次优先级问题（没在本 loop 修）
- [问题 1]（为什么留到后面）
- [问题 2]

### 你的选择
(A) 接受，继续下一步
(B) 哪个点还要调
(C) 再跑一轮 agent loop
```

## 工作原则

- **允许 agent 吵**：agent 之间会有不同视角，主程序负责综合，不要强行合并冲突
- **以共识为修改锚**：三方共指的问题 = 严重，单方指出 = 次优先
- **截图先于 agent**：每一轮的输入是**真实渲染的 UI**，不是代码描述
- **主程序是裁判**：Agent 不直接改代码，主程序汇总后改代码
- **失败降级**：如果 playwright 工具失败（可能是 chrome 被锁），降级为提示用户手动刷新 + 直接代码审视（等同 `/lp-review 前端`）
- **不替代 lp-review**：本 skill 管渲染界面的视觉/交互/产品，代码层质量（命名、模块边界、类型安全、硬编码色）仍由 `/lp-review` 把关

## 常见坑（从第一次使用提炼）

- **Playwright 僵尸进程**：session 间可能残留 chrome 进程占用 profile 目录，必须在 start 前 `pkill -f "ms-playwright/mcp-chrome"`
- **HMR 竞态**：改完代码立即截图可能截到旧页面。每次截图前 `navigate + wait 3s`（比 `wait 1s` 稳）
- **Agent 输出爆炸**：不加字数限制会拿到 1000+ 字的报告，严格限制 ≤ 300 字
- **循环震荡**：Round N 改 A → Round N+1 agent 说 A 改错了 → Round N+2 又改回去。出现这种情况就停，让用户拍板
- **截图文件路径**：playwright MCP 默认保存在 `.playwright-mcp/` 或 cwd。统一用相对项目根的路径 `<name>-v{N}.png`，便于 Read 和对比

## 示例（从 2026-04-19 首页重做 loop 抽取）

- Round 1 发现：CTA 4 个同权 / 空态全"还没有"/ 毛玻璃过浓遮主视觉
- Round 2 修后发现：推荐书颜色过艳 / 入口仍重复 / 核心价值没一句话点破
- Round 3 修后：三方共识降到 2 条次优先级（纸卡实体化 / 一键创建 API） → 收敛交付

---

**执行时注意**：本 skill 的调用需要前端 dev server 在跑 + playwright MCP 已注册。首次调用如果 toolsearch 显示 playwright 工具可用但 navigate 失败，先检查 dev server。
