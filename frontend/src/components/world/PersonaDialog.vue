<template>
  <div v-if="show" class="lp-modal-overlay" @click.self="$emit('close')">
    <div class="lp-modal dlg-modal" role="dialog" aria-modal="true" :aria-labelledby="titleId">
      <div class="lp-modal-header">
        <div class="header-left">
          <span class="header-seal" aria-hidden="true">卷</span>
          <h2 :id="titleId" class="lp-modal-title">自此开卷</h2>
        </div>
        <button class="lp-modal-close" aria-label="关闭" @click="$emit('close')">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
        </button>
      </div>

      <div class="lp-modal-body">
        <div class="dlg-persona-card">
          <span class="dlg-persona-emoji" aria-hidden="true">{{ persona?.avatar_emoji || '📜' }}</span>
          <div class="dlg-persona-info">
            <span class="dlg-persona-name">{{ persona?.name }}</span>
            <p class="dlg-persona-bio">{{ persona?.bio || '（暂无简介）' }}</p>
          </div>
        </div>

        <div class="dlg-checkpoint-info">
          <span class="dlg-cp-title">{{ checkpoint?.title }}</span>
          <span class="dlg-cp-year">{{ checkpoint?.year_label }}</span>
        </div>

        <div class="form-group">
          <label class="form-label">记叙视角</label>
          <div class="perspective-switch">
            <button
              :class="['perspective-btn', { active: perspective === 'god' }]"
              type="button"
              @click="$emit('update:perspective', 'god')"
            >
              <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true"><circle cx="7" cy="7" r="6" stroke="currentColor" stroke-width="1.3"/><path d="M1 7h12M7 1a8 8 0 010 12M7 1a8 8 0 000 12" stroke="currentColor" stroke-width="1.3"/></svg>
              纵观
            </button>
            <button
              :class="['perspective-btn', { active: perspective === 'first_person' }]"
              type="button"
              @click="$emit('update:perspective', 'first_person')"
            >
              <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true"><circle cx="7" cy="4" r="2.5" stroke="currentColor" stroke-width="1.3"/><path d="M2 13c0-2.761 2.239-5 5-5s5 2.239 5 5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
              亲历
            </button>
          </div>
          <p class="perspective-hint">纵观以卷首视角叙写；亲历让研究员直入主角心境。</p>
        </div>

        <p v-if="error" class="lp-form-error">{{ error }}</p>
      </div>

      <div class="lp-modal-footer">
        <button class="lp-btn-ghost-archive" @click="$emit('close')">取消</button>
        <button class="lp-btn-archive" :disabled="creating" @click="$emit('create')">
          <span v-if="creating" class="lp-btn-inline-spinner" aria-hidden="true"></span>
          {{ creating ? '开卷中...' : '落笔开卷 →' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  show: { type: Boolean, default: false },
  checkpoint: { type: Object, default: null },
  persona: { type: Object, default: null },
  perspective: { type: String, default: 'god' },
  creating: { type: Boolean, default: false },
  error: { type: String, default: '' },
})
defineEmits(['close', 'create', 'update:perspective'])

const titleId = computed(() => `dlg-title-${props.checkpoint?.id || 'na'}`)
</script>

<style scoped>
.dlg-modal { max-width: 500px; }

.header-left { display: flex; align-items: center; gap: var(--sp-3); }
.header-seal {
  display: inline-flex; align-items: center; justify-content: center;
  width: 26px; height: 26px;
  background: var(--c-oxblood);
  color: var(--c-ivory-aged);
  font-family: var(--font-serif-alt);
  font-size: 13px; font-weight: 600;
  border-radius: 2px;
  box-shadow: var(--shadow-oxblood-seal);
}

.dlg-persona-card {
  display: flex; align-items: flex-start; gap: var(--sp-3);
  background: var(--c-ivory);
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
  padding: var(--sp-4);
  margin-bottom: var(--sp-3);
}
.dlg-persona-emoji { font-size: 28px; line-height: 1; flex-shrink: 0; }
.dlg-persona-info { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.dlg-persona-name {
  font-family: var(--font-serif-alt);
  font-size: 16px; font-weight: 500;
  color: var(--c-umber-deep);
}
.dlg-persona-bio {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 12px;
  color: var(--c-sepia);
  line-height: 1.7;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}

.dlg-checkpoint-info {
  display: flex; flex-direction: column; gap: 4px;
  padding: var(--sp-3) var(--sp-4);
  background: rgba(168, 137, 78, 0.1);
  border-left: 2px solid var(--c-tarnished-gold);
  border-radius: 0 2px 2px 0;
  margin-bottom: var(--sp-3);
}
.dlg-cp-title {
  font-family: var(--font-serif-alt);
  font-size: 14px; font-weight: 500;
  color: var(--c-umber-deep);
}
.dlg-cp-year {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--c-tarnished-gold);
  letter-spacing: 0.08em;
}

.form-group { display: flex; flex-direction: column; gap: var(--sp-2); }
.form-label {
  font-family: var(--font-serif);
  font-size: 13px; font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.04em;
}
.perspective-switch { display: flex; gap: var(--sp-2); }
.perspective-btn {
  flex: 1;
  display: flex; align-items: center; justify-content: center; gap: var(--sp-2);
  padding: 9px 14px;
  border: 1px solid var(--c-border-archive);
  background: var(--c-ivory);
  border-radius: 2px;
  font-family: var(--font-serif);
  font-size: 13px;
  color: var(--c-umber);
  cursor: pointer;
  transition: all var(--duration-fast);
}
.perspective-btn:hover { border-color: var(--c-tarnished-gold); color: var(--c-umber-deep); }
.perspective-btn.active {
  border-color: var(--c-oxblood);
  background: var(--c-oxblood);
  color: var(--c-ivory-aged);
  font-weight: 500;
}
.perspective-hint {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 12px;
  color: var(--c-sepia);
  line-height: 1.6;
  margin-top: var(--sp-1);
}
</style>
