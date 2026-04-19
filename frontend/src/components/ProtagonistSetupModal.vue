<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="modal-overlay" @click.self="canClose && handleClose()">
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="proto-setup-title">
          <div class="modal-header">
            <div class="header-left">
              <span class="header-seal" aria-hidden="true">立</span>
              <h2 id="proto-setup-title" class="modal-title">为本卷立主</h2>
            </div>
            <button v-if="canClose" class="modal-close" aria-label="关闭" @click="handleClose">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            </button>
          </div>

          <div class="modal-body">
            <p class="hint-text">
              本卷的主角 · 由研究员扮演之人。立主后 AI 会为此卷生成 2-3 位同场角色。
            </p>

            <div class="lp-field">
              <label class="lp-field-label">名字</label>
              <div class="name-assist-row">
                <input
                  v-model="form.name"
                  type="text"
                  class="name-input"
                  :placeholder="namePlaceholder"
                  :maxlength="MAX_NAME_LEN"
                />
                <button
                  type="button"
                  class="btn-assist"
                  :disabled="isAssisting || !form.name.trim()"
                  @click="handleAssist"
                >
                  <span v-if="isAssisting" class="btn-inline-spinner" aria-hidden="true"></span>
                  {{ isAssisting ? `笔录中… ${assistElapsed}s` : 'AI 代笔' }}
                </button>
                <button
                  v-if="isAssisting"
                  type="button"
                  class="btn-icon-cancel"
                  @click="cancelAssist"
                >取消</button>
              </div>
            </div>

            <div class="lp-field">
              <label class="lp-field-label">身份 <span class="lp-field-optional">（选填）</span></label>
              <input v-model="form.role" type="text" placeholder="例如：东吴谋主、霍格沃茨 5 年级生" maxlength="100" />
            </div>

            <div class="lp-field">
              <label class="lp-field-label">背景小传 <span class="lp-field-optional">（选填但推荐）</span></label>
              <textarea v-model="form.bio" rows="5" placeholder="描述主角的来历、动机、独特处境..." maxlength="500" />
            </div>

            <div v-if="formError" class="lp-form-error" role="alert">{{ formError }}</div>
          </div>

          <div class="modal-footer">
            <button v-if="canClose" class="lp-btn-ghost-archive" :disabled="isSaving" @click="handleClose">稍后再说</button>
            <button class="lp-btn-archive" :disabled="isSaving || !form.name.trim()" @click="handleSubmit">
              <span v-if="isSaving" class="btn-inline-spinner" aria-hidden="true"></span>
              {{ isSaving ? '落笔中…' : '立此主角 →' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive, watch, onMounted, onBeforeUnmount } from 'vue'
import { useToast } from '../composables/useToast.js'
import { setUniverseProtagonist, assistProtagonist } from '../api/universe.js'
import { MAX_NAME_LEN } from '../constants/limits.js'

const props = defineProps({
  show: { type: Boolean, required: true },
  universeId: { type: Number, required: true },
  universe: { type: Object, default: null },
  canClose: { type: Boolean, default: true },
})
const emit = defineEmits(['close', 'done'])

const { success } = useToast()

const form = reactive({ name: '', role: '', bio: '' })
const formError = ref('')
const isSaving = ref(false)

const namePlaceholder = ref('例如：贾宝玉、张三、我自己')

let assistAbortCtrl = null
const isAssisting = ref(false)
const assistElapsed = ref(0)
let assistTimerId = null

watch(() => props.show, (v) => {
  if (v) {
    form.name = props.universe?.protagonist_name || ''
    form.role = props.universe?.protagonist_role || ''
    form.bio = props.universe?.protagonist_bio || ''
    formError.value = ''
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
    cancelAssist()
  }
})

function onKeydown(e) {
  if (!props.show || e.key !== 'Escape') return
  if (!props.canClose) return
  e.stopPropagation()
  handleClose()
}
onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
  cancelAssist()
})

async function handleAssist() {
  const name = form.name.trim()
  if (isAssisting.value || !name) return
  cancelAssist()
  assistAbortCtrl = new AbortController()
  isAssisting.value = true
  assistElapsed.value = 0
  assistTimerId = setInterval(() => { assistElapsed.value += 1 }, 1000)
  try {
    const res = await assistProtagonist(props.universeId, name, assistAbortCtrl.signal)
    const r = res.result || {}
    if (r.role) form.role = r.role
    if (r.bio)  form.bio = r.bio
    success('AI 已代笔主角档案')
  } catch (e) {
    if (e?.name === 'CanceledError' || e?.code === 'ERR_CANCELED') { /* 静默 */ }
    else { formError.value = e?.response?.data?.error || e?.message || 'AI 代笔失败，请重试' }
  } finally {
    stopAssistTimer()
    isAssisting.value = false
    assistAbortCtrl = null
  }
}

function cancelAssist() {
  if (assistAbortCtrl) { assistAbortCtrl.abort(); assistAbortCtrl = null }
  stopAssistTimer()
  isAssisting.value = false
}
function stopAssistTimer() {
  if (assistTimerId !== null) { clearInterval(assistTimerId); assistTimerId = null }
}

async function handleSubmit() {
  const name = form.name.trim()
  if (!name) { formError.value = '名字不能为空'; return }
  formError.value = ''
  isSaving.value = true
  try {
    const res = await setUniverseProtagonist(props.universeId, {
      name,
      role: form.role.trim() || null,
      bio: form.bio.trim() || null,
    })
    if (res.universe) emit('done', res.universe)
  } catch (e) {
    formError.value = e?.response?.data?.error || '保存失败，请重试'
  } finally {
    isSaving.value = false
  }
}

function handleClose() {
  if (isSaving.value) return
  emit('close')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(20, 15, 10, 0.55);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  z-index: var(--z-modal);
  padding: var(--sp-4);
}
.modal {
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
  width: 100%;
  max-width: 580px;
  max-height: 90vh;
  display: flex; flex-direction: column;
  box-shadow:
    var(--shadow-modal),
    inset 0 2px 0 var(--c-tarnished-gold),
    inset 0 3px 0 rgba(168, 137, 78, 0.3);
  position: relative;
}

.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: var(--sp-5) var(--sp-6) 0;
}
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
.modal-title {
  font-family: var(--font-serif-alt);
  font-size: 20px;
  font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.03em;
  margin: 0;
}
.modal-close {
  width: 30px; height: 30px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--c-sepia);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  border-radius: 2px;
  transition: all var(--duration-fast);
}
.modal-close:hover {
  border-color: var(--c-border-sepia);
  background: rgba(139, 111, 80, 0.1);
  color: var(--c-umber-deep);
}

.modal-body { padding: var(--sp-5) var(--sp-6); overflow-y: auto; flex: 1; }
.modal-footer {
  display: flex; gap: var(--sp-3); justify-content: flex-end;
  padding: var(--sp-4) var(--sp-6) var(--sp-5);
  border-top: 1px solid var(--c-border-archive);
}

.hint-text {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 13px;
  color: var(--c-sepia);
  line-height: 1.7;
  margin-bottom: var(--sp-4);
  padding: var(--sp-3) var(--sp-4);
  background: rgba(168, 137, 78, 0.08);
  border-left: 2px solid var(--c-tarnished-gold);
  border-radius: 0 2px 2px 0;
}

.lp-field { display: flex; flex-direction: column; gap: var(--sp-2); margin-bottom: var(--sp-4); }
.name-assist-row { display: flex; gap: var(--sp-2); align-items: center; }
.name-input { flex: 1; }

input[type="text"], textarea {
  padding: 9px 12px;
  background: var(--c-ivory);
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
  font-family: var(--font-serif);
  font-size: 13px;
  color: var(--c-umber-deep);
  transition: all var(--duration-fast);
}
input::placeholder, textarea::placeholder { font-style: italic; color: var(--c-sepia); opacity: 0.7; }
input:focus, textarea:focus {
  outline: none;
  border-color: var(--c-tarnished-gold);
  box-shadow: 0 0 0 2px rgba(168, 137, 78, 0.25);
}
textarea { resize: vertical; line-height: 1.7; }

.btn-assist {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 8px 12px;
  background: transparent;
  border: 1px solid var(--c-tarnished-gold);
  border-radius: 2px;
  color: var(--c-tarnished-gold);
  font-family: var(--font-serif);
  font-size: 12px;
  letter-spacing: 0.04em;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: all var(--duration-fast);
}
.btn-assist:hover:not(:disabled) {
  background: var(--c-tarnished-gold);
  color: var(--c-umber-deep);
}
.btn-assist:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-icon-cancel {
  padding: 8px 12px;
  border: 1px solid var(--c-border-sepia);
  border-radius: 2px;
  background: transparent;
  color: var(--c-umber);
  font-family: var(--font-serif);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--duration-fast);
}
.btn-icon-cancel:hover { border-color: var(--c-oxblood); color: var(--c-oxblood); }

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
.fade-enter-active .modal, .fade-leave-active .modal { transition: transform var(--duration-base) var(--ease-out); }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.fade-enter-from .modal, .fade-leave-to .modal { transform: scale(0.96) translateY(8px); }
</style>
