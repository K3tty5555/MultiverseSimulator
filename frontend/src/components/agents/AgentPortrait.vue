<template>
  <div
    class="portrait"
    :style="{
      '--mono-hue': monoHue,
      '--seal-rotate': sealRotate + 'deg',
    }"
    :data-universe="universeType"
  >
    <div class="portrait-bg" aria-hidden="true"></div>
    <div class="portrait-paper" aria-hidden="true"></div>

    <div class="portrait-banner" aria-hidden="true">
      <span class="banner-mark">{{ universeShortMark }}</span>
      <span v-if="worldLabel" class="banner-sub">{{ truncatedLabel }}</span>
    </div>

    <div :class="['portrait-name', nameLayoutClass]" aria-hidden="true">
      <span v-for="(ch, i) in displayChars" :key="i" class="name-char">{{ ch }}</span>
    </div>

    <div :class="['portrait-seal', `seal-${sealShape}`]" aria-hidden="true">
      <span class="seal-glyph">{{ sealGlyph }}</span>
    </div>

    <div class="portrait-corners" aria-hidden="true">
      <span class="pc pc-tl"></span><span class="pc pc-tr"></span>
      <span class="pc pc-bl"></span><span class="pc pc-br"></span>
    </div>

    <span class="visually-hidden">{{ name }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, required: true },
  universeType: { type: String, default: 'historical' }, // historical | fictional | personal
  worldLabel: { type: String, default: '' },
})

const HAN_RE = /[一-龥]/
const LATIN_RE = /[A-Za-z]/

function hashInt(str) {
  let h = 0
  for (const ch of (str || '?')) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return h
}

const cleanName = computed(() => (props.name || '').trim())
const nameHash = computed(() => hashInt(cleanName.value))

const isLatinDominant = computed(() => {
  const n = cleanName.value
  if (!n) return false
  if (HAN_RE.test(n)) return false
  return LATIN_RE.test(n)
})

const nameLayoutClass = computed(() => {
  const n = cleanName.value
  const len = [...n].length
  if (isLatinDominant.value) return 'layout-latin'
  if (len <= 2) return 'layout-vert-lg'
  if (len <= 4) return 'layout-vert-md'
  return 'layout-vert-sm'
})

const displayChars = computed(() => {
  const n = cleanName.value || '?'
  if (isLatinDominant.value) return [n]
  return [...n]
})

const universeShortMark = computed(() => {
  switch (props.universeType) {
    case 'fictional': return '幻'
    case 'personal':  return '己'
    default:          return '史'
  }
})

const truncatedLabel = computed(() => {
  const lab = (props.worldLabel || '').trim()
  if (!lab) return ''
  const arr = [...lab]
  return arr.length > 6 ? arr.slice(0, 6).join('') + '…' : lab
})

const sealShape = computed(() => {
  const shapes = ['round', 'square', 'octagon']
  return shapes[nameHash.value % shapes.length]
})

const sealRotate = computed(() => {
  return ((nameHash.value % 13) - 6) // -6° ~ +6°
})

const sealGlyph = computed(() => {
  const n = cleanName.value
  if (!n) return '？'
  if (isLatinDominant.value) {
    const m = n.match(/[A-Za-z]/)
    return m ? m[0].toUpperCase() : n[0].toUpperCase()
  }
  const arr = [...n]
  return arr[arr.length - 1] || arr[0]
})

const monoHue = computed(() => nameHash.value % 360)
</script>

<style scoped>
.portrait {
  position: relative;
  aspect-ratio: 2 / 3;
  overflow: hidden;
  background: var(--c-umber-deep);
  isolation: isolate;
}

/* 底层 sepia 渐变（hash 决定 hue） */
.portrait-bg {
  position: absolute; inset: 0;
  background: linear-gradient(
    155deg,
    hsl(var(--mono-hue, 25), 22%, 30%) 0%,
    hsl(var(--mono-hue, 25), 18%, 18%) 60%,
    hsl(var(--mono-hue, 25), 22%, 12%) 100%
  );
  filter: sepia(38%);
  z-index: 0;
}
.portrait-bg::after {
  content: '';
  position: absolute; inset: 0;
  background:
    radial-gradient(ellipse at 35% 25%, rgba(232, 223, 200, 0.12) 0%, transparent 55%),
    radial-gradient(ellipse at center, transparent 35%, rgba(20, 15, 10, 0.55) 100%);
  pointer-events: none;
}

/* 纸纹叠加层（轻微噪点 + 老纸黄） */
.portrait-paper {
  position: absolute; inset: 0;
  z-index: 1;
  pointer-events: none;
  background-image:
    repeating-linear-gradient(
      0deg,
      transparent 0px,
      transparent 2px,
      rgba(232, 223, 200, 0.04) 2px,
      rgba(232, 223, 200, 0.04) 3px
    ),
    repeating-linear-gradient(
      90deg,
      transparent 0px,
      transparent 3px,
      rgba(20, 15, 10, 0.05) 3px,
      rgba(20, 15, 10, 0.05) 4px
    );
  mix-blend-mode: overlay;
  opacity: 0.7;
}

/* 顶标 */
.portrait-banner {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 3;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: calc(100% - 20px);
}
.banner-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  background: var(--banner-color, var(--c-tarnished-gold));
  color: var(--c-ivory-aged);
  font-family: var(--font-serif-alt);
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0;
  line-height: 1;
  border-radius: 1px;
  box-shadow: 0 1px 2px rgba(20, 15, 10, 0.4);
}
.banner-sub {
  font-family: var(--font-serif);
  font-size: 10px;
  font-style: italic;
  color: var(--c-ivory-aged);
  letter-spacing: 0.04em;
  text-shadow: 0 1px 2px rgba(20, 15, 10, 0.6);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  opacity: 0.85;
}

/* universe 色变量绑定 */
.portrait[data-universe="historical"] { --banner-color: var(--c-tarnished-gold); }
.portrait[data-universe="fictional"]  { --banner-color: var(--c-deep-teal); }
.portrait[data-universe="personal"]   { --banner-color: var(--c-oxblood); }

/* 中央人物名（多布局） */
.portrait-name {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-serif-alt);
  color: var(--c-ivory-aged);
  letter-spacing: 0;
  user-select: none;
  text-shadow:
    0 2px 6px rgba(20, 15, 10, 0.55),
    0 0 18px rgba(168, 137, 78, 0.18);
  opacity: 0.92;
}
.portrait-name .name-char {
  display: block;
  line-height: 1;
}

/* 竖排：1-2 字 → 大 */
.layout-vert-lg {
  flex-direction: column;
  gap: 4px;
}
.layout-vert-lg .name-char { font-size: 64px; font-weight: 500; }

/* 竖排：3-4 字 → 中 */
.layout-vert-md {
  flex-direction: column;
  gap: 2px;
}
.layout-vert-md .name-char { font-size: 50px; font-weight: 500; }

/* 竖排：5+ 字 → 小 */
.layout-vert-sm {
  flex-direction: column;
  gap: 1px;
}
.layout-vert-sm .name-char { font-size: 32px; font-weight: 500; }

/* 横排：拉丁字符 */
.layout-latin {
  padding: 0 14px;
  text-align: center;
}
.layout-latin .name-char {
  font-size: 28px;
  font-weight: 500;
  letter-spacing: 0.02em;
  word-break: break-word;
  line-height: 1.1;
  hyphens: auto;
}

/* 朱印 */
.portrait-seal {
  position: absolute;
  right: 12px;
  bottom: 14px;
  z-index: 4;
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--c-oxblood);
  color: var(--c-ivory-aged);
  border: 1.5px solid var(--c-oxblood-dark);
  box-shadow:
    0 1px 3px rgba(20, 15, 10, 0.5),
    inset 0 0 4px rgba(255, 230, 200, 0.15);
  transform: rotate(var(--seal-rotate, 0deg));
  /* 印泥磨损：用 mask 制造不均匀边缘 */
  mask-image: radial-gradient(circle at 38% 42%, rgba(0,0,0,1) 65%, rgba(0,0,0,0.85) 80%, rgba(0,0,0,0.6) 100%);
  -webkit-mask-image: radial-gradient(circle at 38% 42%, rgba(0,0,0,1) 65%, rgba(0,0,0,0.85) 80%, rgba(0,0,0,0.6) 100%);
}
.seal-round { border-radius: 50%; }
.seal-square { border-radius: 3px; }
.seal-octagon {
  border-radius: 2px;
  clip-path: polygon(
    30% 0%, 70% 0%, 100% 30%, 100% 70%,
    70% 100%, 30% 100%, 0% 70%, 0% 30%
  );
  border: none; /* 八角靠 clip-path，外描边失效 */
  box-shadow:
    0 1px 3px rgba(20, 15, 10, 0.5),
    inset 0 0 0 1.5px var(--c-oxblood-dark),
    inset 0 0 4px rgba(255, 230, 200, 0.15);
}
.seal-glyph {
  font-family: var(--font-serif-alt);
  font-size: 20px;
  font-weight: 600;
  line-height: 1;
  letter-spacing: 0;
}

/* 四角金线（保留原设计） */
.portrait-corners {
  position: absolute;
  inset: 8px;
  pointer-events: none;
  z-index: 5;
}
.pc {
  position: absolute;
  width: 10px;
  height: 10px;
  border: 1px solid var(--c-tarnished-gold);
  opacity: 0.55;
}
.pc-tl { top: 0; left: 0; border-right: none; border-bottom: none; }
.pc-tr { top: 0; right: 0; border-left: none; border-bottom: none; }
.pc-bl { bottom: 0; left: 0; border-right: none; border-top: none; }
.pc-br { bottom: 0; right: 0; border-left: none; border-top: none; }

.visually-hidden {
  position: absolute;
  width: 1px; height: 1px;
  padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* 响应式：小屏缩字 */
@media (max-width: 640px) {
  .layout-vert-lg .name-char { font-size: 48px; }
  .layout-vert-md .name-char { font-size: 38px; }
  .layout-vert-sm .name-char { font-size: 26px; }
  .layout-latin .name-char { font-size: 22px; }
  .portrait-seal { width: 34px; height: 34px; right: 8px; bottom: 10px; }
  .seal-glyph { font-size: 16px; }
  .banner-mark { width: 20px; height: 20px; font-size: 12px; }
  .banner-sub { font-size: 9px; }
}
</style>
