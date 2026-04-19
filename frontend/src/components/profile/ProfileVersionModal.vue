<template>
  <Teleport to="body">
    <div v-if="show" class="version-backdrop" @click.self="$emit('close')">
      <div class="version-modal" role="dialog" aria-modal="true" aria-labelledby="version-modal-title">
        <h4 id="version-modal-title" class="version-modal-title">登记历史版本</h4>
        <p v-if="versions.length === 0" class="version-empty">暂无历史版本（保存档案后会自动归档）</p>
        <div v-for="v in versions" :key="v.id" class="version-item">
          <div class="version-info">
            <span class="version-name">{{ v.display_name || '未命名' }}</span>
            <span class="version-age">{{ v.age ? v.age + '岁' : '' }}</span>
          </div>
          <span class="version-date">{{ v.saved_at?.slice(0, 10) }}</span>
        </div>
        <button class="lp-btn-ghost-archive close-modal-btn" @click="$emit('close')">关闭</button>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  show: { type: Boolean, default: false },
  versions: { type: Array, default: () => [] },
})
defineEmits(['close'])
</script>

<style scoped>
.version-backdrop {
  position: fixed; inset: 0;
  background: rgba(20, 15, 10, 0.55);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.version-modal {
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
  padding: var(--sp-6);
  min-width: 340px;
  max-width: 420px;
  box-shadow: var(--shadow-modal), inset 0 2px 0 var(--c-tarnished-gold);
}
.version-modal-title {
  font-family: var(--font-serif-alt);
  font-size: 17px;
  font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.03em;
  margin-bottom: var(--sp-4);
}
.version-empty {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 13px;
  color: var(--c-sepia);
  text-align: center;
  padding: var(--sp-4) 0;
}
.version-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: var(--sp-3) 0;
  border-bottom: 1px solid var(--c-border-archive);
}
.version-info { display: flex; gap: var(--sp-2); align-items: center; }
.version-name { font-family: var(--font-serif); font-size: 14px; color: var(--c-umber-deep); }
.version-age { font-family: var(--font-mono); font-size: 11px; color: var(--c-sepia); }
.version-date { font-family: var(--font-mono); font-size: 11px; color: var(--c-sepia); }
.close-modal-btn { margin-top: var(--sp-4); width: 100%; justify-content: center; }
</style>
