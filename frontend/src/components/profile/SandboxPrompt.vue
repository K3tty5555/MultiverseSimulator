<template>
  <div v-if="show" class="sandbox-prompt">
    <div class="sandbox-prompt-text">
      <strong>档案已就绪</strong>
      <span>现在可以开启你的本命卷宗了</span>
    </div>
    <button class="lp-btn-archive" @click="$emit('go')">前往档案馆 →</button>
  </div>
</template>

<script setup>
defineProps({ show: { type: Boolean, default: false } })
defineEmits(['go'])
</script>

<style scoped>
.sandbox-prompt {
  position: sticky; bottom: var(--sp-6);
  display: flex; align-items: center; justify-content: space-between; gap: var(--sp-4);
  padding: var(--sp-4) var(--sp-5);
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-tarnished-gold);
  border-radius: 2px;
  box-shadow: var(--shadow-gold-deep), var(--shadow-paper-edge);
  margin-top: var(--sp-6);
}
.sandbox-prompt-text { display: flex; flex-direction: column; gap: 2px; }
.sandbox-prompt-text strong {
  font-family: var(--font-serif-alt);
  font-size: 14px; font-weight: 500;
  color: var(--c-umber-deep);
}
.sandbox-prompt-text span {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 13px;
  color: var(--c-sepia);
}
</style>
