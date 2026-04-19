<template>
  <section class="lp-panel panel-primary">
    <header class="lp-panel-head">
      <span class="lp-panel-seal" aria-hidden="true">⦿</span>
      <h2 class="lp-panel-title">本命档案</h2>
      <span class="lp-panel-hint">{{ greeting }}</span>
    </header>

    <!-- 档案已登记，沙盘未初始化 -->
    <article v-if="personalInitialized === false" class="primary-card primary-card--ready">
      <div class="primary-edge"></div>
      <div class="primary-inner">
        <div class="primary-badge primary-badge--ready">
          <svg width="10" height="10" viewBox="0 0 12 12" fill="none"><circle cx="6" cy="6" r="5" stroke="currentColor" stroke-width="1"/><path d="M3.5 6l2 2 3-3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
          档案已登记
        </div>
        <h3 class="primary-title">开启本命卷宗</h3>
        <p class="primary-desc">AI 将以你的档案为起点，在时间的纵深中为你推演每一次选择的余波。</p>
        <button class="lp-btn-archive lp-btn-archive--lg" :disabled="starting" @click="$emit('start')">
          {{ starting ? '正在拆封...' : '拆开第一封 →' }}
        </button>
      </div>
    </article>

    <!-- 激活但尚无节点（空卷） -->
    <article
      v-else-if="personalInitialized === true && personalNodeCount === 0"
      class="primary-card primary-card--empty"
    >
      <div class="primary-edge"></div>
      <div class="primary-inner">
        <div class="primary-head">
          <div>
            <div class="primary-badge primary-badge--waiting">
              <span class="badge-dot"></span>卷宗初启
            </div>
            <h3 class="primary-title">你的本命卷宗</h3>
            <p class="primary-desc-mini">尚未启笔 · 此卷等你写下第一个决断</p>
          </div>
          <div class="primary-meta primary-meta--zero">
            <span class="meta-num">0</span>
            <span class="meta-unit">节点</span>
          </div>
        </div>

        <div class="primary-placeholder">
          <span class="placeholder-seal" aria-hidden="true">
            <svg width="28" height="28" viewBox="0 0 32 32" fill="none"><circle cx="16" cy="16" r="13" stroke="currentColor" stroke-width="1" opacity="0.4" stroke-dasharray="2 3"/><path d="M16 9 V23 M9 16 H23" stroke="currentColor" stroke-width="1" opacity="0.5"/></svg>
          </span>
          <span class="placeholder-text">档案馆已为你准备好纸笔，只待研究员决定从何处开笔。</span>
        </div>

        <div class="primary-actions primary-actions--single">
          <button class="lp-btn-archive lp-btn-archive--lg" @click="$emit('continue')">
            写下第一笔 →
          </button>
        </div>
      </div>
    </article>

    <!-- 有节点的激活态 -->
    <article
      v-else-if="personalInitialized === true"
      class="primary-card primary-card--active"
      role="button"
      tabindex="0"
      @click="$emit('continue')"
      @keydown.enter.space.prevent="$emit('continue')"
    >
      <div class="primary-edge"></div>
      <div class="primary-inner">
        <div class="primary-head">
          <div>
            <div class="primary-badge primary-badge--active">
              <span class="badge-dot"></span>本卷活跃
            </div>
            <h3 class="primary-title">你的人生沙盘</h3>
          </div>
          <div class="primary-meta">
            <span class="meta-num">{{ personalNodeCount }}</span>
            <span class="meta-unit">节点</span>
          </div>
        </div>

        <div v-if="lastNode && lastNodeSummary" class="primary-excerpt">
          <span class="excerpt-label">最近推演</span>
          <p class="excerpt-text">{{ lastNodeSummary }}</p>
          <span class="excerpt-time">{{ formatDate(lastNode.created_at) }}</span>
        </div>

        <div class="primary-actions">
          <button class="lp-btn-archive" @click.stop="$emit('continue')">翻至此页 →</button>
          <button class="lp-btn-ghost-archive" @click.stop="$emit('new-chapter')">
            <svg width="12" height="12" viewBox="0 0 14 14" fill="none"><path d="M7 1v12M1 7h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            启新章
          </button>
        </div>
      </div>
    </article>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { formatDate } from '../../utils/format.js'
defineProps({
  personalInitialized: { type: Boolean, default: null },
  personalNodeCount: { type: Number, default: 0 },
  lastNode: { type: Object, default: null },
  lastNodeSummary: { type: String, default: '' },
  starting: { type: Boolean, default: false },
})
defineEmits(['start', 'continue', 'new-chapter'])

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 5) return '午夜值班 · 研究员'
  if (h < 12) return '清晨的档案室 · 研究员'
  if (h < 18) return '午后的档案室 · 研究员'
  return '今夜值班 · 研究员'
})
</script>

<style scoped>
.panel-primary { grid-area: primary; }

.primary-card {
  flex: 1;
  position: relative;
  margin: var(--sp-3) var(--sp-4) var(--sp-4);
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-radius: 3px;
  overflow: hidden;
  display: flex;
  box-shadow:
    inset 0 2px 0 var(--c-tarnished-gold),
    inset 0 3px 0 rgba(168, 137, 78, 0.3),
    var(--shadow-paper-edge);
  transition: box-shadow var(--duration-base) var(--ease-out), transform var(--duration-base) var(--ease-out);
}
.primary-card--active { cursor: pointer; }
.primary-card--active:hover {
  transform: translateY(-2px);
  box-shadow:
    inset 0 2px 0 var(--c-tarnished-gold),
    inset 0 3px 0 rgba(168, 137, 78, 0.3),
    var(--shadow-gold-deep),
    var(--shadow-paper-edge);
}
.primary-card--active:focus-visible { outline: 2px solid var(--c-tarnished-gold); outline-offset: 3px; }

.primary-edge {
  position: absolute; left: 0; top: 0; bottom: 0; width: 6px;
  background: linear-gradient(180deg, var(--c-oxblood) 0%, var(--c-oxblood-dark) 100%);
  border-right: 1px solid var(--c-tarnished-gold);
  flex-shrink: 0;
}
.primary-inner {
  flex: 1;
  padding: var(--sp-4) var(--sp-5) var(--sp-4) calc(var(--sp-5) + 8px);
  display: flex; flex-direction: column;
  gap: var(--sp-3);
  min-height: 0;
  overflow: hidden;
}
.primary-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: var(--sp-4);
}
.primary-badge {
  display: inline-flex; align-items: center; gap: 5px;
  align-self: flex-start;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  padding: 4px 10px;
  border-radius: 2px;
  background: var(--c-umber-deep);
  color: var(--c-ivory-aged);
  margin-bottom: var(--sp-2);
}
.primary-badge--ready { background: var(--c-deep-teal); }
.primary-badge--active { background: var(--c-oxblood); }
.primary-badge--waiting { background: var(--c-umber); }
.badge-dot {
  display: inline-block; width: 5px; height: 5px;
  border-radius: 50%; background: var(--c-tarnished-gold);
  animation: pulse-dot 1.8s ease-in-out infinite;
}
@keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:0.4} }
.primary-title {
  font-family: var(--font-serif-alt);
  font-size: 22px;
  font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.02em;
  margin: 0;
}
.primary-desc {
  font-family: var(--font-serif);
  font-size: 14px;
  color: var(--c-sepia);
  line-height: 1.7;
  max-width: 480px;
  margin: 0;
}
.primary-desc-mini {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 13px;
  color: var(--c-sepia);
  line-height: 1.5;
  margin: 4px 0 0;
}
.primary-meta {
  display: flex; flex-direction: column; align-items: flex-end;
  font-family: var(--font-serif-alt);
  color: var(--c-tarnished-gold);
}
.primary-meta--zero { color: var(--c-sepia-light); opacity: 0.6; }
.meta-num { font-size: 28px; font-weight: 600; line-height: 1; }
.meta-unit {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.15em;
  color: var(--c-sepia);
  text-transform: uppercase;
  margin-top: 2px;
}
.primary-excerpt {
  padding: var(--sp-3) var(--sp-4);
  background: rgba(168, 137, 78, 0.1);
  border-left: 2px solid var(--c-tarnished-gold);
  border-radius: 0 var(--r-sm) var(--r-sm) 0;
  display: flex; flex-direction: column; gap: 4px;
}
.excerpt-label {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--c-tarnished-gold);
}
.excerpt-text {
  font-family: var(--font-serif);
  font-size: 13px;
  color: var(--c-archive-ink);
  line-height: 1.6;
  margin: 0;
}
.excerpt-time {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--c-sepia);
  letter-spacing: 0.05em;
}
.primary-actions {
  display: flex; align-items: center; gap: var(--sp-3);
  flex-wrap: wrap;
  margin-top: var(--sp-2);
}
.primary-actions--single { justify-content: flex-start; }

.primary-placeholder {
  display: flex; align-items: center; gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: rgba(168, 137, 78, 0.08);
  border: 1px dashed rgba(168, 137, 78, 0.4);
  border-radius: 2px;
  color: var(--c-sepia);
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 13px;
  line-height: 1.5;
}
.placeholder-seal {
  color: var(--c-tarnished-gold);
  display: inline-flex;
  flex-shrink: 0;
}
.placeholder-text { letter-spacing: 0.02em; }
</style>
