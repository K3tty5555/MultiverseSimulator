<template>
  <router-view />
  <!-- 全局 Toast 通知 -->
  <teleport to="body">
    <div class="toast-container" aria-live="polite" aria-atomic="true">
      <transition-group name="toast">
        <div
          v-for="t in toasts"
          :key="t.id"
          :class="['toast', `toast-${t.type}`]"
        >{{ t.message }}</div>
      </transition-group>
    </div>
  </teleport>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useToast } from './composables/useToast.js'
const { toasts } = useToast()

// ── 全局键盘快捷键 ────────────────────────────────────────────
function onGlobalKeydown(e) {
  // Cmd/Ctrl+Enter：聚焦在文本框时，点击最近的主操作按钮
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
    const active = document.activeElement
    if (active?.tagName === 'TEXTAREA' || active?.tagName === 'INPUT') {
      e.preventDefault()
      // 优先找最近 form 内的 submit 按钮，否则找页面上第一个可用的 .btn-primary
      const form = active.closest('form')
      const btn = form?.querySelector('button[type="submit"]:not(:disabled)')
        || form?.querySelector('.btn-primary:not(:disabled)')
        || active.closest('.step-body, .panel, .card')?.querySelector('.btn-primary:not(:disabled)')
      btn?.click()
    }
  }
}

onMounted(() => document.addEventListener('keydown', onGlobalKeydown))
onUnmounted(() => document.removeEventListener('keydown', onGlobalKeydown))
</script>

<style>
@import './styles/design.css';

/* Google Fonts 已移至 index.html <head>，此处无需重复 @import */

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  background: var(--c-parchment);
}

#app {
  font-family: var(--font-sans);
  font-size: 16px;
  line-height: 1.6;
  color: var(--c-near-black);
  background: var(--c-parchment);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--c-parchment); }
::-webkit-scrollbar-thumb { background: var(--c-border-warm); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--c-ring); }

/* Global typography */
h1, h2, h3, h4 {
  font-family: var(--font-serif);
  font-weight: 500;
  color: var(--c-near-black);
  line-height: 1.2;
}

button { font-family: var(--font-sans); cursor: pointer; }

a { color: inherit; text-decoration: none; }

input, textarea, select {
  font-family: var(--font-sans);
  font-size: 15px;
  color: var(--c-near-black);
  background: var(--c-white);
  border: 1px solid var(--c-border-warm);
  border-radius: var(--r-lg);
  padding: 10px 14px;
  outline: none;
  width: 100%;
  transition: border-color 0.15s, box-shadow 0.15s;
}

input:focus, textarea:focus {
  border-color: var(--c-focus-blue);
  box-shadow: 0 0 0 3px rgba(56,152,236,0.12);
}

textarea { resize: vertical; line-height: 1.6; }

/* Global button styles */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  background: var(--c-terracotta);
  color: var(--c-ivory);
  border: none;
  border-radius: var(--r-lg);
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-primary:hover { background: var(--c-terracotta-dark); }
.btn-primary:disabled { opacity: 0.5; cursor: default; }

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--c-warm-sand);
  color: var(--c-charcoal);
  border: 1px solid var(--c-border-warm);
  border-radius: var(--r-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-secondary:hover { background: var(--c-border-warm); }
.btn-secondary:disabled { opacity: 0.5; cursor: default; }

.btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: transparent;
  color: var(--c-olive-gray);
  border: 1px solid var(--c-border-warm);
  border-radius: var(--r-md);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.btn-ghost:hover {
  background: var(--c-ivory);
  border-color: var(--c-ring);
  color: var(--c-near-black);
}

/* Cards */
.card {
  background: var(--c-ivory);
  border: 1px solid var(--c-border-cream);
  border-radius: var(--r-xl);
  padding: var(--sp-6);
  box-shadow: var(--shadow-whisper);
}

/* Section title */
.section-label {
  font-family: var(--font-sans);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  color: var(--c-stone-gray);
}

/* Loading indicator */
.loading-dots {
  color: var(--c-stone-gray);
  font-size: 14px;
}

/* Toast 通知 */
.toast-container {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 9999;
  pointer-events: none;
}
.toast {
  padding: 10px 20px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: var(--shadow-toast);
  white-space: nowrap;
}
.toast-success { background: var(--c-near-black); color: var(--c-white); }
.toast-error   { background: var(--c-danger-strong); color: var(--c-white); }
.toast-info    { background: var(--c-charcoal); color: var(--c-white); }
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateY(12px); }
.toast-leave-to   { opacity: 0; transform: translateY(12px); }

/* ── macOS Electron：拖拽区域 + 红绿灯避让 ─────────────────────────────── */
.macos-app .nav {
  -webkit-app-region: drag;
  padding-left: 80px !important;
}

.macos-app .nav * {
  -webkit-app-region: no-drag;
}
</style>
