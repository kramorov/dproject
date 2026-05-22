// src/apps/sku-admin/api.js
import api from '@/shared/api'
const B = '/admin/sku'

export default {
  list(params = {}) { return api.get(`${B}/`, { params }) },
  batchUpdate(data) { return api.post(`${B}/batch/`, data) },

  // Через UniversalAPIView для CRUD
  get(id) { return api.get('/core/', { params: { model: 'sku.SKU', id, fmt: 'compact' } }) },
  create(data) { return api.post('/core/', { model: 'sku.SKU', ...data }) },
  update(id, data) { return api.put('/core/', { model: 'sku.SKU', id, ...data }) },
  delete(id) { return api.delete('/core/', { params: { model: 'sku.SKU', id } }) },
}
