<template>
  <div class="narrative-stream">
    <!-- 顶部：主角信息 + 视角切换 + Agent 列表 -->
    <StreamHeader
      :universe="universe"
      :agents="agents"
      :current-perspective="currentPerspective"
      :perspective-switching="perspectiveSwitching"
      :retro-loading="retroLoading"
      :npc-ready="npcReady"
      @switch-perspective="handlePerspectiveSwitch"
    />

    <!-- 叙事线程 -->
    <StreamTurnList
      ref="turnListRef"
      :universe="universe"
      :thread="thread"
      :starter-actions="starterActions"
      :agent-count="agents.length"
      :current-perspective="currentPerspective"
      :retro-loading="retroLoading"
      :streaming="streaming"
      :streaming-narrator="streamingNarrator"
      :streaming-thinking="streamingThinking"
      :thinking-expanded="thinkingExpanded"
      :streaming-narration-done="streamingNarrationDone"
      :streaming-reactions="streamingReactions"
      :pending-action="pendingAction"
      :stream-error="streamError"
      :render-md="renderMd"
      @fill-action="fillAction"
      @clear-error="streamError = ''"
      @toggle-thinking="thinkingExpanded = !thinkingExpanded"
    />

    <!-- 输入区：历史节点提示 + 分叉选项 + 文本框 + 提交按钮 -->
    <StreamInputArea
      v-model="input"
      :streaming="streaming"
      :is-historical-node="isHistoricalNode"
      :branch-data="branchData"
      :thread-empty="thread.length === 0"
      @submit="submitAction"
      @select-branch="selectBranch"
      @dismiss-branch="branchData = null"
    />

    <!-- 新 NPC 出现 Toast -->
    <transition name="toast-slide">
      <div v-if="newAgentToast" class="new-agent-toast" aria-live="polite">
        新角色「{{ newAgentToast }}」已生成档案
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, watch, toRef } from 'vue'
import StreamHeader from './StreamHeader.vue'
import StreamTurnList from './StreamTurnList.vue'
import StreamInputArea from './StreamInputArea.vue'
import { useNarrativeStream } from '../composables/useNarrativeStream.js'

const props = defineProps({
  universe: { type: Object, default: null },
  selectedNodeId: { type: Number, default: null },
  initialInput: { type: String, default: '' },
  // 三态布尔：null=未知、true=就绪、false=生成中
  npcReady: { type: Boolean, default: null },
})

const emit = defineEmits(['node-created', 'perspective-changed', 'agent-created'])

// 滚动容器通过子组件 ref 暴露
const turnListRef = ref(null)
const turnsEl = ref(null)

watch(turnListRef, (comp) => {
  if (comp) turnsEl.value = comp.turnsEl
})

const {
  thread,
  agents,
  currentPerspective,
  starterActions,
  streaming,
  streamingNarrator,
  streamingThinking,
  thinkingExpanded,
  streamingNarrationDone,
  streamingReactions,
  branchData,
  streamError,
  pendingAction,
  input,
  retroLoading,
  perspectiveSwitching,
  isHistoricalNode,
  newAgentToast,
  handlePerspectiveSwitch,
  submitAction,
  selectBranch,
  fillAction,
  renderMd,
} = useNarrativeStream(
  toRef(props, 'universe'),
  toRef(props, 'selectedNodeId'),
  toRef(props, 'initialInput'),
  emit,
  turnsEl,
)
</script>

<style scoped>
.narrative-stream {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 0;
}

/* New agent toast */
.new-agent-toast {
  position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%);
  background: var(--c-near-black); color: var(--c-ivory);
  padding: 8px 18px; border-radius: var(--r-2xl);
  font-size: 13px; white-space: nowrap; z-index: 500;
  pointer-events: none;
}
.toast-slide-enter-active, .toast-slide-leave-active { transition: all 0.25s ease; }
.toast-slide-enter-from, .toast-slide-leave-to { opacity: 0; transform: translateX(-50%) translateY(8px); }
</style>
