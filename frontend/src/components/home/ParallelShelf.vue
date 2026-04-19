<template>
  <section class="lp-panel panel-shelf">
    <header class="lp-panel-head">
      <span class="lp-panel-seal" aria-hidden="true">❧</span>
      <h2 class="lp-panel-title">平行档案卷宗</h2>
      <span class="lp-panel-hint">
        <template v-if="universes.length > 0">{{ universes.length }} 个被归档的可能性 · 推演每一次「若我是…」</template>
        <template v-else>在平行时空 · 推演每一次「若我是…」的可能</template>
      </span>
    </header>

    <div class="shelf" tabindex="0">
      <!-- 已有的平行卷宗 -->
      <article
        v-for="u in universes"
        :key="u.id"
        class="volume"
        role="button"
        tabindex="0"
        @click="$emit('enter-universe', u.id)"
        @keydown.enter.space.prevent="$emit('enter-universe', u.id)"
        :title="u.title"
      >
        <div class="volume-cover" :style="{ '--volume-hue': volumeHue(u.id) }">
          <div class="volume-cover-bg"></div>
          <div class="volume-spine">
            <span class="spine-vol">VOL.{{ u.id }}</span>
            <span class="spine-type">{{ u.universe_type === 'historical' ? '史' : '幻' }}</span>
          </div>
          <div class="volume-corners" aria-hidden="true">
            <span class="vol-c vol-c-tl"></span><span class="vol-c vol-c-tr"></span>
            <span class="vol-c vol-c-bl"></span><span class="vol-c vol-c-br"></span>
          </div>
        </div>
        <div class="volume-title">{{ u.title || '未命名卷宗' }}</div>
        <div class="volume-sub">
          <span v-if="u.world_label">{{ u.world_label }}</span>
          <span v-if="u.protagonist_name"> · {{ u.protagonist_name }}</span>
        </div>
      </article>

      <!-- 馆藏推荐（仅 0 卷宗态） -->
      <article
        v-for="(rec, i) in recommendations"
        v-if="universes.length === 0"
        :key="'rec-' + i"
        class="volume volume--rec"
        :class="{ 'volume--has-cover': !!rec.cover }"
        role="button"
        tabindex="0"
        @click="$emit('new-universe')"
        @keydown.enter.space.prevent="$emit('new-universe')"
        :title="rec.title + ' · ' + rec.hook"
      >
        <div class="volume-cover volume-cover--rec" :style="{ '--volume-hue': rec.hue }">
          <div
            class="volume-cover-bg"
            :style="rec.cover ? { backgroundImage: `url('${rec.cover}')` } : {}"
          ></div>
          <!-- 真封面已包含书脊/四角/编号，无图时 fallback -->
          <template v-if="!rec.cover">
            <div class="volume-spine">
              <span class="spine-vol">REC.{{ i + 1 }}</span>
              <span class="spine-type">{{ rec.mark }}</span>
            </div>
            <div class="volume-corners" aria-hidden="true">
              <span class="vol-c vol-c-tl"></span><span class="vol-c vol-c-tr"></span>
              <span class="vol-c vol-c-bl"></span><span class="vol-c vol-c-br"></span>
            </div>
          </template>
          <div class="volume-rec-label">推荐</div>
        </div>
        <div class="volume-title">{{ rec.title }}</div>
        <div class="volume-sub volume-sub--hook">{{ rec.hook }}</div>
      </article>

      <!-- 统一的新建入口（始终在最右） -->
      <article
        class="volume volume--new"
        role="button"
        tabindex="0"
        @click="$emit('new-universe')"
        @keydown.enter.space.prevent="$emit('new-universe')"
        title="开启新卷宗"
      >
        <div class="volume-cover volume-cover--new">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none"><path d="M14 4 V24 M4 14 H24" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><circle cx="14" cy="14" r="11" stroke="currentColor" stroke-width="0.8" stroke-dasharray="2 2" opacity="0.6"/></svg>
        </div>
        <div class="volume-title volume-title--muted">开启新卷宗</div>
        <div class="volume-sub">{{ universes.length === 0 ? '或自定义一段未写的可能' : '展开一段未写的可能' }}</div>
      </article>
    </div>
  </section>
</template>

<script setup>
defineProps({ universes: { type: Array, default: () => [] } })
defineEmits(['enter-universe', 'new-universe'])

function volumeHue(id) {
  const hues = [25, 175, 340, 200, 60, 280]
  return hues[id % hues.length]
}

/* 馆藏推荐：已配真实档案封面图（文生图产出） */
const recommendations = [
  { title: '三国乱世', hook: '若你是曹操 · 赤壁战前夜',   mark: '史', hue: 25,  cover: '/art/cover-sanguo.png' },
  { title: '红楼梦',   hook: '若你是贾宝玉 · 太虚幻境醒时', mark: '幻', hue: 340, cover: '/art/cover-hongloumeng.png' },
  { title: '宋',       hook: '若你是苏轼 · 黄州被贬之年',   mark: '史', hue: 175, cover: '/art/cover-song.png' },
  { title: '明',       hook: '若你是王阳明 · 龙场悟道之夜', mark: '史', hue: 200, cover: '/art/cover-ming.png' },
]
</script>

<style scoped>
.panel-shelf { grid-area: shelf; }

.shelf {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-4);
  padding: var(--sp-3) var(--sp-5) var(--sp-4);
  overflow-x: auto;
  overflow-y: hidden;
  scroll-behavior: smooth;
  scrollbar-width: thin;
  scrollbar-color: rgba(168, 137, 78, 0.4) transparent;
}
.shelf::-webkit-scrollbar { height: 8px; }
.shelf::-webkit-scrollbar-track { background: transparent; }
.shelf::-webkit-scrollbar-thumb { background: rgba(168, 137, 78, 0.4); border-radius: 4px; }
.shelf:focus { outline: none; }

.volume {
  flex-shrink: 0;
  width: 160px;
  min-width: 0;
  overflow: hidden;
  display: flex; flex-direction: column;
  cursor: pointer;
  transition: transform var(--duration-base) var(--ease-out);
  outline: none;
}
.volume:hover { transform: translateY(-4px); }
.volume:focus-visible { outline: 2px solid var(--c-tarnished-gold); outline-offset: 4px; border-radius: 2px; }

.volume-cover {
  position: relative;
  aspect-ratio: 2 / 3;
  border-radius: 2px 4px 4px 2px;
  overflow: hidden;
  box-shadow:
    -4px 4px 0 -1px rgba(20, 15, 10, 0.3),
    var(--shadow-paper-edge);
  transition: box-shadow var(--duration-base);
}
.volume:hover .volume-cover {
  box-shadow:
    -6px 6px 0 -1px rgba(20, 15, 10, 0.4),
    var(--shadow-gold-deep),
    var(--shadow-paper-edge);
}
.volume-cover-bg {
  position: absolute; inset: 0;
  background-image: linear-gradient(135deg,
    hsl(var(--volume-hue, 25), 22%, 26%) 0%,
    hsl(var(--volume-hue, 25), 15%, 12%) 100%);
  background-size: cover;
  background-position: center;
  filter: sepia(35%);
}
.volume-cover::after {
  content: '';
  position: absolute; inset: 0;
  background:
    radial-gradient(ellipse at 30% 20%, rgba(232, 223, 200, 0.1) 0%, transparent 50%),
    radial-gradient(ellipse at center, transparent 40%, rgba(20, 15, 10, 0.45) 100%);
  pointer-events: none;
}

/* 推荐书（无真封面回退）：加重 sepia 融入档案馆 */
.volume-cover--rec .volume-cover-bg {
  background-image: linear-gradient(135deg,
    hsl(var(--volume-hue, 25), 18%, 22%) 0%,
    hsl(var(--volume-hue, 25), 12%, 10%) 100%);
  filter: sepia(55%) brightness(0.82) contrast(1.05);
}
/* 真封面已经是 sepia 档案感 + 自带书脊/边框，去掉二次 filter 和暗角 */
.volume--has-cover .volume-cover-bg { filter: none; }
.volume--has-cover .volume-cover::after { display: none; }

.volume-spine {
  position: absolute;
  top: 0; left: 0;
  width: 18px; height: 100%;
  background: linear-gradient(to right, rgba(20, 15, 10, 0.78) 0%, transparent 100%);
  border-right: 1px solid rgba(168, 137, 78, 0.3);
  display: flex; flex-direction: column; align-items: center; justify-content: space-between;
  padding: 12px 0;
  z-index: 1;
}
.spine-vol {
  font-family: var(--font-mono);
  font-size: 8px;
  color: var(--c-tarnished-gold);
  letter-spacing: 0.15em;
  writing-mode: vertical-rl;
  text-orientation: mixed;
}
.spine-type {
  font-family: var(--font-serif-alt);
  font-size: 14px;
  color: var(--c-tarnished-gold);
}
.volume-corners { position: absolute; inset: 8px; pointer-events: none; }
.vol-c {
  position: absolute;
  width: 10px; height: 10px;
  border: 1px solid var(--c-tarnished-gold);
  opacity: 0.5;
}
.vol-c-tl { top: 0; left: 0; border-right: none; border-bottom: none; }
.vol-c-tr { top: 0; right: 0; border-left: none; border-bottom: none; }
.vol-c-bl { bottom: 0; left: 0; border-right: none; border-top: none; }
.vol-c-br { bottom: 0; right: 0; border-left: none; border-top: none; }

.volume-cover--new {
  background: repeating-linear-gradient(
    45deg,
    var(--c-ivory-aged) 0, var(--c-ivory-aged) 6px,
    rgba(201, 176, 145, 0.22) 6px, rgba(201, 176, 145, 0.22) 12px);
  border: 1px dashed var(--c-sepia);
  display: flex; align-items: center; justify-content: center;
  color: var(--c-sepia);
  aspect-ratio: 2 / 3;
  border-radius: 2px 4px 4px 2px;
  overflow: hidden;
  box-shadow: var(--shadow-paper-edge);
  transition: all var(--duration-base);
  position: relative;
}
.volume-cover--new::after { display: none; }
.volume--new:hover .volume-cover--new {
  background: rgba(232, 223, 200, 0.95);
  border-color: var(--c-tarnished-gold);
  color: var(--c-tarnished-gold);
}

/* 推荐标签：sepia 暖调替代原来艳丽的 oxblood */
.volume-rec-label {
  position: absolute;
  top: 10px; right: -22px;
  transform: rotate(45deg);
  font-family: var(--font-mono);
  font-size: 8px;
  letter-spacing: 0.2em;
  color: var(--c-ivory-aged);
  background: var(--c-tarnished-gold);
  padding: 2px 24px;
  z-index: 2;
  box-shadow: 0 1px 3px rgba(20, 15, 10, 0.35);
}

.volume-title {
  font-family: var(--font-serif-alt);
  font-size: 14px;
  font-weight: 500;
  color: var(--c-umber-deep);
  line-height: 1.35;
  margin-top: var(--sp-3);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  /* 中文单行标题不强制 2 行高度，避免 hook 被挤出容器 */
}
.volume-title--muted { color: var(--c-sepia); font-style: italic; }
.volume-sub {
  font-family: var(--font-serif);
  font-size: 11px;
  color: var(--c-sepia);
  line-height: 1.5;
  margin-top: 3px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  word-break: break-word;
  max-width: 100%;
}
.volume-sub--hook {
  font-style: italic;
  color: var(--c-umber);
}
</style>
