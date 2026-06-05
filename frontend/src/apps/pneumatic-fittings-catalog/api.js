// pneumatic-fittings-catalog/api.js
// API-клиент для пневматических фитингов.
import api from '@/shared/api'
import { ENDPOINTS } from '@/shared/endpoints'

const E = ENDPOINTS.pneumaticFittings

export default {
  list(params)   { return api.get(E.catalog, { params }) },
  getDetail(id)  { return api.get(E.detail(id)) },
  getFilters(params) { return api.get(E.filters, { params }) },
  getEngineer(params) { return api.get(E.engineer, { params }) },
  getEngineerFilters(params) { return api.get(E.engineerFilters, { params }) },
  getQuickSelect(mlId, filters = {}) {
    return api.get(E.quickselect, { params: { model_line_id: mlId, ...filters } })
  },
  getMeta()      { return api.get(E.meta) },
}
