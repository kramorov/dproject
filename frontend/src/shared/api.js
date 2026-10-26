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
  const data = error.response?.data
  let msg = null
  if (typeof data?.error === 'string') msg = data.error
  else if (typeof data?.detail === 'string') msg = data.detail
  if (!msg && data && typeof data === 'object') {
    // DRF-ошибки полей вида {code: ['...'], section: ['...']} — собрать в строку
    const parts = []
    for (const [k, v] of Object.entries(data)) {
      if (Array.isArray(v)) parts.push(`${k}: ${v.join('; ')}`)
      else if (typeof v === 'string') parts.push(`${k}: ${v}`)
      else if (v && typeof v === 'object') {
        for (const [k2, v2] of Object.entries(v)) {
          const val = Array.isArray(v2) ? v2.join('; ') : String(v2)
          parts.push(`${k}.${k2}: ${val}`)
        }
      }
    }
    msg = parts.join('; ')
  }
  if (!msg) msg = error.message || 'Unknown error'
  return Promise.reject({ ...error, displayMessage: msg })
})

export default api
