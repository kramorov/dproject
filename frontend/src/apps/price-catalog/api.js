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

  // Model lines (shared)
  getModelLines() { return api.get('/electric_actuators/constructor/model_lines/') },
  getModelLineItems(mlId) { return api.get(`/electric_actuators/constructor/model-lines/${mlId}/items/`) },
  getConstructorOptions(params) { return api.get('/electric_actuators/constructor/options/', { params }) },

  // EA Price Configurator
  getEaConfigOptions(psId) { return api.get(`${B}/ea-configurator/options/`, { params: { power_supply_id: psId } }) },
  getEaConfigDocs() { return api.get(`${B}/ea-configurator/documents/`) },
  getEaConfigDoc(id) { return api.get(`${B}/ea-configurator/documents/${id}/`) },
  createEaConfigDoc(data) { return api.post(`${B}/ea-configurator/create/`, data) },
  deleteEaConfigDoc(id) { return api.delete(`${B}/ea-configurator/documents/${id}/`) },
  postEaConfigDoc(id) { return api.post(`${B}/ea-configurator/documents/${id}/post/`) },
  unpostEaConfigDoc(id) { return api.post(`${B}/ea-configurator/documents/${id}/unpost/`) },
  exportEaConfigDoc(id) { return api.get(`${B}/ea-configurator/documents/${id}/export/`, { responseType: 'blob' }) },
  importEaConfigDoc(id, file) {
    const fd = new FormData()
    fd.append('file', file)
    return api.post(`${B}/ea-configurator/documents/${id}/import/`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  printEaConfigDoc(id) { return api.get(`${B}/ea-configurator/documents/${id}/print/`) },
}
