// src/apps/media-library/api.js
import api from '@/shared/api'

const BASE = '/admin/media'

export default {
  upload(formData) {
    return api.post(`${BASE}/upload/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  update(id, data) { return api.put(`${BASE}/${id}/`, data) },
  patch(id, data) { return api.patch(`${BASE}/${id}/`, data) },
  replaceFile(id, formData) {
    return api.patch(`${BASE}/${id}/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  remove(id, force = false) {
    const params = force ? { force: 'true' } : {}
    return api.delete(`${BASE}/${id}/`, { params })
  },
  copy(id) { return api.post(`${BASE}/${id}/copy/`) },
  recreatePreview(id) { return api.post(`${BASE}/${id}/recreate-preview/`) },
  getVariants(id) { return api.get(`${BASE}/${id}/variants/`) },
  regenerateVariants(id, formData) {
    return api.post(`${BASE}/${id}/regenerate-variants/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  list(params = {}) {
    return api.get('/core/', { params: { model: 'media_library.MediaLibraryItem', fmt: 'compact', ...params } })
  },
  detail(id) {
    return api.get('/core/', { params: { model: 'media_library.MediaLibraryItem', id } })
  },
  filterOptions(scope = 'used') {
    return api.get(`${BASE}/filters/`, { params: { scope } })
  },
  previewUrl(id) { return `/api/media/${id}/view/` },
  downloadUrl(id) { return `/api/media/${id}/download/` },
}