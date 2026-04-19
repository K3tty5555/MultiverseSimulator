<template>
  <div class="empty-hero">
    <div class="empty-meta">
      <span class="meta-tag">CATALOGUE · {{ todayLabel }}</span>
    </div>
    <h1 class="empty-title">档案研究员的书桌</h1>
    <p class="empty-quote">「每一卷卷宗，都是一个曾经可能的你。」</p>
    <div class="empty-cta">
      <router-link to="/profile" class="lp-btn-archive lp-btn-archive--lg">前往登记处 →</router-link>
      <router-link to="/universe" class="lp-btn-ghost-archive empty-ghost">浏览历史世界</router-link>
    </div>
  </div>
</template>

<script setup>
import { formatToday } from '../../utils/format.js'
const todayLabel = formatToday()
</script>

<style scoped>
.empty-hero {
  grid-area: empty;
  display: flex; flex-direction: column; align-items: center;
  gap: var(--sp-4);
  text-align: center;
  max-width: 560px;
  padding: var(--sp-6);
  animation: hero-fade-in var(--duration-slower) var(--ease-out);
}
@keyframes hero-fade-in {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
.empty-meta {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--c-tarnished-gold);
  letter-spacing: 0.18em;
  text-transform: uppercase;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(168, 137, 78, 0.35);
}
.empty-title {
  font-family: var(--font-serif-alt);
  font-size: 48px;
  font-weight: 500;
  color: var(--c-ivory-aged);
  letter-spacing: 0.02em;
  line-height: 1.1;
  text-shadow: 0 2px 12px rgba(20, 15, 10, 0.7);
  margin: 0;
}
.empty-quote {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 18px;
  color: var(--c-dust);
  line-height: 1.5;
  margin: 0;
}
.empty-cta {
  display: flex; align-items: center; gap: var(--sp-4);
  margin-top: var(--sp-5);
}
.empty-ghost {
  color: var(--c-sepia-light);
  border-color: rgba(201, 176, 145, 0.4);
}
.empty-ghost:hover {
  background: rgba(232, 223, 200, 0.1);
  color: var(--c-ivory-aged);
  border-color: var(--c-tarnished-gold);
}
@media (max-width: 640px) {
  .empty-title { font-size: 32px; }
  .empty-quote { font-size: 15px; }
}
</style>
