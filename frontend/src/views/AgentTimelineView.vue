<template>
  <div class="timeline-view lp-archive-bg-canvas">
    <header class="nav lp-archive-topbar">
      <div class="nav-left">
        <router-link to="/agents" class="lp-back-btn" aria-label="返回角色长廊" title="返回角色长廊">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M10 3 L5 8 L10 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>角色长廊</span>
        </router-link>
        <div class="nav-title-group">
          <h1 class="nav-title">{{ decodedName }}</h1>
          <span class="nav-sub">{{ subtitleText }}</span>
        </div>
      </div>
    </header>

    <div class="content">
      <div v-if="initialLoading !== false" class="empty-state">翻开卷宗...</div>

      <EmptyTimelinePanel
        v-else-if="canonicalEvents.length === 0 && !isGenerating"
        :name="decodedName"
        :type-text="typeText"
        :generating="isGenerating"
        :elapsed="generateElapsed"
        :reason="emptyReason"
        @generate="handleGenerate"
      />

      <div v-else-if="isGenerating && canonicalEvents.length === 0" class="empty-state">
        <p>AI 正在梳理 {{ decodedName }} 的生平年表… {{ generateElapsed }}s</p>
      </div>

      <!-- 主视图：年表 + 分叉 -->
      <div v-else class="canonical-timeline">
        <div v-if="isGenerating" class="generating-bar">
          AI 正在重新梳理 {{ decodedName }} 的生平年表… {{ generateElapsed }}s
        </div>

        <ol class="event-list">
          <CanonicalEventCard
            v-for="(ev, idx) in canonicalEvents"
            :key="ev.id"
            :event="ev"
            :universes="universesByEvent[ev.id] || []"
            :is-last="idx === canonicalEvents.length - 1"
            @edit="openEdit"
            @fork="forkFromEvent"
            @enter-universe="enterUniverse"
          />
        </ol>

        <TimelineUnlinkedList
          v-if="unlinkedUniverses.length > 0"
          :universes="unlinkedUniverses"
          @enter="enterUniverse"
        />

        <div class="regenerate-row">
          <button class="lp-btn-ghost-archive" :disabled="isGenerating" @click="confirmRegenerate = true">
            重新梳理年表
          </button>
          <span class="regenerate-hint">（会删除未被你修订过的节点，重新调 AI 梳理）</span>
        </div>
      </div>
    </div>

    <CanonicalEventEditModal
      v-if="editingEvent"
      :show="editingEvent !== null"
      :event="editingEvent"
      @close="editingEvent = null"
      @saved="onEventSaved"
      @deleted="onEventDeleted"
    />

    <NewUniverseModal
      :show="newUniverseBasedOn !== null"
      :based-on-event="newUniverseBasedOn"
      :protagonist-name="decodedName"
      :fixed-type="universeType"
      :fixed-world-label="currentWorldLabel"
      @close="newUniverseBasedOn = null"
      @created="onUniverseCreated"
    />

    <ConfirmModal
      :show="confirmRegenerate"
      message="确认重新梳理生平年表？将删除所有未被你修订过的节点，重新调 AI 梳理。"
      confirm-label="重新梳理"
      :danger="true"
      @confirm="handleRegenerate"
      @cancel="confirmRegenerate = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '../composables/useToast.js'
import {
  listCanonicalEvents, generateCanonicalEvents, bulkDeleteCanonicalEvents,
  listUniversesWithAgents,
} from '../api/universe.js'
import CanonicalEventEditModal from '../components/CanonicalEventEditModal.vue'
import NewUniverseModal from '../components/NewUniverseModal.vue'
import ConfirmModal from '../components/ConfirmModal.vue'
import CanonicalEventCard from '../components/agents/CanonicalEventCard.vue'
import EmptyTimelinePanel from '../components/agents/EmptyTimelinePanel.vue'
import TimelineUnlinkedList from '../components/agents/TimelineUnlinkedList.vue'

const props = defineProps({ name: { type: String, required: true } })
const route = useRoute()
const router = useRouter()
const { success, error: toastError } = useToast()

const decodedName = computed(() => {
  try { return decodeURIComponent(props.name) } catch { return props.name }
})
const universeType = computed(() => route.query.type || 'historical')
const worldLabelParam = computed(() => route.query.world_label || '')
const typeText = computed(() =>
  universeType.value === 'historical' ? '史料' : '原著'
)

const canonicalEvents = ref([])
const universes = ref([])
const initialLoading = ref(null)
const emptyReason = ref('')

const involvedUniverses = computed(() =>
  universes.value.filter(u =>
    u.universe_type === universeType.value &&
    (u.protagonist_name === decodedName.value ||
      (u.agents || []).some(a => a.name === decodedName.value))
  )
)
const universesByEvent = computed(() => {
  const map = {}
  for (const u of involvedUniverses.value) {
    const eid = u.canonical_event_id
    if (!eid) continue
    if (!map[eid]) map[eid] = []
    map[eid].push(u)
  }
  return map
})
const unlinkedUniverses = computed(() =>
  involvedUniverses.value.filter(u => !u.canonical_event_id)
)
const currentWorldLabel = computed(() => {
  for (const u of involvedUniverses.value) {
    if (u.world_label) return u.world_label
  }
  return ''
})
const subtitleText = computed(() => {
  const base = universeType.value === 'historical' ? '史' : '幻'
  const world = currentWorldLabel.value
  const prefix = world ? `${base}·${world}` : base
  const n = involvedUniverses.value.length
  return `${prefix} · 登场于 ${n} 卷`
})

const isGenerating = ref(false)
const generateElapsed = ref(0)
let genTimerId = null
let genAbortController = null

function startGenTimer() {
  generateElapsed.value = 0
  genTimerId = setInterval(() => { generateElapsed.value += 1 }, 1000)
}
function stopGenTimer() {
  if (genTimerId !== null) { clearInterval(genTimerId); genTimerId = null }
}

async function handleGenerate() {
  if (isGenerating.value) return
  emptyReason.value = ''
  isGenerating.value = true
  genAbortController = new AbortController()
  startGenTimer()
  try {
    const res = await generateCanonicalEvents({
      name: decodedName.value,
      universe_type: universeType.value,
      world_label: currentWorldLabel.value || '',
    }, genAbortController.signal)
    if (res.events && res.events.length > 0) {
      canonicalEvents.value = res.events
      success('已梳理生平年表')
    } else {
      emptyReason.value = res.reason || 'AI 未能梳理可考证的节点，稍后可重试或手动编辑。'
    }
  } catch (e) {
    if (e.name === 'AbortError' || e.code === 'ERR_CANCELED') return
    toastError(e?.response?.data?.error || e?.message || '梳理失败，请重试')
  } finally {
    genAbortController = null
    stopGenTimer()
    isGenerating.value = false
  }
}

const confirmRegenerate = ref(false)
async function handleRegenerate() {
  confirmRegenerate.value = false
  if (isGenerating.value) return
  try {
    await bulkDeleteCanonicalEvents({
      name: decodedName.value,
      universe_type: universeType.value,
      world_label: currentWorldLabel.value || '',
    })
    canonicalEvents.value = canonicalEvents.value.filter(e => e.is_edited)
    await handleGenerate()
    await reloadCanonical()
  } catch (e) {
    toastError(e?.response?.data?.error || '重新梳理失败')
  }
}

const editingEvent = ref(null)
function openEdit(ev) { editingEvent.value = { ...ev } }
function onEventSaved(updated) {
  const i = canonicalEvents.value.findIndex(e => e.id === updated.id)
  if (i !== -1) canonicalEvents.value[i] = updated
  editingEvent.value = null
  success('已保存')
}
function onEventDeleted(id) {
  canonicalEvents.value = canonicalEvents.value.filter(e => e.id !== id)
  editingEvent.value = null
  success('已除名')
}

const newUniverseBasedOn = ref(null)
function forkFromEvent(ev) { newUniverseBasedOn.value = ev }
function onUniverseCreated(universe) {
  newUniverseBasedOn.value = null
  router.push({
    path: `/universe/${universe.id}`,
    query: { setup_protagonist: universe.protagonist_name ? undefined : '1' },
  })
}

function enterUniverse(universeId) { router.push(`/universe/${universeId}`) }

async function reloadCanonical() {
  try {
    const res = await listCanonicalEvents(
      decodedName.value, universeType.value, currentWorldLabel.value || ''
    )
    canonicalEvents.value = res.events || []
  } catch { /* 静默 */ }
}

let loadVersion = 0
async function load() {
  const version = ++loadVersion
  initialLoading.value = true
  try {
    const [canonRes, univRes] = await Promise.allSettled([
      listCanonicalEvents(decodedName.value, universeType.value, ''),
      listUniversesWithAgents(),
    ])
    if (version !== loadVersion) return
    if (univRes.status === 'fulfilled') {
      universes.value = univRes.value.universes || []
    }
    let worldLabelForQuery = worldLabelParam.value
    for (const u of universes.value) {
      if (u.universe_type === universeType.value && u.world_label &&
          (u.protagonist_name === decodedName.value ||
           (u.agents || []).some(a => a.name === decodedName.value))) {
        worldLabelForQuery = u.world_label
        break
      }
    }
    if (canonRes.status === 'fulfilled' && canonRes.value.events?.length > 0) {
      canonicalEvents.value = canonRes.value.events
    } else if (worldLabelForQuery) {
      try {
        const r2 = await listCanonicalEvents(decodedName.value, universeType.value, worldLabelForQuery)
        canonicalEvents.value = r2.events || []
      } catch { /* 静默 */ }
    }
  } finally {
    if (version === loadVersion) initialLoading.value = false
  }
}

onMounted(load)
onBeforeUnmount(() => {
  stopGenTimer()
  if (genAbortController) genAbortController.abort()
})
</script>

<style scoped>
.timeline-view {
  min-height: 100vh;
  background: var(--c-parchment);
  --bg-canvas-img: var(--img-hero);
}

.nav-left { display: flex; align-items: center; gap: var(--sp-4); min-width: 0; }
.nav-title-group { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.nav-title {
  font-family: var(--font-serif-alt);
  font-size: 18px; font-weight: 500;
  color: var(--c-ivory-aged);
  letter-spacing: 0.04em;
  margin: 0; line-height: 1;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.nav-sub {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 11px;
  color: var(--c-sepia-light);
  letter-spacing: 0.03em;
}

.content {
  max-width: 860px;
  margin: 0 auto;
  padding: var(--sp-8) var(--sp-8) 80px;
  position: relative; z-index: 1;
}

.empty-state {
  text-align: center;
  padding: var(--sp-10) var(--sp-6);
  font-family: var(--font-serif);
  font-style: italic;
  color: var(--c-sepia);
  font-size: 14px;
}

.canonical-timeline { display: flex; flex-direction: column; gap: var(--sp-5); }
.event-list {
  list-style: none; margin: 0; padding: 0;
  display: flex; flex-direction: column;
  gap: var(--sp-5);
}

.generating-bar {
  padding: var(--sp-3) var(--sp-4);
  background: var(--c-tarnished-gold-ring);
  border: 1px solid var(--c-tarnished-gold-border);
  border-radius: var(--r-sm);
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 13px;
  color: var(--c-sepia);
  text-align: center;
}

.regenerate-row {
  margin-top: var(--sp-6);
  padding-top: var(--sp-4);
  border-top: 1px dashed var(--c-border-sepia);
  display: flex; align-items: center; gap: var(--sp-3);
}
.regenerate-hint {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 11px;
  color: var(--c-sepia);
}
</style>
