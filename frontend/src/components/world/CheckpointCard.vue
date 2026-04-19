<template>
  <div class="cp-item">
    <div class="timeline-track">
      <div class="timeline-dot"></div>
      <div v-if="!isLast" class="timeline-line"></div>
    </div>

    <div class="cp-card">
      <div class="cp-card-header">
        <div class="cp-titles">
          <h2 class="cp-title">{{ checkpoint.title }}</h2>
          <span class="cp-year">{{ checkpoint.year_label }}</span>
        </div>
        <span :class="['difficulty-badge', `diff-${checkpoint.difficulty}`]">{{ difficultyLabel(checkpoint.difficulty) }}</span>
      </div>

      <p class="cp-premise">{{ checkpoint.premise }}</p>

      <div class="persona-section">
        <span class="persona-hint">选定主角 · 开卷：</span>
        <div class="persona-chips">
          <button
            v-for="p in checkpoint.personas"
            :key="p.name"
            class="persona-chip"
            @click="$emit('select', checkpoint, p)"
          >
            <span class="chip-emoji" aria-hidden="true">{{ p.avatar_emoji || '📜' }}</span>
            <span class="chip-name">{{ p.name }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  checkpoint: { type: Object, required: true },
  isLast: { type: Boolean, default: false },
})
defineEmits(['select'])

function difficultyLabel(d) {
  return { easy: '入门', medium: '进阶', hard: '挑战' }[d] || d
}
</script>

<style scoped>
.cp-item { display: flex; gap: var(--sp-4); align-items: flex-start; }

.timeline-track {
  display: flex; flex-direction: column; align-items: center;
  flex-shrink: 0; width: 16px; padding-top: 18px;
}
.timeline-dot {
  width: 14px; height: 14px; border-radius: 50%;
  background: var(--c-tarnished-gold);
  box-shadow: 0 0 0 4px rgba(168, 137, 78, 0.18);
}
.timeline-line {
  width: 2px; flex: 1; min-height: 24px;
  background: rgba(168, 137, 78, 0.35);
  margin-top: 4px;
}

.cp-card {
  flex: 1; min-width: 0;
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-left: 3px solid var(--c-oxblood);
  border-radius: 2px;
  padding: var(--sp-4) var(--sp-5);
  margin-bottom: var(--sp-4);
  display: flex; flex-direction: column; gap: var(--sp-3);
  box-shadow: var(--shadow-paper-edge);
  transition: box-shadow var(--duration-fast);
}
.cp-card:hover { box-shadow: var(--shadow-gold-deep), var(--shadow-paper-edge); }

.cp-card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--sp-3); }
.cp-titles { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.cp-title {
  font-family: var(--font-serif-alt);
  font-size: 17px; font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.02em;
  line-height: 1.3;
  margin: 0;
}
.cp-year {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--c-tarnished-gold);
  letter-spacing: 0.08em;
}

.difficulty-badge {
  flex-shrink: 0;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 2px;
  white-space: nowrap;
  margin-top: 2px;
  letter-spacing: 0.08em;
}
.diff-easy { background: var(--c-deep-teal-soft); color: var(--c-ivory-aged); }
.diff-medium { background: var(--c-tarnished-gold); color: var(--c-umber-deep); }
.diff-hard { background: var(--c-oxblood); color: var(--c-ivory-aged); }

.cp-premise {
  font-family: var(--font-serif);
  font-size: 13px;
  color: var(--c-archive-ink);
  line-height: 1.75;
  margin: 0;
}

.persona-section { display: flex; flex-direction: column; gap: var(--sp-2); }
.persona-hint {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 12px;
  color: var(--c-sepia);
}
.persona-chips { display: flex; flex-wrap: wrap; gap: var(--sp-2); }
.persona-chip {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 6px 12px;
  background: var(--c-ivory);
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
  font-family: var(--font-serif);
  font-size: 13px;
  color: var(--c-umber-deep);
  cursor: pointer;
  transition: all var(--duration-fast);
}
.persona-chip:hover {
  border-color: var(--c-tarnished-gold);
  background: rgba(168, 137, 78, 0.1);
}
.chip-emoji { font-size: 14px; line-height: 1; }
</style>
