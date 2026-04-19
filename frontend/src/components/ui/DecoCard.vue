<template>
  <div class="deco-card" :class="[variant && `deco-card--${variant}`, { 'deco-card--no-deco': noDeco }]">
    <slot />
  </div>
</template>

<script setup>
defineProps({
  /**
   * 变体：'default' | 'gold' | 'subtle'
   * - default: 羊皮纸底色 + 标准边框
   * - gold:    加金色角饰强调
   * - subtle:  无背景，只有角饰
   */
  variant: { type: String, default: 'default' },
  /** 禁用 Art Deco 角饰（只保留边框和背景） */
  noDeco: { type: Boolean, default: false },
})
</script>

<style scoped>
.deco-card {
  position: relative;
  background: var(--c-ivory);
  border: 1px solid var(--c-border-cream);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-card);
}

/* ── Art Deco 角饰：左上 + 右下 ── */
.deco-card:not(.deco-card--no-deco)::before,
.deco-card:not(.deco-card--no-deco)::after {
  content: '';
  position: absolute;
  width: 14px;
  height: 14px;
  border: 1.5px solid var(--c-gold-primary);
  pointer-events: none;
  z-index: 1;
}

.deco-card:not(.deco-card--no-deco)::before {
  top: -1px;
  left: -1px;
  border-right: none;
  border-bottom: none;
  border-top-left-radius: var(--r-lg);
}

.deco-card:not(.deco-card--no-deco)::after {
  bottom: -1px;
  right: -1px;
  border-left: none;
  border-top: none;
  border-bottom-right-radius: var(--r-lg);
}

/* ── 金色变体：整体加金色描边 ── */
.deco-card--gold {
  border-color: var(--c-border-gold);
  box-shadow: var(--shadow-card), var(--shadow-gold-glow);
}

.deco-card--gold::before,
.deco-card--gold::after {
  border-color: var(--c-gold-primary);
  width: 18px;
  height: 18px;
}

/* ── 无背景变体 ── */
.deco-card--subtle {
  background: transparent;
  box-shadow: none;
  border-color: var(--c-border-warm);
}
</style>
