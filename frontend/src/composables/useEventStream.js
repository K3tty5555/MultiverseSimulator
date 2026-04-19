/**
 * useEventStream — 封装 EventSource 生命周期管理。
 *
 * 解决问题：
 *  - 组件卸载时未关闭 EventSource 导致内存/连接泄漏
 *  - 超时检测：N 秒无消息自动关闭并触发 onError
 *  - 统一连接状态（idle / connecting / connected / reconnecting / failed）
 */
import { ref, onBeforeUnmount } from 'vue'

/**
 * @typedef {'idle'|'connecting'|'connected'|'reconnecting'|'failed'} StreamStatus
 */

export function useEventStream() {
  /** @type {import('vue').Ref<EventSource|null>} */
  const es = ref(null)
  /** @type {import('vue').Ref<StreamStatus>} */
  const status = ref('idle')

  let _timeoutId = null

  /**
   * 打开 SSE 连接。
   *
   * @param {string} url
   * @param {object} options
   * @param {(data: any) => void} options.onMessage  收到消息回调（自动 JSON.parse）
   * @param {(err: Error) => void} [options.onError]  连接失败 / 超时回调
   * @param {number} [options.timeout=45000]          无消息超时毫秒数
   */
  function open(url, { onMessage, onError, timeout = 45000 } = {}) {
    close()
    status.value = 'connecting'

    const source = new EventSource(url)
    es.value = source

    source.onopen = () => {
      status.value = 'connected'
      _resetTimeout(timeout, onError)
    }

    source.onmessage = (e) => {
      _resetTimeout(timeout, onError)
      try {
        onMessage?.(JSON.parse(e.data))
      } catch {
        onMessage?.(e.data)
      }
    }

    source.onerror = () => {
      if (source.readyState === EventSource.CONNECTING) {
        status.value = 'reconnecting'
        return
      }
      // readyState === CLOSED
      status.value = 'failed'
      _clearTimeout()
      onError?.(new Error('SSE 连接失败'))
      close()
    }
  }

  function _resetTimeout(ms, onError) {
    _clearTimeout()
    _timeoutId = setTimeout(() => {
      status.value = 'failed'
      onError?.(new Error('SSE 超时：等待响应超过 ' + Math.round(ms / 1000) + 's'))
      close()
    }, ms)
  }

  function _clearTimeout() {
    if (_timeoutId !== null) {
      clearTimeout(_timeoutId)
      _timeoutId = null
    }
  }

  function close() {
    _clearTimeout()
    if (es.value) {
      es.value.close()
      es.value = null
    }
    status.value = 'idle'
  }

  // 组件卸载时自动关闭，防止泄漏
  onBeforeUnmount(close)

  return { open, close, status }
}
