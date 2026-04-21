<template>
  <div class="empty-hero">
    <div class="empty-meta">
      <span class="meta-tag">CATALOGUE · {{ todayLabel }}</span>
    </div>
    <h1 class="empty-title">档案研究员的书桌</h1>
    <p class="empty-quote">「每一卷卷宗，都是一个曾经可能的你。」</p>
    <p class="empty-guide">填写你的人生档案，AI 将为你推演平行宇宙中的另一种可能。</p>
    <div class="empty-cta">
      <router-link to="/profile" class="lp-btn-archive lp-btn-archive--lg">前往登记处 →</router-link>
      <router-link to="/universe" class="empty-skip">先看看其他人的宇宙 →</router-link>
    </div>
  </div>
</template>

<script setup>
import { formatToday } from '../../utils/format.js'
const todayLabel = formatToday()
</script>

<style scoped>
.empty-hero {
  display: flex; flex-direction: column; align-items: center;
  gap: var(--sp-4);
  text-align: center;
  max-width: 560px;
  padding: var(--sp-8) var(--sp-6);
  animation: hero-fade-in var(--duration-slower) var(--ease-out) both;
  /* 软底板：径向渐变暗晕，无硬边，保持沉浸感 */
  background: radial-gradient(
    ellipse 540px 360px at center,
    rgba(10, 7, 4, 0.65) 0%,
    rgba(10, 7, 4, 0.42) 55%,
    transparent 100%
  );
  backdrop-filter: blur(2.5px) brightness(0.78);
  -webkit-backdrop-filter: blur(2.5px) brightness(0.78);
  border-radius: 4px;
  margin-top: -24px;
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
  border-bottom: 1px solid rgba(168, 137, 78, 0.5);
  text-shadow: 0 1px 6px rgba(20, 15, 10, 0.9);
}
.empty-title {
  font-family: var(--font-serif-alt);
  font-size: 48px;
  font-weight: 500;
  color: var(--c-ivory-aged);
  letter-spacing: 0.02em;
  line-height: 1.1;
  text-shadow:
    0 1px 0 rgba(20, 15, 10, 0.9),
    0 2px 6px rgba(20, 15, 10, 0.85),
    0 4px 24px rgba(20, 15, 10, 0.75),
    0 8px 48px rgba(20, 15, 10, 0.5);
  margin: 0;
}
.empty-quote {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 18px;
  color: var(--c-sepia-light);
  line-height: 1.5;
  margin: 0;
  text-shadow:
    0 1px 4px rgba(20, 15, 10, 0.8),
    0 2px 12px rgba(20, 15, 10, 0.6);
}
.empty-guide {
  font-family: var(--font-serif);
  font-size: 13px;
  color: rgba(201, 176, 145, 0.8);
  line-height: 1.5;
  margin: 0;
  text-shadow: 0 1px 4px rgba(20, 15, 10, 0.8);
  letter-spacing: 0.01em;
}
.empty-cta {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-3);
  margin-top: var(--sp-5);
}
.empty-cta .lp-btn-archive {
  box-shadow:
    0 2px 8px rgba(201, 100, 66, 0.45),
    0 0 0 1px rgba(201, 100, 66, 0.3);
}
.empty-skip {
  font-family: var(--font-serif);
  font-size: 13px;
  color: rgba(201, 176, 145, 0.75);
  text-decoration: none;
  letter-spacing: 0.03em;
  text-shadow: 0 1px 4px rgba(20, 15, 10, 0.7);
  border-bottom: 1px solid rgba(201, 176, 145, 0.35);
  padding-bottom: 1px;
  transition: color var(--duration-fast), border-color var(--duration-fast);
}
.empty-skip:hover {
  color: var(--c-sepia-light);
  border-bottom-color: rgba(201, 176, 145, 0.7);
}
@media (max-width: 640px) {
  .empty-title { font-size: 32px; }
  .empty-quote { font-size: 15px; }
}
</style>
