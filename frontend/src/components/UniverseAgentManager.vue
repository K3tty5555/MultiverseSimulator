<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="lp-modal-overlay" @click.self="handleClose">
        <div class="lp-modal modal" role="dialog" aria-modal="true" aria-labelledby="agent-mgr-title">
          <div class="lp-modal-header">
            <h2 id="agent-mgr-title" class="lp-modal-title">{{ titleText }}</h2>
            <button class="lp-modal-close" aria-label="关闭" @click="handleClose">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <!-- LIST 态 -->
          <div v-if="view === 'list'" class="lp-modal-body">
            <AgentList
              :agents="agents"
              :loading="listRequest.loading.value"
              v-model:search-query="searchQuery"
              :highlight-agent-id="highlightAgentId"
              @create="startCreate"
              @edit="startEdit"
              @delete="requestDelete"
            />
          </div>

          <!-- CREATE / EDIT 态 -->
          <div v-else class="lp-modal-body">
            <div class="lp-field">
              <label class="lp-field-label">名字</label>
              <div class="lp-name-assist-row">
                <input
                  v-model="form.name"
                  type="text"
                  class="name-input lp-input-archive"
                  placeholder="角色姓名，例如：鲁肃"
                  :maxlength="MAX_NAME_LEN"
                />
                <button
                  type="button"
                  class="lp-btn-assist"
                  :disabled="isAssisting || !form.name.trim()"
                  :title="view.type === 'edit' ? '将用 AI 覆盖当前字段' : 'AI 辅助生成完整档案'"
                  @click="handleAssistRequest"
                >
                  <span v-if="isAssisting" class="lp-btn-inline-spinner" aria-hidden="true"></span>
                  {{ isAssisting ? `生成中… ${assistElapsed}s` : 'AI 辅助填写' }}
                </button>
                <button
                  v-if="isAssisting"
                  type="button"
                  class="btn-icon btn-cancel"
                  @click="cancelAssist"
                  aria-label="取消 AI 生成"
                >取消</button>
              </div>
              <p v-if="view.type === 'edit'" class="lp-field-hint-small">
                修改名字会自动重命名，保留该角色 的记忆与历史节点引用
              </p>
            </div>

            <AgentFormFields :form="form" />

            <div v-if="formError" class="lp-form-error" role="alert">{{ formError }}</div>
          </div>

          <div v-if="view !== 'list'" class="lp-modal-footer">
            <button class="lp-btn-ghost-archive" :disabled="isSaving || isAssisting" @click="backToList">取消</button>
            <button class="lp-btn-archive" :disabled="isSaving" @click="handleSubmit">
              <span v-if="isSaving" class="lp-btn-inline-spinner" aria-hidden="true"></span>
              {{ isSaving ? (view.type === 'create' ? '创建中…' : '保存中…')
                          : (view.type === 'create' ? '创建' : '保存') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 删除二次确认 -->
    <ConfirmModal
      :show="deleteTarget !== null"
      :message="deleteConfirmMessage"
      :loading="removeRequest.loading.value"
      :danger="true"
      confirm-label="删除"
      @confirm="confirmDelete"
      @cancel="deleteTarget = null"
    />

    <!-- 覆盖确认（edit 态 AI 辅助） -->
    <ConfirmModal
      :show="showAssistOverwriteConfirm"
      message="AI 重新生成会覆盖当前所有字段（身份、立场、性格、MBTI、背景），确认继续吗？"
      confirm-label="继续生成"
      @confirm="performAssistAfterConfirm"
      @cancel="showAssistOverwriteConfirm = false"
    />
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import ConfirmModal from './ConfirmModal.vue'
import AgentFormFields from './AgentFormFields.vue'
import AgentList from './universe/AgentList.vue'
import { useToast } from '../composables/useToast.js'
import { useApiRequest } from '../composables/useApiRequest.js'
import {
  listAgents, addAgent, updateAgent, deleteAgent, assistAgent, renameAgent,
} from '../api/universe.js'
import { MAX_NAME_LEN } from '../constants/limits.js'

const props = defineProps({
  show: { type: Boolean, required: true },
  universeId: { type: Number, required: true },
})
const emit = defineEmits(['close', 'changed'])

const { success } = useToast()

// ── 状态机：view 是 'list' 或判别式对象 ──────────────────────────────
// { type: 'create' } | { type: 'edit', id, originalName }
const view = ref('list')

const agents = ref([])
const searchQuery = ref('')
const highlightAgentId = ref(null)
const highlightRowEl = ref(null)

const form = reactive(emptyForm())
const formError = ref('')
const deleteTarget = ref(null)
const showAssistOverwriteConfirm = ref(false)

// AI 辅助取消支持 + 经过时间
let assistAbortCtrl = null
const isAssisting = ref(false)
const assistElapsed = ref(0)
let assistTimerId = null

function emptyForm() {
  return { name: '', role: '', bio: '', persona: '', mbti: '', stance: 'neutral' }
}

// ── API 请求（走 useApiRequest 统一 loading/error/toast） ─────────────
const listRequest = useApiRequest(
  (uid) => listAgents(uid).then(r => r.agents || []),
  { showErrorToast: true }
)
const submitRequest = useApiRequest(
  async () => {
    if (view.value.type === 'create') {
      const res = await addAgent(props.universeId, { name: form.name.trim(), ...stripForm() })
      return res.agent
    }
    // edit 态：可能需要先 rename（name 变了），再 update 其他字段
    const newName = form.name.trim()
    const { id, originalName } = view.value
    if (newName !== originalName) {
      await renameAgent(props.universeId, id, newName)
    }
    const res = await updateAgent(props.universeId, id, stripForm())
    return res.agent
  },
  { showErrorToast: false }   // 错误在 formError 里显示，避免 toast 重复
)
const removeRequest = useApiRequest(
  (agentId) => deleteAgent(props.universeId, agentId),
  { showErrorToast: true }
)

const isSaving = computed(() => submitRequest.loading.value)

function stripForm() {
  return {
    role:    form.role.trim() || null,
    bio:     form.bio.trim() || null,
    persona: form.persona.trim() || null,
    mbti:    form.mbti.trim() || null,
    stance:  form.stance,
  }
}

// ── 标题 ─────────────────────────────────────────────────────────────
const titleText = computed(() => {
  if (view.value === 'list') return '角色名录'
  if (view.value.type === 'create') return '新增角色'
  return `编辑「${view.value.originalName}」`
})

// ── 删除确认文案（明示后果） ──────────────────────────────────────────
const deleteConfirmMessage = computed(() => {
  if (!deleteTarget.value) return ''
  const t = deleteTarget.value
  const hasMemory = !!(t.memory_summary || t.last_node_id)
  const base = `确认删除 角色「${t.name}」？`
  const consequence = hasMemory
    ? '该角色 已有剧情记忆，删除后：名字仍保留在历史节点的 agent_reactions 快照中，但不再参与新剧情。'
    : '删除后该角色 不再参与新剧情。'
  return `${base}\n${consequence}\n此操作可被"新增同名角色"恢复。`
})

// ── 生命周期 & 显隐 ──────────────────────────────────────────────────
let listSeq = 0   // 并发守卫：旧 loadList 的回调如晚到则丢弃

async function loadList() {
  const mySeq = ++listSeq
  try {
    const result = await listRequest.execute(props.universeId)
    if (mySeq !== listSeq) return   // 已被新一轮替代
    agents.value = Array.isArray(result) ? result : []
  } catch { /* toast 已 handle */ }
}

watch(() => props.show, (v) => {
  if (v) {
    view.value = 'list'
    searchQuery.value = ''
    highlightAgentId.value = null
    loadList()
    // body 滚动冻结
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
    // 关闭时取消在飞的 AI 请求
    cancelAssist()
  }
})

function onKeydown(e) {
  if (!props.show) return
  if (e.key !== 'Escape') return
  // 叠加的 ConfirmModal 若打开，让它先消费（内部亦应监听 ESC）
  if (deleteTarget.value !== null || showAssistOverwriteConfirm.value) return
  e.stopPropagation()
  handleClose()
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
  cancelAssist()
})

// ── 导航 ─────────────────────────────────────────────────────────────
function startCreate() {
  view.value = { type: 'create' }
  Object.assign(form, emptyForm())
  formError.value = ''
}

function startEdit(a) {
  view.value = { type: 'edit', id: a.id, originalName: a.name }
  form.name = a.name
  form.role = a.role || ''
  form.bio = a.bio || ''
  form.persona = a.persona || ''
  form.mbti = a.mbti || ''
  form.stance = a.stance || 'neutral'
  formError.value = ''
}

function backToList() {
  if (isSaving.value || isAssisting.value) return
  view.value = 'list'
  formError.value = ''
}

// ── AI 辅助（支持取消 + 经过时间 + 覆盖确认） ────────────────────────
function handleAssistRequest() {
  if (view.value.type === 'edit') {
    showAssistOverwriteConfirm.value = true
  } else {
    performAssist()
  }
}
function performAssistAfterConfirm() {
  showAssistOverwriteConfirm.value = false
  performAssist()
}
async function performAssist() {
  const name = form.name.trim()
  if (isAssisting.value || !name) return
  cancelAssist()   // 确保干净
  assistAbortCtrl = new AbortController()
  isAssisting.value = true
  assistElapsed.value = 0
  assistTimerId = setInterval(() => { assistElapsed.value += 1 }, 1000)
  try {
    const res = await assistAgent(props.universeId, name, assistAbortCtrl.signal)
    const r = res.result || {}
    if (r.role !== undefined)    form.role = r.role
    if (r.bio !== undefined)     form.bio = r.bio
    if (r.persona !== undefined) form.persona = r.persona
    if (r.mbti !== undefined)    form.mbti = r.mbti
    if (r.stance)                form.stance = r.stance
    success('AI 已代笔角色档案')
  } catch (e) {
    if (e?.name === 'CanceledError' || e?.code === 'ERR_CANCELED') {
      // 用户主动取消，静默
    } else {
      formError.value = e.response?.data?.error || e.message || 'AI 辅助失败，请重试'
    }
  } finally {
    stopAssistTimer()
    isAssisting.value = false
    assistAbortCtrl = null
  }
}
function cancelAssist() {
  if (assistAbortCtrl) {
    assistAbortCtrl.abort()
    assistAbortCtrl = null
  }
  stopAssistTimer()
  isAssisting.value = false
}
function stopAssistTimer() {
  if (assistTimerId !== null) { clearInterval(assistTimerId); assistTimerId = null }
}

// ── 保存（创建 / 编辑） ──────────────────────────────────────────────
async function handleSubmit() {
  formError.value = ''
  const name = form.name.trim()
  if (!name) { formError.value = '名字不能为空'; return }
  try {
    const saved = await submitRequest.execute()
    success(view.value.type === 'create' ? '角色已登记' : '已保存')
    emit('changed')
    const savedId = saved?.id || null
    view.value = 'list'
    await loadList()
    if (savedId) highlightAndScroll(savedId)
  } catch (e) {
    formError.value = e.response?.data?.error || '保存失败，请重试'
  }
}

async function highlightAndScroll(agentId) {
  highlightAgentId.value = agentId
  await nextTick()
  highlightRowEl.value?.scrollIntoView?.({ block: 'nearest', behavior: 'smooth' })
  // 1.5s 后取消高亮
  setTimeout(() => {
    if (highlightAgentId.value === agentId) highlightAgentId.value = null
  }, 1500)
}

// ── 删除 ─────────────────────────────────────────────────────────────
function requestDelete(a) { deleteTarget.value = a }

async function confirmDelete() {
  if (!deleteTarget.value) return
  try {
    await removeRequest.execute(deleteTarget.value.id)
    success('角色已除名')
    emit('changed')
    deleteTarget.value = null
    await loadList()
  } catch { /* toast handled */ }
}

// ── 关闭 ─────────────────────────────────────────────────────────────
function handleClose() {
  if (isSaving.value || removeRequest.loading.value) return
  // AI 辅助运行中，关闭时会 abort（watch show 里处理）
  emit('close')
}
</script>

<style scoped>
/* modal 外壳已迁移至 design.css 的 .lp-modal-* 全局原语 */
.modal { max-width: 620px; }

/* LIST 相关 style 已迁移至 AgentList 子组件 */

/* btn-icon · 取消 AI 辅助场景 */
.btn-icon {
  padding: 5px 12px; border: 1px solid var(--c-border-sepia); border-radius: 2px;
  background: transparent; color: var(--c-umber);
  font-family: var(--font-serif); font-size: 12px; letter-spacing: 0.04em;
  cursor: pointer; transition: all var(--duration-fast);
}
.btn-icon:hover:not(:disabled) { border-color: var(--c-tarnished-gold); color: var(--c-umber-deep); background: rgba(168, 137, 78, 0.1); }
.btn-icon:disabled { opacity: 0.5; cursor: default; }
.btn-icon.btn-cancel:hover:not(:disabled) { border-color: var(--c-oxblood); color: var(--c-oxblood); }

/* Form 局部补充（通用样式已提到 design.css 的 lp-* 原语） */
.lp-field { display: flex; flex-direction: column; gap: var(--sp-2); margin-bottom: var(--sp-4); }
.name-input { flex: 1; }

.fade-enter-active, .fade-leave-active { transition: opacity var(--duration-base) var(--ease-out); }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
