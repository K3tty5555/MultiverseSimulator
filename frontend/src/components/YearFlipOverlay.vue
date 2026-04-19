<template>
  <Teleport to="body">
    <Transition name="yf-fade">
      <div
        v-if="show"
        ref="rootEl"
        class="yf-root"
        tabindex="-1"
        @keydown.esc.stop="skipToEnd"
      >
        <div :class="['yf-stage', { 'yf-landing': isLanding, 'yf-settled': isSettled }]">
          <!-- 上方标签 -->
          <p class="yf-label">{{ labelText }}</p>

          <!-- 翻牌数字盘 -->
          <div class="yf-board" :class="{ 'yf-board--fast': isFast }">
            <div v-for="idx in 4" :key="idx" class="yf-cell">
              <!-- 常态数字（始终显示当前值） -->
              <div class="yf-digit" aria-hidden="true">{{ cur[idx - 1] }}</div>
              <!-- 中间分割线 -->
              <div class="yf-hinge" aria-hidden="true" />
              <!-- 翻牌片段：旧值下半，翻走后露出新值下半 -->
              <div v-if="flipping[idx - 1]" class="yf-flap" aria-hidden="true">
                <div class="yf-flap-inner">{{ prev[idx - 1] }}</div>
              </div>
            </div>
          </div>

          <!-- 年份单位 -->
          <span class="yf-unit" aria-live="polite">年</span>

          <!-- 跳过提示 -->
          <p class="yf-hint">按 ESC 跳过</p>

          <!-- A2: 屏幕阅读器一次性播报（视觉上隐藏） -->
          <div class="sr-only" aria-live="assertive" aria-atomic="true">
            {{ announceText }}
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  show:       { type: Boolean, required: true },
  targetYear: { type: Number,  required: true },
  labelText:  { type: String,  default: '时光逆流' },
})
const emit = defineEmits(['complete'])

// ── DOM & 状态 ────────────────────────────────────────────
const rootEl   = ref(null)
const isFast   = ref(false)
const isLanding = ref(false)
const isSettled = ref(false)
const announceText = ref('')

// 4 位数字的当前值与上一值
const cur     = ref(['0', '0', '0', '0'])
const prev    = ref(['0', '0', '0', '0'])
const flipping = ref([false, false, false, false])

// ── 取消令牌（每次新动画 +1，旧循环检测到则退出）────────────
let animId = 0
let emitGuard = false   // 幂等保护：防止 complete 被多次 emit

// ── 工具函数 ─────────────────────────────────────────────
function padYear(y) {
  return String(Math.max(1, Math.round(y))).padStart(4, '0')
}

function setYear(y) {
  cur.value = padYear(y).split('')
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

function cancelled(id) {
  return animId !== id
}

// ── 动画入口 ─────────────────────────────────────────────
watch(() => props.show, async (v) => {
  if (!v) {
    announceText.value = ''
    return
  }
  emitGuard = false   // 每次新动画重置幂等标志
  // A2: 动画开始时给屏幕阅读器一次性播报
  announceText.value = `${props.labelText}，正在回溯至公元 ${props.targetYear} 年`
  await nextTick()
  rootEl.value?.focus()
  const id = ++animId
  await runAnimation(id)
})

async function runAnimation(id) {
  const currentYear = new Date().getFullYear()
  const target = props.targetYear
  const gap    = currentYear - target

  // 重置
  isFast.value    = false
  isLanding.value = false
  isSettled.value = false
  flipping.value  = [false, false, false, false]
  setYear(currentYear)
  prev.value = [...cur.value]

  if (gap <= 0) {
    // 目标年份 >= 当前年份，无需倒流，直接结束
    safeEmit()
    return
  }

  if (gap > 10) {
    await fastPhase(id, currentYear, target + 10)
    if (cancelled(id)) return
    await slowPhase(id, target + 10, target)
  } else {
    await slowPhase(id, currentYear, target)
  }

  if (cancelled(id)) return
  await doLanding(id)
}

// ── 快速阶段：模糊滚动 ─────────────────────────────────────
async function fastPhase(id, fromYear, toYear) {
  isFast.value = true
  const DURATION = 1300   // ms
  const TICK     = 20     // ms
  const steps    = Math.round(DURATION / TICK)
  const stepSize = (fromYear - toYear) / steps

  let y = fromYear
  for (let i = 0; i < steps; i++) {
    await sleep(TICK)
    if (cancelled(id)) { isFast.value = false; return }
    y -= stepSize
    setYear(y)
  }
  setYear(toYear)
  isFast.value = false
}

// ── 慢速阶段：split-flap 翻牌 ───────────────────────────
const SLOW_INTERVALS = [80, 100, 120, 145, 175, 210, 250, 305, 360, 420]

async function slowPhase(id, fromYear, toYear) {
  let year  = fromYear
  const steps = fromYear - toYear
  for (let i = 0; i < steps; i++) {
    const delay = SLOW_INTERVALS[Math.min(i, SLOW_INTERVALS.length - 1)]
    await sleep(delay)
    if (cancelled(id)) return
    const nextY = year - 1
    await flipToYear(id, year, nextY)
    if (cancelled(id)) return
    year = nextY
  }
}

async function flipToYear(id, oldYear, newYear) {
  const oldDigits = padYear(oldYear).split('')
  const newDigits = padYear(newYear).split('')

  const changed = []
  for (let i = 0; i < 4; i++) {
    if (oldDigits[i] !== newDigits[i]) changed.push(i)
  }

  if (changed.length === 0) {
    setYear(newYear)
    return
  }

  // 记录旧值，更新当前值
  prev.value = oldDigits
  setYear(newYear)

  // 等 DOM 更新后（.yf-digit 已显示新值），再挂载翻牌片段
  await nextTick()
  changed.forEach(i => { flipping.value[i] = true })

  // 等翻牌动画完成（0.28s CSS + 40ms 缓冲）
  await sleep(320)

  // 无论是否取消，都清理 flipping 状态，防止残留
  changed.forEach(i => { flipping.value[i] = false })
  if (cancelled(id)) return
}

// ── 落幕：弹跳 + 发光 + 停留 ───────────────────────────
async function doLanding(id) {
  isLanding.value = true
  await sleep(150)
  if (cancelled(id)) return
  isSettled.value = true
  await sleep(900)
  if (cancelled(id)) return
  safeEmit()
}

// ── 幂等 emit，防止多次触发 ───────────────────────────────
function safeEmit() {
  if (emitGuard) return
  emitGuard = true
  emit('complete')
}

// ── ESC 跳过 ─────────────────────────────────────────────
function skipToEnd() {
  if (!props.show) return   // overlay 未显示时不触发
  animId++                  // 取消所有在途动画
  safeEmit()
}

// ── 切换标签页时自动跳过 ──────────────────────────────────
function onVisibilityChange() {
  if (document.hidden && props.show) skipToEnd()
}
onMounted(()   => document.addEventListener('visibilitychange', onVisibilityChange))
onUnmounted(() => {
  animId++  // 卸载时取消所有在途动画，防止卸载后继续 emit
  document.removeEventListener('visibilitychange', onVisibilityChange)
})
</script>

<style scoped>
/* ── 全屏遮罩 ─────────────────────────────────────────── */
.yf-root {
  position: fixed;
  inset: 0;
  z-index: 9000;
  background:
    linear-gradient(rgba(28, 26, 20, 0.88), rgba(28, 26, 20, 0.88)),
    var(--img-yearflip, #1c1a14);
  background-size: cover;
  background-position: center;
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  outline: none;
}

/* 遮罩淡入/淡出（落幕延长至 0.8s，避免黑底到羊皮纸色温断层） */
.yf-fade-enter-active { transition: opacity 0.3s ease; }
.yf-fade-leave-active { transition: opacity 0.8s ease-out; }
.yf-fade-enter-from,
.yf-fade-leave-to    { opacity: 0; }

/* ── 中央容器 ────────────────────────────────────────── */
.yf-stage {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.yf-landing {
  animation: yf-bounce 0.7s cubic-bezier(0.2, 0.8, 0.4, 1) forwards;
}

@keyframes yf-bounce {
  0%   { transform: scale(1); }
  35%  { transform: scale(1.07); }
  100% { transform: scale(1); }
}

/* ── 标签 ────────────────────────────────────────────── */
.yf-label {
  font-family: var(--font-serif);
  font-size: 13px;
  font-weight: 400;
  letter-spacing: 6px;
  color: var(--c-terracotta);
  opacity: 0;
  animation: yf-label-in 0.5s 0.1s ease forwards;
}

@keyframes yf-label-in {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ── 数字盘 ──────────────────────────────────────────── */
.yf-board {
  display: flex;
  gap: 6px;
}

/* ── 单个数字卡片 ─────────────────────────────────────── */
.yf-cell {
  position: relative;
  width: 60px;
  height: 84px;
  background: var(--c-overlay-dark);
  border-radius: 8px;
  box-shadow:
    0 0 0 1px rgba(255, 255, 255, 0.07),
    0 6px 20px rgba(0, 0, 0, 0.6);
  perspective: 300px;
}

/* 顶部高光，模拟机械牌受光效果 */
.yf-cell::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 50%;
  background: linear-gradient(180deg, rgba(255,255,255,0.04) 0%, transparent 100%);
  border-radius: 8px 8px 0 0;
  pointer-events: none;
  z-index: 2;
}

/* ── 常态数字（始终显示当前值） ──────────────────────── */
.yf-digit {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Georgia', var(--font-serif);
  font-size: 54px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--c-overlay-text);
  line-height: 1;
  transition: text-shadow 0.4s ease;
  z-index: 1;
}

/* 快速滚动时的模糊动画 */
.yf-board--fast .yf-digit {
  animation: yf-scroll-blur 0.12s linear infinite;
}

@keyframes yf-scroll-blur {
  0%   { filter: blur(0);    transform: translateY(0); }
  35%  { filter: blur(3px);  transform: translateY(-7px); }
  65%  { filter: blur(3px);  transform: translateY(7px); }
  100% { filter: blur(0);    transform: translateY(0); }
}

/* 定格后：发光 */
.yf-settled .yf-digit {
  text-shadow: 0 0 28px rgba(201, 100, 66, 0.45);
}

/* ── 中间分割线 ──────────────────────────────────────── */
.yf-hinge {
  position: absolute;
  top: 50%;
  left: 4px; right: 4px;
  height: 1px;
  background: rgba(0, 0, 0, 0.7);
  z-index: 10;
  pointer-events: none;
}

/* ── 翻牌片段（旧值下半，翻走后露出新值） ──────────────── */
.yf-flap {
  position: absolute;
  bottom: 0;
  left: 0; right: 0;
  height: 50%;        /* = 42px（cell 的下半） */
  overflow: hidden;
  background: var(--c-overlay-dark);
  transform-origin: top center;   /* 铰链在 cell 正中 */
  animation: yf-flip-away 0.28s ease-in forwards;
  border-radius: 0 0 8px 8px;
  z-index: 5;
}

/* 翻牌片段内部：将整行数字上移，使下半对齐 */
.yf-flap-inner {
  position: absolute;
  top: -42px;   /* = -(cell height / 2) = -(84/2) */
  left: 0; right: 0;
  height: 84px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Georgia', var(--font-serif);
  font-size: 54px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--c-overlay-text);
  line-height: 1;
}

@keyframes yf-flip-away {
  0%   { transform: rotateX(0deg); }
  100% { transform: rotateX(-90deg); }
}

/* ── 年份单位 ─────────────────────────────────────────── */
.yf-unit {
  font-family: var(--font-serif);
  font-size: 20px;
  color: var(--c-overlay-text);
  letter-spacing: 3px;
  opacity: 0;
  transition: opacity 0.5s 0.2s ease;
}

.yf-settled .yf-unit {
  opacity: 1;
}

/* ── 跳过提示 ─────────────────────────────────────────── */
.yf-hint {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.42);   /* 提升对比度至约 3:1 */
  letter-spacing: 1px;
  margin-top: 4px;
  opacity: 0;
  animation: yf-hint-in 0.4s 1.2s ease forwards;  /* 1.2s 后出现，不破坏沉浸感 */
}

@keyframes yf-hint-in {
  to { opacity: 1; }
}

/* A2: 视觉隐藏但屏幕阅读器可读 */
.sr-only {
  position: absolute;
  width: 1px; height: 1px;
  margin: -1px; padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* A4: 小屏缩放数字盘 */
@media (max-width: 400px) {
  .yf-cell { width: 48px; height: 66px; }
  .yf-digit { font-size: 42px; }
  .yf-flap-inner { top: -33px; height: 66px; font-size: 42px; }
  .yf-board { gap: 4px; }
}
</style>
