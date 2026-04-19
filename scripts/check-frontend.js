#!/usr/bin/env node
/**
 * 前端冒烟检查
 * 1. Vue 文件中零硬编码十六进制颜色
 * 2. design.css 中存在所有必要 token
 * 3. 关键修复模式存在于对应组件中
 *
 * 用法：node scripts/check-frontend.js
 */

const fs = require('fs')
const path = require('path')

const ROOT = path.resolve(__dirname, '..')
const FRONTEND_SRC = path.join(ROOT, 'frontend', 'src')
const DESIGN_CSS = path.join(FRONTEND_SRC, 'styles', 'design.css')

let exitCode = 0
const errors = []
const ok = []

function fail(msg) {
  errors.push('  ✗ ' + msg)
  exitCode = 1
}
function pass(msg) {
  ok.push('  ✓ ' + msg)
}

// ─────────────────────────────────────────────────────────────────
// 工具：递归收集 .vue 文件
// ─────────────────────────────────────────────────────────────────
function collectVueFiles(dir) {
  const result = []
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) result.push(...collectVueFiles(full))
    else if (entry.name.endsWith('.vue')) result.push(full)
  }
  return result
}

// ─────────────────────────────────────────────────────────────────
// 工具：从文件读取 <style> 块内容
// ─────────────────────────────────────────────────────────────────
function extractStyleBlocks(content) {
  const blocks = []
  const re = /<style[^>]*>([\s\S]*?)<\/style>/gi
  let m
  while ((m = re.exec(content)) !== null) blocks.push(m[1])
  return blocks.join('\n')
}

// ─────────────────────────────────────────────────────────────────
// 检查 1：Vue 文件中禁止硬编码十六进制颜色
// ─────────────────────────────────────────────────────────────────
console.log('\n[1] 检查硬编码颜色...')

// D3 颜色映射表中的字面量是允许的（annotated with token name comments）
// 匹配模式：#RRGGBB 或 #RGB，排除注释行和 D3 常量映射中
const HEX_RE = /#[0-9a-fA-F]{3,8}\b/g
// 允许的例外：D3 const C = {...} 块（DecisionTreePanel.vue）
const D3_CONST_BLOCK_RE = /const C\s*=\s*\{[\s\S]*?\}/

const vueFiles = collectVueFiles(FRONTEND_SRC)
const hardcodedViolations = []

for (const file of vueFiles) {
  const content = fs.readFileSync(file, 'utf8')
  const styleContent = extractStyleBlocks(content)

  // 从 <style> 块中查找硬编码颜色
  const styleLines = styleContent.split('\n')
  for (let i = 0; i < styleLines.length; i++) {
    const line = styleLines[i].trim()
    // 跳过注释行
    if (line.startsWith('//') || line.startsWith('*') || line.startsWith('/*')) continue
    const matches = line.match(HEX_RE)
    if (matches) {
      // 检查是否在 CSS 变量定义（design.css 本身允许）
      const rel = path.relative(ROOT, file)
      hardcodedViolations.push(`${rel}:style ~L${i + 1}: ${line.trim()} (${matches.join(', ')})`)
    }
  }

  // 从 <script> 块中查找硬编码颜色，排除 D3 const C 映射
  const scriptRe = /<script[^>]*>([\s\S]*?)<\/script>/gi
  let sm
  while ((sm = scriptRe.exec(content)) !== null) {
    let scriptContent = sm[1]
    // 移除 D3 const C 映射块（允许字面量）
    scriptContent = scriptContent.replace(D3_CONST_BLOCK_RE, '')
    const scriptLines = scriptContent.split('\n')
    for (let i = 0; i < scriptLines.length; i++) {
      const line = scriptLines[i].trim()
      if (line.startsWith('//') || line.startsWith('*')) continue
      // 仅检查字符串中的颜色（排除注释中的说明）
      const strMatches = line.match(/['"`]([^'"`]*#[0-9a-fA-F]{6}[^'"`]*)[`'"]/g)
      if (strMatches) {
        for (const s of strMatches) {
          if (/#[0-9a-fA-F]{6}/.test(s)) {
            const rel = path.relative(ROOT, file)
            hardcodedViolations.push(`${rel}:script ~L${i + 1}: ${line.trim()}`)
          }
        }
      }
    }
  }
}

if (hardcodedViolations.length === 0) {
  pass(`所有 ${vueFiles.length} 个 Vue 文件无硬编码颜色`)
} else {
  fail(`发现 ${hardcodedViolations.length} 处硬编码颜色：`)
  hardcodedViolations.slice(0, 20).forEach(v => errors.push('    ' + v))
  if (hardcodedViolations.length > 20) {
    errors.push(`    ... 还有 ${hardcodedViolations.length - 20} 处`)
  }
}

// ─────────────────────────────────────────────────────────────────
// 检查 2：design.css 包含所有必要 token
// ─────────────────────────────────────────────────────────────────
console.log('\n[2] 检查 design.css token 完整性...')

const REQUIRED_TOKENS = [
  '--c-parchment',
  '--c-terracotta',
  '--c-terracotta-dark',
  '--c-terracotta-tint',
  '--c-overlay-dark',
  '--c-overlay-text',
  '--c-builtin-bg',
  '--c-builtin-text',
  '--c-builtin-border',
  '--c-sky-bg',
  '--c-sky-text',
  '--c-success-dark',
  '--shadow-lift',
  '--shadow-modal',
  '--shadow-toast',
  '--shadow-terracotta-ring',
  '--c-danger-bg',
  '--c-danger-border',
  '--c-danger-text',
  '--c-warning-bg',
  '--c-warning-text',
  '--font-serif',
  '--font-sans',
]

const cssContent = fs.readFileSync(DESIGN_CSS, 'utf8')
const missingTokens = REQUIRED_TOKENS.filter(t => !cssContent.includes(t))

if (missingTokens.length === 0) {
  pass(`design.css 包含全部 ${REQUIRED_TOKENS.length} 个必要 token`)
} else {
  fail(`design.css 缺少以下 token：${missingTokens.join(', ')}`)
}

// ─────────────────────────────────────────────────────────────────
// 检查 3：关键修复模式
// ─────────────────────────────────────────────────────────────────
console.log('\n[3] 检查关键修复模式...')

const PATTERN_CHECKS = [
  {
    file: 'frontend/src/components/Step3Simulation.vue',
    pattern: /createSimulationStream/,
    desc: 'Step3 使用 SSE 流式推演（createSimulationStream）',
  },
  {
    file: 'frontend/src/components/Step3Simulation.vue',
    pattern: /resultsByOption/,
    desc: 'Step3 使用 Map 存储结果（按 option_id 去重，支持断线重连）',
  },
  {
    file: 'frontend/src/components/Step4Report.vue',
    pattern: /reportError/,
    desc: 'Step4 包含 reportError 状态（SSE 断开时显示错误）',
  },
  {
    file: 'frontend/src/components/Step4Report.vue',
    pattern: /MODE_GEN_PHASES/,
    desc: 'Step4 包含 MODE_GEN_PHASES 模式文案映射',
  },
  {
    file: 'frontend/src/components/Step5Interaction.vue',
    pattern: /aria-hidden="true"/,
    desc: 'Step5 消息头像添加 aria-hidden="true"（无效 ARIA 角色修复）',
  },
  {
    file: 'frontend/src/components/Step5Interaction.vue',
    pattern: /const sending\s*=\s*ref\(false\)/,
    desc: 'Step5 包含 sending 防重复提交锁',
  },
  {
    file: 'frontend/src/views/DecisionView.vue',
    pattern: /decisionMode\s*!==\s*null/,
    desc: 'DecisionView 步骤渲染用 decisionMode !== null 守卫（防空白屏）',
  },
  {
    file: 'frontend/src/views/DecisionView.vue',
    pattern: /stepNames\s*=\s*computed/,
    desc: 'DecisionView stepNames 为 computed（模式动态切换）',
  },
  {
    file: 'frontend/src/components/Step3Simulation.vue',
    pattern: /streamError/,
    desc: 'Step3 包含 streamError 状态（SSE 断开时显示错误）',
  },
]

for (const check of PATTERN_CHECKS) {
  const fullPath = path.join(ROOT, check.file)
  if (!fs.existsSync(fullPath)) {
    fail(`文件不存在：${check.file}`)
    continue
  }
  const content = fs.readFileSync(fullPath, 'utf8')
  if (check.pattern.test(content)) {
    pass(check.desc)
  } else {
    fail(check.desc)
  }
}

// ─────────────────────────────────────────────────────────────────
// 汇总
// ─────────────────────────────────────────────────────────────────
console.log('\n─────────────────────────────────────────')
ok.forEach(m => console.log(m))
if (errors.length > 0) {
  console.log('')
  errors.forEach(m => console.error(m))
}
console.log('─────────────────────────────────────────')
console.log(`\n结果：${ok.length} 项通过，${errors.length > 0 ? errors.filter(e => e.trim().startsWith('✗')).length : 0} 项失败\n`)

process.exit(exitCode)
