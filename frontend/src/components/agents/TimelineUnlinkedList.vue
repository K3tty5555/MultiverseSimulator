<template>
  <div class="unlinked-section">
    <h4 class="unlinked-title">未系节点的推演</h4>
    <p class="unlinked-hint">这些卷宗创建时未绑定具体节点（多为旧卷或 checkpoint 卷）。</p>
    <ul class="unlinked-list">
      <li v-for="u in universes" :key="u.universe_id" class="branch-item">
        <span class="branch-title">{{ u.title }}</span>
        <span class="branch-meta">{{ u.node_count || 0 }} 批注</span>
        <button class="btn-link-archive" @click="$emit('enter', u.universe_id)">翻至此卷 →</button>
      </li>
    </ul>
  </div>
</template>

<script setup>
defineProps({
  universes: { type: Array, default: () => [] },
})
defineEmits(['enter'])
</script>

<style scoped>
.unlinked-section {
  margin-top: var(--sp-6);
  padding-top: var(--sp-5);
  border-top: 1px dashed var(--c-border-sepia);
}
.unlinked-title {
  font-family: var(--font-serif-alt);
  font-size: 14px; font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.04em;
  margin: 0 0 var(--sp-2);
}
.unlinked-hint {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 12px;
  color: var(--c-sepia);
  margin: 0 0 var(--sp-3);
}
.unlinked-list {
  list-style: none; margin: 0; padding: 0;
  display: flex; flex-direction: column;
  gap: var(--sp-2);
}
.branch-item {
  display: flex; align-items: center; gap: var(--sp-3);
  padding: var(--sp-2) var(--sp-3);
  background: var(--c-ivory-aged);
  border: 1px solid var(--c-border-archive);
  border-radius: 2px;
}
.branch-title {
  flex: 1;
  font-family: var(--font-serif-alt);
  font-size: 13px;
  color: var(--c-umber-deep);
  font-weight: 500;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.branch-meta {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--c-sepia);
  flex-shrink: 0;
  letter-spacing: 0.05em;
}
.btn-link-archive {
  background: transparent; border: none;
  color: var(--c-oxblood);
  font-family: var(--font-serif);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  flex-shrink: 0;
  letter-spacing: 0.04em;
}
.btn-link-archive:hover { text-decoration: underline; color: var(--c-tarnished-gold); }
</style>
