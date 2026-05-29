// filter-regulator-catalog/api.js
// API-клиент для фильтр-регуляторов. Использует общий @/shared/api и централизованные эндпоинты.
import api from '@/shared/api'
import { ENDPOINTS } from '@/shared/endpoints'

const E = ENDPOINTS.filterRegulator
const A = ENDPOINTS.admin

export default {
  list(params)    { return api.get(E.catalog, { params }) },
  getDetail(id)   { return api.get(E.detail(id)) },
  getFilters(params) { return api.get(E.filters, { params }) },
  getQuickSelect(mlId, filters = {}) {
    return api.get(E.quickselect, { params: { model_line_id: mlId, ...filters } })
  },
  getMeta()       { return api.get(E.meta) },
  getPrices(codes) { return api.get(A.pricesSnapshot, { params: { code: codes.join(',') } }) },
}
