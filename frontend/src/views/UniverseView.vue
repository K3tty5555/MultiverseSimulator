<template>
  <div class="universe-view">
    <!-- Topbar -->
    <UniverseTopbar
      v-if="universe"
      :universe="universe"
      :selected-node-id="selectedNodeId"
      :agent-count="agentCount"
      :view-mode="viewMode"
      :view-modes="viewModes"
      @open-npc="showAgentManager = true"
      @view-change="onViewChange"
    />

    <!-- Loading（动画播放期间不显示，避免视觉叠加 V4） -->
    <div v-if="loading && !showYearFlip" class="loading-full">
      <div class="loading-pulse" aria-hidden="true"></div>
      <span>翻开卷宗...</span>
    </div>

    <!-- Main -->
    <div v-else-if="universe && !showYearFlip" :class="['main-area', `mode-${viewMode}`]">
      <!-- Left: Tree Panel -->
      <aside class="panel-left" v-show="viewMode !== 'work'">
        <UniverseTreePanel
          :universe="universe"
          :tree-data="treeData"
          :selected-node-id="selectedNodeId"
          @select-node="onSelectNode"
          @node-delete-request="onNodeDeleteRequest"
        />
      </aside>

      <div class="panel-divider" v-show="viewMode === 'split'" />

      <!-- Work mode: EntityStatePanel on the left -->
      <aside class="panel-entity" v-show="viewMode === 'work'">
        <EntityStatePanel
          ref="entityPanelRef"
          :universe-id="Number(currentUniverseId)"
        />
      </aside>

      <div class="panel-divider" v-show="viewMode === 'work'" />

      <!-- Right: Narrative Stream -->
      <section class="panel-right" v-show="viewMode !== 'tree'">
        <NarrativeStream
          :universe="universe"
          :selected-node-id="selectedNodeId"
          :initial-input="initialInput"
          :npc-ready="npcReady"
          @node-created="onNodeCreated"
          @perspective-changed="onPerspectiveChanged"
          @agent-created="onAgentCreated"
        />
      </section>
    </div>

    <!-- Error（动画播放期间不显示，避免仪式感被错误页割裂 S1） -->
    <div v-else-if="!showYearFlip" class="error-area">
      <p>卷宗翻阅失败</p>
      <router-link to="/" class="btn-secondary">返档案馆</router-link>
    </div>

    <!-- 删除节点确认弹层 -->
    <ConfirmModal
      :show="deleteConfirm !== null"
      :message="deleteConfirmMessage"
      :loading="deleting"
      :danger="true"
      confirm-label="删除"
      @confirm="confirmDelete"
      @cancel="deleteConfirm = null"
    />

    <!-- 时光逆流翻牌动画（从世界节点进入时，用"穿越时空"区别于自己回溯过往的"时光逆流"） -->
    <YearFlipOverlay
      :show="showYearFlip"
      :target-year="flipTargetYear || currentYear"
      label-text="穿越时空"
      @complete="onFlipComplete"
    />

    <!-- NPC 管理弹层 -->
    <UniverseAgentManager
      v-if="universe"
      :show="showAgentManager"
      :universe-id="Number(currentUniverseId)"
      @close="showAgentManager = false"
      @changed="refreshUniverse"
    />

    <!-- 主角设定弹层（新宇宙首次进入或主动编辑） -->
    <ProtagonistSetupModal
      v-if="universe"
      :show="showProtagonistSetup"
      :universe-id="Number(currentUniverseId)"
      :universe="universe"
      :can-close="!protagonistEmpty"
      @close="showProtagonistSetup = false"
      @done="onProtagonistDone"
    />

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import UniverseTopbar from '../components/universe/UniverseTopbar.vue'
import UniverseTreePanel from '../components/UniverseTreePanel.vue'
import NarrativeStream from '../components/NarrativeStream.vue'
import EntityStatePanel from '../components/EntityStatePanel.vue'
import ConfirmModal from '../components/ConfirmModal.vue'
import YearFlipOverlay from '../components/YearFlipOverlay.vue'
import UniverseAgentManager from '../components/UniverseAgentManager.vue'
import ProtagonistSetupModal from '../components/ProtagonistSetupModal.vue'
import { getUniverse, getUniverseTree, deleteNode } from '../api/universe.js'
import { useToast } from '../composables/useToast.js'
import { useYearFlipEntry } from '../composables/useYearFlipEntry.js'
import { useNpcReady } from '../composables/useNpcReady.js'

const props = defineProps({ universeId: String })
const route = useRoute()
const router = useRouter()
const { error: toastError } = useToast()

const currentUniverseId = computed(() => props.universeId || route.params.universeId)

// 新决策节点：从 History API state 读取预填文本（不出现在 URL，保护隐私）
const initialInput = history.state?.situation || ''

const universe = ref(null)
const treeData = ref(null)
const loading = ref(true)
const selectedNodeId = ref(null)
const viewMode = ref('split')
const entityPanelRef = ref(null)

// 删除节点状态
const deleteConfirm = ref(null)  // null | { nodeId, descendantCount }
const deleting = ref(false)

// 时光逆流动画（从世界节点进入时触发）
const {
  showYearFlip,
  flipTargetYear,
  currentYear,
  startFromQuery: startYearFlipFromQuery,
  cancel: cancelYearFlip,
  markDataReady: markUniverseReady,
  handleComplete: onFlipComplete,
} = useYearFlipEntry()

// NPC 预生成骨架轮询（composable 内部 watch universe.id 自动启停）
const { npcReady } = useNpcReady(universe)

// NPC 管理弹层
const showAgentManager = ref(false)
const agentCount = computed(() => universe.value?.agents?.length || 0)

// 主角设定弹层（新宇宙无主角时强制显示）
const showProtagonistSetup = ref(false)
const protagonistEmpty = computed(() =>
  !(universe.value?.protagonist_name || '').trim()
)

function onProtagonistDone(updated) {
  universe.value = updated
  showProtagonistSetup.value = false
  // 清除 setup_protagonist query（避免刷新页面重弹）
  if (route.query.setup_protagonist) {
    router.replace({ path: route.path, query: {} })
  }
}

async function refreshUniverse() {
  // NPC CRUD 后刷新 universe 拿最新 agents，让 StreamHeader chip 同步
  try {
    const res = await getUniverse(currentUniverseId.value)
    if (res.universe) universe.value = res.universe
  } catch {
    toastError('刷新宇宙数据失败，请手动刷新页面以同步 NPC 列表')
  }
}

const viewModes = [
  { key: 'tree',  label: '图谱', hint: '看本卷的决策分支全貌' },
  { key: 'split', label: '对读', hint: '分支图与正文并列对读' },
  { key: 'work',  label: '书房', hint: '世界状态与正文并列' },
]

function onViewChange(mode) {
  viewMode.value = mode
  if (mode === 'work') {
    entityPanelRef.value?.refresh()
  }
}

const selectedNodeInfo = computed(() => {
  if (!selectedNodeId.value) return ''
  return `#${selectedNodeId.value}`
})

const deleteConfirmMessage = computed(() => {
  if (!deleteConfirm.value) return ''
  const { nodeId, descendantCount, isRoot } = deleteConfirm.value
  if (isRoot && descendantCount === 0) {
    return `确认清空此卷？这将删除当前内容，卷宗回到空白状态，你可以重新开笔。此操作不可撤销。`
  }
  if (isRoot) {
    return `确认重开此卷？这将删除根批注及全部 ${descendantCount} 条后续批注，卷宗将回到空白。此操作不可撤销。`
  }
  if (descendantCount > 0) {
    return `确认删除此批注及其 ${descendantCount} 条后续批注？此操作不可撤销。`
  }
  return '确认删除此批注？此操作不可撤销。'
})

onMounted(async () => {
  startYearFlipFromQuery()
  await loadUniverse()
  // 加载完主角为空 → 强制弹主角设定（不可关闭），引导用户完成创建
  if (protagonistEmpty.value) {
    showProtagonistSetup.value = true
  }
  // 从 /agents 跳转来时自动打开 NPC 管理器
  else if (route.query.open_agents === '1') {
    showAgentManager.value = true
    router.replace({ path: route.path, query: {} })
  }
  // 从时间轴页「在此分叉」跳转：定位到指定节点，后续输入即从该节点分叉
  else if (route.query.focus_node) {
    const nodeId = parseInt(route.query.focus_node, 10)
    if (Number.isFinite(nodeId)) selectedNodeId.value = nodeId
    router.replace({ path: route.path, query: {} })
  }
})

async function loadUniverse() {
  loading.value = true
  try {
    const res = await getUniverse(currentUniverseId.value)
    universe.value = res.universe
    markUniverseReady()
    await loadTree()
  } catch {
    universe.value = null
    if (showYearFlip.value) {
      cancelYearFlip()
      toastError('卷宗翻阅失败，请重试')
    }
  } finally {
    loading.value = false
  }
}

async function loadTree() {
  try {
    const res = await getUniverseTree(currentUniverseId.value)
    treeData.value = res.tree
  } catch { /* tree not ready yet */ }
}

function onSelectNode(nodeId) {
  selectedNodeId.value = nodeId
}

async function onNodeCreated(nodeId) {
  selectedNodeId.value = nodeId
  await loadTree()
  // 延迟刷新实体状态：等待后台 LLM 提取完成（通常 5-8s）
  setTimeout(() => entityPanelRef.value?.refresh(), 8000)
}

function onPerspectiveChanged(perspective) {
  if (universe.value) universe.value.perspective = perspective
}

function onAgentCreated(agent) {
  if (universe.value) {
    universe.value.agents = [...(universe.value.agents || []), agent]
  }
}

// ── 删除节点 ────────────────────────────────────────────────

function countDescendantsFromTree(nodeId) {
  function countKids(node) {
    if (!node.children?.length) return 0
    return node.children.reduce((s, c) => s + 1 + countKids(c), 0)
  }
  function findNode(node) {
    if (node.id === nodeId) return node
    for (const c of node.children || []) {
      const found = findNode(c)
      if (found) return found
    }
    return null
  }
  const target = treeData.value ? findNode(treeData.value) : null
  return target ? countKids(target) : 0
}

function onNodeDeleteRequest(nodeId) {
  const descendantCount = countDescendantsFromTree(nodeId)
  const isRoot = treeData.value?.id === nodeId
  deleteConfirm.value = { nodeId, descendantCount, isRoot }
}

async function confirmDelete() {
  if (!deleteConfirm.value || deleting.value) return
  deleting.value = true
  const { nodeId } = deleteConfirm.value
  try {
    await deleteNode(currentUniverseId.value, nodeId)
    selectedNodeId.value = null  // 无条件清空，避免后代节点 id 悬空
    deleteConfirm.value = null
    await loadTree()
  } catch (e) {
    // 保留弹层，展示错误提示
    const msg = e?.response?.data?.error || '删除失败，请重试'
    toastError(msg)
  } finally {
    deleting.value = false
  }
}
</script>

<style scoped>
.universe-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--c-parchment);
  overflow: hidden;
  position: relative;
}
/* 档案桌面底纹：轻度 sepia vignette，不压过 panel 内容 */
.universe-view::before {
  content: '';
  position: absolute; inset: 0;
  background: var(--img-hero, var(--c-umber-deep)) center/cover no-repeat;
  opacity: 0.18;
  pointer-events: none;
  z-index: 0;
}

.loading-full, .error-area {
  flex: 1;
  display: flex; align-items: center; justify-content: center;
  gap: var(--sp-3);
  font-family: var(--font-serif);
  color: var(--c-sepia);
  font-size: 14px;
  letter-spacing: 0.05em;
  position: relative; z-index: 1;
}
.error-area { flex-direction: column; gap: var(--sp-4); }
.loading-pulse {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--c-tarnished-gold);
  animation: pulse-archive 1.4s infinite;
}
@keyframes pulse-archive { 0%,100%{opacity:1; transform:scale(1)} 50%{opacity:.3; transform:scale(0.8)} }

.main-area { flex: 1; display: flex; overflow: hidden; position: relative; z-index: 1; }
.mode-tree  .panel-left   { flex: 1; }
.mode-split .panel-left   { flex: 1; }
.mode-split .panel-right  { flex: 1; }
.mode-work  .panel-entity { width: 240px; flex-shrink: 0; display: flex; flex-direction: column; }
.mode-work  .panel-right  { flex: 1; }

.panel-left, .panel-right, .panel-entity {
  overflow: hidden;
  background: var(--c-ivory-aged);
  position: relative;
}
.panel-entity { display: none; }
.panel-right { display: flex; flex-direction: column; }
/* 左 panel 纸纹：隐约的暗金 + 暗斑，消除空白塑料感 */
.panel-left::before {
  content: '';
  position: absolute; inset: 0;
  background:
    radial-gradient(ellipse at 18% 15%, rgba(168, 137, 78, 0.08) 0%, transparent 45%),
    radial-gradient(ellipse at 82% 85%, rgba(107, 79, 53, 0.06) 0%, transparent 50%);
  pointer-events: none;
}
/* 书脊装订：中央 divider 金色渐变 */
.panel-divider {
  width: 4px;
  background:
    linear-gradient(to right,
      rgba(20, 15, 10, 0.14) 0%,
      rgba(168, 137, 78, 0.22) 50%,
      rgba(20, 15, 10, 0.14) 100%);
  flex-shrink: 0;
  box-shadow: inset 0 2px 6px rgba(20, 15, 10, 0.10);
}

</style>
