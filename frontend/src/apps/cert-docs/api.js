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

  // === Медиатека: поиск существующих файлов ===
  async searchMedia({ query = '', equipment_type_id = null, brand_id = null } = {}) {
    // Ищем CERTIFICATE категорию
    const catRes = await api.get('/core/', {
      params: { model: 'media_library.MediaCategory', code: 'CERTIFICATE' },
    })
    const cat = Array.isArray(catRes.data?.data) ? catRes.data.data[0] : null
    const params = { model: 'media_library.MediaLibraryItem', fmt: 'compact' }
    if (cat) params.category_id = cat.id
    if (equipment_type_id) params.equipment_type_id = equipment_type_id
    if (brand_id) params.brand_id = brand_id
    if (query) params.keywords__icontains = query
    const res = await api.get('/core/', { params })
    return Array.isArray(res.data?.data) ? res.data.data : []
  },

  // === Замена файла в существующем media_item ===
  replaceMediaFile(mediaId, formData) {
    return api.patch(`/admin/media/${mediaId}/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}
