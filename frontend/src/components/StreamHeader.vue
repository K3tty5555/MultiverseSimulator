<template>
  <div class="stream-header-wrap">
    <div class="stream-header">
      <div class="protagonist-info">
        <span class="protagonist-seal" aria-hidden="true">主</span>
        <span class="protagonist-name">{{ universe?.protagonist_name }}</span>
        <span v-if="universe?.protagonist_role" class="protagonist-role">· {{ universe.protagonist_role }}</span>
      </div>
      <div class="header-actions">
        <div class="perspective-toggle" role="group" aria-label="叙事视角">
          <button
            :class="['ptoggle-btn', { active: currentPerspective === 'god' }]"
            :aria-pressed="currentPerspective === 'god'"
            :disabled="perspectiveSwitching"
            title="纵观 · 从卷首俯瞰全局"
            @click="emit('switch-perspective', 'god')"
          >
            <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true"><circle cx="7" cy="7" r="6" stroke="currentColor" stroke-width="1.3"/><path d="M1 7h12M7 1a8 8 0 010 12M7 1a8 8 0 000 12" stroke="currentColor" stroke-width="1.3"/></svg>
            纵观
          </button>
          <button
            :class="['ptoggle-btn', { active: currentPerspective === 'first_person' }]"
            :aria-pressed="currentPerspective === 'first_person'"
            :disabled="perspectiveSwitching"
            title="亲历 · 以主角第一视角亲临"
            @click="emit('switch-perspective', 'first_person')"
          >
            <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true"><circle cx="7" cy="4" r="2.5" stroke="currentColor" stroke-width="1.3"/><path d="M2 13c0-2.761 2.239-5 5-5s5 2.239 5 5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
            亲历
          </button>
        </div>
        <div v-if="retroLoading" class="retro-loading" aria-live="polite">
          <div class="retro-dot" aria-hidden="true"></div>
          <span>视角转换中...</span>
        </div>
      </div>
    </div>

    <!-- 在场角色列表（三态防 CLS） -->
    <div v-if="npcReady === true && agents.length > 0" class="agents-strip">
      <span class="agents-label">在场</span>
      <div class="agents-list">
        <span
          v-for="agent in agents"
          :key="agent.id"
          :class="['agent-chip', `stance-${agent.stance}`]"
          :title="`${agent.role || ''} — ${agent.persona || ''}`"
        >
          <span class="chip-dot" aria-hidden="true"></span>{{ agent.name }}
        </span>
      </div>
    </div>

    <div v-else-if="npcReady === false" class="agents-strip" aria-label="角色生成中...">
      <span class="agents-label">在场</span>
      <div class="agents-list">
        <span
          v-for="placeholder in skeletonPlaceholders"
          :key="placeholder"
          class="agent-chip agent-chip-skeleton"
          aria-hidden="true"
        >{{ placeholder }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  universe: { type: Object, default: null },
  agents: { type: Array, default: () => [] },
  currentPerspective: { type: String, default: 'god' },
  perspectiveSwitching: { type: Boolean, default: false },
  retroLoading: { type: Boolean, default: false },
  npcReady: { type: Boolean, default: null },
})

const emit = defineEmits(['switch-perspective'])

const skeletonPlaceholders = ['占位贰', '占位四字名', '占位三字']
</script>

<style scoped>
.stream-header-wrap {
  background: var(--c-ivory-aged);
  flex-shrink: 0;
}

.stream-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: var(--sp-3) var(--sp-5);
  border-bottom: 1px solid var(--c-border-archive);
  gap: var(--sp-3);
}

/* 主角区：印章 + 衬线姓名 */
.protagonist-info { display: flex; align-items: center; gap: var(--sp-2); min-width: 0; }
.protagonist-seal {
  display: inline-flex; align-items: center; justify-content: center;
  width: 22px; height: 22px;
  background: var(--c-oxblood);
  color: var(--c-ivory-aged);
  font-family: var(--font-serif-alt);
  font-size: 12px;
  font-weight: 600;
  border-radius: 2px;
  box-shadow: 0 1px 2px rgba(20, 15, 10, 0.3);
  flex-shrink: 0;
}
.protagonist-name {
  font-family: var(--font-serif-alt);
  font-size: 17px;
  font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.02em;
}
.protagonist-role {
  font-family: var(--font-serif);
  font-size: 12px;
  color: var(--c-sepia);
  font-style: italic;
}

.header-actions { display: flex; align-items: center; gap: var(--sp-3); flex-shrink: 0; }

/* 视角切换：档案风 toggle */
.perspective-toggle {
  display: flex;
  background: transparent;
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
  padding: 2px;
  gap: 0;
}
.ptoggle-btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 4px 12px;
  border: none;
  background: transparent;
  font-family: var(--font-serif);
  font-size: 12px;
  color: var(--c-sepia);
  cursor: pointer;
  transition: all var(--duration-fast);
  letter-spacing: 0.04em;
  border-radius: 1px;
}
.ptoggle-btn:hover:not(.active):not(:disabled) {
  color: var(--c-umber-deep);
  background: rgba(168, 137, 78, 0.08);
}
.ptoggle-btn.active {
  background: var(--c-oxblood);
  color: var(--c-ivory-aged);
  font-weight: 500;
}
.ptoggle-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.retro-loading {
  display: flex; align-items: center; gap: var(--sp-2);
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 12px;
  color: var(--c-tarnished-gold);
}
.retro-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--c-tarnished-gold);
  animation: pulse-retro 1.4s infinite;
}
@keyframes pulse-retro { 0%,100%{opacity:1} 50%{opacity:.3} }

/* 在场角色列表：古籍印泥色 + 圆点图例 */
.agents-strip {
  display: flex; align-items: center; gap: var(--sp-3);
  padding: var(--sp-2) var(--sp-5);
  border-bottom: 1px solid var(--c-border-archive);
  background: rgba(232, 223, 200, 0.4);
  flex-shrink: 0;
  overflow-x: auto;
}
.agents-label {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--c-sepia);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  flex-shrink: 0;
}
.agents-list {
  display: flex; gap: var(--sp-3);
  flex-wrap: nowrap;
  align-items: center;
}
.agent-chip {
  display: inline-flex; align-items: center; gap: 5px;
  font-family: var(--font-serif);
  font-size: 12px;
  color: var(--c-umber-deep);
  white-space: nowrap;
  letter-spacing: 0.02em;
}
.chip-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}
/* 立场色：古籍印泥三色，低饱和统一 sepia 调 */
.stance-ally     { color: var(--c-deep-teal-soft); }  /* 靛青 · 盟友 */
.stance-neutral  { color: var(--c-umber); }           /* 赭石 · 中立 */
.stance-adversary{ color: var(--c-oxblood); }         /* 朱砂 · 对手 */

.agent-chip-skeleton {
  color: transparent !important;
  background: rgba(168, 137, 78, 0.2) !important;
  border-radius: 2px;
  padding: 2px 8px;
  animation: chip-shimmer 1.4s ease-in-out infinite;
  user-select: none;
}
.agent-chip-skeleton .chip-dot { display: none; }
@keyframes chip-shimmer {
  0%, 100% { opacity: 0.5; }
  50%      { opacity: 0.25; }
}
</style>
