<template>
  <div class="lp-form-stack">
    <div class="lp-field">
      <label class="lp-field-label">身份/职位 <span class="lp-field-optional">（选填）</span></label>
      <input v-model="form.role" type="text" placeholder="例如：东吴谋主" :maxlength="MAX_ROLE_LEN" />
    </div>

    <div class="lp-field">
      <label class="lp-field-label">立场</label>
      <div class="lp-type-toggle" role="group" aria-label="立场">
        <button
          v-for="opt in stanceOptions"
          :key="opt.value"
          type="button"
          :class="['lp-type-btn', { active: form.stance === opt.value }]"
          :aria-pressed="form.stance === opt.value"
          @click="form.stance = opt.value"
        >{{ opt.label }}</button>
      </div>
    </div>

    <div class="lp-field">
      <label class="lp-field-label">性格 <span class="lp-field-optional">（5-10 个形容词）</span></label>
      <input v-model="form.persona" type="text" placeholder="例如：机敏 保守 远见" :maxlength="MAX_PERSONA_LEN" />
    </div>

    <div class="lp-field">
      <label class="lp-field-label">MBTI <span class="lp-field-optional">（选填）</span></label>
      <input v-model="form.mbti" type="text" placeholder="例如：INTJ" :maxlength="MAX_MBTI_LEN" class="mbti-input" />
    </div>

    <div class="lp-field">
      <label class="lp-field-label">背景简介 <span class="lp-field-optional">（与主角的关系/决策动机）</span></label>
      <textarea v-model="form.bio" rows="5" placeholder="描述 NPC 的来历、与主角的关联、动机..." :maxlength="MAX_BIO_LEN" />
    </div>
  </div>
</template>

<script setup>
import { MAX_ROLE_LEN, MAX_PERSONA_LEN, MAX_MBTI_LEN, MAX_BIO_LEN } from '../constants/limits.js'

defineProps({
  form: { type: Object, required: true },
})

const stanceOptions = [
  { value: 'ally',      label: '盟友' },
  { value: 'neutral',   label: '中立' },
  { value: 'adversary', label: '对手' },
]
</script>

<style scoped>
.mbti-input { width: 120px; }
textarea { resize: vertical; }
</style>
