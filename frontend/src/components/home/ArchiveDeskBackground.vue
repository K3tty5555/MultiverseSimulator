<template>
  <div class="desk-bg" aria-hidden="true">
    <div class="desk-layer desk-image"></div>
    <div class="desk-layer desk-grain"></div>
    <div class="desk-layer desk-vignette"></div>
    <div class="desk-layer desk-top-shade"></div>
  </div>
</template>

<script setup></script>

<style scoped>
.desk-bg { position: absolute; inset: 0; z-index: 0; pointer-events: none; }
.desk-layer { position: absolute; inset: 0; }
.desk-image {
  background: var(--img-hero, var(--c-umber-deep)) center/cover no-repeat;
}
.desk-grain {
  background-image: repeating-linear-gradient(90deg, rgba(61, 46, 31, 0.02) 0, rgba(61, 46, 31, 0.02) 1px, transparent 1px, transparent 3px);
  mix-blend-mode: overlay;
  opacity: 0.5;
}
.desk-vignette {
  background: radial-gradient(ellipse at center, transparent 50%, rgba(20, 15, 10, 0.28) 100%);
}
.desk-top-shade {
  background: linear-gradient(to bottom, rgba(20, 15, 10, 0.5) 0%, transparent 100%);
  height: 120px;
  inset: 0 0 auto 0;
}
</style>
