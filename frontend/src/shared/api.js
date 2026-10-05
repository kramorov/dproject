import axios from 'axios'
import { API_URL, API_PREFIX } from './config'
import { getLocale } from './i18n'

const api = axios.create({
  baseURL: `${API_URL}${API_PREFIX}`,
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

// CSRF-токен из cookie
function getCSRF() {
  const m = document.cookie.match(/csrftoken=([^;]+)/)
  return m ? m[1] : ''
}
api.interceptors.request.use(c => {
  const method = c.method?.toLowerCase()
  if (method === 'post' || method === 'put' || method === 'patch' || method === 'delete') {
    c.headers['X-CSRFToken'] = getCSRF()
  }
  // Локализация данных на бэкенде (Фаза 4)
  const l = getLocale()
  c.headers['Accept-Language'] = l === 'cn' ? 'zh-CN' : l
  return c
})

api.interceptors.response.use(r => r, error => {
  const msg = error.response?.data?.error || error.response?.data?.detail || error.message || 'Unknown error'
  return Promise.reject({ ...error, displayMessage: msg })
})

export default api
