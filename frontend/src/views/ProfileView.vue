<template>
  <div class="profile-view">
    <header class="nav lp-archive-topbar">
      <div class="nav-left">
        <router-link to="/" class="lp-back-btn" aria-label="返档案馆" title="返档案馆">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M10 3 L5 8 L10 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>档案馆</span>
        </router-link>
        <div class="nav-title-group">
          <h1 class="nav-title">研究员登记簿</h1>
          <span class="nav-sub">档案越完整，推演越贴合你的真实处境</span>
        </div>
      </div>
      <div class="nav-actions">
        <button class="lp-btn-ghost-archive version-btn" @click="openVersionHistory">历史版本</button>
        <button class="lp-btn-archive" :disabled="saving" @click="saveProfile">
          {{ saving ? '落笔中...' : '保存登记' }}
        </button>
      </div>
    </header>

    <div class="content">
      <ProfileImpactHint />

      <!-- 基本信息 -->
      <section class="section">
        <h2 class="section-title">基本信息</h2>
        <div class="form-grid">
          <div class="field">
            <label class="field-label" for="profile-name">姓名</label>
            <input id="profile-name" v-model="form.name" type="text" placeholder="你的名字" />
          </div>
          <div class="field">
            <label class="field-label" for="profile-age">年龄</label>
            <input id="profile-age" v-model="form.age" type="number" min="1" max="120" placeholder="岁" />
          </div>
          <div class="field">
            <label class="field-label" for="profile-career">职业 / 行业</label>
            <input id="profile-career" v-model="form.career" type="text" placeholder="例：软件工程师 / 互联网" />
          </div>
          <div class="field">
            <label class="field-label" for="profile-location">所在城市</label>
            <input id="profile-location" v-model="form.location" type="text" placeholder="例：北京" />
          </div>
          <div class="field field-full">
            <label class="field-label" for="profile-family">家庭状况</label>
            <textarea id="profile-family" v-model="form.family" rows="3" placeholder="例：已婚，有一个孩子，父母在老家..." />
          </div>
        </div>
      </section>

      <!-- 价值观权重 -->
      <section class="section">
        <h2 class="section-title">价值观权衡</h2>
        <p class="section-desc">拖动标尺，设定各维度对你此刻的重要程度（1-10）</p>
        <div class="values-stack">
          <div v-for="(val, key) in form.values" :key="key" class="value-row">
            <div class="value-meta">
              <span class="value-name">{{ valueLabels[key] }}</span>
              <span class="value-score">{{ val }}</span>
            </div>
            <input v-model="form.values[key]" type="range" min="1" max="10" class="value-slider" />
          </div>
        </div>
      </section>

      <ProfileDataSources
        :files="uploadedFiles"
        :importing="importing"
        :import-result="importResult"
        @import-claude="importClaude"
        @upload="uploadSelected"
        @remove="removeFile"
      />

      <ProfileSummary
        :summary="profile?.summary || ''"
        :updated-at="profile?.updated_at || ''"
        :synthesizing="synthesizing"
        @synthesize="doSynthesize"
      />

      <SandboxPrompt :show="showSandboxPrompt" @go="router.push('/')" />
    </div>
  </div>

  <ProfileVersionModal
    :show="showVersions"
    :versions="versions"
    @close="showVersions = false"
  />
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '../composables/useToast.js'
import {
  getProfile, saveProfile as apiSave, autoImportClaude,
  getImportTask as pollImportTask, uploadFiles, deleteFile, synthesizeProfile,
  getProfileVersions
} from '../api/profile.js'
import ProfileDataSources from '../components/profile/ProfileDataSources.vue'
import ProfileVersionModal from '../components/profile/ProfileVersionModal.vue'
import ProfileSummary from '../components/profile/ProfileSummary.vue'
import ProfileImpactHint from '../components/profile/ProfileImpactHint.vue'
import SandboxPrompt from '../components/profile/SandboxPrompt.vue'

const router = useRouter()
const { success, error: toastError } = useToast()
const profile = ref(null)
const showSandboxPrompt = ref(false)
const initiallyEmpty = ref(true)
const saving = ref(false)
const importing = ref(false)
const synthesizing = ref(false)
const importResult = ref('')
const uploadedFiles = ref([])
let isMounted = true
const showVersions = ref(false)
const versions = ref([])

onBeforeUnmount(() => { isMounted = false })

const valueLabels = { career:'事业发展', finance:'财务安全', relationships:'人际关系', wellbeing:'身心健康', freedom:'自由度' }

const form = reactive({
  name: '', age: '', career: '', location: '', family: '',
  values: { career: 5, finance: 5, relationships: 5, wellbeing: 5, freedom: 5 }
})

onMounted(async () => {
  try {
    const res = await getProfile()
    if (res.profile) {
      profile.value = res.profile
      const s = res.profile.structured || {}
      initiallyEmpty.value = !s.name && !s.career
      form.name = s.name || ''
      form.age = s.age || ''
      form.career = s.career || ''
      form.location = s.location || ''
      form.family = s.family || ''
      if (s.values) Object.assign(form.values, s.values)
      uploadedFiles.value = res.profile.files || []
    }
  } catch {}
})

async function saveProfile() {
  saving.value = true
  try {
    const res = await apiSave({
      name: form.name, age: form.age ? parseInt(form.age) : null,
      structured: { name: form.name, age: form.age, career: form.career, location: form.location, family: form.family, values: form.values }
    })
    profile.value = res.profile
    success('登记已归档')
    if (initiallyEmpty.value && (form.name || form.career)) {
      showSandboxPrompt.value = true
      initiallyEmpty.value = false
    }
  } catch {
    toastError('保存失败，请重试')
  } finally { saving.value = false }
}

async function importClaude() {
  importing.value = true; importResult.value = ''
  try {
    const res = await autoImportClaude()
    await pollTask(res.task_id, task => {
      if (task.status === 'completed') {
        importResult.value = `导入完成，找到 ${task.result?.sessions_found || 0} 个会话`
        uploadedFiles.value = task.result?.files || uploadedFiles.value
      }
    })
  } finally { importing.value = false }
}

async function pollTask(taskId, onComplete) {
  while (isMounted) {
    await new Promise(r => setTimeout(r, 2000))
    if (!isMounted) break
    try {
      const res = await pollImportTask(taskId)
      if (res.task.status === 'completed') { onComplete(res.task); break }
      if (res.task.status === 'failed') {
        toastError(res.task.error || '任务失败，请重试')
        break
      }
    } catch { break }
  }
}

async function uploadSelected(files) {
  const fd = new FormData()
  files.forEach(f => fd.append('files', f))
  try {
    const res = await uploadFiles(fd)
    uploadedFiles.value = res.files
    success(`已上传 ${files.length} 个文件`)
  } catch {
    toastError('上传失败，请检查文件格式和大小（最大 10MB）')
  }
}

async function removeFile(id) {
  await deleteFile(id)
  uploadedFiles.value = uploadedFiles.value.filter(f => f.id !== id)
}

async function doSynthesize() {
  synthesizing.value = true
  try {
    const res = await synthesizeProfile()
    await pollTask(res.task_id, task => {
      if (profile.value) profile.value.summary = task.result?.summary
      else profile.value = { summary: task.result?.summary }
    })
  } finally { synthesizing.value = false }
}

async function openVersionHistory() {
  showVersions.value = true
  try {
    const res = await getProfileVersions()
    versions.value = res.versions || []
  } catch { /* 静默 */ }
}

function formatDate(iso) { return new Date(iso).toLocaleString('zh-CN', { month:'short', day:'numeric', hour:'2-digit', minute:'2-digit' }) }
</script>

<style scoped>
.profile-view {
  min-height: 100vh;
  background: var(--c-parchment);
  position: relative;
  isolation: isolate;
}
.profile-view::before {
  content: '';
  position: absolute; inset: 0;
  background: var(--img-hero, var(--c-umber-deep)) center/cover no-repeat;
  opacity: 0.14;
  pointer-events: none;
  z-index: 0;
}

.nav {
  justify-content: space-between;
  gap: var(--sp-4);
}
.nav-left { display: flex; align-items: center; gap: var(--sp-4); min-width: 0; }
.nav-title-group { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.nav-title {
  font-family: var(--font-serif-alt);
  font-size: 17px; font-weight: 500;
  color: var(--c-ivory-aged);
  letter-spacing: 0.04em;
  margin: 0; line-height: 1;
}
.nav-sub {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 11px;
  color: var(--c-sepia-light);
  letter-spacing: 0.03em;
}
.nav-actions { display: flex; align-items: center; gap: var(--sp-3); flex-shrink: 0; }

.content {
  max-width: 760px;
  margin: 0 auto;
  padding: var(--sp-8) var(--sp-8) 80px;
  position: relative; z-index: 1;
}

.section { margin-bottom: var(--sp-12); }
.section-title {
  font-family: var(--font-serif-alt);
  font-size: 20px; font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.04em;
  margin-bottom: var(--sp-4);
  padding-bottom: var(--sp-3);
  border-bottom: 1px solid rgba(168, 137, 78, 0.4);
}
.section-desc {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 13px;
  color: var(--c-sepia);
  margin-bottom: var(--sp-5);
}

.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-4); }
.field { display: flex; flex-direction: column; gap: var(--sp-2); }
.field-full { grid-column: 1 / -1; }
.field-label {
  font-family: var(--font-serif);
  font-size: 13px; font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.04em;
}

input[type="text"], input[type="number"], textarea {
  padding: 9px 12px;
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
  font-family: var(--font-serif);
  font-size: 13px;
  color: var(--c-umber-deep);
  transition: all var(--duration-fast);
}
input::placeholder, textarea::placeholder { font-style: italic; color: var(--c-sepia); opacity: 0.7; }
input:focus, textarea:focus {
  outline: none;
  border-color: var(--c-tarnished-gold);
  box-shadow: 0 0 0 2px rgba(168, 137, 78, 0.25);
}
textarea { resize: vertical; line-height: 1.7; }

.values-stack { display: flex; flex-direction: column; gap: var(--sp-5); }
.value-row { display: flex; flex-direction: column; gap: var(--sp-2); }
.value-meta { display: flex; justify-content: space-between; align-items: center; }
.value-name { font-family: var(--font-serif); font-size: 14px; color: var(--c-umber); }
.value-score {
  font-family: var(--font-serif-alt);
  font-size: 17px;
  font-weight: 600;
  color: var(--c-oxblood);
  width: 26px;
  text-align: right;
}
.value-slider { width: 100%; accent-color: var(--c-oxblood); cursor: pointer; }

.version-btn { font-size: 12px !important; padding: 5px 12px !important; }
</style>
