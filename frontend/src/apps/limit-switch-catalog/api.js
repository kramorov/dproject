// limit-switch-catalog/api.js
import axios from 'axios'

const BASE = '/api/pa-controls'

export default {
  list(params) { return axios.get(`${BASE}/catalog/`, { params }) },
  getDetail(id) { return axios.get(`${BASE}/catalog/${id}/`) },
  getFilters() { return axios.get(`${BASE}/filters/`) },
  getMeta() { return axios.get(`${BASE}/meta/`) },
}
