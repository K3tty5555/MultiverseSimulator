<template>
  <section class="section">
    <div class="synth-row">
      <div>
        <h2 class="section-title" style="margin-bottom: 4px">档案摘要</h2>
        <p class="section-desc" v-if="updatedAt">
          上次合成：{{ formatDate(updatedAt) }}
        </p>
      </div>
      <button class="lp-btn-ghost-archive" :disabled="synthesizing" @click="$emit('synthesize')">
        {{ synthesizing ? '合成中...' : '重新合成' }}
      </button>
    </div>
    <div v-if="summary" class="summary-card">
      <div class="summary-header">
        <p class="summary-label">AI 研究员侧写</p>
        <button class="summary-toggle" @click="expanded = !expanded" :aria-expanded="expanded">
          {{ expanded ? '收起' : '展开' }}
        </button>
      </div>
      <p class="summary-text" :class="{ 'summary-collapsed': !expanded }">{{ summary }}</p>
    </div>
    <div v-else class="summary-empty">
      <p>上传素材后点击「重新合成」，AI 会基于你的登记生成一段侧写，用于推演时的背景上下文。</p>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  summary: { type: String, default: '' },
  updatedAt: { type: String, default: '' },
  synthesizing: { type: Boolean, default: false },
})
defineEmits(['synthesize'])

const expanded = ref(false)

function formatDate(iso) { return new Date(iso).toLocaleString('zh-CN', { month:'short', day:'numeric', hour:'2-digit', minute:'2-digit' }) }
</script>

<style scoped>
.section { margin-bottom: var(--sp-12); }
.section-title {
  font-family: var(--font-serif-alt);
  font-size: 20px; font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.04em;
  margin-bottom: var(--sp-4);
  padding-bottom: var(--sp-3);
  border-bottom: 1px solid rgba(168, 137, 78, 0.4);
}
.section-desc {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 13px;
  color: var(--c-sepia);
}

.synth-row {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: var(--sp-4); margin-bottom: var(--sp-5);
}

.summary-card {
  padding: var(--sp-5) var(--sp-6);
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-left: 3px solid var(--c-oxblood);
  border-radius: 2px;
  box-shadow: var(--shadow-paper-edge);
}
.summary-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--sp-3); }
.summary-label {
  font-family: var(--font-mono);
  font-size: 10px; font-weight: 500;
  letter-spacing: 0.15em;
  color: var(--c-oxblood);
  text-transform: uppercase;
}
.summary-toggle {
  font-family: var(--font-serif);
  font-size: 12px;
  color: var(--c-sepia);
  background: none;
  border: 1px solid transparent;
  cursor: pointer;
  padding: 2px 8px;
  border-radius: 2px;
  transition: all var(--duration-fast);
}
.summary-toggle:hover { border-color: var(--c-border-sepia); color: var(--c-umber-deep); background: rgba(139, 111, 80, 0.08); }
.summary-text {
  font-family: var(--font-serif);
  font-size: 14px;
  color: var(--c-archive-ink);
  line-height: 1.85;
}
.summary-collapsed {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.summary-empty {
  padding: var(--sp-5) var(--sp-6);
  background: rgba(232, 223, 200, 0.3);
  border: 1px dashed var(--c-border-sepia);
  border-radius: 2px;
}
.summary-empty p {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 13px;
  color: var(--c-sepia);
  line-height: 1.7;
}
</style>
