<template>
  <div class="home">
    <ArchiveDeskBackground />

    <HomeNav :app-version="appVersion" :empty-state="profileComplete === false" />

    <SetupBanner v-if="llmConfigured === false" />

    <div v-if="loading" class="loading-full">
      <div class="loading-pulse" aria-hidden="true"></div>
      <span>正在打开档案室...</span>
    </div>

    <main v-else class="workspace" :class="{ 'workspace--empty': profileComplete === false }">
      <EmptyHero v-if="profileComplete === false" />
      <template v-else>
        <PrimaryArchiveCard
          :personal-initialized="personalInitialized"
          :personal-node-count="personalNodeCount"
          :last-node="lastNode"
          :last-node-summary="lastNodeSummary"
          :starting="starting"
          @start="startSandbox"
          @continue="continueSandbox"
          @new-chapter="newChapterDialogOpen = true"
        />
        <RecentEventsPanel
          :events="recentEvents"
          @enter-universe="enterUniverse"
          @open-universe-list="openNewUniverse"
        />
        <ParallelShelf
          :universes="parallelUniverses"
          @enter-universe="enterUniverse"
          @new-universe="openNewUniverse"
        />
      </template>
    </main>

    <NewChapterDialog v-model="newChapterDialogOpen" @confirm="onNewChapter" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
const appVersion = __APP_VERSION__
import { useRouter } from 'vue-router'
import { getProfile } from '../api/profile.js'
import { getSettings } from '../api/settings.js'
import { getPersonalUniverse, initPersonalUniverse, listUniversesWithAgents } from '../api/universe.js'
import { useToast } from '../composables/useToast.js'
import NewChapterDialog from '../components/NewChapterDialog.vue'
import ArchiveDeskBackground from '../components/home/ArchiveDeskBackground.vue'
import HomeNav from '../components/home/HomeNav.vue'
import SetupBanner from '../components/home/SetupBanner.vue'
import EmptyHero from '../components/home/EmptyHero.vue'
import PrimaryArchiveCard from '../components/home/PrimaryArchiveCard.vue'
import RecentEventsPanel from '../components/home/RecentEventsPanel.vue'
import ParallelShelf from '../components/home/ParallelShelf.vue'

const router = useRouter()
const { error: toastError } = useToast()

const loading = ref(true)
const llmConfigured = ref(null)
const profileComplete = ref(null)
const personalUniverseId = ref(null)
const personalInitialized = ref(null)
const personalNodeCount = ref(0)
const lastNode = ref(null)
const starting = ref(false)
const newChapterDialogOpen = ref(false)


const allUniverses = ref([])
const parallelUniverses = computed(() =>
  allUniverses.value.filter(u => !u.is_personal_main && u.status === 'active')
)

const lastNodeSummary = computed(() => {
  if (!lastNode.value) return ''
  const action = lastNode.value.protagonist_action
  if (action) return action.length > 60 ? action.slice(0, 60) + '…' : action
  const narr = lastNode.value.narrator_content?.replace(/[#*>`_~\[\]]/g, '') ?? ''
  return narr.length > 60 ? narr.slice(0, 60) + '…' : narr
})

const recentEvents = computed(() => {
  const evs = []
  if (personalInitialized.value && lastNode.value?.created_at) {
    evs.push({
      universeId: personalUniverseId.value,
      universeTitle: '本命档案',
      time: lastNode.value.created_at,
      text: lastNodeSummary.value || '推演了一个新节点',
    })
  }
  for (const u of parallelUniverses.value) {
    if (u.last_node_at) {
      evs.push({
        universeId: u.id,
        universeTitle: u.title || '未命名卷宗',
        time: u.last_node_at,
        text: `于${u.world_label || '此卷'}内新增批注`,
      })
    }
  }
  return evs.sort((a, b) => new Date(b.time) - new Date(a.time)).slice(0, 8)
})

onMounted(async () => {
  await Promise.allSettled([
    loadPersonalUniverse(),
    checkProfile(),
    checkSettings(),
    loadAllUniverses(),
  ])
  loading.value = false
})

async function checkSettings() {
  try { llmConfigured.value = (await getSettings()).configured }
  catch { llmConfigured.value = false }
}
async function checkProfile() {
  try {
    const res = await getProfile()
    const s = res.profile?.structured || {}
    profileComplete.value = !!(s.name || s.career)
  } catch { profileComplete.value = false }
}
async function loadPersonalUniverse() {
  try {
    const res = await getPersonalUniverse()
    personalUniverseId.value = res.universe?.id ?? null
    personalInitialized.value = res.initialized === true
    personalNodeCount.value = (res.nodes || []).filter(n => n.node_type !== 'root').length
    lastNode.value = res.last_node || null
  } catch { personalInitialized.value = false }
}
async function loadAllUniverses() {
  try { allUniverses.value = (await listUniversesWithAgents()).universes || [] }
  catch { allUniverses.value = [] }
}

async function startSandbox() {
  if (starting.value) return
  starting.value = true
  try {
    const res = await initPersonalUniverse({})
    const uid = res.universe?.id ?? personalUniverseId.value
    if (uid) router.push(`/universe/${uid}`)
    else toastError('初始化失败，请重试')
  } catch { toastError('初始化失败，请重试') }
  finally { starting.value = false }
}
function continueSandbox() { if (personalUniverseId.value) router.push(`/universe/${personalUniverseId.value}`) }
function onNewChapter(situationText) {
  if (!personalUniverseId.value) return
  router.push({ path: `/universe/${personalUniverseId.value}`, state: { situation: situationText } })
}
function enterUniverse(id) { router.push(`/universe/${id}`) }
function openNewUniverse() { router.push('/universe') }
</script>

<style scoped>
/* ══════════════════════════════════════════════════════════════
   Home orchestrator · 只管整体 layout（nav / grid / banner / loading）
   各 panel 内部样式在子组件 scoped style 里独立维护
   ══════════════════════════════════════════════════════════════ */

.home {
  height: 100vh;
  overflow: hidden;
  display: grid;
  grid-template-rows: 60px auto 1fr;
  background: var(--c-parchment);
  position: relative;
}

.loading-full {
  grid-row: 3;
  display: flex; align-items: center; justify-content: center;
  gap: var(--sp-3);
  color: var(--c-ivory-aged);
  font-family: var(--font-serif);
  font-size: 15px;
  letter-spacing: 0.05em;
  position: relative; z-index: 10;
}
.loading-pulse {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--c-tarnished-gold);
  animation: pulse-archive 1.4s infinite;
}
@keyframes pulse-archive { 0%,100%{opacity:1; transform:scale(1)} 50%{opacity:.3; transform:scale(0.8)} }

/* ── Workspace · 主工作区 Grid 分区 ── */
.workspace {
  grid-row: 3;
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr);
  /*
   * 行高策略（1100×760 Electron 窗口适配）：
   *   第一行（primary + events）：1fr 自然扩展，min 220px
   *   第二行（shelf）：书封 240px + header 44 + title/padding ≈ 350px
   *     min 320px 保证书封主体可见，max 36vh 限制大窗口占比
   */
  grid-template-rows: minmax(220px, 1fr) minmax(320px, 36vh);
  grid-template-areas:
    "primary events"
    "shelf   shelf";
  gap: var(--sp-8);
  padding: var(--sp-6) var(--sp-10) var(--sp-8);
  max-width: 1440px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
  min-height: 0;
  /* 兜底：极端小窗口允许整体滚动，正常使用 hidden 保持桌面感 */
  overflow: auto;
}

.workspace--empty {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 矮窗口（Electron 760px 高）：压缩 gap/padding，书架保留完整高度 */
@media (max-height: 820px) {
  .workspace {
    padding: var(--sp-3) var(--sp-8) var(--sp-4);
    gap: var(--sp-3);
    grid-template-rows: minmax(200px, 1fr) minmax(340px, 34vh);
  }
}

/* 窄屏（< 860px）：改单列布局 */
@media (max-width: 860px) {
  .workspace {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(220px, 1fr) minmax(140px, 20vh) minmax(280px, 32vh);
    grid-template-areas:
      "primary"
      "events"
      "shelf";
    padding: var(--sp-6);
    gap: var(--sp-5);
  }
}
</style>
