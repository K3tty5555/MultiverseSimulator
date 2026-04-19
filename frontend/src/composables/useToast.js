import { ref } from 'vue'

const toasts = ref([])
let _id = 0

export function useToast() {
  function show(message, type = 'info', duration = 2500) {
    const id = ++_id
    toasts.value.push({ id, message, type })
    setTimeout(() => {
      toasts.value = toasts.value.filter(t => t.id !== id)
    }, duration)
  }

  return {
    toasts,
    success: (msg) => show(msg, 'success'),
    error: (msg) => show(msg, 'error', 4000),
    info: (msg) => show(msg, 'info'),
  }
}
