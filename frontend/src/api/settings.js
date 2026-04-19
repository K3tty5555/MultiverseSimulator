import api from './index.js'

export const getSettings = () => api.get('/settings')
export const updateSettings = (data) => api.put('/settings', data)
export const testConnection = (data) => api.post('/settings/test', data)
