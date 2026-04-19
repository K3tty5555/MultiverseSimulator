# 视觉档案 · Canonical 页面定稿截图

2026-04-19 立。每张是该页面的"当前定稿态"快照，供回溯与文档引用。

升级页面时请**同步更新对应截图**（保持文件名不变，覆盖即可）。一次性验证流程截图应放在 `.playwright-mcp/`（已 gitignored），不要堆在此处或项目根。

| 文件 | 页面 | 说明 |
|------|------|------|
| `home.png` | `/` | 档案馆首页 · 本命档案 + 最近批注 + 平行档案卷宗架 |
| `profile.png` | `/profile` | 研究员登记簿 · 基本信息 + 价值观权衡 |
| `settings.png` | `/settings` | 馆舍设置 · AI 模型配置 |
| `agents-gallery.png` | `/agents` | 角色长廊 · 11 张三国立绘 v3 终版 |
| `world-explore.png` | `/universe` | 历史卷宗索引 · 典藏 + 我的卷宗 tab |
| `universe-split.png` | `/universe/:id` | 卷宗对读 · 左批注索引 + 右叙事流 + panel-divider |

---

## Playwright MCP 截图约定

- 一次性验证截图（iteration checks）→ `.playwright-mcp/`（gitignored）
- 定稿截图（canonical snapshot）→ `docs/screenshots/`（入库）
- 禁止截图落到项目根

生成命令示例：
```js
await page.screenshot({ path: 'docs/screenshots/<name>.png' })
```
