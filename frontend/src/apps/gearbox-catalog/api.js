// src/apps/gearbox-catalog/api.js
import api from '@/shared/api'

const B = '/gearbox'

export default {
  // Каталог
  list(params = {}) { return api.get(`${B}/catalog/`, { params }) },
  getDetail(id) { return api.get(`${B}/catalog/${id}/`) },
  getFilters() { return api.get(`${B}/filters/`) },

  // Цены — через существующий снэпшот
  getPrices(skuCodes) {
    return api.get('/admin/prices/snapshot/', {
      params: { code: skuCodes.join(',') }
    })
  },
}
