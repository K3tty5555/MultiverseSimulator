<template>
  <div class="settings-view">
    <header class="nav lp-archive-topbar">
      <div class="nav-left">
        <router-link to="/" class="lp-back-btn" aria-label="返档案馆" title="返档案馆">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M10 3 L5 8 L10 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>档案馆</span>
        </router-link>
        <div class="nav-title-group">
          <h1 class="nav-title">馆舍设置</h1>
          <span class="nav-sub">配置档案馆的 AI 模型接入</span>
        </div>
      </div>
      <button class="lp-btn-archive" :disabled="saving" @click="save">
        {{ saving ? '保存中...' : '保存设置' }}
      </button>
    </header>

    <div class="content">
      <section class="section">
        <h2 class="section-title">AI 模型配置</h2>
        <p class="section-desc">
          支持任何兼容 OpenAI 接口的服务，例如 OpenAI、火山引擎、DeepSeek、智谱 AI、本地 Ollama 等。
        </p>

        <div class="form-stack">
          <div class="field">
            <label class="field-label">API Key</label>
            <div class="key-row">
              <input
                v-model="form.llm_api_key"
                :type="showKey ? 'text' : 'password'"
                placeholder="sk-... 或其他格式"
                autocomplete="off"
              />
              <button class="btn-icon-archive" @click="showKey = !showKey" type="button">
                {{ showKey ? '隐藏' : '显示' }}
              </button>
            </div>
          </div>

          <div class="field">
            <label class="field-label">Base URL</label>
            <input
              v-model="form.llm_base_url"
              type="text"
              placeholder="例：https://ark.cn-beijing.volces.com/api/coding/v3"
            />
            <span class="field-hint">留空则使用 OpenAI 官方地址</span>
          </div>

          <div class="field">
            <label class="field-label">模型名称</label>
            <input
              v-model="form.llm_model_name"
              type="text"
              placeholder="例：gpt-4o、kimi-k2.5、deepseek-chat"
            />
          </div>
        </div>

        <div class="test-row">
          <button class="lp-btn-ghost-archive" :disabled="testing" @click="test">
            {{ testing ? '测试中...' : '测试连接' }}
          </button>
          <div v-if="testResult" :class="['test-result', testResult.ok ? 'ok' : 'err']">
            {{ testResult.ok ? `连接成功，模型回复：${testResult.reply}` : `连接失败：${testResult.error}` }}
          </div>
        </div>
      </section>

      <section class="section">
        <h2 class="section-title">常用服务 · 一键填入</h2>
        <div class="preset-grid">
          <button
            v-for="p in presets"
            :key="p.name"
            class="preset-card"
            @click="applyPreset(p)"
          >
            <span class="preset-name">{{ p.name }}</span>
            <span class="preset-url">{{ p.base_url || 'api.openai.com' }}</span>
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getSettings, updateSettings, testConnection } from '../api/settings.js'
import { useToast } from '../composables/useToast.js'

const { success, error: toastError } = useToast()
const saving = ref(false)
const testing = ref(false)
const showKey = ref(false)
const testResult = ref(null)

const form = ref({
  llm_api_key: '',
  llm_base_url: '',
  llm_model_name: '',
})

const presets = [
  { name: 'OpenAI', base_url: '', model: 'gpt-4o-mini' },
  { name: '火山引擎', base_url: 'https://ark.cn-beijing.volces.com/api/coding/v3', model: 'doubao-pro-32k' },
  { name: 'DeepSeek', base_url: 'https://api.deepseek.com/v1', model: 'deepseek-chat' },
  { name: '智谱 AI', base_url: 'https://open.bigmodel.cn/api/paas/v4', model: 'glm-4-flash' },
  { name: 'Moonshot', base_url: 'https://api.moonshot.cn/v1', model: 'moonshot-v1-8k' },
  { name: 'Ollama（本地）', base_url: 'http://localhost:11434/v1', model: 'llama3' },
]

onMounted(async () => {
  try {
    const res = await getSettings()
    form.value.llm_api_key = res.llm_api_key || ''
    form.value.llm_base_url = res.llm_base_url || ''
    form.value.llm_model_name = res.llm_model_name || ''
  } catch {}
})

async function save() {
  saving.value = true
  testResult.value = null
  try {
    await updateSettings(form.value)
    success('设置已保存')
  } catch {
    toastError('保存失败，请重试')
  } finally { saving.value = false }
}

async function test() {
  testing.value = true
  testResult.value = null
  try {
    const res = await testConnection(form.value)
    testResult.value = { ok: true, reply: res.reply }
  } catch (e) {
    testResult.value = { ok: false, error: e.response?.data?.error || e.message || '未知错误' }
  } finally { testing.value = false }
}

function applyPreset(p) {
  form.value.llm_base_url = p.base_url
  form.value.llm_model_name = p.model
}
</script>

<style scoped>
.settings-view {
  min-height: 100vh;
  background: var(--c-parchment);
  position: relative;
  isolation: isolate;
}
.settings-view::before {
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
  max-width: 680px;
  margin: 0 auto;
  padding: var(--sp-10) var(--sp-8) 80px;
  position: relative; z-index: 1;
}

.section { margin-bottom: var(--sp-12); }
.section-title {
  font-family: var(--font-serif-alt);
  font-size: 22px;
  font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.03em;
  margin-bottom: var(--sp-3);
  padding-bottom: var(--sp-3);
  border-bottom: 1px solid rgba(168, 137, 78, 0.4);
}
.section-desc {
  font-family: var(--font-serif);
  font-size: 13px;
  color: var(--c-sepia);
  line-height: 1.7;
  margin-bottom: var(--sp-6);
}

.form-stack { display: flex; flex-direction: column; gap: var(--sp-5); margin-bottom: var(--sp-6); }
.field { display: flex; flex-direction: column; gap: var(--sp-2); }
.field-label {
  font-family: var(--font-serif);
  font-size: 13px;
  font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.04em;
}
.field-hint {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 12px;
  color: var(--c-sepia);
}
input[type="text"], input[type="password"], input[type="number"] {
  padding: 9px 12px;
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
  font-family: var(--font-serif);
  font-size: 13px;
  color: var(--c-umber-deep);
  transition: all var(--duration-fast);
}
input::placeholder { font-style: italic; color: var(--c-sepia); opacity: 0.7; }
input:focus {
  outline: none;
  border-color: var(--c-tarnished-gold);
  box-shadow: 0 0 0 2px rgba(168, 137, 78, 0.25);
}

.key-row { display: flex; gap: var(--sp-2); }
.key-row input { flex: 1; }

.btn-icon-archive {
  padding: 0 var(--sp-4);
  border: 1px solid var(--c-border-sepia);
  border-radius: 2px;
  background: transparent;
  color: var(--c-umber);
  font-family: var(--font-serif);
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
  transition: all var(--duration-fast);
}
.btn-icon-archive:hover { border-color: var(--c-tarnished-gold); color: var(--c-umber-deep); background: rgba(168, 137, 78, 0.08); }

.test-row { display: flex; align-items: center; gap: var(--sp-4); flex-wrap: wrap; }
.test-result { font-family: var(--font-serif); font-size: 13px; line-height: 1.6; font-style: italic; }
.test-result.ok { color: var(--c-success-text); }
.test-result.err { color: var(--c-danger-strong); }

.preset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--sp-3);
}
.preset-card {
  display: flex; flex-direction: column;
  gap: 4px;
  padding: var(--sp-4) var(--sp-5);
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
  text-align: left;
  cursor: pointer;
  box-shadow: var(--shadow-paper-edge);
  transition: all var(--duration-fast);
}
.preset-card:hover {
  border-color: var(--c-tarnished-gold);
  background: rgba(168, 137, 78, 0.08);
  box-shadow: var(--shadow-gold-deep);
}
.preset-name {
  font-family: var(--font-serif-alt);
  font-size: 14px;
  font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.02em;
}
.preset-url {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--c-sepia);
  letter-spacing: 0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
