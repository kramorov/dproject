// src/apps/price-catalog/api.js
import api from '@/shared/api'
const B = '/admin/prices'

export default {
  // Каталог цен
  listPrices(params = {}) { return api.get(`${B}/`, { params }) },
  filterOptions() { return api.get(`${B}/filters/`) },

  // Срез цен
  getSnapshot(params = {}) { return api.get(`${B}/snapshot/`, { params }) },

  // Документы
  listDocuments(params = {}) { return api.get(`${B}/documents/`, { params }) },
  createDocument(data) { return api.post(`${B}/documents/`, data) },
  getDocument(id) { return api.get(`${B}/documents/${id}/`) },
  updateDocument(id, data) { return api.put(`${B}/documents/${id}/`, data) },
  deleteDocument(id) { return api.delete(`${B}/documents/${id}/`) },
  applyDocument(id) { return api.post(`${B}/documents/${id}/apply/`) },
  unapplyDocument(id) { return api.post(`${B}/documents/${id}/unapply/`) },

  // Строки документа
  getItems(docId) { return api.get(`${B}/documents/${docId}/items/`) },
  addItem(docId, data) { return api.post(`${B}/documents/${docId}/items/`, data) },
  deleteItem(docId, itemId) { return api.delete(`${B}/documents/${docId}/items/?id=${itemId}`) },

  // Excel export/import
  exportDocument(id) { return api.get(`${B}/documents/${id}/export/`, { responseType: 'blob' }) },
  importDocument(id, file) {
    const fd = new FormData()
    fd.append('file', file)
    return api.post(`${B}/documents/${id}/import/`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
}
