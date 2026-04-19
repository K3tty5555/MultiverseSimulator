<template>
  <div class="profile-impact-hint">
    <div class="hint-seal" aria-hidden="true">印</div>
    <div class="hint-text">
      <strong>为何登记如此郑重？</strong>
      <p>你的价值观权重会影响 AI 在推演第 2 步的追问方向，以及第 4 步报告中的个性化建议。越真实，推演越贴身。</p>
    </div>
  </div>
</template>

<script setup></script>

<style scoped>
.profile-impact-hint {
  display: flex; align-items: flex-start; gap: var(--sp-4);
  padding: var(--sp-4) var(--sp-5);
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-left: 4px solid var(--c-tarnished-gold);
  border-radius: 2px;
  margin-bottom: var(--sp-8);
  box-shadow: var(--shadow-paper-edge);
}
.hint-seal {
  display: inline-flex; align-items: center; justify-content: center;
  width: 32px; height: 32px;
  flex-shrink: 0;
  background: var(--c-oxblood);
  color: var(--c-ivory-aged);
  font-family: var(--font-serif-alt);
  font-size: 14px; font-weight: 600;
  border-radius: 2px;
  box-shadow: var(--shadow-oxblood-seal);
}
.hint-text { display: flex; flex-direction: column; gap: 4px; }
.hint-text strong {
  font-family: var(--font-serif-alt);
  font-size: 14px; font-weight: 600;
  color: var(--c-umber-deep);
  letter-spacing: 0.02em;
}
.hint-text p {
  font-family: var(--font-serif);
  font-size: 13px; line-height: 1.7;
  margin: 0;
  color: var(--c-umber);
}
</style>
