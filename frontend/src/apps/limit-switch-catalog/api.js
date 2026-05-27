// limit-switch-catalog/api.js
// API-клиент для блоков концевых выключателей. Использует общий @/shared/api и централизованные эндпоинты.
import api from '@/shared/api'
import { ENDPOINTS } from '@/shared/endpoints'

const E = ENDPOINTS.limitSwitch

export default {
  list(params)    { return api.get(E.catalog, { params }) },
  getDetail(id)   { return api.get(E.detail(id)) },
  getFilters()    { return api.get(E.filters) },
  getQuickSelect(mlId, filters = {}) {
    return api.get(E.quickselect, { params: { model_line_id: mlId, ...filters } })
  },
  getMeta()       { return api.get(E.meta) },
}
