// src/shared/api.js
import axios from 'axios'
import { API_URL, API_PREFIX } from './config'

const api = axios.create({
  baseURL: `${API_URL}${API_PREFIX}`,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (r) => r,
  (error) => {
    const msg = error.response?.data?.error
      || error.response?.data?.detail
      || error.message
      || 'Unknown error'
    return Promise.reject({ ...error, displayMessage: msg })
  },
)

export default api
