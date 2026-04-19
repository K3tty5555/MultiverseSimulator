<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="lp-modal-overlay" @click.self="handleClose">
        <div class="lp-modal uni-modal" role="dialog" aria-modal="true" aria-labelledby="new-uni-title">
          <div class="lp-modal-header">
            <div class="header-left">
              <span class="header-seal" aria-hidden="true">卷</span>
              <h2 id="new-uni-title" class="lp-modal-title">
                {{ step === 'seed' ? '开启新卷宗' : '拟定卷宗骨架' }}
              </h2>
            </div>
            <button class="lp-modal-close" aria-label="关闭" @click="handleClose">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            </button>
          </div>

          <!-- Step A：类型 + 题材 -->
          <div v-if="step === 'seed'" class="lp-modal-body">
            <div class="lp-field">
              <label class="lp-field-label">卷宗类型</label>
              <div class="lp-type-toggle" role="group" aria-label="卷宗类型">
                <button
                  v-for="opt in typeOptions"
                  :key="opt.value"
                  type="button"
                  :class="['lp-type-btn', { active: universeType === opt.value }]"
                  :aria-pressed="universeType === opt.value"
                  @click="universeType = opt.value"
                >{{ opt.label }}</button>
              </div>
              <p class="lp-field-hint-small">{{ typeHint }}</p>
            </div>

            <div class="lp-field">
              <label class="lp-field-label">题材 / 关键词</label>
              <textarea
                v-model="keywords"
                rows="3"
                class="lp-input-archive desc-textarea"
                :placeholder="keywordPlaceholder"
                maxlength="200"
              />
              <p class="lp-field-hint-small">{{ keywords.length }}/200</p>
            </div>

            <div v-if="formError" class="lp-form-error" role="alert">{{ formError }}</div>
          </div>

          <!-- Step B：AI 拟稿确认 -->
          <div v-else class="lp-modal-body">
            <div class="lp-field">
              <label class="lp-field-label">卷宗名</label>
              <input v-model="scaffold.title" type="text" maxlength="200" class="lp-input-archive" />
            </div>
            <div class="lp-field">
              <label class="lp-field-label">世界标签 <span class="lp-field-optional">（IP / 题材名，供角色长廊分类）</span></label>
              <input v-model="scaffold.world_label" type="text" class="lp-input-archive" :placeholder="worldLabelPlaceholder" maxlength="40" />
            </div>
            <div v-if="universeType === 'historical'" class="lp-field">
              <label class="lp-field-label">时期 / 年号 <span class="lp-field-optional">（选填）</span></label>
              <input v-model="scaffold.era_label" type="text" class="lp-input-archive" placeholder="例如：汉末三国 · 208 AD" maxlength="100" />
            </div>
            <div class="lp-field">
              <label class="lp-field-label">卷首小引</label>
              <textarea v-model="scaffold.premise" rows="8" class="lp-input-archive desc-textarea" maxlength="2000" />
              <p class="lp-field-hint-small">{{ scaffold.premise.length }}/2000</p>
            </div>

            <div v-if="formError" class="lp-form-error" role="alert">{{ formError }}</div>
          </div>

          <!-- 按钮区 -->
          <div class="lp-modal-footer">
            <template v-if="step === 'seed'">
              <button class="lp-btn-ghost-archive" :disabled="isGenerating" @click="handleClose">取消</button>
              <button
                v-if="isGenerating"
                class="btn-cancel-assist"
                @click="cancelGenerate"
              >停笔</button>
              <button class="lp-btn-archive" :disabled="isGenerating || !canGenerate" @click="handleGenerate">
                <span v-if="isGenerating" class="lp-btn-inline-spinner" aria-hidden="true"></span>
                {{ isGenerating ? `拟稿中… ${elapsed}s` : 'AI 拟稿' }}
              </button>
            </template>
            <template v-else>
              <button class="lp-btn-ghost-archive" :disabled="isCreating" @click="step = 'seed'">返回重拟</button>
              <button class="lp-btn-archive" :disabled="isCreating || !canCreate" @click="handleCreate">
                <span v-if="isCreating" class="lp-btn-inline-spinner" aria-hidden="true"></span>
                {{ isCreating ? '开卷中…' : '开卷 →' }}
              </button>
            </template>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useToast } from '../composables/useToast.js'
import { scaffoldUniverse, createUniverse } from '../api/universe.js'

const props = defineProps({
  show: { type: Boolean, required: true },
  basedOnEvent: { type: Object, default: null },
  fixedType: { type: String, default: '' },
  fixedWorldLabel: { type: String, default: '' },
})
const emit = defineEmits(['close', 'created'])

const { error: toastError } = useToast()

const step = ref('seed')
const universeType = ref('historical')
const keywords = ref('')

const scaffold = reactive({ title: '', premise: '', era_label: '', world_label: '' })

const worldLabelPlaceholder = computed(() =>
  universeType.value === 'historical'
    ? '例如：三国 / 明朝 / 大航海时代'
    : '例如：红楼梦 / 赛博朋克 2077 / 哈利波特'
)
const formError = ref('')

let abortCtrl = null
const isGenerating = ref(false)
const elapsed = ref(0)
let timerId = null

const isCreating = ref(false)

const typeOptions = [
  { value: 'historical', label: '史卷' },
  { value: 'fictional',  label: '幻卷' },
]
const typeHint = computed(() =>
  universeType.value === 'historical'
    ? '真实历史时期 · 适合推演帝王将相或历史关头'
    : '文学 / 游戏 / 未来设定 · 适合推演小说人物或假想场景'
)
const keywordPlaceholder = computed(() =>
  universeType.value === 'historical'
    ? '例如：明朝中期的倭寇之乱；1969 阿波罗登月；三国官渡之战前夜...'
    : '例如：红楼梦大观园；赛博朋克 2077 夜之城；哈利波特霍格沃茨 5 年级...'
)

const canGenerate = computed(() => keywords.value.trim().length > 0)
const canCreate = computed(() =>
  scaffold.title.trim().length > 0 && scaffold.premise.trim().length > 0
)

watch(() => props.show, (v) => {
  if (v) {
    reset()
    if (props.basedOnEvent) {
      universeType.value = props.fixedType || 'historical'
      const ev = props.basedOnEvent
      scaffold.title = `如果${ev.title}…`
      scaffold.premise = ev.description
        ? `${ev.description}\n\n—— 然而此时，命运的分岔即将展开...`
        : `基于「${ev.title}」的假设分叉。`
      if (props.fixedWorldLabel) scaffold.world_label = props.fixedWorldLabel
      if (ev.year) scaffold.era_label = `${ev.title} · ${ev.year > 0 ? ev.year + ' AD' : '前 ' + (-ev.year) + ' 年'}`
      step.value = 'confirm'
    }
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
    cancelGenerate()
  }
})

function reset() {
  step.value = 'seed'
  universeType.value = 'historical'
  keywords.value = ''
  scaffold.title = ''
  scaffold.premise = ''
  scaffold.era_label = ''
  scaffold.world_label = ''
  formError.value = ''
}

function onKeydown(e) {
  if (!props.show || e.key !== 'Escape') return
  e.stopPropagation()
  handleClose()
}
onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
  cancelGenerate()
})

async function handleGenerate() {
  if (!canGenerate.value || isGenerating.value) return
  formError.value = ''
  cancelGenerate()
  abortCtrl = new AbortController()
  isGenerating.value = true
  elapsed.value = 0
  timerId = setInterval(() => { elapsed.value += 1 }, 1000)
  try {
    const res = await scaffoldUniverse({
      universe_type: universeType.value,
      keywords: keywords.value.trim(),
    }, abortCtrl.signal)
    const r = res.result || {}
    scaffold.title = r.title || ''
    scaffold.premise = r.premise || ''
    scaffold.era_label = r.era_label || ''
    scaffold.world_label = r.world_label || ''
    step.value = 'confirm'
  } catch (e) {
    if (e?.name === 'CanceledError' || e?.code === 'ERR_CANCELED') {
      /* 静默 */
    } else {
      formError.value = e?.response?.data?.error || e?.message || 'AI 拟稿失败，请重试'
    }
  } finally {
    stopTimer()
    isGenerating.value = false
    abortCtrl = null
  }
}

function cancelGenerate() {
  if (abortCtrl) { abortCtrl.abort(); abortCtrl = null }
  stopTimer()
  isGenerating.value = false
}
function stopTimer() {
  if (timerId !== null) { clearInterval(timerId); timerId = null }
}

async function handleCreate() {
  if (!canCreate.value || isCreating.value) return
  formError.value = ''
  isCreating.value = true
  try {
    const res = await createUniverse({
      title: scaffold.title.trim(),
      premise: scaffold.premise.trim(),
      protagonist_name: '',
      universe_type: universeType.value,
      era_label: scaffold.era_label.trim() || null,
      world_label: scaffold.world_label.trim() || null,
      canonical_event_id: props.basedOnEvent?.id || null,
      perspective: 'god',
    })
    if (res.universe) emit('created', res.universe)
    else toastError('开卷失败：档案未就绪')
  } catch (e) {
    formError.value = e?.response?.data?.error || '开卷失败，请重试'
  } finally {
    isCreating.value = false
  }
}

function handleClose() {
  if (isCreating.value) return
  emit('close')
}
</script>

<style scoped>
.uni-modal { max-width: 600px; }

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
.desc-textarea { resize: vertical; line-height: 1.7; }

.btn-cancel-assist {
  padding: 7px 12px;
  border: 1px solid var(--c-border-sepia);
  border-radius: 2px;
  background: transparent;
  color: var(--c-umber);
  font-family: var(--font-serif);
  font-size: 12px;
  letter-spacing: 0.04em;
  cursor: pointer;
  transition: all var(--duration-fast);
}
.btn-cancel-assist:hover {
  border-color: var(--c-oxblood);
  color: var(--c-oxblood);
  background: rgba(107, 46, 42, 0.08);
}

.fade-enter-active, .fade-leave-active { transition: opacity var(--duration-base) var(--ease-out); }
.fade-enter-active .lp-modal, .fade-leave-active .lp-modal { transition: transform var(--duration-base) var(--ease-out); }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.fade-enter-from .lp-modal, .fade-leave-to .lp-modal { transform: scale(0.96) translateY(8px); }
</style>
