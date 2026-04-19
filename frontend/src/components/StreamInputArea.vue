<template>
  <div class="input-area">
    <!-- 历史节点提示 -->
    <div v-if="isHistoricalNode && !streaming" class="historical-hint" role="status">
      <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
        <path d="M7 1v3M7 10v3M1 7h3M10 7h3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
        <circle cx="7" cy="7" r="3" stroke="currentColor" stroke-width="1.3"/>
      </svg>
      正在翻阅旧批注 — 此笔将在此处分枝
    </div>

    <!-- 分叉选项卡 -->
    <div v-if="branchData && !streaming" class="branch-card" aria-live="polite">
      <p class="branch-prompt">{{ branchData.prompt }}</p>
      <div class="branch-options">
        <button
          v-for="opt in branchData.options"
          :key="opt.label"
          class="branch-option-btn"
          @click="emit('select-branch', opt)"
        >
          <span class="opt-label">{{ opt.label }}</span>
          <span v-if="opt.description" class="opt-desc">{{ opt.description }}</span>
        </button>
      </div>
      <button class="branch-dismiss" @click="emit('dismiss-branch')">忽略此引，自由落笔</button>
    </div>

    <textarea
      :value="modelValue"
      :disabled="streaming"
      :placeholder="textareaPlaceholder"
      rows="3"
      class="action-input"
      @input="emit('update:modelValue', $event.target.value)"
      @keydown.ctrl.enter.prevent="emit('submit')"
    />
    <button
      class="lp-btn-archive submit-btn"
      :disabled="streaming || !modelValue.trim()"
      @click="emit('submit')"
    >
      {{ submitLabel }}
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  streaming: { type: Boolean, default: false },
  isHistoricalNode: { type: Boolean, default: false },
  branchData: { type: Object, default: null },
  threadEmpty: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'submit', 'select-branch', 'dismiss-branch'])

const textareaPlaceholder = computed(() => {
  if (props.threadEmpty) return '此卷第一笔 · 从何处开篇？'
  if (props.isHistoricalNode) return '自此分笔 · 下一步行动...'
  return '下一笔批注... (Ctrl+Enter 记下)'
})

const submitLabel = computed(() => {
  if (props.streaming) return '推演中...'
  if (props.threadEmpty) return '开卷第一笔 →'
  if (props.isHistoricalNode) return '自此分笔 →'
  return '记下此笔 →'
})
</script>

<style scoped>
/* 历史节点提示：档案化 */
.historical-hint {
  display: flex; align-items: center; gap: var(--sp-2);
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 12px;
  color: var(--c-sepia);
  padding: var(--sp-2) var(--sp-3);
  background: rgba(168, 137, 78, 0.1);
  border-left: 2px solid var(--c-tarnished-gold);
  border-radius: 0 2px 2px 0;
  margin-bottom: var(--sp-2);
  width: 100%;
}

/* 分叉选项卡：档案引文 */
.branch-card {
  width: 100%;
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-oxblood);
  border-left: 4px solid var(--c-oxblood);
  border-radius: 2px;
  padding: var(--sp-4) var(--sp-5);
  display: flex; flex-direction: column; gap: var(--sp-3);
  box-shadow: var(--shadow-paper-edge);
  position: relative;
}
.branch-card::before {
  content: '引';
  position: absolute;
  top: -10px; left: 12px;
  font-family: var(--font-serif-alt);
  font-size: 12px;
  letter-spacing: 0.1em;
  padding: 2px 8px;
  background: var(--c-oxblood);
  color: var(--c-ivory-aged);
  border-radius: 2px;
}
.branch-prompt {
  font-family: var(--font-serif);
  font-size: 14px;
  font-weight: 500;
  color: var(--c-umber-deep);
  line-height: 1.6;
}
.branch-options { display: flex; flex-direction: column; gap: var(--sp-2); }
.branch-option-btn {
  display: flex; flex-direction: column; gap: 3px;
  text-align: left; padding: 10px 14px;
  background: var(--c-ivory);
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
  cursor: pointer;
  transition: all var(--duration-fast);
}
.branch-option-btn:hover {
  border-color: var(--c-tarnished-gold);
  background: rgba(168, 137, 78, 0.08);
  box-shadow: var(--shadow-paper-edge);
}
.opt-label {
  font-family: var(--font-serif-alt);
  font-size: 13px; font-weight: 500;
  color: var(--c-umber-deep);
}
.opt-desc {
  font-family: var(--font-serif);
  font-size: 12px;
  color: var(--c-sepia);
  line-height: 1.5;
}
.branch-dismiss {
  align-self: flex-start;
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 12px;
  color: var(--c-sepia);
  background: none; border: none;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 3px;
}
.branch-dismiss:hover { color: var(--c-umber-deep); }

/* 输入区：档案纸 + 金线焦点 */
.input-area {
  display: flex; gap: var(--sp-3); align-items: flex-end; flex-wrap: wrap;
  padding: var(--sp-4) var(--sp-5);
  border-top: 1px solid var(--c-border-archive);
  background: rgba(232, 223, 200, 0.5);
  flex-shrink: 0;
}
.action-input {
  flex: 1;
  min-height: 72px;
  padding: 10px 14px;
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
  background: var(--c-ivory);
  font-family: var(--font-serif);
  font-size: 14px;
  color: var(--c-umber-deep);
  line-height: 1.7;
  resize: none;
  transition: border-color var(--duration-fast), box-shadow var(--duration-fast);
}
.action-input::placeholder {
  font-style: italic;
  color: var(--c-sepia);
  opacity: 0.7;
}
.action-input:focus {
  outline: none;
  border-color: var(--c-tarnished-gold);
  box-shadow: 0 0 0 2px rgba(168, 137, 78, 0.25);
}
.action-input:disabled { opacity: 0.5; }
.submit-btn {
  flex-shrink: 0;
  padding: 10px 22px;
  font-size: 14px;
  min-width: 120px;
  justify-content: center;
}
</style>
