<template>
  <div class="world-detail">
    <header class="nav lp-archive-topbar">
      <div class="nav-left">
        <router-link to="/universe" class="lp-back-btn" aria-label="返历史卷宗" title="返历史卷宗">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M10 3 L5 8 L10 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>历史卷宗</span>
        </router-link>
        <div class="nav-title-group" v-if="world">
          <h1 class="nav-title">{{ world.name }}</h1>
          <span class="nav-sub">{{ world.era }}</span>
        </div>
      </div>
    </header>

    <div v-if="loading" class="loading-full">
      <div class="loading-pulse" aria-hidden="true"></div>
      <span>翻开卷宗...</span>
    </div>

    <div v-else-if="!world" class="error-area">
      <p>卷宗翻阅失败</p>
      <router-link to="/universe" class="lp-btn-ghost-archive">返档案馆</router-link>
    </div>

    <div v-else class="main-content">
      <section class="world-intro">
        <p class="world-desc-text">{{ world.description }}</p>
      </section>

      <div class="timeline-header">
        <span class="section-seal" aria-hidden="true">节</span>
        <span class="section-label">关键节点</span>
        <span class="cp-count">{{ world.checkpoints.length }}</span>
      </div>

      <div class="timeline">
        <CheckpointCard
          v-for="(cp, idx) in world.checkpoints"
          :key="cp.id"
          :checkpoint="cp"
          :is-last="idx === world.checkpoints.length - 1"
          @select="openDialog"
        />
      </div>
    </div>

    <PersonaDialog
      :show="dialog.open"
      :checkpoint="dialog.checkpoint"
      :persona="dialog.persona"
      :perspective="dialog.perspective"
      :creating="dialog.creating"
      :error="dialog.error"
      @close="closeDialog"
      @create="doCreate"
      @update:perspective="dialog.perspective = $event"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { getWorld, createUniverseFromCheckpoint } from '../api/universe.js'
import PersonaDialog from '../components/world/PersonaDialog.vue'
import CheckpointCard from '../components/world/CheckpointCard.vue'

const props = defineProps({ worldId: String })
const router = useRouter()

const world = ref(null)
const loading = ref(true)

onMounted(async () => {
  loading.value = true
  try {
    const res = await getWorld(props.worldId)
    world.value = res.world
  } catch {
    world.value = null
  } finally {
    loading.value = false
  }
})

const dialog = reactive({
  open: false, checkpoint: null, persona: null,
  perspective: 'god', creating: false, error: '',
})

function openDialog(cp, persona) {
  dialog.checkpoint = cp
  dialog.persona = persona
  dialog.perspective = 'god'
  dialog.creating = false
  dialog.error = ''
  dialog.open = true
}

function closeDialog() {
  if (!dialog.creating) dialog.open = false
}

function onKeydown(e) {
  if (e.key === 'Escape' && dialog.open) closeDialog()
}
onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))

async function doCreate() {
  if (dialog.creating) return
  dialog.error = ''
  dialog.creating = true
  try {
    const res = await createUniverseFromCheckpoint({
      checkpoint_id: dialog.checkpoint.id,
      persona_name: dialog.persona.name,
      perspective: dialog.perspective,
    })
    dialog.open = false
    const yearMatch = (dialog.checkpoint?.year_label || '').match(/(\d{3,4})/)
    const targetYear = yearMatch ? parseInt(yearMatch[1], 10) : null
    const query = targetYear && targetYear < new Date().getFullYear()
      ? { play_intro: '1', target_year: String(targetYear) }
      : {}
    router.push({ path: `/universe/${res.universe.id}`, query })
  } catch (e) {
    dialog.error = e.response?.data?.error || e.message || '开卷失败，请重试'
  } finally {
    dialog.creating = false
  }
}

</script>

<style scoped>
.world-detail {
  height: 100vh;
  display: flex; flex-direction: column;
  background: var(--c-parchment);
  overflow: hidden;
  position: relative;
  isolation: isolate;
}
.world-detail::before {
  content: '';
  position: absolute; inset: 0;
  background: var(--img-hero, var(--c-umber-deep)) center/cover no-repeat;
  opacity: 0.14;
  pointer-events: none;
  z-index: 0;
}

.nav {
  flex-shrink: 0;
  position: relative; z-index: 10;
}
.nav-left { display: flex; align-items: center; gap: var(--sp-4); min-width: 0; }
.nav-title-group { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.nav-title {
  font-family: var(--font-serif-alt);
  font-size: 17px; font-weight: 500;
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
}

.loading-full, .error-area {
  flex: 1;
  display: flex; align-items: center; justify-content: center;
  gap: var(--sp-3);
  font-family: var(--font-serif);
  color: var(--c-sepia);
  font-size: 14px;
  position: relative; z-index: 1;
}
.error-area { flex-direction: column; gap: var(--sp-4); }
.loading-pulse {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--c-tarnished-gold);
  animation: pulse-archive 1.4s infinite;
}
@keyframes pulse-archive { 0%,100%{opacity:1; transform:scale(1)} 50%{opacity:.3; transform:scale(0.8)} }

.main-content {
  flex: 1; overflow-y: auto;
  padding: var(--sp-6) var(--sp-8) var(--sp-10);
  max-width: 820px; width: 100%; margin: 0 auto; box-sizing: border-box;
  display: flex; flex-direction: column; gap: var(--sp-6);
  position: relative; z-index: 1;
}

.world-intro {
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-left: 3px solid var(--c-tarnished-gold);
  border-radius: 2px;
  padding: var(--sp-5) var(--sp-6);
  box-shadow: var(--shadow-paper-edge);
}
.world-desc-text {
  font-family: var(--font-serif);
  font-size: 14px;
  color: var(--c-archive-ink);
  line-height: 1.85;
  margin: 0;
}

.timeline-header {
  display: flex; align-items: center; gap: var(--sp-3);
  padding-bottom: var(--sp-3);
  border-bottom: 1px solid rgba(168, 137, 78, 0.4);
}
.section-seal {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px;
  background: var(--c-oxblood);
  color: var(--c-ivory-aged);
  font-family: var(--font-serif-alt);
  font-size: 12px; font-weight: 600;
  border-radius: 2px;
  box-shadow: var(--shadow-oxblood-seal);
}
.section-label {
  font-family: var(--font-serif-alt);
  font-size: 16px; font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.04em;
}
.cp-count {
  font-family: var(--font-mono);
  font-size: 10px; font-weight: 600;
  color: var(--c-ivory-aged);
  background: var(--c-umber);
  padding: 2px 7px;
  border-radius: 2px;
  letter-spacing: 0.08em;
}

.timeline { display: flex; flex-direction: column; }

/* PersonaDialog modal 样式已迁移到子组件 */
</style>
