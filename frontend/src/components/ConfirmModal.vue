<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="modal-backdrop"
        @click.self="$emit('cancel')"
        @keydown.esc="$emit('cancel')"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="labelId"
      >
        <div class="modal-box">
          <div class="modal-seal" aria-hidden="true">{{ danger ? '封' : '令' }}</div>
          <p :id="labelId" class="modal-msg">{{ message }}</p>
          <div class="modal-actions">
            <button ref="cancelBtn" class="modal-cancel" @click="$emit('cancel')">取消</button>
            <button
              :class="['modal-confirm', { 'modal-confirm--danger': danger }]"
              :disabled="loading"
              @click="$emit('confirm')"
            >{{ loading ? '处理中…' : confirmLabel }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, useId } from 'vue'

const props = defineProps({
  show:         Boolean,
  message:      String,
  confirmLabel: { type: String, default: '确认' },
  loading:      { type: Boolean, default: false },
  danger:       { type: Boolean, default: false },
})
defineEmits(['confirm', 'cancel'])

const cancelBtn = ref(null)
const labelId = useId ? useId() : 'confirm-modal-label'

let previousActiveEl = null
watch(() => props.show, (val) => {
  if (val) {
    previousActiveEl = document.activeElement
    setTimeout(() => cancelBtn.value?.focus(), 50)
  } else if (previousActiveEl && typeof previousActiveEl.focus === 'function') {
    previousActiveEl.focus()
    previousActiveEl = null
  }
})
</script>

<style scoped>
.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(20, 15, 10, 0.55);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  z-index: var(--z-modal-confirm);
}

.modal-box {
  position: relative;
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-left: 4px solid var(--c-oxblood);
  border-radius: 2px;
  padding: var(--sp-6) var(--sp-6) var(--sp-5);
  box-shadow:
    var(--shadow-modal),
    inset 0 2px 0 var(--c-tarnished-gold),
    inset 0 3px 0 rgba(168, 137, 78, 0.3);
  max-width: 380px;
  width: 90%;
}

.modal-seal {
  position: absolute;
  top: -14px; left: var(--sp-5);
  width: 28px; height: 28px;
  background: var(--c-oxblood);
  color: var(--c-ivory-aged);
  font-family: var(--font-serif-alt);
  font-size: 14px;
  font-weight: 600;
  display: flex; align-items: center; justify-content: center;
  border-radius: 2px;
  box-shadow: var(--shadow-oxblood-seal);
  letter-spacing: 0.05em;
}

.modal-msg {
  font-family: var(--font-serif);
  font-size: 14px;
  line-height: 1.75;
  color: var(--c-archive-ink);
  margin: var(--sp-3) 0 var(--sp-5);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-3);
}

.modal-cancel {
  font-family: var(--font-serif);
  font-size: 13px;
  padding: 7px 16px;
  background: transparent;
  color: var(--c-umber);
  border: 1px solid var(--c-border-sepia);
  border-radius: 2px;
  cursor: pointer;
  letter-spacing: 0.04em;
  transition: all var(--duration-fast);
}
.modal-cancel:hover {
  background: rgba(139, 111, 80, 0.1);
  border-color: var(--c-umber);
  color: var(--c-umber-deep);
}

.modal-confirm {
  font-family: var(--font-serif);
  font-size: 13px;
  padding: 7px 18px;
  background: var(--c-oxblood);
  color: var(--c-ivory-aged);
  border: 1px solid var(--c-oxblood-dark);
  border-radius: 2px;
  cursor: pointer;
  letter-spacing: 0.04em;
  box-shadow: var(--shadow-oxblood-seal);
  transition: all var(--duration-fast);
}
.modal-confirm:hover:not(:disabled) {
  background: var(--c-oxblood-dark);
  box-shadow: var(--shadow-oxblood-seal), 0 0 0 2px rgba(168, 137, 78, 0.3);
}
.modal-confirm:disabled { opacity: 0.6; cursor: not-allowed; }

/* 危险操作：印泥更深 + 填色反转 */
.modal-confirm--danger {
  background: var(--c-oxblood-dark);
  border-color: var(--c-oxblood-dark);
}
.modal-confirm--danger:hover:not(:disabled) {
  background: var(--c-oxblood-dark);
  box-shadow: var(--shadow-oxblood-seal), 0 0 0 3px var(--c-tarnished-gold);
}

.modal-enter-active, .modal-leave-active { transition: opacity var(--duration-base) var(--ease-out); }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-active .modal-box, .modal-leave-active .modal-box { transition: transform var(--duration-base) var(--ease-out); }
.modal-enter-from .modal-box, .modal-leave-to .modal-box { transform: scale(0.95) translateY(8px); }
</style>
