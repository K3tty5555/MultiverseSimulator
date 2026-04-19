---
name: art-pipeline
description: >
  LifePlanner 美术素材流水线。从需求确认到集成验证的完整流程，
  确保素材在生成前就确定了集成方案。
argument-hint: "[用途描述，如：MyUniverseView 空态插画]"
---

按照 LifePlanner 美术素材流水线执行素材生成与集成。

## 流程

### 阶段 1：需求确认

先确认以下信息（$ARGUMENTS 未提供的需向用户询问）：
- 素材用途：用在哪个页面/组件的什么位置？
- 视觉角色：主视觉插画（`<img>` 标签）还是装饰纹理（`::before/::after` 伪元素）？
- 尺寸比例：16:9 / 4:3 / 1:1 / 3:2

### 阶段 2：设计集成方案

**先确定怎么放，再生成图。** 读取 `.claude/agents/visual-design.md`，用视觉设计 Agent 确定：
- AI 生成 prompt（融合"重返未来 1999 + 羊皮纸"风格）
- CSS 集成方案（选择下方某一种）：
  - **主视觉**：`<img>` 标签，指定 width/height/object-fit/border-radius
  - **装饰纹理**：`::before/::after` + opacity 15-25% + `mask-image` 渐变淡出
  - **全屏背景**：`background: linear-gradient(overlay), var(--img-*)` 多层叠加
- 放置位置的 CSS 细节（定位、层级、与现有元素的空间关系）

### 阶段 3：生成素材

调用 baoyuskill：
```bash
npx -y bun /Users/xiaowu/.claude/skills/baoyu-imagine/scripts/main.ts \
  --prompt "{prompt}" \
  --image "frontend/public/art/{filename}.png" \
  --ar "{aspect_ratio}"
```

### 阶段 4：CSS 集成

1. 在 `frontend/src/styles/design.css` 添加 CSS 变量：`--img-{name}: url('/art/{filename}.png')`
2. 按阶段 2 的方案写入目标组件的 `<template>` 和 `<style>`

### 阶段 5：视觉验证

启动开发服务器（如未运行），在浏览器中检查：
- 素材是否在预定位置正确显示
- 是否与周围 UI 元素和谐（不遮盖文字、不破坏布局）
- 不同窗口宽度下表现是否合理

## 集成红线

- 禁止 opacity < 10%（不可见等于没做）
- 装饰纹理必须加 `mask-image` 渐变淡出，禁止硬边
- 装饰纹理仅覆盖非文字区域
- 生成前必须确定集成方案，禁止先生成再找位置

## 项目风格关键词

Retro-futuristic 1999, aged parchment texture, Art Deco geometric patterns,
warm sepia + neon cyan/amber accents, clockwork/compass motifs,
calligraphy meets circuit traces, dreamy bokeh, watercolor-digital mixed media
