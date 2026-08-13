import api from '@/shared/api'

const R = '/client_requests'

export default {
  // Заявки
  listRequests(params = {}) { return api.get(`${R}/requests/`, { params }) },
  getRequest(id) { return api.get(`${R}/requests/${id}/`) },
  createRequest(data) { return api.post(`${R}/requests/`, data) },
  updateRequest(id, data) { return api.patch(`${R}/requests/${id}/`, data) },
  deleteRequest(id) { return api.delete(`${R}/requests/${id}/`) },

  // Позиции
  listItems(params = {}) { return api.get(`${R}/items/`, { params }) },
  createItem(data) { return api.post(`${R}/items/`, data) },
  updateItem(id, data) { return api.patch(`${R}/items/${id}/`, data) },
  deleteItem(id) { return api.delete(`${R}/items/${id}/`) },

  // Типы подбора
  itemTypes() { return api.get(`${R}/item-types/`) },
}
