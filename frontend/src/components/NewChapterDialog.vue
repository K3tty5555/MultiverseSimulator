<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      class="lp-modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="ncd-title"
      @click.self="close"
      @keydown="handleKeydown"
    >
      <div ref="dialogEl" class="lp-modal dialog">
        <div class="lp-modal-header">
          <div class="header-left">
            <span class="header-seal" aria-hidden="true">章</span>
            <h2 id="ncd-title" class="lp-modal-title">启新一章</h2>
          </div>
          <button class="lp-modal-close" aria-label="关闭" @click="close">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </button>
        </div>

        <div class="lp-modal-body">
          <label class="field-label" for="ncd-situation">你此刻面临什么情况？</label>
          <textarea
            id="ncd-situation"
            ref="textareaEl"
            v-model="situation"
            class="situation-input"
            rows="5"
            placeholder="例：我在考虑是否接受一个异地工作的 offer，薪资提升 30%，但要离开现在的城市和家人..."
            maxlength="500"
          />
          <div class="meta-row">
            <p class="field-hint">情境会直接预填到推演输入框 · 提交后可修改</p>
            <span :class="['char-count', charCountClass]">{{ situation.length }} / 500</span>
          </div>
        </div>

        <div class="lp-modal-footer">
          <button class="lp-btn-ghost-archive" @click="close">取消</button>
          <button
            class="lp-btn-archive"
            :disabled="!situation.trim()"
            @click="confirm"
          >落笔推演 →</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false }
})
const emit = defineEmits(['update:modelValue', 'confirm'])

const situation = ref('')
const dialogEl = ref(null)
const textareaEl = ref(null)
let returnFocusEl = null

const charCountClass = computed(() => {
  const len = situation.value.length
  if (len >= 490) return 'char-danger'
  if (len >= 450) return 'char-warn'
  return ''
})

watch(() => props.modelValue, async (val) => {
  if (val) {
    returnFocusEl = document.activeElement
    situation.value = ''
    await nextTick()
    textareaEl.value?.focus()
  } else {
    await nextTick()
    returnFocusEl?.focus()
    returnFocusEl = null
  }
})

function close() { emit('update:modelValue', false) }
function confirm() {
  const text = situation.value.trim()
  if (!text) return
  emit('confirm', text)
  emit('update:modelValue', false)
}

function handleKeydown(e) {
  if (e.key === 'Escape') { close(); return }
  if (e.key !== 'Tab' || !dialogEl.value) return
  const focusable = [...dialogEl.value.querySelectorAll('button, textarea, [tabindex="0"]')].filter(el => !el.disabled)
  if (!focusable.length) return
  const first = focusable[0], last = focusable[focusable.length - 1]
  if (e.shiftKey) { if (document.activeElement === first) { last.focus(); e.preventDefault() } }
  else { if (document.activeElement === last) { first.focus(); e.preventDefault() } }
}
</script>

<style scoped>
.dialog { max-width: 500px; }
.header-left { display: flex; align-items: center; gap: var(--sp-3); }
.header-seal {
  display: inline-flex; align-items: center; justify-content: center;
  width: 26px; height: 26px;
  background: var(--c-oxblood);
  color: var(--c-ivory-aged);
  font-family: var(--font-serif-alt);
  font-size: 13px; font-weight: 600;
  border-radius: 2px;
  box-shadow: var(--shadow-oxblood-seal);
}

.field-label {
  font-family: var(--font-serif);
  font-size: 13px;
  font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.04em;
  margin-bottom: var(--sp-2);
}

.situation-input {
  resize: vertical;
  min-height: 120px;
  font-family: var(--font-serif);
  font-size: 14px;
  line-height: 1.7;
  color: var(--c-umber-deep);
  background: var(--c-ivory);
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
  padding: var(--sp-3) var(--sp-4);
  transition: all var(--duration-fast);
}
.situation-input:focus {
  outline: none;
  border-color: var(--c-tarnished-gold);
  box-shadow: 0 0 0 2px rgba(168, 137, 78, 0.25);
}
.situation-input::placeholder {
  font-style: italic;
  color: var(--c-sepia);
  opacity: 0.7;
}

.meta-row {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: var(--sp-3);
  margin-top: var(--sp-2);
}
.field-hint {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 11px;
  color: var(--c-sepia);
  line-height: 1.5;
  flex: 1;
}
.char-count {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--c-sepia);
  white-space: nowrap;
  flex-shrink: 0;
  transition: color var(--duration-fast);
}
.char-count.char-warn { color: var(--c-warning-text); }
.char-count.char-danger { color: var(--c-danger-strong); font-weight: 600; }
</style>
