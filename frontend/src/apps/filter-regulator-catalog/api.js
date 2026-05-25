// filter-regulator-catalog/api.js
// API-клиент для фильтр-регуляторов.
// Все URL как у gearbox, только модель другая.
import axios from 'axios'

const BASE = '/api/filter-regulator'

export default {
  list(params) { return axios.get(`${BASE}/catalog/`, { params }) },
  getDetail(id) { return axios.get(`${BASE}/catalog/${id}/`) },
  getFilters() { return axios.get(`${BASE}/filters/`) },
  getEngineer(mlId, filters = {}) {
    return axios.get(`${BASE}/engineer/`, { params: { model_line_id: mlId, ...filters } })
  },
  getMeta() { return axios.get(`${BASE}/meta/`) },
  getPrices(codes) { return axios.get(`/api/admin/prices/snapshot/`, { params: { codes: codes.join(',') } }) },
}
