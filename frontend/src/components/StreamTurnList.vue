<template>
  <div class="turns-area" ref="turnsEl">
    <!-- 空态 -->
    <div v-if="thread.length === 0 && !streaming" class="empty-state">
      <!-- 前情提要 -->
      <div v-if="universe?.premise" class="premise-card">
        <div class="premise-label">前情提要</div>
        <p class="premise-text">{{ universe.premise }}</p>
      </div>
      <p v-else class="empty-hint-plain">在下方写下第一笔批注，开启这卷平行档案。</p>
      <!-- 预制行动选项 -->
      <div v-if="starterActions.length > 0" class="starter-section">
        <span class="starter-label">馆藏开篇</span>
        <div class="starter-chips">
          <button
            v-for="action in starterActions"
            :key="action"
            class="starter-chip"
            @click="emit('fill-action', action)"
          >{{ action }}</button>
        </div>
      </div>
    </div>

    <!-- 历史轮次（v-memo：仅在 turn 内容或视角切换后更新时重渲染） -->
    <div
      v-for="turn in thread"
      :key="turn.id"
      v-memo="[turn.id, turn.narrator_content, turn.perspective_alt, turn.agent_reactions, currentPerspective, retroLoading]"
      class="turn"
    >
      <div v-if="turn.protagonist_action" class="turn-action">
        <span class="action-label" aria-hidden="true">批</span>
        <span class="action-text">{{ turn.protagonist_action }}</span>
      </div>

      <div v-if="turn.narrator_content" class="turn-narrator">
        <!-- 回溯加载中骨架屏 -->
        <div
          v-if="retroLoading && currentPerspective !== turn.perspective && !turn.perspective_alt"
          class="narrator-skeleton"
          aria-label="正在切换视角..."
        >
          <p class="skeleton-hint">正在切换视角…</p>
          <div class="skeleton-line" />
          <div class="skeleton-line" />
          <div class="skeleton-line short" />
        </div>
        <!-- 优先显示回溯内容 -->
        <div
          v-else
          class="narrator-content"
          v-html="renderMd(currentPerspective !== turn.perspective && turn.perspective_alt
            ? turn.perspective_alt
            : turn.narrator_content)"
        />
      </div>

      <div v-if="turn.agent_reactions && turn.agent_reactions.length > 0" class="turn-reactions">
        <div v-for="r in turn.agent_reactions" :key="r.agent_id" class="reaction-item">
          <span class="reaction-name">{{ r.name }}</span>
          <span class="reaction-text">{{ r.reaction }}</span>
        </div>
      </div>
    </div>

    <!-- 正在推演的轮次 -->
    <div v-if="streaming || streamingNarrator" class="turn streaming-turn">
      <div v-if="pendingAction" class="turn-action">
        <span class="action-label" aria-hidden="true">批</span>
        <span class="action-text">{{ pendingAction }}</span>
      </div>
      <div v-if="streamingNarrator" class="turn-narrator">
        <div class="narrator-content" v-html="renderMd(streamingNarrator)" />
        <span v-if="streaming && !streamingNarrationDone" class="cursor" aria-hidden="true">|</span>
      </div>
      <div v-if="streamingReactions.length > 0" class="turn-reactions">
        <div v-for="r in streamingReactions" :key="r.agent_id" class="reaction-item">
          <span class="reaction-name">{{ r.name }}</span>
          <span class="reaction-text">{{ r.reaction }}</span>
        </div>
      </div>
      <div
        v-if="streaming && streamingNarrationDone && streamingReactions.length === 0 && agentCount > 0"
        class="reactions-loading"
        aria-live="polite"
      >
        <div class="loading-dot" aria-hidden="true"></div>
        <span>等角色落笔反应...</span>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="streamError" class="stream-error">
      <span>{{ streamError }}</span>
      <button class="btn-secondary error-retry" @click="emit('clear-error')">关闭</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  universe: { type: Object, default: null },
  thread: { type: Array, default: () => [] },
  starterActions: { type: Array, default: () => [] },
  agentCount: { type: Number, default: 0 },
  currentPerspective: { type: String, default: 'god' },
  retroLoading: { type: Boolean, default: false },
  streaming: { type: Boolean, default: false },
  streamingNarrator: { type: String, default: '' },
  streamingNarrationDone: { type: Boolean, default: false },
  streamingReactions: { type: Array, default: () => [] },
  pendingAction: { type: String, default: '' },
  streamError: { type: String, default: '' },
  renderMd: { type: Function, required: true },
})

const emit = defineEmits(['fill-action', 'clear-error'])

// 滚动容器 ref，由父组件通过 turnsEl prop 传入外部引用
const turnsEl = ref(null)

defineExpose({ turnsEl })
</script>

<style scoped>
/* Turns area · 档案页正文 */
.turns-area {
  flex: 1; overflow-y: auto;
  padding: var(--sp-5) var(--sp-5) var(--sp-4);
  display: flex; flex-direction: column; gap: var(--sp-6);
}

.empty-state {
  display: flex; flex-direction: column; gap: var(--sp-4);
}

/* 前情 · 档案首页戳印卡 */
.premise-card {
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-left: 3px solid var(--c-oxblood);
  border-radius: 2px;
  padding: var(--sp-4) var(--sp-5);
  box-shadow: var(--shadow-paper-edge);
  position: relative;
}
.premise-label {
  font-family: var(--font-mono);
  font-size: 10px; font-weight: 500;
  letter-spacing: 0.15em;
  color: var(--c-oxblood);
  text-transform: uppercase;
  margin-bottom: var(--sp-2);
}
.premise-text {
  font-family: var(--font-serif);
  font-size: 14px;
  color: var(--c-archive-ink);
  line-height: 1.8;
  margin: 0;
  white-space: pre-wrap;
}

.empty-hint-plain {
  display: flex; align-items: center; justify-content: center;
  min-height: 80px;
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 14px;
  color: var(--c-sepia);
  text-align: center;
  border: 1px dashed var(--c-border-sepia);
  border-radius: 2px;
  padding: var(--sp-5);
}

/* 开篇选项 · 馆藏开篇 */
.starter-section { display: flex; flex-direction: column; gap: var(--sp-2); }
.starter-label {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  color: var(--c-sepia);
  letter-spacing: 0.15em;
  text-transform: uppercase;
}
.starter-chips { display: flex; flex-direction: column; gap: var(--sp-2); }
.starter-chip {
  text-align: left;
  padding: 10px 14px;
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
  cursor: pointer;
  font-family: var(--font-serif);
  font-size: 13px;
  color: var(--c-umber-deep);
  line-height: 1.5;
  transition: all var(--duration-fast);
}
.starter-chip:hover {
  border-color: var(--c-tarnished-gold);
  background: rgba(168, 137, 78, 0.08);
  box-shadow: var(--shadow-paper-edge);
}

/* 轮次 */
.turn { display: flex; flex-direction: column; gap: var(--sp-3); }

/* 玩家批注：档案式，右对齐，oxblood 印泥框 */
.turn-action {
  display: flex; align-items: flex-start; gap: var(--sp-3);
  justify-content: flex-end;
}
.action-label {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px;
  background: var(--c-oxblood);
  color: var(--c-ivory-aged);
  border: 1px solid var(--c-tarnished-gold);
  border-radius: 2px;
  font-family: var(--font-serif-alt);
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
  order: 2;
  box-shadow: 0 1px 2px rgba(20, 15, 10, 0.3);
}
.action-text {
  max-width: 70%;
  padding: 10px 14px;
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-oxblood);
  color: var(--c-umber-deep);
  border-radius: 2px;
  font-family: var(--font-serif);
  font-size: 14px;
  line-height: 1.7;
  order: 1;
  box-shadow: var(--shadow-paper-edge);
}

/* 叙事正文：档案页 */
.turn-narrator {
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
  padding: var(--sp-4) var(--sp-5);
  box-shadow: var(--shadow-paper-edge);
  position: relative;
}
.narrator-content {
  font-family: var(--font-serif);
  font-size: 14px;
  color: var(--c-archive-ink);
  line-height: 1.85;
}
.narrator-content :deep(p) { margin: 0 0 0.7em 0; }
.narrator-content :deep(p:last-child) { margin-bottom: 0; }
.narrator-content :deep(strong) { color: var(--c-umber-deep); font-weight: 600; }
.narrator-content :deep(em) { color: var(--c-sepia); font-style: italic; }

.cursor { animation: blink 1s infinite; margin-left: 2px; font-size: 14px; color: var(--c-tarnished-gold); }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

.streaming-turn .turn-narrator {
  border-color: var(--c-tarnished-gold);
  box-shadow: 0 0 0 1px rgba(168, 137, 78, 0.2), var(--shadow-paper-edge);
}

/* 角色反应：眉批风格，竖线引出 */
.turn-reactions {
  display: flex; flex-direction: column; gap: var(--sp-2);
  padding-left: var(--sp-4);
  border-left: 1px dashed var(--c-border-sepia);
  margin-left: var(--sp-3);
}
.reaction-item { display: flex; gap: var(--sp-3); align-items: flex-start; }
.reaction-name {
  flex-shrink: 0;
  font-family: var(--font-serif-alt);
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  background: var(--c-oxblood);
  color: var(--c-ivory-aged);
  border-radius: 2px;
  margin-top: 2px;
  letter-spacing: 0.02em;
}
.reaction-text {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 13px;
  color: var(--c-umber);
  line-height: 1.7;
}

.reactions-loading {
  display: flex; align-items: center; gap: var(--sp-2);
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 12px;
  color: var(--c-sepia);
  padding-left: var(--sp-4);
}
.loading-dot {
  width: 5px; height: 5px; border-radius: 50%;
  background: var(--c-tarnished-gold);
  animation: pulse 1.2s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }

/* 错误提示 */
.stream-error {
  display: flex; align-items: center; justify-content: space-between; gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: var(--c-danger-bg);
  border: 1px solid var(--c-danger-border);
  border-radius: 2px;
  font-family: var(--font-serif);
  font-size: 13px;
  color: var(--c-danger-strong);
}
.error-retry { padding: 4px 12px !important; font-size: 12px !important; }

/* 骨架屏 */
.narrator-skeleton { display: flex; flex-direction: column; gap: 8px; padding: 4px 0; }
.skeleton-hint {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 11px;
  color: var(--c-sepia);
  letter-spacing: 0.03em;
  margin-bottom: 2px;
}
.skeleton-line {
  height: 12px;
  background: rgba(168, 137, 78, 0.2);
  border-radius: 2px;
  animation: shimmer 1.4s ease-in-out infinite;
}
.skeleton-line.short { width: 55%; }
@keyframes shimmer { 0%,100%{opacity:0.4} 50%{opacity:0.8} }
</style>
