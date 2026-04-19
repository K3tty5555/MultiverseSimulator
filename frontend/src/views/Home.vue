<template>
  <div class="home">
    <ArchiveDeskBackground />

    <HomeNav :app-version="appVersion" />

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
  isolation: isolate;
}

.loading-full {
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
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
  /* primary 足够容纳 badge+title+excerpt+actions；shelf 容纳 160x240 书本 + title + hook 副文 */
  grid-template-rows: minmax(320px, 38vh) minmax(360px, 42vh);
  grid-template-areas:
    "primary events"
    "shelf   shelf";
  gap: var(--sp-8);
  padding: var(--sp-8) var(--sp-10);
  max-width: 1440px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
  min-height: 0;
  overflow: hidden;
  animation: workspace-fade-in var(--duration-slower) var(--ease-out);
}
@keyframes workspace-fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

.workspace--empty {
  grid-template-areas: "empty empty";
  grid-template-columns: 1fr;
  grid-template-rows: 1fr;
  align-items: center;
  justify-items: center;
}

@media (max-width: 1100px) {
  .workspace {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(260px, 36vh) minmax(160px, 22vh) minmax(320px, 36vh);
    grid-template-areas:
      "primary"
      "events"
      "shelf";
    padding: var(--sp-6);
    gap: var(--sp-5);
  }
}
</style>
