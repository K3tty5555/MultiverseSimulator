<template>
  <div
    class="universe-card"
    role="button"
    tabindex="0"
    @click="$emit('open', universe.id)"
    @keydown.enter.prevent="$emit('open', universe.id)"
    @keydown.space.prevent="$emit('open', universe.id)"
  >
    <div class="card-header">
      <h3 class="card-title">{{ universe.title }}</h3>
      <div class="card-meta-row">
        <span class="perspective-badge">
          {{ universe.perspective === 'first_person' ? '亲历' : '纵观' }}
        </span>
        <span class="node-count">{{ universe.node_count || 0 }} 批注</span>
        <span v-if="universe.checkpoint_title" class="source-badge">{{ universe.checkpoint_title }}</span>
      </div>
    </div>
    <p class="card-premise">{{ universe.premise }}</p>
    <div v-if="confirming" class="archive-confirm" @click.stop role="alertdialog">
      <span class="archive-confirm-text">归档后不再显示，确认？</span>
      <button class="archive-yes" @click.stop="$emit('archive', universe.id)">归档</button>
      <button class="archive-no" @click.stop="$emit('cancel-archive')">取消</button>
    </div>
    <div v-else class="card-footer">
      <span class="card-protagonist">主角：{{ universe.protagonist_name }}</span>
      <button
        class="card-delete-btn"
        aria-label="归档卷宗"
        @click.stop="$emit('request-archive', universe.id)"
      >
        <svg width="13" height="13" viewBox="0 0 14 14" fill="none"><path d="M1 3.5h12M5 3.5V2.5a1 1 0 011-1h2a1 1 0 011 1v1M11.5 3.5l-.7 8a1 1 0 01-1 .93H4.2a1 1 0 01-1-.93l-.7-8" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  universe: { type: Object, required: true },
  confirming: { type: Boolean, default: false },
})
defineEmits(['open', 'request-archive', 'archive', 'cancel-archive'])
</script>

<style scoped>
.universe-card {
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-left: 3px solid var(--c-oxblood);
  border-radius: 2px;
  padding: var(--sp-5);
  cursor: pointer;
  transition: box-shadow var(--duration-base), border-color var(--duration-base);
  box-shadow: var(--shadow-paper-edge);
  display: flex; flex-direction: column; gap: var(--sp-3);
}
.universe-card:hover { border-color: var(--c-tarnished-gold); box-shadow: var(--shadow-gold-deep), var(--shadow-paper-edge); }

.card-header { display: flex; flex-direction: column; gap: var(--sp-2); }
.card-title {
  font-family: var(--font-serif-alt);
  font-size: 15px; font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.02em;
  line-height: 1.3;
  margin: 0;
}
.card-meta-row { display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; }
.perspective-badge {
  font-family: var(--font-mono);
  font-size: 10px; font-weight: 500;
  padding: 2px 8px;
  background: var(--c-deep-teal-soft);
  color: var(--c-ivory-aged);
  border-radius: 2px;
  letter-spacing: 0.08em;
}
.node-count {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--c-sepia);
  letter-spacing: 0.05em;
}
.source-badge {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--c-tarnished-gold);
  padding: 2px 8px;
  border: 1px solid rgba(168, 137, 78, 0.4);
  border-radius: 2px;
  max-width: 160px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  letter-spacing: 0.05em;
}
.card-premise {
  font-family: var(--font-serif);
  font-size: 13px;
  color: var(--c-archive-ink);
  line-height: 1.7;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
  flex: 1;
  margin: 0;
}
.card-footer { display: flex; align-items: center; justify-content: space-between; }
.card-protagonist {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 12px;
  color: var(--c-sepia);
}
.card-delete-btn {
  width: 24px; height: 24px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--c-sepia);
  border-radius: 2px;
  cursor: pointer;
  opacity: 0;
  transition: all var(--duration-fast);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.universe-card:hover .card-delete-btn,
.universe-card:focus-within .card-delete-btn { opacity: 1; }
.card-delete-btn:hover {
  border-color: var(--c-oxblood);
  color: var(--c-oxblood);
  background: rgba(107, 46, 42, 0.08);
}
@media (hover: none) { .card-delete-btn { opacity: 1; } }

.archive-confirm {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-3);
  background: var(--c-danger-bg);
  border: 1px solid var(--c-danger-border);
  border-radius: 2px;
}
.archive-confirm-text {
  font-family: var(--font-serif);
  font-size: 12px;
  color: var(--c-danger-strong);
  flex: 1;
}
.archive-yes {
  font-family: var(--font-serif);
  font-size: 11px;
  font-weight: 500;
  padding: 3px 10px;
  background: var(--c-oxblood);
  color: var(--c-ivory-aged);
  border: none;
  border-radius: 2px;
  cursor: pointer;
}
.archive-yes:hover { background: var(--c-oxblood-dark); }
.archive-no {
  font-family: var(--font-serif);
  font-size: 11px;
  padding: 3px 10px;
  background: transparent;
  color: var(--c-sepia);
  border: 1px solid var(--c-border-sepia);
  border-radius: 2px;
  cursor: pointer;
}
.archive-no:hover { background: rgba(139, 111, 80, 0.1); }
</style>
