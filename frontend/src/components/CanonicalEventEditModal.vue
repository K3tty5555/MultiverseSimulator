<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="lp-modal-overlay" @click.self="handleClose">
        <div class="lp-modal event-modal" role="dialog" aria-modal="true" aria-labelledby="edit-event-title">
          <div class="lp-modal-header">
            <div class="header-left">
              <span class="header-seal" aria-hidden="true">史</span>
              <h2 id="edit-event-title" class="lp-modal-title">修订史实节点</h2>
            </div>
            <button class="lp-modal-close" aria-label="关闭" @click="handleClose">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            </button>
          </div>

          <div class="lp-modal-body">
            <div class="lp-form-stack">
              <div class="lp-field">
                <label class="lp-field-label">标题</label>
                <input v-model="form.title" type="text" maxlength="200" placeholder="如：官渡之战" class="lp-input-archive" />
              </div>
              <div class="lp-field">
                <label class="lp-field-label">年份 <span class="lp-field-optional">（选填，公元前用负数）</span></label>
                <input v-model.number="form.year" type="number" placeholder="如 200，或留空" class="lp-input-archive" />
              </div>
              <div class="lp-field">
                <label class="lp-field-label">描述 <span class="lp-field-optional">（100-200 字）</span></label>
                <textarea v-model="form.description" rows="5" maxlength="1000" placeholder="事件经过与对角色的意义..." class="lp-input-archive desc-textarea" />
              </div>
            </div>
            <div v-if="formError" class="lp-form-error" role="alert">{{ formError }}</div>
          </div>

          <div class="lp-modal-footer">
            <button class="btn-delete" :disabled="isSaving" @click="confirmDelete = true">
              除名
            </button>
            <span class="footer-spacer"></span>
            <button class="lp-btn-ghost-archive" :disabled="isSaving" @click="handleClose">取消</button>
            <button class="lp-btn-archive" :disabled="isSaving || !form.title.trim()" @click="handleSave">
              <span v-if="isSaving" class="btn-inline-spinner" aria-hidden="true"></span>
              {{ isSaving ? '落笔中…' : '保存修订' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <ConfirmModal
      :show="confirmDelete"
      :message="`确认除名史实节点「${form.title}」？已关联此节点的宇宙会取消关联（宇宙本身保留）。`"
      confirm-label="除名"
      :danger="true"
      :loading="isDeleting"
      @confirm="handleDelete"
      @cancel="confirmDelete = false"
    />
  </Teleport>
</template>

<script setup>
import { ref, reactive, watch, onMounted, onBeforeUnmount } from 'vue'
import { useToast } from '../composables/useToast.js'
import { updateCanonicalEvent, deleteCanonicalEvent } from '../api/universe.js'
import ConfirmModal from './ConfirmModal.vue'

const props = defineProps({
  show: { type: Boolean, required: true },
  event: { type: Object, default: null },
})
const emit = defineEmits(['close', 'saved', 'deleted'])
const { error: toastError } = useToast()

const form = reactive({ title: '', year: null, description: '' })
const formError = ref('')
const isSaving = ref(false)
const isDeleting = ref(false)
const confirmDelete = ref(false)

watch(() => props.show, (v) => {
  if (v && props.event) {
    form.title = props.event.title || ''
    form.year = props.event.year ?? null
    form.description = props.event.description || ''
    formError.value = ''
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

function onKeydown(e) {
  if (!props.show || e.key !== 'Escape' || confirmDelete.value) return
  e.stopPropagation()
  handleClose()
}
onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})

async function handleSave() {
  if (!form.title.trim()) { formError.value = '标题不能为空'; return }
  formError.value = ''
  isSaving.value = true
  try {
    const res = await updateCanonicalEvent(props.event.id, {
      title: form.title.trim(),
      year: form.year === null || form.year === '' ? null : Number(form.year),
      description: form.description.trim(),
    })
    if (res.event) emit('saved', res.event)
  } catch (e) {
    formError.value = e?.response?.data?.error || '保存失败，请重试'
  } finally {
    isSaving.value = false
  }
}

async function handleDelete() {
  isDeleting.value = true
  try {
    await deleteCanonicalEvent(props.event.id)
    confirmDelete.value = false
    emit('deleted', props.event.id)
  } catch (e) {
    toastError(e?.response?.data?.error || '除名失败')
  } finally {
    isDeleting.value = false
  }
}

function handleClose() {
  if (isSaving.value) return
  emit('close')
}
</script>

<style scoped>
.event-modal { max-width: 560px; }

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

.lp-field { display: flex; flex-direction: column; gap: var(--sp-2); margin-bottom: var(--sp-4); }
.desc-textarea { resize: vertical; min-height: 120px; line-height: 1.7; }

.footer-spacer { flex: 1; }

.btn-delete {
  padding: 7px 16px;
  border: 1px solid var(--c-border-sepia);
  border-radius: 2px;
  background: transparent;
  color: var(--c-sepia);
  font-family: var(--font-serif);
  font-size: 13px;
  letter-spacing: 0.04em;
  cursor: pointer;
  transition: all var(--duration-fast);
}
.btn-delete:hover:not(:disabled) {
  border-color: var(--c-oxblood);
  color: var(--c-oxblood);
  background: rgba(107, 46, 42, 0.08);
}
.btn-delete:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-inline-spinner {
  display: inline-block;
  width: 10px; height: 10px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: btn-spin 0.7s linear infinite;
  margin-right: 5px;
}
@keyframes btn-spin { to { transform: rotate(360deg); } }

.fade-enter-active, .fade-leave-active { transition: opacity var(--duration-base) var(--ease-out); }
.fade-enter-active .lp-modal, .fade-leave-active .lp-modal { transition: transform var(--duration-base) var(--ease-out); }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.fade-enter-from .lp-modal, .fade-leave-to .lp-modal { transform: scale(0.96) translateY(8px); }
</style>
