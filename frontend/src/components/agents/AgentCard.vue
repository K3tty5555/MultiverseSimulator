<template>
  <article
    class="agent-card"
    :title="tooltip"
    role="button"
    tabindex="0"
    :aria-label="`${agent.name} - ${tooltip} - 点击查看时间轴`"
    @click="$emit('select', agent)"
    @keydown.enter.prevent="$emit('select', agent)"
  >
    <AgentPortrait
      :name="agent.name"
      :universe-type="agent.universe_type"
      :world-label="agent.world_label"
    />

    <div class="agent-info">
      <div class="agent-name">{{ agent.name }}</div>
      <div class="agent-origin">{{ originText }}</div>
      <div v-if="agent.occurrences.length === 0" class="agent-occurrences agent-occurrences--none">
        尚未登场
      </div>
      <div v-else-if="agent.occurrences.length > 1" class="agent-occurrences">
        登场于 {{ agent.occurrences.length }} 卷
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import AgentPortrait from './AgentPortrait.vue'

const props = defineProps({
  agent: { type: Object, required: true },
})
defineEmits(['select'])

const typeMap = { historical: '史', fictional: '幻', personal: '己' }

const originText = computed(() => {
  const t = typeMap[props.agent.universe_type] || '史'
  return props.agent.world_label ? `${t} · ${props.agent.world_label}` : (t === '史' ? '史卷' : '幻卷')
})
const tooltip = computed(() => {
  const n = props.agent.occurrences.length
  return n === 0 ? `${originText.value} · 尚未登场` : `${originText.value} · 登场于 ${n} 卷`
})
</script>

<style scoped>
.agent-card {
  display: flex; flex-direction: column;
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
  overflow: hidden;
  cursor: pointer;
  box-shadow: var(--shadow-paper-edge);
  transition: transform var(--duration-base) var(--ease-out),
              box-shadow var(--duration-base) var(--ease-out),
              border-color var(--duration-base);
}
.agent-card:hover {
  transform: translateY(-3px);
  border-color: var(--c-tarnished-gold);
  box-shadow: var(--shadow-gold-deep), var(--shadow-paper-edge);
}
.agent-card:focus-visible {
  outline: 2px solid var(--c-tarnished-gold);
  outline-offset: 3px;
}

.agent-info {
  padding: var(--sp-3) var(--sp-4);
  display: flex; flex-direction: column;
  gap: 3px;
  border-top: 1px solid var(--c-border-archive);
  background: var(--c-ivory-aged);
}
.agent-name {
  font-family: var(--font-serif-alt);
  font-size: 16px;
  font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.02em;
  line-height: 1.3;
}
.agent-origin {
  font-family: var(--font-serif);
  font-size: 12px;
  color: var(--c-sepia);
  font-style: italic;
  letter-spacing: 0.02em;
  margin-top: 2px;
}
.agent-occurrences {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--c-tarnished-gold);
  letter-spacing: 0.1em;
  margin-top: 4px;
  padding-top: 4px;
  border-top: 1px dashed rgba(168, 137, 78, 0.35);
}
.agent-occurrences--none {
  color: var(--c-sepia-light);
  opacity: 0.7;
}
</style>
