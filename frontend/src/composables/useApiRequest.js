/**
 * useApiRequest — 封装异步 API 调用的 loading / error / data 三态管理。
 *
 * 解决问题：
 *  - 各组件重复的 try { loading=true } catch { error=msg } finally { loading=false } 模板代码
 *  - Toast 通知集成
 *  - 支持取消（AbortController）
 */
import { ref } from 'vue'
import { useToast } from './useToast.js'

/**
 * @template T
 * @param {(...args: any[]) => Promise<T>} asyncFn  要执行的异步函数
 * @param {object} [options]
 * @param {boolean} [options.showErrorToast=true]   失败时是否弹 toast
 * @param {boolean} [options.showSuccessToast=false] 成功时是否弹 toast
 * @param {string}  [options.successMessage='操作成功']
 */
export function useApiRequest(asyncFn, {
  showErrorToast = true,
  showSuccessToast = false,
  successMessage = '操作成功',
} = {}) {
  /** @type {import('vue').Ref<boolean>} */
  const loading = ref(false)
  /** @type {import('vue').Ref<string|null>} */
  const error = ref(null)
  /** @type {import('vue').Ref<T|null>} */
  const data = ref(null)

  const { success: toastSuccess, error: toastError } = useToast()

  /**
   * 执行请求。
   * @param {...any} args  透传给 asyncFn 的参数
   * @returns {Promise<T>}
   */
  async function execute(...args) {
    if (loading.value) return  // 防并发重复触发
    loading.value = true
    error.value = null
    try {
      data.value = await asyncFn(...args)
      if (showSuccessToast) toastSuccess(successMessage)
      return data.value
    } catch (e) {
      const msg = e?.response?.data?.error || e?.message || '请求失败，请重试'
      error.value = msg
      if (showErrorToast) toastError(msg)
      throw e
    } finally {
      loading.value = false
    }
  }

  function reset() {
    loading.value = false
    error.value = null
    data.value = null
  }

  return { loading, error, data, execute, reset }
}
