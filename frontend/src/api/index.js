import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' }
})

// 每次请求动态读取语言设置，而非在模块加载时固定
api.interceptors.request.use(config => {
  config.headers['Accept-Language'] = localStorage.getItem('locale') || 'zh'
  return config
})

api.interceptors.response.use(
  response => response.data,
  error => {
    const message = error.response?.data?.error || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

export default api
