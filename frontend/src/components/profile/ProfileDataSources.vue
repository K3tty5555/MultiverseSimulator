<template>
  <section class="section">
    <h2 class="section-title">档案素材来源</h2>

    <div class="source-card">
      <div class="source-info">
        <span class="source-name">从 Claude 对话历史导入</span>
        <span class="source-desc">自动读取 ~/.claude/ 目录中的对话记录和记忆文件</span>
      </div>
      <button class="lp-btn-ghost-archive" :disabled="importing" @click="$emit('import-claude')">
        {{ importing ? '读取中...' : '导入 Claude 历史' }}
      </button>
    </div>
    <div v-if="importResult" class="import-notice">{{ importResult }}</div>

    <div
      class="upload-zone"
      :class="{ dragging }"
      @dragover.prevent="onDragOver"
      @dragleave="onDragLeave"
      @drop.prevent="onDrop"
      @click="fileInput.click()"
    >
      <input
        ref="fileInput"
        type="file"
        multiple
        accept=".pdf,.txt,.md,.markdown"
        style="display:none"
        @change="onSelect"
      />
      <div class="upload-icon">↑</div>
      <p class="upload-title">上传档案附件</p>
      <p class="upload-hint">支持聊天记录导出、简历、日记（PDF、TXT、MD）</p>
    </div>

    <div v-if="files.length > 0" class="file-list">
      <div v-for="f in files" :key="f.id" class="file-item">
        <span class="file-icon" v-html="fileIcon"></span>
        <span class="file-name">{{ f.filename }}</span>
        <span class="file-source">{{ f.source === 'claude_auto' ? 'Claude' : '上传' }}</span>
        <button class="file-remove" @click.stop="$emit('remove', f.id)" aria-label="移除附件">×</button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  files: { type: Array, default: () => [] },
  importing: { type: Boolean, default: false },
  importResult: { type: String, default: '' },
})
const emit = defineEmits(['import-claude', 'upload', 'remove'])

const fileInput = ref(null)
const dragging = ref(false)

function onDragOver() { dragging.value = true }
function onDragLeave() { dragging.value = false }
function onDrop(e) { dragging.value = false; emit('upload', Array.from(e.dataTransfer.files)) }
function onSelect(e) { emit('upload', Array.from(e.target.files)) }

const fileIcon = `<svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M8 1H3a1 1 0 00-1 1v10a1 1 0 001 1h8a1 1 0 001-1V6M8 1L12 5M8 1v4h4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/><path d="M4.5 8h5M4.5 10h3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>`
</script>

<style scoped>
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

.source-card {
  display: flex; align-items: center; justify-content: space-between; gap: var(--sp-4);
  padding: var(--sp-4) var(--sp-5);
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
  margin-bottom: var(--sp-4);
  box-shadow: var(--shadow-paper-edge);
}
.source-info { display: flex; flex-direction: column; gap: 4px; }
.source-name {
  font-family: var(--font-serif-alt);
  font-size: 14px; font-weight: 500;
  color: var(--c-umber-deep);
}
.source-desc {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 12px;
  color: var(--c-sepia);
}
.import-notice {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 13px;
  color: var(--c-success-text);
  margin-bottom: var(--sp-4);
}

.upload-zone {
  border: 1.5px dashed var(--c-border-sepia);
  border-radius: 2px;
  padding: var(--sp-8) var(--sp-6);
  text-align: center;
  cursor: pointer;
  background: rgba(232, 223, 200, 0.3);
  transition: all var(--duration-fast);
  margin-bottom: var(--sp-4);
}
.upload-zone:hover, .upload-zone.dragging {
  border-color: var(--c-tarnished-gold);
  background: rgba(168, 137, 78, 0.08);
}
.upload-icon { font-family: var(--font-serif-alt); font-size: 28px; color: var(--c-tarnished-gold); margin-bottom: var(--sp-2); }
.upload-title { font-family: var(--font-serif-alt); font-size: 14px; font-weight: 500; color: var(--c-umber-deep); margin-bottom: 4px; }
.upload-hint { font-family: var(--font-serif); font-style: italic; font-size: 12px; color: var(--c-sepia); }

.file-list { display: flex; flex-direction: column; gap: var(--sp-2); }
.file-item {
  display: flex; align-items: center; gap: var(--sp-3);
  padding: 10px var(--sp-4);
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
}
.file-icon { width: 16px; height: 16px; display: flex; align-items: center; flex-shrink: 0; color: var(--c-sepia); }
.file-name {
  flex: 1;
  font-family: var(--font-serif);
  font-size: 13px;
  color: var(--c-umber-deep);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.file-source {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--c-sepia);
  background: rgba(168, 137, 78, 0.15);
  padding: 2px 8px;
  border-radius: 2px;
  letter-spacing: 0.08em;
}
.file-remove {
  border: 1px solid transparent;
  background: none;
  color: var(--c-sepia);
  font-size: 18px;
  cursor: pointer;
  padding: 0 6px;
  border-radius: 2px;
  transition: all var(--duration-fast);
}
.file-remove:hover { border-color: var(--c-oxblood); color: var(--c-oxblood); background: rgba(107, 46, 42, 0.08); }
</style>
