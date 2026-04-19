<template>
  <li class="event-item">
    <div class="event-marker" aria-hidden="true">
      <span class="marker-dot"></span>
      <span v-if="!isLast" class="marker-line"></span>
    </div>

    <div class="event-card">
      <div class="event-head">
        <span class="event-year">{{ formatYear(event.year) }}</span>
        <h3 class="event-title">{{ event.title }}</h3>
        <span v-if="event.is_edited" class="event-edited" title="已编辑">已改</span>
        <button class="btn-icon-archive" @click="$emit('edit', event)">编辑</button>
      </div>
      <p v-if="event.description" class="event-desc">{{ event.description }}</p>

      <div v-if="universes.length > 0" class="event-branches">
        <span class="branches-label">基于此节点的平行卷宗</span>
        <ul class="branches-list">
          <li
            v-for="u in universes"
            :key="u.universe_id"
            class="branch-item"
          >
            <span class="branch-title" :title="u.title">{{ u.title }}</span>
            <span class="branch-meta">
              {{ u.node_count || 0 }} 批注
              <span v-if="u.updated_at"> · {{ formatRelative(u.updated_at) }}</span>
            </span>
            <button class="btn-link-archive" @click="$emit('enter-universe', u.universe_id)">翻至此卷 →</button>
          </li>
        </ul>
      </div>

      <button class="btn-fork-archive" @click="$emit('fork', event)">
        + 从此处分笔开卷
      </button>
    </div>
  </li>
</template>

<script setup>
defineProps({
  event: { type: Object, required: true },
  universes: { type: Array, default: () => [] },
  isLast: { type: Boolean, default: false },
})
defineEmits(['edit', 'fork', 'enter-universe'])

function formatYear(y) {
  if (y === null || y === undefined) return ''
  if (y < 0) return `前 ${-y} 年`
  return `${y} AD`
}
function formatRelative(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const diff = (Date.now() - d.getTime()) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`
  return `${Math.floor(diff / 86400)} 天前`
}
</script>

<style scoped>
.event-item { display: flex; gap: var(--sp-4); }

.event-marker {
  flex-shrink: 0;
  width: 16px;
  display: flex; flex-direction: column; align-items: center;
  padding-top: 18px;
}
.marker-dot {
  width: 14px; height: 14px; border-radius: 50%;
  background: var(--c-tarnished-gold);
  box-shadow: 0 0 0 4px rgba(168, 137, 78, 0.18);
  flex-shrink: 0;
}
.marker-line {
  flex: 1;
  width: 2px;
  background: rgba(168, 137, 78, 0.35);
  margin-top: var(--sp-2);
  min-height: 24px;
}

.event-card {
  flex: 1;
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-left: 3px solid var(--c-oxblood);
  border-radius: 2px;
  padding: var(--sp-4) var(--sp-5);
  box-shadow: var(--shadow-paper-edge);
}

.event-head {
  display: flex; align-items: center; gap: var(--sp-3);
  flex-wrap: wrap;
}
.event-year {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  color: var(--c-tarnished-gold);
  letter-spacing: 0.08em;
  padding: 3px 10px;
  border: 1px solid rgba(168, 137, 78, 0.4);
  border-radius: 2px;
  flex-shrink: 0;
}
.event-title {
  font-family: var(--font-serif-alt);
  font-size: 17px; font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.02em;
  margin: 0;
  flex: 1;
  min-width: 0;
}
.event-edited {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--c-oxblood);
  padding: 2px 8px;
  border: 1px solid var(--c-oxblood);
  border-radius: 2px;
  letter-spacing: 0.08em;
}
.btn-icon-archive {
  padding: 4px 10px;
  border: 1px solid var(--c-border-sepia);
  border-radius: 2px;
  background: transparent;
  color: var(--c-umber);
  font-family: var(--font-serif);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--duration-fast);
  letter-spacing: 0.04em;
}
.btn-icon-archive:hover {
  border-color: var(--c-tarnished-gold);
  color: var(--c-umber-deep);
  background: rgba(168, 137, 78, 0.1);
}

.event-desc {
  font-family: var(--font-serif);
  font-size: 13px;
  color: var(--c-archive-ink);
  line-height: 1.85;
  margin: var(--sp-3) 0 var(--sp-2);
}

.event-branches {
  margin-top: var(--sp-3);
  padding: var(--sp-3);
  background: rgba(168, 137, 78, 0.08);
  border-left: 2px solid var(--c-tarnished-gold);
  border-radius: 0 var(--r-sm) var(--r-sm) 0;
}
.branches-label {
  display: block;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  color: var(--c-tarnished-gold);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  margin-bottom: var(--sp-2);
}
.branches-list {
  list-style: none; margin: 0; padding: 0;
  display: flex; flex-direction: column;
  gap: var(--sp-2);
}
.branch-item {
  display: flex; align-items: center; gap: var(--sp-3);
  padding: var(--sp-2) var(--sp-3);
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
}
.branch-title {
  flex: 1;
  font-family: var(--font-serif-alt);
  font-size: 13px;
  color: var(--c-umber-deep);
  font-weight: 500;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.branch-meta {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--c-sepia);
  flex-shrink: 0;
  letter-spacing: 0.05em;
}
.btn-link-archive {
  background: transparent; border: none;
  color: var(--c-oxblood);
  font-family: var(--font-serif);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  flex-shrink: 0;
  letter-spacing: 0.04em;
}
.btn-link-archive:hover { text-decoration: underline; color: var(--c-tarnished-gold); }

.btn-fork-archive {
  display: inline-block;
  margin-top: var(--sp-3);
  padding: 6px 14px;
  border: 1px dashed var(--c-oxblood);
  border-radius: 2px;
  background: transparent;
  color: var(--c-oxblood);
  font-family: var(--font-serif);
  font-size: 12px;
  letter-spacing: 0.04em;
  cursor: pointer;
  transition: all var(--duration-fast);
}
.btn-fork-archive:hover {
  background: var(--c-oxblood);
  color: var(--c-ivory-aged);
  border-style: solid;
}
</style>
