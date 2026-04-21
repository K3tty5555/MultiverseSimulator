<template>
  <div v-if="!dismissed" class="setup-banner" role="status" aria-label="应用配置提示">
    <div class="setup-banner-inner">
      <span class="setup-banner-icon" aria-hidden="true">
        <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
          <path d="M10 2 L18 10 L10 18 L2 10 Z" stroke="currentColor" stroke-width="1.4" fill="none"/>
          <path d="M10 7 L10 11.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
          <circle cx="10" cy="14" r="0.8" fill="currentColor"/>
        </svg>
      </span>
      <div class="setup-banner-text">
        <strong>需要配置 AI 模型</strong>
        <span>连接 AI 服务后即可开启平行宇宙推演</span>
      </div>
    </div>
    <div class="setup-banner-actions">
      <router-link to="/settings" class="setup-btn" aria-label="前往设置页面配置 AI 模型">
        前往设置室
        <svg width="13" height="13" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </router-link>
      <button class="setup-dismiss" @click="dismissed = true" aria-label="暂时关闭提示">
        <svg width="13" height="13" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const dismissed = ref(false)
</script>

<style scoped>
.setup-banner {
  display: flex; align-items: center; justify-content: space-between;
  gap: var(--sp-4);
  padding: var(--sp-3) var(--sp-8);
  background: rgba(45, 32, 22, 0.90);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  border-left: 3px solid var(--c-tarnished-gold);
  border-bottom: 1px solid rgba(168, 137, 78, 0.25);
  position: relative; z-index: 10;
}
.setup-banner-inner {
  display: flex; align-items: center; gap: var(--sp-3);
}
.setup-banner-icon {
  display: inline-flex;
  color: var(--c-tarnished-gold);
  flex-shrink: 0;
  opacity: 0.9;
}
.setup-banner-text {
  display: flex; flex-direction: column; gap: var(--sp-1);
}
.setup-banner-text strong {
  font-family: var(--font-serif);
  font-size: var(--fs-body);
  font-weight: 600;
  color: var(--c-tarnished-gold);
  letter-spacing: 0.03em;
}
.setup-banner-text span {
  font-size: var(--fs-body-sm);
  color: var(--c-sepia-light);
  letter-spacing: 0.01em;
}
.setup-banner-actions {
  display: flex; align-items: center; gap: var(--sp-3);
  flex-shrink: 0;
}
.setup-btn {
  display: inline-flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  border: 1px solid var(--c-tarnished-gold-border);
  color: var(--c-tarnished-gold);
  background: transparent;
  border-radius: 3px;
  font-family: var(--font-serif);
  font-size: var(--fs-body-sm);
  letter-spacing: 0.03em;
  text-decoration: none;
  transition: background var(--duration-fast), border-color var(--duration-fast), color var(--duration-fast);
}
.setup-btn:hover {
  background: var(--c-tarnished-gold-tint);
  border-color: var(--c-tarnished-gold);
}
.setup-dismiss {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px;
  background: transparent;
  border: none;
  color: var(--c-sepia-light);
  cursor: pointer;
  opacity: 0.55;
  border-radius: 2px;
  transition: opacity var(--duration-fast), color var(--duration-fast);
  padding: 0;
}
.setup-dismiss:hover {
  opacity: 1;
  color: var(--c-ivory-aged);
}
@media (max-width: 640px) {
  .setup-banner { padding: var(--sp-3) var(--sp-4); }
  .setup-banner-text span { display: none; }
}
</style>
