import api from './index.js'

// 仅保留读取端点。写入功能已废弃——角色通过「新建宇宙」流程产生，
// 主角存储在 parallel_universes.protagonist_* 字段，NPC 存储在 universe_agents 表。
export const listPersonas   = ()    => api.get('/persona')
export const getPersona     = (id)  => api.get(`/persona/${id}`)
export const getPersonaUniverses = (id) => api.get(`/persona/${id}/universes`)
