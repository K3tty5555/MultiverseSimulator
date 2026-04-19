<template>
  <div class="entity-panel">
    <div class="panel-header">
      <span class="panel-title">世界状态</span>
      <span v-if="loading" class="panel-hint">更新中…</span>
      <span v-else-if="states.length" class="panel-hint">第 {{ latestTurn }} 回</span>
    </div>

    <!-- 空态 -->
    <div v-if="!loading && states.length === 0" class="empty-state">
      <p>推演开始后<br/>实体状态将在此显示</p>
    </div>

    <!-- 实体列表 -->
    <ul v-else class="entity-list">
      <li
        v-for="entity in states"
        :key="entity.entity_name"
        class="entity-item"
      >
        <div class="entity-row">
          <span class="entity-name">{{ entity.entity_name }}</span>
          <span class="entity-category">{{ categoryLabel(entity.category) }}</span>
        </div>
        <p class="entity-summary">{{ entity.summary }}</p>
        <!-- 立场条（仅非 unknown） -->
        <div v-if="entity.stance !== 'unknown'" class="stance-bar-wrap">
          <div
            class="stance-bar"
            :style="stanceBarStyle(entity.stance_score)"
            :aria-label="`对主角立场：${stanceText(entity.stance_score)}`"
          ></div>
          <span class="stance-label">{{ stanceText(entity.stance_score) }}</span>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getEntityStates } from '../api/universe.js'

const props = defineProps({
  universeId: { type: Number, required: true }
})

const states  = ref([])
const loading = ref(false)

const latestTurn = computed(() =>
  states.value.length ? Math.max(...states.value.map(s => s.updated_turn)) : 0
)

async function refresh() {
  if (!props.universeId) return
  loading.value = true
  try {
    const res = await getEntityStates(props.universeId)
    states.value = res.data?.states ?? []
  } catch {
    // 静默失败，不打断主流程
  } finally {
    loading.value = false
  }
}

onMounted(refresh)

// 暴露给父组件，node_done 后调用
defineExpose({ refresh })

// ── 辅助函数 ────────────────────────────────────────────────────
function categoryLabel(cat) {
  return { person: '人物', faction: '势力', location: '地点', situation: '局势' }[cat] ?? cat
}

function stanceText(score) {
  if (score >  0.6) return '强力支持'
  if (score >  0.3) return '倾向友善'
  if (score > -0.3) return '中立'
  if (score > -0.6) return '倾向敌对'
  return '强烈敌对'
}

function stanceBarStyle(score) {
  // score: -1 ~ +1，映射到左右两侧填充
  const pct  = Math.abs(score) * 100
  const warm = 'var(--c-terracotta)'
  const cool = 'var(--c-stone-gray)'
  if (score >= 0) {
    return {
      background: `linear-gradient(to right, var(--c-border-warm) 50%, ${warm} 50%)`,
      backgroundSize: `${50 + pct / 2}% 100%`,
    }
  } else {
    return {
      background: `linear-gradient(to left, var(--c-border-warm) 50%, ${cool} 50%)`,
      backgroundSize: `${50 + pct / 2}% 100%`,
    }
  }
}
</script>

<style scoped>
.entity-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--c-ivory);
  border-right: 1px solid var(--c-border-cream);
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-4) var(--sp-4) var(--sp-3);
  border-bottom: 1px solid var(--c-border-cream);
  flex-shrink: 0;
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-near-black);
  letter-spacing: 0.02em;
}

.panel-hint {
  font-size: 11px;
  color: var(--c-stone-gray);
  margin-left: auto;
}

/* 空态 */
.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--sp-6);
}
.empty-state p {
  font-size: 12px;
  color: var(--c-stone-gray);
  text-align: center;
  line-height: 1.7;
}

/* 实体列表 */
.entity-list {
  flex: 1;
  overflow-y: auto;
  list-style: none;
  margin: 0;
  padding: var(--sp-2) 0;
}

.entity-item {
  padding: var(--sp-3) var(--sp-4);
  border-bottom: 1px solid var(--c-border-cream);
}
.entity-item:last-child {
  border-bottom: none;
}

.entity-row {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
  margin-bottom: var(--sp-1);
}

.entity-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-near-black);
}

.entity-category {
  font-size: 10px;
  color: var(--c-stone-gray);
  background: var(--c-border-cream);
  padding: 1px 6px;
  border-radius: var(--r-xs);
}

.entity-summary {
  font-size: 12px;
  color: var(--c-charcoal);
  line-height: 1.55;
  margin: 0 0 var(--sp-2);
}

/* 立场条 */
.stance-bar-wrap {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.stance-bar {
  height: 4px;
  width: 80px;
  border-radius: var(--r-xs);
  background: var(--c-border-warm);
  flex-shrink: 0;
}

.stance-label {
  font-size: 10px;
  color: var(--c-stone-gray);
}
</style>
