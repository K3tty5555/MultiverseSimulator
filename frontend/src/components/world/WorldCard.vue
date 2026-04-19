<template>
  <div
    class="world-card"
    :class="{ 'world-card--create': variant === 'create' }"
    role="button"
    tabindex="0"
    @click="$emit('click')"
    @keydown.enter.prevent="$emit('click')"
    @keydown.space.prevent="$emit('click')"
  >
    <div class="world-card-icon" aria-hidden="true">
      <slot name="icon">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <circle cx="16" cy="16" r="14" stroke="currentColor" stroke-width="1.4" stroke-dasharray="4 3"/>
          <circle cx="16" cy="16" r="8" stroke="currentColor" stroke-width="1.4"/>
          <circle cx="16" cy="16" r="3" fill="currentColor" opacity="0.4"/>
        </svg>
      </slot>
    </div>
    <div class="world-card-body">
      <div class="world-card-header">
        <h3 class="world-name">{{ title }}</h3>
        <span v-if="eraTag" class="world-era-tag">{{ eraTag }}</span>
      </div>
      <p class="world-desc">{{ description }}</p>
      <div class="world-card-footer">
        <span v-if="footerLeft" class="checkpoint-count">{{ footerLeft }}</span>
        <span class="explore-link">{{ footerRight || '翻开此卷 →' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  eraTag: { type: String, default: '' },
  footerLeft: { type: String, default: '' },
  footerRight: { type: String, default: '' },
  variant: { type: String, default: 'normal' },  // 'normal' | 'create'
})
defineEmits(['click'])
</script>

<style scoped>
.world-card {
  display: flex; align-items: flex-start; gap: var(--sp-5);
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-left: 3px solid var(--c-oxblood);
  border-radius: 2px;
  padding: var(--sp-5) var(--sp-6);
  cursor: pointer;
  transition: box-shadow var(--duration-base), border-color var(--duration-base);
  box-shadow: var(--shadow-paper-edge);
}
.world-card:hover {
  border-color: var(--c-tarnished-gold);
  border-left-color: var(--c-tarnished-gold);
  box-shadow: var(--shadow-gold-deep), var(--shadow-paper-edge);
}
.world-card--create {
  border-style: dashed;
  border-left-style: dashed;
  border-left-color: var(--c-border-sepia);
  background: rgba(232, 223, 200, 0.4);
}
.world-card--create:hover {
  border-color: var(--c-tarnished-gold);
  border-left-color: var(--c-tarnished-gold);
  background: var(--c-ivory-aged);
}

.world-card-icon { color: var(--c-tarnished-gold); flex-shrink: 0; margin-top: 2px; }

.world-card-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: var(--sp-2); }
.world-card-header { display: flex; align-items: baseline; gap: var(--sp-2); flex-wrap: wrap; }
.world-name {
  font-family: var(--font-serif-alt);
  font-size: 17px; font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.02em;
  margin: 0;
}
.world-era-tag {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--c-tarnished-gold);
  padding: 2px 8px;
  border: 1px solid rgba(168, 137, 78, 0.4);
  border-radius: 2px;
  letter-spacing: 0.08em;
}

.world-desc {
  font-family: var(--font-serif);
  font-size: 13px;
  color: var(--c-archive-ink);
  line-height: 1.75;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
  margin: 0;
}

.world-card-footer {
  display: flex; align-items: center; justify-content: space-between; margin-top: var(--sp-1);
}
.checkpoint-count {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--c-sepia);
  letter-spacing: 0.05em;
}
.explore-link {
  font-family: var(--font-serif);
  font-size: 13px;
  font-weight: 500;
  color: var(--c-oxblood);
  letter-spacing: 0.04em;
}
</style>
