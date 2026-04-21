<template>
  <header class="nav">
    <div class="nav-brand">
      <span class="brand-mark" aria-hidden="true">
        <svg width="18" height="18" viewBox="0 0 20 20" fill="none"><path d="M10 1 L19 10 L10 19 L1 10 Z" stroke="currentColor" stroke-width="1.2" fill="none"/><path d="M10 5.5 L14.5 10 L10 14.5 L5.5 10 Z" stroke="currentColor" stroke-width="0.9" fill="none"/></svg>
      </span>
      <div class="brand-text">
        <div class="brand-name-row">
          <span class="brand-name">多元宇宙档案馆</span>
          <span class="brand-version">No.{{ appVersion }}</span>
        </div>
        <span class="brand-tagline">翻阅每一个可能存在过的自己</span>
      </div>
    </div>
    <nav class="nav-links">
      <template v-if="!emptyState">
        <router-link to="/profile"  class="nav-link" active-class="nav-link-active">研究员</router-link>
        <router-link to="/agents"   class="nav-link" active-class="nav-link-active">角色长廊</router-link>
        <router-link to="/universe" class="nav-link" active-class="nav-link-active">历史卷宗</router-link>
      </template>
      <router-link to="/settings" class="nav-link" active-class="nav-link-active">设置</router-link>
    </nav>
  </header>
</template>

<script setup>
defineProps({
  appVersion: { type: String, required: true },
  emptyState: { type: Boolean, default: false },
})
</script>

<style scoped>
.nav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 var(--sp-8); height: 60px;
  background: rgba(45, 32, 22, 0.85);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(168, 137, 78, 0.25);
  position: relative; z-index: 10;
}
.nav-brand { display: flex; align-items: center; gap: var(--sp-3); }
.brand-mark { display: inline-flex; color: var(--c-tarnished-gold); flex-shrink: 0; }
.brand-text { display: flex; flex-direction: column; gap: 2px; }
.brand-name-row { display: flex; align-items: baseline; gap: 6px; }
.brand-name {
  font-family: var(--font-serif-alt);
  font-size: 17px; font-weight: 600;
  color: var(--c-ivory-aged);
  letter-spacing: 0.04em;
}
.brand-version {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--c-sepia-light);
  opacity: 0.6;
  letter-spacing: 0.1em;
}
.brand-tagline {
  font-family: var(--font-serif);
  font-size: 11px;
  font-style: italic;
  color: var(--c-tarnished-gold);
  opacity: 0.9;
  letter-spacing: 0.05em;
}
.nav-links { display: flex; align-items: center; gap: var(--sp-5); }
.nav-link {
  font-family: var(--font-serif);
  font-size: 14px;
  color: var(--c-sepia-light);
  letter-spacing: 0.03em;
  transition: color var(--duration-fast);
}
.nav-link:hover { color: var(--c-ivory-aged); }
.nav-link-active {
  color: var(--c-tarnished-gold) !important;
  font-weight: 500;
  border-bottom: 1px solid var(--c-tarnished-gold);
  padding-bottom: 2px;
}
@media (max-width: 640px) {
  .nav-links { gap: var(--sp-3); }
  .nav-link { font-size: 13px; }
}
</style>
