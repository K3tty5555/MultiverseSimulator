/**
 * useNarrativeStream — NarrativeStream 核心业务逻辑。
 *
 * 负责：SSE 推演流、回溯叙事流、分支选择、视角切换、新 Agent 提示。
 * 纯逻辑，不含任何模板/样式。
 */
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useEventStream } from './useEventStream.js'
import {
  getThread,
  switchPerspective,
  prepareTurn,
} from '../api/universe.js'

/**
 * @param {import('vue').Ref} universeRef      — props.universe
 * @param {import('vue').Ref} selectedNodeIdRef — props.selectedNodeId
 * @param {import('vue').Ref} initialInputRef   — props.initialInput
 * @param {Function} emit                        — 组件 emit 函数
 * @param {import('vue').Ref} turnsEl            — 滚动容器 ref（由父组件传入）
 */
export function useNarrativeStream(
  universeRef,
  selectedNodeIdRef,
  initialInputRef,
  emit,
  turnsEl,
) {
  // ─── 叙事数据 ────────────────────────────────────────────────
  const thread = ref([])
  const agents = computed(() => universeRef.value?.agents || [])
  const currentPerspective = ref(universeRef.value?.perspective || 'god')
  const starterActions = computed(() => universeRef.value?.starter_actions || [])

  // ─── 推演流状态 ───────────────────────────────────────────────
  const streaming = ref(false)
  const streamingNarrator = ref('')
  const streamingNarrationDone = ref(false)
  const streamingReactions = ref([])
  const branchData = ref(null)
  const streamError = ref('')
  const pendingAction = ref('')
  const input = ref('')

  // ─── 视角切换 / 回溯 ─────────────────────────────────────────
  const retroLoading = ref(false)
  const perspectiveSwitching = ref(false)

  // ─── 节点跟踪 ────────────────────────────────────────────────
  const latestNodeId = ref(null)

  // ─── Toast ───────────────────────────────────────────────────
  const newAgentToast = ref('')
  let toastTimer = null

  // ─── SSE ─────────────────────────────────────────────────────
  const turnStream = useEventStream()
  const retroStream = useEventStream()
  let retroTimeout = null

  // ─── 计算属性 ────────────────────────────────────────────────
  const isHistoricalNode = computed(() => {
    if (!latestNodeId.value || thread.value.length === 0) return false
    const lastInThread = thread.value[thread.value.length - 1]
    return lastInThread?.id !== latestNodeId.value
  })

  // ─── Watchers ────────────────────────────────────────────────

  // 从 universe prop 同步视角
  watch(
    () => universeRef.value?.perspective,
    (val) => { if (val) currentPerspective.value = val },
    { immediate: true },
  )

  // selectedNodeId 变化时重新加载线程
  watch(
    () => selectedNodeIdRef.value,
    async (nodeId) => {
      if (nodeId !== null) await loadThread(nodeId)
    },
    { immediate: false },
  )

  // 预填输入框（只在输入框为空时生效一次）
  watch(
    () => initialInputRef.value,
    (val) => { if (val && !input.value) input.value = val },
    { immediate: true },
  )

  // ─── 生命周期 ────────────────────────────────────────────────
  onMounted(async () => {
    if (universeRef.value) await loadThread(selectedNodeIdRef.value)
  })

  onBeforeUnmount(() => {
    clearTimeout(toastTimer)
    clearTimeout(retroTimeout)
    // turnStream / retroStream 由各自的 useEventStream onBeforeUnmount 关闭
  })

  // ─── 加载线程 ────────────────────────────────────────────────
  async function loadThread(nodeId) {
    if (!universeRef.value) return
    try {
      const res = await getThread(universeRef.value.id, nodeId || undefined)
      thread.value = res.thread || []
      const lastTurn = thread.value[thread.value.length - 1]
      // 记录最新节点
      if (!nodeId && lastTurn) latestNodeId.value = lastTurn.id
      // 恢复上次到达的分叉选项
      if (lastTurn?.branch_options?.length > 0 && !branchData.value) {
        branchData.value = {
          prompt: lastTurn.branch_prompt || '上次到达了一个分叉点，选择继续方向',
          options: lastTurn.branch_options,
        }
      }
      await scrollBottom()
    } catch {
      thread.value = []
    }
  }

  // ─── 视角切换 ────────────────────────────────────────────────
  async function handlePerspectiveSwitch(perspective) {
    if (
      perspective === currentPerspective.value ||
      !universeRef.value ||
      perspectiveSwitching.value
    ) return

    perspectiveSwitching.value = true
    const prev = currentPerspective.value
    currentPerspective.value = perspective // 乐观更新

    try {
      await switchPerspective(universeRef.value.id, perspective)
      emit('perspective-changed', perspective)

      const lastNodes = thread.value.slice(-3)
      if (lastNodes.length === 0) {
        perspectiveSwitching.value = false
        return
      }
      const nodeIds = lastNodes.map((n) => n.id)

      retroLoading.value = true
      // 30s 超时保护，防止永久 loading
      retroTimeout = setTimeout(() => {
        retroLoading.value = false
        perspectiveSwitching.value = false
        retroStream.close()
      }, 30000)

      const retroParams = new URLSearchParams({ node_ids: nodeIds.join(','), perspective })
      const retroUrl = `/api/universe/${universeRef.value.id}/retrospect/stream?${retroParams}`
      retroStream.open(retroUrl, {
        onMessage(data) {
          if (data.type === 'retro_done') {
            const node = thread.value.find((n) => n.id === data.node_id)
            if (node) node.perspective_alt = data.alt_content
          } else if (data.type === 'done' || data.type === 'error') {
            clearTimeout(retroTimeout)
            retroTimeout = null
            retroLoading.value = false
            perspectiveSwitching.value = false
            retroStream.close()
          }
        },
        onError() {
          clearTimeout(retroTimeout)
          retroTimeout = null
          retroLoading.value = false
          perspectiveSwitching.value = false
        },
        timeout: 35000,
      })
    } catch {
      currentPerspective.value = prev
      perspectiveSwitching.value = false
    }
  }

  // ─── 提交行动 ────────────────────────────────────────────────
  async function submitAction() {
    if (!input.value.trim() || streaming.value || !universeRef.value) return
    const action = input.value.trim()
    input.value = ''
    branchData.value = null
    pendingAction.value = action

    streaming.value = true
    streamingNarrator.value = ''
    streamingNarrationDone.value = false
    streamingReactions.value = []
    streamError.value = ''

    const lastNode = thread.value[thread.value.length - 1]
    const parentNodeId = lastNode?.id ?? selectedNodeIdRef.value ?? null

    turnStream.close()

    try {
      const lang = localStorage.getItem('locale') || 'zh'
      const res = await prepareTurn(universeRef.value.id, {
        action,
        parent_node_id: parentNodeId,
        lang,
      })

      const turnUrl = `/api/universe/${universeRef.value.id}/turn/stream?token=${encodeURIComponent(res.token)}`
      turnStream.open(turnUrl, {
        async onMessage(data) {
          await handleStreamEvent(data)
          if (data.type !== 'narrator_chunk') await scrollBottom()
        },
        onError() {
          input.value = pendingAction.value
          pendingAction.value = ''
          streamingNarrator.value = ''
          streamingReactions.value = []
          streaming.value = false
          streamError.value = '推演连接中断，请重试'
        },
        timeout: 45000,
      })
    } catch {
      streaming.value = false
      pendingAction.value = ''
      input.value = action
      streamError.value = '推演请求失败，请重试'
    }
  }

  // ─── 处理 SSE 事件 ────────────────────────────────────────────
  async function handleStreamEvent(data) {
    if (data.type === 'agent_created') {
      emit('agent-created', data.agent)
      showAgentToast(data.agent.name)
    } else if (data.type === 'narrator_chunk') {
      streamingNarrator.value += data.chunk
    } else if (data.type === 'narrator_done') {
      streamingNarrator.value = data.content
      streamingNarrationDone.value = true
    } else if (data.type === 'agent_reaction') {
      streamingReactions.value.push({
        agent_id: data.agent_id,
        name: data.name,
        reaction: data.reaction,
      })
    } else if (data.type === 'branch_prompt') {
      branchData.value = { prompt: data.prompt, options: data.options || [] }
    } else if (data.type === 'node_done') {
      thread.value.push({
        id: data.node_id,
        turn_number: data.turn_number,
        protagonist_action: pendingAction.value,
        narrator_content: streamingNarrator.value,
        perspective: currentPerspective.value,
        perspective_alt: null,
        agent_reactions: [...streamingReactions.value],
        branch_prompt: branchData.value?.prompt || null,
        branch_options: branchData.value?.options || [],
      })
      latestNodeId.value = data.node_id
      streamingNarrator.value = ''
      streamingNarrationDone.value = false
      streamingReactions.value = []
      pendingAction.value = ''
      streaming.value = false
      turnStream.close()
      emit('node-created', data.node_id)
      await scrollBottom()
    } else if (data.type === 'error') {
      input.value = pendingAction.value
      pendingAction.value = ''
      streamingNarrator.value = ''
      streamingReactions.value = []
      streaming.value = false
      streamError.value = data.message || '推演失败，请重试'
      turnStream.close()
    }
  }

  // ─── 工具函数 ─────────────────────────────────────────────────
  function selectBranch(opt) {
    input.value = opt.description || opt.label
    branchData.value = null
  }

  function fillAction(action) {
    input.value = action
  }

  function showAgentToast(name) {
    newAgentToast.value = name
    clearTimeout(toastTimer)
    toastTimer = setTimeout(() => { newAgentToast.value = '' }, 3000)
  }

  async function scrollBottom() {
    await nextTick()
    if (turnsEl.value) turnsEl.value.scrollTop = turnsEl.value.scrollHeight
  }

  function renderMd(text) {
    if (!text) return ''
    return DOMPurify.sanitize(marked.parse(text))
  }

  return {
    // 数据
    thread,
    agents,
    currentPerspective,
    starterActions,
    // 推演流
    streaming,
    streamingNarrator,
    streamingNarrationDone,
    streamingReactions,
    branchData,
    streamError,
    pendingAction,
    input,
    // 视角 / 回溯
    retroLoading,
    perspectiveSwitching,
    // 节点
    isHistoricalNode,
    // Toast
    newAgentToast,
    // 方法
    handlePerspectiveSwitch,
    submitAction,
    selectBranch,
    fillAction,
    renderMd,
  }
}
