<template>
  <div class="empty-panel">
    <div class="panel-seal" aria-hidden="true">{{ typeText === '史料' ? '史' : '幻' }}</div>
    <h3 class="panel-title">尚无「{{ name }}」的生平年表</h3>
    <p class="panel-hint">
      AI 可从{{ typeText === '史料' ? '史料与考证文献' : '原著' }}梳理 5-8 个关键时序。<br/>
      生成后可编辑、除名，或从任一节点分笔开卷。
    </p>
    <button class="lp-btn-archive" :disabled="generating" @click="$emit('generate')">
      <span v-if="generating" class="lp-btn-inline-spinner" aria-hidden="true"></span>
      {{ generating ? `AI 梳理中… ${elapsed}s` : '梳理生平年表 →' }}
    </button>
    <p v-if="reason" class="empty-reason">{{ reason }}</p>
  </div>
</template>

<script setup>
defineProps({
  name: { type: String, required: true },
  typeText: { type: String, default: '史料' },
  generating: { type: Boolean, default: false },
  elapsed: { type: Number, default: 0 },
  reason: { type: String, default: '' },
})
defineEmits(['generate'])
</script>

<style scoped>
.empty-panel {
  text-align: center;
  padding: var(--sp-10) var(--sp-6);
  background: var(--c-ivory-aged);
  border: 1px dashed var(--c-border-sepia);
  border-radius: 2px;
  box-shadow: var(--shadow-paper-edge);
}
.panel-seal {
  display: inline-flex; align-items: center; justify-content: center;
  width: 40px; height: 40px;
  background: var(--c-oxblood);
  color: var(--c-ivory-aged);
  font-family: var(--font-serif-alt);
  font-size: 18px; font-weight: 600;
  border-radius: 2px;
  box-shadow: var(--shadow-oxblood-seal);
  margin-bottom: var(--sp-4);
}
.panel-title {
  font-family: var(--font-serif-alt);
  font-size: 20px; font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.03em;
  margin: 0 0 var(--sp-3);
}
.panel-hint {
  font-family: var(--font-serif);
  font-size: 13px;
  color: var(--c-sepia);
  line-height: 1.8;
  margin: 0 0 var(--sp-5);
}
.empty-reason {
  margin-top: var(--sp-4);
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 12px;
  color: var(--c-oxblood);
}
</style>
