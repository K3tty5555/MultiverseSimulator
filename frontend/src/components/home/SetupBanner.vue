<template>
  <div class="setup-banner">
    <div class="setup-banner-text">
      <strong>需要配置 AI 模型</strong>
      <span>填写你的 API Key 后即可开启档案研究</span>
    </div>
    <router-link to="/settings" class="btn-primary setup-btn">去配置 →</router-link>
  </div>
</template>

<script setup></script>

<style scoped>
.setup-banner {
  display: flex; align-items: center; justify-content: space-between; gap: var(--sp-4);
  padding: 12px var(--sp-8);
  background: var(--c-warning-bg);
  border-bottom: 1px solid var(--c-warning-border);
  position: relative; z-index: 10;
}
.setup-banner-text { display: flex; flex-direction: column; gap: 2px; }
.setup-banner-text strong { font-size: 14px; color: var(--c-warning-text); }
.setup-banner-text span { font-size: 13px; color: var(--c-warning-sub); }
.setup-btn { text-decoration: none; padding: 8px 18px !important; font-size: 13px !important; }
</style>
