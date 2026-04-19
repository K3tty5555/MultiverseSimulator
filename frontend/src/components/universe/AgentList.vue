<template>
  <div>
    <div v-if="loading && agents.length === 0" class="empty-state">加载中...</div>

    <div v-else-if="agents.length === 0" class="empty-state">
      <div class="empty-illustration" aria-hidden="true">
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
          <circle cx="24" cy="18" r="7" stroke="currentColor" stroke-width="1.5" stroke-opacity="0.5"/>
          <path d="M10 40c0-7 6-13 14-13s14 6 14 13" stroke="currentColor" stroke-width="1.5" stroke-opacity="0.5" stroke-linecap="round"/>
        </svg>
      </div>
      <p>本卷尚无其他角色。点击下方按钮新增一位，或由 AI 在推演中自动生成。</p>
    </div>

    <template v-else>
      <input
        v-if="agents.length > 8"
        :value="searchQuery"
        @input="$emit('update:searchQuery', $event.target.value)"
        type="text"
        class="agent-search lp-input-archive"
        placeholder="搜索角色名字/身份..."
        aria-label="搜索角色"
      />

      <div v-for="group in groupedAgents" :key="group.stance" class="agent-group">
        <h4 class="agent-group-title">{{ group.label }}<span class="agent-group-count">{{ group.list.length }}</span></h4>
        <ul class="agent-rows">
          <li
            v-for="a in group.list"
            :key="a.id"
            :ref="el => onRowMount(a.id, el)"
            :class="['agent-row', { 'is-highlighted': a.id === highlightAgentId }]"
          >
            <div class="agent-row-main">
              <span class="agent-row-name">{{ a.name }}</span>
              <span v-if="a.role" class="agent-row-role">{{ a.role }}</span>
            </div>
            <div class="agent-row-actions">
              <button class="btn-icon" @click="$emit('edit', a)">编辑</button>
              <button class="btn-icon btn-danger" @click="$emit('delete', a)">除名</button>
            </div>
          </li>
        </ul>
      </div>
    </template>

    <div class="list-actions">
      <button class="lp-btn-ghost-archive" @click="$emit('create')">+ 新增角色</button>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick } from 'vue'

const props = defineProps({
  agents: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  searchQuery: { type: String, default: '' },
  highlightAgentId: { type: Number, default: null },
})
defineEmits(['update:searchQuery', 'create', 'edit', 'delete'])

const filteredAgents = computed(() => {
  const q = props.searchQuery.trim().toLowerCase()
  if (!q) return props.agents
  return props.agents.filter(a =>
    (a.name || '').toLowerCase().includes(q) ||
    (a.role || '').toLowerCase().includes(q)
  )
})

const groupedAgents = computed(() => {
  const groups = { ally: [], neutral: [], adversary: [] }
  for (const a of filteredAgents.value) {
    (groups[a.stance] || groups.neutral).push(a)
  }
  return [
    { stance: 'ally',      label: '盟友', list: groups.ally },
    { stance: 'neutral',   label: '中立', list: groups.neutral },
    { stance: 'adversary', label: '对手', list: groups.adversary },
  ].filter(g => g.list.length > 0)
})

function onRowMount(agentId, el) {
  if (agentId === props.highlightAgentId && el) {
    nextTick(() => el.scrollIntoView?.({ block: 'nearest', behavior: 'smooth' }))
  }
}
</script>

<style scoped>
.empty-state {
  text-align: center;
  padding: var(--sp-8) var(--sp-4);
  font-family: var(--font-serif);
  font-style: italic;
  color: var(--c-sepia);
  font-size: 14px;
  line-height: 1.7;
}
.empty-illustration { margin-bottom: var(--sp-3); color: var(--c-tarnished-gold); opacity: 0.7; }

.agent-search {
  width: 100%;
  margin-bottom: var(--sp-3);
}

.agent-group { margin-bottom: var(--sp-4); }
.agent-group:last-child { margin-bottom: 0; }
.agent-group-title {
  position: sticky; top: 0;
  display: flex; align-items: center; gap: var(--sp-2);
  margin: 0 0 var(--sp-2);
  padding: 6px 2px;
  background: var(--c-ivory-aged);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  color: var(--c-tarnished-gold);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  z-index: 1;
}
.agent-group-count {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 18px; height: 16px; padding: 0 4px;
  background: var(--c-oxblood);
  color: var(--c-ivory-aged);
  font-family: var(--font-mono);
  font-size: 10px;
  border-radius: 2px;
  letter-spacing: 0.05em;
}

.agent-rows {
  list-style: none; margin: 0; padding: 0;
  display: flex; flex-direction: column; gap: var(--sp-2);
}
.agent-row {
  display: flex; align-items: center; justify-content: space-between;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: var(--c-ivory);
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
  transition: background 0.5s ease, border-color 0.5s ease, box-shadow var(--duration-fast);
}
.agent-row:hover { border-color: var(--c-tarnished-gold); box-shadow: var(--shadow-paper-edge); }
.agent-row.is-highlighted {
  background: rgba(168, 137, 78, 0.12);
  border-color: var(--c-tarnished-gold);
  box-shadow: var(--shadow-gold-deep);
}
.agent-row-main {
  display: flex; align-items: center; gap: var(--sp-2);
  min-width: 0; flex: 1; flex-wrap: wrap;
}
.agent-row-name {
  font-family: var(--font-serif-alt);
  font-size: 15px; font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.02em;
}
.agent-row-role {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 12px;
  color: var(--c-sepia);
}
.agent-row-actions { display: flex; gap: var(--sp-2); flex-shrink: 0; }

.list-actions { margin-top: var(--sp-4); display: flex; justify-content: center; }

.btn-icon {
  padding: 5px 12px;
  border: 1px solid var(--c-border-sepia);
  border-radius: 2px;
  background: transparent;
  color: var(--c-umber);
  font-family: var(--font-serif);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--duration-fast);
  letter-spacing: 0.04em;
}
.btn-icon:hover:not(:disabled) {
  border-color: var(--c-tarnished-gold);
  color: var(--c-umber-deep);
  background: rgba(168, 137, 78, 0.1);
}
.btn-danger:hover:not(:disabled) {
  border-color: var(--c-oxblood) !important;
  color: var(--c-oxblood) !important;
  background: rgba(107, 46, 42, 0.08) !important;
}
</style>
