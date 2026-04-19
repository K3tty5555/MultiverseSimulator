<template>
  <header class="nav lp-archive-topbar">
    <div class="nav-left">
      <router-link to="/" class="lp-back-btn" aria-label="返档案馆" title="返档案馆（首页）">
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M10 3 L5 8 L10 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span class="back-label">档案馆</span>
      </router-link>
      <div class="title-group">
        <span class="vol-label">VOL · {{ universe.id }}</span>
        <span v-if="universe.world_label" class="era-label">{{ universe.world_label }}</span>
        <h1 class="universe-title">{{ universe.title || '平行卷宗' }}</h1>
        <span v-if="selectedNodeId" class="node-info">· 批注 #{{ selectedNodeId }}</span>
      </div>
    </div>

    <div class="nav-right">
      <button
        v-if="!universe.is_personal_main"
        class="role-btn"
        :title="`此卷角色 ${agentCount} 位`"
        aria-label="管理角色"
        @click="$emit('open-npc')"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <circle cx="7" cy="4.5" r="2.2" stroke="currentColor" stroke-width="1.3"/>
          <path d="M2.5 12c0-2.2 2-4 4.5-4s4.5 1.8 4.5 4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
        </svg>
        <span v-if="agentCount > 0" class="role-count">{{ agentCount }}</span>
      </button>

      <div class="view-switcher">
        <button
          v-for="m in viewModes"
          :key="m.key"
          :class="['view-btn', { active: viewMode === m.key }]"
          :title="m.hint || m.label"
          @click="$emit('view-change', m.key)"
        >
          {{ m.label }}
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
defineProps({
  universe: { type: Object, required: true },
  selectedNodeId: { type: Number, default: null },
  agentCount: { type: Number, default: 0 },
  viewMode: { type: String, required: true },
  viewModes: { type: Array, required: true },
})
defineEmits(['open-npc', 'view-change'])
</script>

<style scoped>
.nav {
  justify-content: space-between;
  flex-shrink: 0;
  gap: var(--sp-4);
  position: relative;
  z-index: 10;
}

.nav-left {
  display: flex; align-items: center; gap: var(--sp-3);
  min-width: 0; flex: 1;
}

.back-label { font-weight: 500; }

.title-group {
  display: flex; align-items: baseline; gap: var(--sp-2);
  min-width: 0; overflow: hidden;
}
.vol-label {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--c-tarnished-gold);
  letter-spacing: 0.15em;
  padding: 2px 6px;
  border: 1px solid rgba(168, 137, 78, 0.4);
  border-radius: 2px;
  flex-shrink: 0;
}
.era-label {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 12px;
  color: var(--c-tarnished-gold);
  letter-spacing: 0.05em;
  flex-shrink: 0;
}
.universe-title {
  font-family: var(--font-serif-alt);
  font-size: 17px;
  font-weight: 500;
  color: var(--c-ivory-aged);
  letter-spacing: 0.04em;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.node-info {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--c-sepia-light);
  letter-spacing: 0.05em;
  white-space: nowrap;
  flex-shrink: 0;
}

.nav-right {
  display: flex; align-items: center; gap: var(--sp-3);
  flex-shrink: 0;
}

/* 降权为图标按钮：视图切换才是主操作，角色管理是次级入口 */
.role-btn {
  display: inline-flex; align-items: center; gap: 4px;
  width: 30px; height: 30px;
  padding: 0;
  border: 1px solid rgba(168, 137, 78, 0.25);
  border-radius: 2px;
  background: transparent;
  color: var(--c-sepia-light);
  cursor: pointer;
  transition: all var(--duration-fast);
  position: relative;
}
.role-btn:hover {
  background: rgba(168, 137, 78, 0.15);
  color: var(--c-ivory-aged);
  border-color: var(--c-tarnished-gold);
}
.role-btn > svg { margin: 0 auto; }
.role-count {
  position: absolute;
  top: -6px; right: -6px;
  min-width: 16px; height: 14px;
  padding: 0 4px;
  background: var(--c-tarnished-gold);
  color: var(--c-umber-deep);
  border-radius: 7px;
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.02em;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 2px rgba(20, 15, 10, 0.35);
}

.view-switcher {
  display: flex; gap: 0;
  background: rgba(20, 15, 10, 0.3);
  border: 1px solid rgba(168, 137, 78, 0.35);
  border-radius: 2px;
  padding: 2px;
}
.view-btn {
  padding: 5px 12px; border: none; background: transparent;
  font-family: var(--font-serif);
  font-size: 12px;
  color: var(--c-sepia-light);
  letter-spacing: 0.04em;
  cursor: pointer;
  transition: all var(--duration-fast);
  border-radius: 1px;
}
.view-btn:hover { color: var(--c-ivory-aged); }
.view-btn.active {
  background: var(--c-tarnished-gold);
  color: var(--c-umber-deep);
  font-weight: 500;
}
</style>
