/**
 * profile store — 用户档案缓存。
 *
 * 职责：
 *  - 避免多个组件重复 fetch /api/profile
 *  - 缓存 LLM 配置状态 / 档案完整度
 *  - 提供统一的刷新接口
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API = '/api'

export const useProfileStore = defineStore('profile', () => {
  const profile        = ref(null)      // 完整档案对象
  const llmConfigured  = ref(null)      // null=未知, true/false
  const loading        = ref(false)
  const lastFetchedAt  = ref(null)

  const CACHE_TTL_MS = 60_000  // 1 分钟缓存

  const isProfileComplete = computed(() => {
    if (!profile.value) return false
    const p = profile.value
    return !!(p.display_name && p.summary)
  })

  async function fetchProfile(force = false) {
    const now = Date.now()
    if (!force && lastFetchedAt.value && (now - lastFetchedAt.value) < CACHE_TTL_MS) return
    loading.value = true
    try {
      const res = await axios.get(`${API}/profile`)
      profile.value = res.data.profile || null
      lastFetchedAt.value = now
    } catch {
      profile.value = null
    } finally {
      loading.value = false
    }
  }

  async function fetchLlmStatus(force = false) {
    if (!force && llmConfigured.value !== null) return
    try {
      const res = await axios.get(`${API}/settings/llm-status`)
      llmConfigured.value = res.data.configured === true
    } catch {
      llmConfigured.value = false
    }
  }

  function invalidate() {
    lastFetchedAt.value = null
  }

  return {
    profile, llmConfigured, loading,
    isProfileComplete,
    fetchProfile, fetchLlmStatus, invalidate,
  }
})
