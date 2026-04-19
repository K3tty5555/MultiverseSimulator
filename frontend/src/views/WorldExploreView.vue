<template>
  <div class="world-explore">
    <header class="nav lp-archive-topbar">
      <div class="nav-left">
        <router-link to="/" class="lp-back-btn" aria-label="返档案馆" title="返档案馆">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M10 3 L5 8 L10 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>档案馆</span>
        </router-link>
        <h1 class="page-title">历史卷宗</h1>
      </div>
      <div class="tab-switcher">
        <button :class="['tab-btn', { active: tab === 'discover' }]" @click="tab = 'discover'">典藏</button>
        <button :class="['tab-btn', { active: tab === 'mine' }]" @click="tab = 'mine'">我的卷宗</button>
      </div>
    </header>

    <!-- 典藏 Tab -->
    <main v-show="tab === 'discover'" class="tab-content">
      <div v-if="worldsLoading" class="loading-area">
        <div class="loading-pulse" aria-hidden="true"></div>
        <span>翻开典藏...</span>
      </div>
      <div v-else class="discover-grid">
        <WorldCard
          v-for="w in worlds"
          :key="w.id"
          :title="w.name"
          :description="w.description"
          :era-tag="w.era"
          :footer-left="`${w.checkpoint_count} 个关键节点`"
          footer-right="翻开此卷 →"
          @click="goToWorld(w.id)"
        />

        <WorldCard
          title="开启新卷宗"
          description="输入任意历史时期或虚构场景题材，AI 自动生成卷首与角色。"
          footer-right="开卷 →"
          variant="create"
          @click="showNewUniverseModal = true"
        >
          <template #icon>
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <rect x="3" y="3" width="26" height="26" rx="2" stroke="currentColor" stroke-width="1.4" stroke-dasharray="4 3"/>
              <path d="M16 10v12M10 16h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </template>
        </WorldCard>
      </div>
    </main>

    <NewUniverseModal
      :show="showNewUniverseModal"
      @close="showNewUniverseModal = false"
      @created="onUniverseCreated"
    />

    <!-- 我的卷宗 Tab -->
    <main v-show="tab === 'mine'" class="tab-content">
      <div v-if="mineLoading" class="loading-area">
        <div class="loading-pulse" aria-hidden="true"></div>
        <span>翻开卷宗...</span>
      </div>

      <section v-else-if="universes.length === 0" class="empty-section">
        <div class="empty-seal" aria-hidden="true">空</div>
        <h2 class="empty-title">尚无自建卷宗</h2>
        <p class="empty-desc">前往「典藏」选节点开卷，或开启一部新的卷宗。</p>
        <button class="lp-btn-archive" @click="tab = 'discover'">去典藏 →</button>
      </section>

      <div v-else class="mine-section">
        <div class="mine-toolbar">
          <span class="section-seal" aria-hidden="true">我</span>
          <span class="section-label">我的卷宗</span>
          <span class="mine-count">{{ universes.length }}</span>
          <button class="lp-btn-ghost-archive mine-create-btn" @click="showNewUniverseModal = true">+ 开启新卷宗</button>
        </div>

        <div class="universe-grid">
          <UniverseCard
            v-for="u in universes"
            :key="u.id"
            :universe="u"
            :confirming="confirmingArchiveId === u.id"
            @open="openUniverse"
            @request-archive="confirmingArchiveId = $event"
            @archive="confirmArchive"
            @cancel-archive="confirmingArchiveId = null"
          />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listWorlds, listUniverses, archiveUniverse } from '../api/universe.js'
import NewUniverseModal from '../components/NewUniverseModal.vue'
import WorldCard from '../components/world/WorldCard.vue'
import UniverseCard from '../components/world/UniverseCard.vue'

const router = useRouter()
const showNewUniverseModal = ref(false)

function onUniverseCreated(universe) {
  showNewUniverseModal.value = false
  router.push({ path: `/universe/${universe.id}`, query: { setup_protagonist: '1' } })
}

const tab = ref('discover')

const worlds = ref([])
const worldsLoading = ref(true)

async function loadWorlds() {
  worldsLoading.value = true
  try {
    const res = await listWorlds()
    worlds.value = res.worlds || []
  } catch { worlds.value = [] }
  finally { worldsLoading.value = false }
}

function goToWorld(id) { router.push(`/universe/worlds/${id}`) }

const universes = ref([])
const mineLoading = ref(true)
const confirmingArchiveId = ref(null)

async function loadMine() {
  mineLoading.value = true
  try {
    const res = await listUniverses()
    universes.value = (res.universes || []).filter(u => !u.is_personal_main)
  } catch { universes.value = [] }
  finally { mineLoading.value = false }
}

async function confirmArchive(id) {
  confirmingArchiveId.value = null
  try {
    await archiveUniverse(id)
    universes.value = universes.value.filter(u => u.id !== id)
  } catch {
    /* silent */
  }
}

function openUniverse(id) { router.push(`/universe/${id}`) }

onMounted(() => {
  loadWorlds()
  loadMine()
})
</script>

<style scoped>
.world-explore {
  height: 100vh;
  display: flex; flex-direction: column;
  background: var(--c-parchment);
  overflow: hidden;
  position: relative;
  isolation: isolate;
}
.world-explore::before {
  content: '';
  position: absolute; inset: 0;
  background: var(--img-hero, var(--c-umber-deep)) center/cover no-repeat;
  opacity: 0.08;
  pointer-events: none;
  z-index: 0;
}

.nav {
  justify-content: space-between;
  flex-shrink: 0;
  gap: var(--sp-4);
  position: relative; z-index: 10;
}
.nav-left { display: flex; align-items: center; gap: var(--sp-4); min-width: 0; flex: 1; }
.page-title {
  font-family: var(--font-serif-alt);
  font-size: 17px; font-weight: 500;
  color: var(--c-ivory-aged);
  letter-spacing: 0.04em;
  margin: 0;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

.tab-switcher {
  display: flex;
  background: rgba(20, 15, 10, 0.3);
  border: 1px solid rgba(168, 137, 78, 0.35);
  border-radius: 2px;
  padding: 2px;
  flex-shrink: 0;
}
.tab-btn {
  padding: 5px 14px; border: none; background: transparent;
  font-family: var(--font-serif);
  font-size: 12px;
  color: var(--c-sepia-light);
  letter-spacing: 0.04em;
  cursor: pointer;
  transition: all var(--duration-fast);
  border-radius: 1px;
}
.tab-btn:hover { color: var(--c-ivory-aged); }
.tab-btn.active {
  background: var(--c-tarnished-gold);
  color: var(--c-umber-deep);
  font-weight: 500;
}

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--sp-6) var(--sp-8) var(--sp-10);
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
  position: relative; z-index: 1;
}

.loading-area {
  display: flex; align-items: center; justify-content: center;
  gap: var(--sp-3); min-height: 200px;
  font-family: var(--font-serif);
  color: var(--c-sepia);
  font-size: 14px;
}
.loading-pulse {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--c-tarnished-gold);
  animation: pulse-archive 1.4s infinite;
}
@keyframes pulse-archive { 0%,100%{opacity:1; transform:scale(1)} 50%{opacity:.3; transform:scale(0.8)} }

.discover-grid { display: flex; flex-direction: column; gap: var(--sp-4); }

/* Mine */
.empty-section {
  display: flex; flex-direction: column; align-items: center; gap: var(--sp-4);
  padding: 60px var(--sp-8);
  text-align: center;
}
.empty-seal {
  display: inline-flex; align-items: center; justify-content: center;
  width: 48px; height: 48px;
  background: var(--c-oxblood);
  color: var(--c-ivory-aged);
  font-family: var(--font-serif-alt);
  font-size: 20px; font-weight: 600;
  border-radius: 2px;
  box-shadow: var(--shadow-oxblood-seal);
}
.empty-title {
  font-family: var(--font-serif-alt);
  font-size: 20px; font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.04em;
  margin: 0;
}
.empty-desc {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 13px;
  color: var(--c-sepia);
  line-height: 1.7; max-width: 360px;
  margin: 0 0 var(--sp-2);
}

.mine-section { display: flex; flex-direction: column; gap: var(--sp-5); }

.mine-toolbar {
  display: flex; align-items: center; gap: var(--sp-3);
  padding-bottom: var(--sp-3);
  border-bottom: 1px solid rgba(168, 137, 78, 0.4);
}
.section-seal {
  display: inline-flex; align-items: center; justify-content: center;
  width: 22px; height: 22px;
  background: var(--c-oxblood);
  color: var(--c-ivory-aged);
  font-family: var(--font-serif-alt);
  font-size: 12px; font-weight: 600;
  border-radius: 2px;
  box-shadow: var(--shadow-oxblood-seal);
}
.section-label {
  font-family: var(--font-serif-alt);
  font-size: 15px; font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.03em;
}
.mine-count {
  font-family: var(--font-mono);
  font-size: 10px; font-weight: 600;
  color: var(--c-ivory-aged);
  background: var(--c-umber);
  padding: 2px 7px;
  border-radius: 2px;
  letter-spacing: 0.08em;
}
.mine-create-btn {
  margin-left: auto;
  padding: 5px 14px !important;
  font-size: 12px !important;
}

.universe-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--sp-4);
}
/* universe-card 样式已迁移至 UniverseCard 子组件 */
</style>
