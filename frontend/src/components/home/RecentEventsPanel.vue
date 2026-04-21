<template>
  <section class="lp-panel panel-events">
    <header class="lp-panel-head">
      <span class="lp-panel-seal" aria-hidden="true">☞</span>
      <h2 class="lp-panel-title">最近的批注</h2>
      <span class="lp-panel-spacer"></span>
    </header>

    <ul v-if="events.length > 0" class="events-list">
      <li
        v-for="(ev, i) in events"
        :key="i"
        class="event-item"
        role="button"
        tabindex="0"
        @click="$emit('enter-universe', ev.universeId)"
        @keydown.enter.space.prevent="$emit('enter-universe', ev.universeId)"
      >
        <span class="event-dot" aria-hidden="true"></span>
        <div class="event-body">
          <div class="event-top">
            <span class="event-time">{{ formatRelativeTime(ev.time) }}</span>
            <span class="event-sep">·</span>
            <span class="event-universe">{{ ev.universeTitle }}</span>
          </div>
          <div class="event-text">{{ ev.text }}</div>
        </div>
      </li>
    </ul>

    <!-- 空态：档案馆守夜氛围卡 -->
    <div
      v-else
      class="events-empty-diary"
      role="button"
      tabindex="0"
      @click="$emit('open-universe-list')"
      @keydown.enter.space.prevent="$emit('open-universe-list')"
    >
      <div class="diary-stamp" aria-hidden="true">
        <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
          <circle cx="40" cy="40" r="36" stroke="currentColor" stroke-width="1.4" opacity="0.55"/>
          <circle cx="40" cy="40" r="28" stroke="currentColor" stroke-width="0.8" opacity="0.3" stroke-dasharray="3 3"/>
          <circle cx="40" cy="40" r="20" stroke="currentColor" stroke-width="0.5" opacity="0.2"/>
          <text x="40" y="36" font-family="serif" font-size="10" fill="currentColor" text-anchor="middle" opacity="0.6" letter-spacing="3">多元宇宙</text>
          <text x="40" y="50" font-family="serif" font-size="13" fill="currentColor" text-anchor="middle" opacity="0.75" font-weight="500">档案馆</text>
        </svg>
      </div>
      <div class="diary-content">
        <div class="diary-date">{{ dateStamp }}</div>
        <p class="diary-line">档案馆已静候多时。</p>
        <p class="diary-line diary-line--italic">灯下等待的第一笔批注，会被永远存档。</p>
        <p class="diary-line diary-line--sub">进入任意卷宗后，推演记录将在此汇集。</p>
      </div>
      <div class="diary-cta">
        <span class="diary-cta-text">打开一份卷宗，开始推演</span>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
          <path d="M2 6h8M7 3l3 3-3 3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { formatRelativeTime } from '../../utils/format.js'
defineProps({
  events: { type: Array, default: () => [] },
})
defineEmits(['enter-universe', 'open-universe-list'])

const dateStamp = computed(() => {
  const d = new Date()
  const year = d.getFullYear()
  const months = ['一月','二月','三月','四月','五月','六月','七月','八月','九月','十月','十一月','十二月']
  return `${year} · ${months[d.getMonth()]}${d.getDate()}日`
})
</script>

<style scoped>
.panel-events { grid-area: events; padding-bottom: var(--sp-4); }

.events-list {
  list-style: none;
  padding: var(--sp-4) var(--sp-5) var(--sp-4) calc(var(--sp-5) + var(--sp-4));
  margin: 0 0 0 var(--sp-5);
  flex: 1;
  overflow-y: auto;
  border-left: 1px dashed rgba(168, 137, 78, 0.4);
  display: flex; flex-direction: column;
  gap: var(--sp-3);
}
.event-item {
  display: flex; align-items: flex-start; gap: var(--sp-3);
  font-family: var(--font-serif);
  font-size: 13px;
  color: var(--c-umber-deep);
  line-height: 1.5;
  cursor: pointer;
  transition: color var(--duration-fast);
  position: relative;
  padding-left: 4px;
}
.event-item:hover { color: var(--c-oxblood); }
.event-item:focus-visible { outline: 1px dashed var(--c-tarnished-gold); outline-offset: 4px; }
.event-dot {
  position: absolute;
  left: calc(-1 * var(--sp-4) - 7px);
  top: 6px;
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--c-tarnished-gold);
  box-shadow: 0 0 0 2px var(--c-ivory-aged);
}
.event-body { flex: 1; min-width: 0; }
.event-top {
  display: flex; align-items: baseline; gap: 6px;
  flex-wrap: wrap;
}
.event-time {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--c-sepia);
  letter-spacing: 0.05em;
}
.event-sep { color: var(--c-sepia); opacity: 0.5; }
.event-universe {
  font-style: italic;
  color: var(--c-oxblood);
  font-size: 12px;
}
.event-text {
  color: var(--c-umber);
  font-size: 13px;
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* 空态 · 档案馆守夜氛围卡 */
.events-empty-diary {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  padding: var(--sp-6) var(--sp-6) var(--sp-5);
  margin: var(--sp-4) var(--sp-4) 0;
  background: rgba(168, 137, 78, 0.06);
  border: 1px solid rgba(168, 137, 78, 0.25);
  border-radius: 2px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: background var(--duration-fast), border-color var(--duration-fast);
}
.events-empty-diary::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: repeating-linear-gradient(
    0deg,
    rgba(107, 79, 53, 0.07) 0,
    rgba(107, 79, 53, 0.07) 1px,
    transparent 1px,
    transparent 26px
  );
  pointer-events: none;
  z-index: 0;
}
.events-empty-diary > * { position: relative; z-index: 1; }
.events-empty-diary:hover {
  background: rgba(168, 137, 78, 0.11);
  border-color: var(--c-tarnished-gold);
}
.events-empty-diary:focus-visible {
  outline: 1px dashed var(--c-tarnished-gold);
  outline-offset: 3px;
}
.diary-stamp {
  color: var(--c-oxblood);
  flex-shrink: 0;
  opacity: 0.65;
}
.diary-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  text-align: center;
}
.diary-date {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--c-tarnished-gold);
  letter-spacing: 0.15em;
  padding-bottom: 4px;
  border-bottom: 1px dashed rgba(168, 137, 78, 0.3);
  margin-bottom: 4px;
}
.diary-line {
  font-family: var(--font-serif);
  font-size: 14px;
  color: var(--c-umber-deep);
  line-height: 1.6;
  margin: 0;
}
.diary-line--italic {
  font-style: italic;
  color: var(--c-sepia);
}
.diary-line--sub {
  font-size: 12px;
  color: var(--c-sepia-light);
  margin-top: var(--sp-2);
  opacity: 0.8;
}
.diary-cta {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  border: 1px dashed var(--c-tarnished-gold);
  border-radius: 2px;
  margin-bottom: var(--sp-3);
  color: var(--c-tarnished-gold);
  transition: color var(--duration-fast), border-color var(--duration-fast);
}
.events-empty-diary:hover .diary-cta {
  color: var(--c-oxblood);
  border-color: var(--c-oxblood);
}
.diary-cta-text {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.08em;
}
</style>
