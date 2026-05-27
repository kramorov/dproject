import axios from 'axios'
import { API_URL, API_PREFIX } from './config'

const api = axios.create({
  baseURL: `${API_URL}${API_PREFIX}`,
  timeout: 15000,
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
  return c
})

api.interceptors.response.use(r => r, error => {
  const msg = error.response?.data?.error || error.response?.data?.detail || error.message || 'Unknown error'
  return Promise.reject({ ...error, displayMessage: msg })
})

export default api
