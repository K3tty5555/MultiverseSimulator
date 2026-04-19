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
    <div v-else class="events-empty-diary">
      <div class="diary-stamp" aria-hidden="true">
        <svg width="40" height="40" viewBox="0 0 48 48" fill="none">
          <circle cx="24" cy="24" r="21" stroke="currentColor" stroke-width="1.2" opacity="0.5"/>
          <circle cx="24" cy="24" r="16" stroke="currentColor" stroke-width="0.7" opacity="0.3" stroke-dasharray="2 2"/>
          <text x="24" y="28" font-family="serif" font-size="11" fill="currentColor" text-anchor="middle" opacity="0.7">档案</text>
        </svg>
      </div>
      <div class="diary-content">
        <div class="diary-date">{{ dateStamp }}</div>
        <p class="diary-line">档案馆已静候多时。</p>
        <p class="diary-line diary-line--italic">灯下等待的第一笔批注，会被永远存档。</p>
        <p class="diary-hint">—— 推演任一卷宗，批注自此浮现。</p>
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
defineEmits(['enter-universe'])

const dateStamp = computed(() => {
  const d = new Date()
  const year = d.getFullYear()
  const months = ['一月','二月','三月','四月','五月','六月','七月','八月','九月','十月','十一月','十二月']
  return `${year} · ${months[d.getMonth()]}${d.getDate()}日`
})
</script>

<style scoped>
.panel-events { grid-area: events; }

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
  align-items: center;
  gap: var(--sp-5);
  padding: var(--sp-5) var(--sp-6);
  margin: var(--sp-4) var(--sp-4);
  background: rgba(168, 137, 78, 0.06);
  border: 1px solid rgba(168, 137, 78, 0.25);
  border-radius: 2px;
  position: relative;
}
.events-empty-diary::before {
  content: '';
  position: absolute;
  top: -4px; right: 24px;
  width: 32px; height: 12px;
  background: repeating-linear-gradient(90deg, rgba(168,137,78,0.35) 0 3px, transparent 3px 6px);
  opacity: 0.7;
}
.diary-stamp {
  color: var(--c-oxblood);
  flex-shrink: 0;
  opacity: 0.7;
}
.diary-content {
  display: flex; flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}
.diary-date {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--c-tarnished-gold);
  letter-spacing: 0.15em;
  text-transform: uppercase;
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
.diary-hint {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--c-sepia);
  letter-spacing: 0.05em;
  margin-top: var(--sp-2);
  opacity: 0.8;
}
</style>
