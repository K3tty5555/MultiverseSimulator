import { ref, watch, onBeforeUnmount } from 'vue'
import { getUniverse } from '../api/universe.js'

/**
 * 轮询 parallel_universes.npc_ready 字段直到 NPC 预生成完成。
 *
 * 机制：
 * - 进入宇宙时若 npc_ready === 0 启动 2s 轮询
 * - 拿到 npc_ready === 1 停止轮询、把新的 agents 回写到 universeRef
 * - 最长等 60s（30 次）兜底，避免后台任务卡死时前端永远骨架态
 * - 切 universe 或组件卸载时自动清理
 */
export function useNpcReady(universeRef, { intervalMs = 2000, maxAttempts = 30 } = {}) {
  // 遵循三态约定：null=未知，true=就绪，false=生成中
  const npcReady = ref(null)
  let timerId = null
  let attempts = 0
  // 版本号：每次新的 start() 递增，防止旧的 in-flight pollOnce 覆盖新数据
  let generation = 0

  function stop() {
    if (timerId !== null) {
      clearInterval(timerId)
      timerId = null
    }
  }

  async function pollOnce(universeId, gen) {
    attempts += 1
    try {
      const res = await getUniverse(universeId)
      if (gen !== generation) return   // 已被新一轮取代，丢弃
      if (res.universe?.npc_ready === 1) {
        universeRef.value = res.universe
        npcReady.value = true
        stop()
        return
      }
    } catch {
      if (gen !== generation) return
    }
    if (attempts >= maxAttempts) {
      npcReady.value = true
      stop()
    }
  }

  function start(universeId) {
    stop()
    attempts = 0
    generation += 1
    const gen = generation
    const current = universeRef.value?.npc_ready
    if (current === 1 || current == null) {
      // 已就绪 / 老数据没字段 / universe 尚未加载：直接视为 ready，不轮询
      npcReady.value = true
      return
    }
    npcReady.value = false
    timerId = setInterval(() => pollOnce(universeId, gen), intervalMs)
  }

  // 唯一的启动路径：watch universe.id 变化，immediate 捕获首次加载
  watch(
    () => universeRef.value?.id,
    (newId) => {
      if (newId != null) start(newId)
      else stop()
    },
    { immediate: true }
  )

  onBeforeUnmount(() => { generation += 1; stop() })

  return { npcReady, stop }
}
