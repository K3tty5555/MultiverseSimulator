<template>
  <div class="agents-view">
    <header class="nav lp-archive-topbar">
      <div class="nav-left">
        <router-link to="/" class="lp-back-btn" aria-label="返档案馆" title="返档案馆（首页）">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M10 3 L5 8 L10 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>档案馆</span>
        </router-link>
        <div class="nav-title-group">
          <h1 class="nav-title">角色长廊</h1>
          <span class="nav-sub">翻阅每一位登场之人 · 点画像进入其时间轴</span>
        </div>
      </div>
    </header>

    <div class="content">
      <div v-if="loading && universes.length === 0" class="empty-state">翻开档案...</div>

      <div v-else-if="error" class="error-state" role="alert">
        <p>卷宗翻阅失败</p>
        <button class="lp-btn-ghost-archive" @click="load">重试</button>
      </div>

      <div v-else-if="dedupedAgents.length === 0" class="empty-state">
        <p class="empty-text">
          长廊尚空，无人登场。<br />
          去<router-link to="/universe" class="empty-link">历史卷宗</router-link>或
          <router-link to="/" class="empty-link">档案馆</router-link>开启一段卷宗。
        </p>
      </div>

      <template v-else>
        <div class="filter-bar">
          <span class="count-label">登录在册 · {{ dedupedAgents.length }} 位</span>
          <input
            v-model="searchQuery"
            type="text"
            class="search-input"
            placeholder="搜索角色 / 卷宗..."
            aria-label="搜索角色"
          />
        </div>

        <div v-if="filteredAgents.length > 0" class="agents-grid">
          <AgentCard
            v-for="c in filteredAgents"
            :key="`${c.name}:${c.universe_type}`"
            :agent="c"
            :portrait="portraitMap[c.name] || null"
            @select="openTimeline"
          />
        </div>

        <div v-else class="empty-state">
          <p class="empty-text">没有匹配的登录之人</p>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApiRequest } from '../composables/useApiRequest.js'
import { listUniversesWithAgents } from '../api/universe.js'
import AgentCard from '../components/agents/AgentCard.vue'

const router = useRouter()
const universes = ref([])
const searchQuery = ref('')

const listRequest = useApiRequest(
  () => listUniversesWithAgents().then(r => r.universes || []),
  { showErrorToast: true }
)
const loading = listRequest.loading
const error = listRequest.error

// 已有真立绘的角色映射（未来扩展可对接后端动态生成）
const portraitMap = {
  '诸葛亮': '/art/portrait-zhugeliang.png',
  '曹操':   '/art/portrait-caocao.png',
  '关羽':   '/art/portrait-guanyu.png',
  '张飞':   '/art/portrait-zhangfei.png',
  '周瑜':   '/art/portrait-zhouyu.png',
  '赵云':   '/art/portrait-zhaoyun.png',
  '黄盖':   '/art/portrait-huanggai.png',
  '金旋':   '/art/portrait-jinxuan.png',
  '刘度':   '/art/portrait-liudu.png',
  '鲁肃':   '/art/portrait-lusu.png',
  '孙权':   '/art/portrait-sunquan.png',
}

const dedupedAgents = computed(() => {
  const map = new Map()
  function push(name, u) {
    if (!name) return
    const key = `${name}:${u.universe_type}`
    if (!map.has(key)) {
      map.set(key, { name, universe_type: u.universe_type, world_label: u.world_label || '', occurrences: [] })
    }
    const entry = map.get(key)
    entry.occurrences.push({ universe_id: u.universe_id, universe_title: u.title })
    if (!entry.world_label && u.world_label) entry.world_label = u.world_label
  }
  for (const u of universes.value) {
    if (u.protagonist_name) push(u.protagonist_name, u)
    for (const a of u.agents) push(a.name, u)
  }
  return [...map.values()].sort((a, b) => a.name.localeCompare(b.name, 'zh'))
})

const filteredAgents = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return dedupedAgents.value
  return dedupedAgents.value.filter(c =>
    (c.name || '').toLowerCase().includes(q) ||
    (c.world_label || '').toLowerCase().includes(q) ||
    c.occurrences.some(o => (o.universe_title || '').toLowerCase().includes(q))
  )
})

function openTimeline(c) {
  router.push({
    path: `/agents/${encodeURIComponent(c.name)}`,
    query: { type: c.universe_type },
  })
}
async function load() {
  try {
    const result = await listRequest.execute()
    universes.value = Array.isArray(result) ? result : []
  } catch { /* toast */ }
}
onMounted(load)
</script>

<style scoped>
.agents-view {
  min-height: 100vh;
  background: var(--c-parchment);
  position: relative;
  isolation: isolate;
}
/* 档案桌面底纹 */
.agents-view::before {
  content: '';
  position: absolute; inset: 0;
  background: var(--img-hero, var(--c-umber-deep)) center/cover no-repeat;
  opacity: 0.14;
  pointer-events: none;
  z-index: 0;
}

.nav-left { display: flex; align-items: center; gap: var(--sp-4); }
.nav-title-group { display: flex; flex-direction: column; gap: 2px; }
.nav-title {
  font-family: var(--font-serif-alt);
  font-size: 17px;
  font-weight: 500;
  color: var(--c-ivory-aged);
  letter-spacing: 0.04em;
  margin: 0;
  line-height: 1;
}
.nav-sub {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 11px;
  color: var(--c-sepia-light);
  letter-spacing: 0.03em;
}

.content {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--sp-8) var(--sp-8) 80px;
  position: relative;
  z-index: 1;
}

.filter-bar {
  display: flex; align-items: center; justify-content: space-between;
  gap: var(--sp-4);
  margin-bottom: var(--sp-6);
  padding-bottom: var(--sp-3);
  border-bottom: 1px solid rgba(168, 137, 78, 0.35);
}
.count-label {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--c-tarnished-gold);
  letter-spacing: 0.15em;
  text-transform: uppercase;
}
.search-input {
  width: 280px; max-width: 60%;
  padding: 8px 12px;
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
  font-family: var(--font-serif);
  font-size: 13px;
  color: var(--c-umber-deep);
  transition: all var(--duration-fast);
}
.search-input::placeholder { font-style: italic; color: var(--c-sepia); opacity: 0.7; }
.search-input:focus {
  border-color: var(--c-tarnished-gold);
  outline: none;
  box-shadow: 0 0 0 2px rgba(168, 137, 78, 0.2);
}

.empty-state {
  text-align: center;
  padding: var(--sp-12) var(--sp-6);
  font-family: var(--font-serif);
  font-style: italic;
  color: var(--c-sepia);
  font-size: 14px;
  line-height: 1.8;
}
.empty-text { line-height: 1.8; }
.empty-link { color: var(--c-oxblood); text-decoration: underline; text-underline-offset: 3px; }
.empty-link:hover { color: var(--c-tarnished-gold); }

.error-state {
  text-align: center;
  padding: var(--sp-10) var(--sp-6);
  border: 1px solid var(--c-danger-border);
  border-radius: 2px;
  background: var(--c-danger-bg);
  color: var(--c-danger-text);
  font-family: var(--font-serif);
  display: flex; flex-direction: column; align-items: center; gap: var(--sp-3);
}

/* 角色档案卡网格 */
.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--sp-5);
}

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


@media (max-width: 640px) {
  .agents-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: var(--sp-3); }
  .search-input { width: 160px; max-width: 50%; }
}
</style>
