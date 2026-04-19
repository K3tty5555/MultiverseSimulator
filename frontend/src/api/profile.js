import api from './index.js'

export const getProfile = () => api.get('/profile')

export const saveProfile = (data) => api.post('/profile', data)

export const updateProfile = (data) => api.put('/profile', data)

export const autoImportClaude = () => api.post('/profile/auto-import')

export const getImportTask = (taskId) => api.get(`/profile/task/${taskId}`)

export const uploadFiles = (formData) => api.post('/profile/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})

export const deleteFile = (fileId) => api.delete(`/profile/files/${fileId}`)

export const synthesizeProfile = () => api.post('/profile/synthesize')

export const getProfileVersions = () => api.get('/profile/versions')

export const getProfileVersion = (versionId) => api.get(`/profile/versions/${versionId}`)
