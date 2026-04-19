<template>
  <div class="portrait">
    <img
      v-if="portrait"
      :src="portrait"
      :alt="`${name} 立绘`"
      class="portrait-img"
    />
    <template v-else>
      <div class="portrait-bg" :style="{ '--mono-hue': monoHue(name) }"></div>
      <span class="portrait-monogram" aria-hidden="true">{{ firstChar(name) }}</span>
      <div class="portrait-corners" aria-hidden="true">
        <span class="pc pc-tl"></span><span class="pc pc-tr"></span>
        <span class="pc pc-bl"></span><span class="pc pc-br"></span>
      </div>
    </template>
  </div>
</template>

<script setup>
defineProps({
  name: { type: String, required: true },
  portrait: { type: String, default: null },
})

function firstChar(name) {
  return name?.trim()[0]?.toUpperCase() || '?'
}
function monoHue(name) {
  let h = 0
  for (const ch of (name || '?')) h = (h * 31 + ch.charCodeAt(0)) % 360
  return h
}
</script>

<style scoped>
.portrait {
  position: relative;
  /* 2:3 匹配真实立绘封面比例（如诸葛亮/曹操），避免 object-fit:cover 裁脸 */
  aspect-ratio: 2 / 3;
  overflow: hidden;
  background: var(--c-umber-deep);
}
.portrait-img {
  width: 100%; height: 100%;
  object-fit: cover;
  object-position: center top;
  display: block;
}
.portrait-bg {
  position: absolute; inset: 0;
  background: linear-gradient(135deg,
    hsl(var(--mono-hue, 25), 22%, 28%) 0%,
    hsl(var(--mono-hue, 25), 15%, 12%) 100%);
  filter: sepia(35%);
}
.portrait-bg::after {
  content: '';
  position: absolute; inset: 0;
  background:
    radial-gradient(ellipse at 30% 20%, rgba(232, 223, 200, 0.1) 0%, transparent 50%),
    radial-gradient(ellipse at center, transparent 40%, rgba(20, 15, 10, 0.45) 100%);
  pointer-events: none;
}
.portrait-monogram {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-serif-alt);
  font-size: 72px;
  font-weight: 500;
  color: var(--c-ivory-aged);
  opacity: 0.75;
  user-select: none;
  z-index: 1;
  text-shadow: 0 2px 6px rgba(20, 15, 10, 0.4);
}
.portrait-corners { position: absolute; inset: 8px; pointer-events: none; z-index: 2; }
.pc {
  position: absolute;
  width: 10px; height: 10px;
  border: 1px solid var(--c-tarnished-gold);
  opacity: 0.55;
}
.pc-tl { top: 0; left: 0; border-right: none; border-bottom: none; }
.pc-tr { top: 0; right: 0; border-left: none; border-bottom: none; }
.pc-bl { bottom: 0; left: 0; border-right: none; border-top: none; }
.pc-br { bottom: 0; right: 0; border-left: none; border-top: none; }

@media (max-width: 640px) {
  .portrait-monogram { font-size: 52px; }
}
</style>
