import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

/**
 * 时光逆流动画入口统一管理：
 * - startFromQuery() 从 URL query 读取 play_intro / target_year 并触发
 * - start(year) 直接指定目标年份触发
 * - markDataReady() 父组件数据就绪时调用，动画收场前等待它为真（避免 ESC 跳过时落地骨架屏）
 * - cancel() 数据加载失败时立即取消动画
 * - handleComplete() 绑定到 YearFlipOverlay @complete；结束时清 URL query（省略 path 避免导航竞态）
 */
export function useYearFlipEntry(options = {}) {
  const {
    clearQueryOnComplete = true,
    maxWaitAfterSkip = 10000,
  } = options

  const route = useRoute()
  const router = useRouter()

  const showYearFlip = ref(false)
  const flipTargetYear = ref(null)
  const currentYear = new Date().getFullYear()
  const dataReady = ref(false)

  function start(targetYear) {
    const year = Number(targetYear)
    if (!Number.isFinite(year) || year >= currentYear) return false
    flipTargetYear.value = year
    dataReady.value = false
    showYearFlip.value = true
    return true
  }

  function startFromQuery() {
    if (route.query.play_intro !== '1') return false
    return start(parseInt(route.query.target_year, 10))
  }

  function cancel() {
    showYearFlip.value = false
  }

  function markDataReady() {
    dataReady.value = true
  }

  async function handleComplete() {
    // ESC 早跳时数据可能还没加载完，等它就绪再收场（最长等 10s 兜底）
    if (!dataReady.value) {
      await new Promise(resolve => {
        const stop = watch(dataReady, v => { if (v) { stop(); resolve() } })
        setTimeout(() => { stop(); resolve() }, maxWaitAfterSkip)
      })
    }
    showYearFlip.value = false
    if (clearQueryOnComplete) {
      router.replace({ query: {} })
    }
  }

  return {
    showYearFlip,
    flipTargetYear,
    currentYear,
    dataReady,
    start,
    startFromQuery,
    cancel,
    markDataReady,
    handleComplete,
  }
}
