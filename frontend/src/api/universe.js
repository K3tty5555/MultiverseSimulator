import api from './index.js'

export const listUniverses = () => api.get('/universe')

/** 跨宇宙 NPC 总览（/agents 页用）：返回所有活跃宇宙及其活跃 agents */
export const listUniversesWithAgents = () => api.get('/universe/with-agents')

/** 角色跨宇宙时间轴：该 name+universe_type 参与过的所有节点 */
export const getAgentTimeline = (name, universeType) =>
  api.get('/universe/agent-timeline', { params: { name, type: universeType } })

/** 角色史实年表：LLM 生成并持久化的 canonical events */
export const listCanonicalEvents = (name, universeType, worldLabel = '') =>
  api.get('/universe/canonical/events', {
    params: { name, type: universeType, world_label: worldLabel || '' },
  })

export const generateCanonicalEvents = (data, signal) =>
  api.post('/universe/canonical/events/generate', data, { signal })

export const updateCanonicalEvent = (id, data) =>
  api.put(`/universe/canonical/events/${id}`, data)

export const deleteCanonicalEvent = (id) =>
  api.delete(`/universe/canonical/events/${id}`)

export const bulkDeleteCanonicalEvents = (data) =>
  api.post('/universe/canonical/events/bulk-delete', data)

export const createUniverse = (data) => api.post('/universe', data)

/** AI 生成新宇宙骨架 {title, premise, era_label}，同步返回 */
export const scaffoldUniverse = (data, signal) =>
  api.post('/universe/scaffold', data, { signal })

/** 设定/更新宇宙主角；首次设定触发 NPC 后台预生成 */
export const setUniverseProtagonist = (universeId, data) =>
  api.put(`/universe/${universeId}/protagonist`, data)

/** AI 辅助生成主角 {role, bio} */
export const assistProtagonist = (universeId, name, signal) =>
  api.post(`/universe/${universeId}/protagonist/assist`, { name }, { signal })

export const getUniverse = (id) => api.get(`/universe/${id}`)

export const archiveUniverse = (id) => api.delete(`/universe/${id}`)

export const getUniverseTree = (id) => api.get(`/universe/${id}/tree`)

export const getThread = (id, nodeId = null) => {
  const params = nodeId ? `?node_id=${nodeId}` : ''
  return api.get(`/universe/${id}/thread${params}`)
}

export const listAgents = (id) => api.get(`/universe/${id}/agents`)

export const addAgent = (id, data) => api.post(`/universe/${id}/agents`, data)

export const updateAgent = (universeId, agentId, data) =>
  api.put(`/universe/${universeId}/agents/${agentId}`, data)

export const deleteAgent = (universeId, agentId) =>
  api.delete(`/universe/${universeId}/agents/${agentId}`)

/** AI 辅助生成 NPC 档案（基于宇宙 premise + 主角）；传 signal 支持 AbortController */
export const assistAgent = (universeId, name, signal) =>
  api.post(`/universe/${universeId}/agents/assist`, { name }, { signal })

/** 重命名 NPC（保留 id/memory/last_node_id/agent_reactions 历史引用） */
export const renameAgent = (universeId, agentId, newName) =>
  api.post(`/universe/${universeId}/agents/rename`, { agent_id: agentId, new_name: newName })

export const switchPerspective = (id, perspective) =>
  api.put(`/universe/${id}/perspective`, { perspective })

/** 第一步：POST 行动到服务端获取 token */
export const prepareTurn = (universeId, data) =>
  api.post(`/universe/${universeId}/turn/prepare`, data)

/** 第二步：使用 token 建立 SSE 流（避免行动内容暴露在 URL 中） */
export const createTurnStream = (universeId, token) =>
  new EventSource(`/api/universe/${universeId}/turn/stream?token=${encodeURIComponent(token)}`)

/** 获取「我的宇宙」及时间线节点 */
export const getPersonalUniverse = () =>
  api.get('/universe/personal')

/** 完成引导初始化，创建根节点 */
export const initPersonalUniverse = (answers) =>
  api.post('/universe/personal/init', { answers })

/** 从历史角色快速创建平行宇宙（含 NPC 预生成，约 5-8 秒） */
export const createUniverseFromPersona = (data) =>
  api.post('/universe/from-persona', data)

/** 获取宇宙当前实体世界状态 */
export const getEntityStates = (id) => api.get(`/universe/${id}/entity_states`)

/** 获取世界列表（含 checkpoint 数量） */
export const listWorlds = () => api.get('/worlds')

/** 获取世界详情（含完整 checkpoints 及可选角色信息） */
export const getWorld = (id) => api.get(`/worlds/${id}`)

/** 从世界节点 + 角色名称创建宇宙 */
export const createUniverseFromCheckpoint = (data) =>
  api.post('/universe/from-checkpoint', data)

/** 删除节点及其所有后代 */
export const deleteNode = (universeId, nodeId) =>
  api.delete(`/universe/${universeId}/nodes/${nodeId}`)

/** 用最新档案重新生成「我的宇宙」根节点叙事（档案更新后同步） */
export const reinitPersonalUniverse = () =>
  api.post('/universe/personal/reinit')

/** 获取个人宇宙洞察数据（决策统计） */
export const getPersonalInsights = () =>
  api.get('/universe/personal/insights')

/** 获取内置角色列表（供角色长廊展示） */
export const listBuiltinPersonas = () => api.get('/worlds/personas')

export const createRetrospectStream = (universeId, nodeIds, perspective) => {
  const params = new URLSearchParams({
    node_ids: nodeIds.join(','),
    perspective,
  })
  return new EventSource(`/api/universe/${universeId}/retrospect/stream?${params}`)
}
