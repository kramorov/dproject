// src/apps/cert-docs/api.js
import api from '@/shared/api'

const BASE = '/admin/certs'

export default {
  create(data) { return api.post(`${BASE}/`, data) },
  update(id, data) { return api.put(`${BASE}/${id}/`, data) },
  patch(id, data) { return api.patch(`${BASE}/${id}/`, data) },
  remove(id) { return api.delete(`${BASE}/${id}/`) },
  copy(id) { return api.post(`${BASE}/${id}/copy/`) },
  list(params = {}) {
    return api.get('/core/', { params: { model: 'cert_doc.CertData', fmt: 'compact', ...params } })
  },
  filterOptions() {
    return api.get(`${BASE}/filters/`)
  },
  uploadMedia(formData) {
    return api.post(`${BASE}/upload-media/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}
