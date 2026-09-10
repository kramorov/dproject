// cg-constructor/api.js
import api from '@/shared/api'
import { ENDPOINTS } from '@/shared/endpoints'

const E = ENDPOINTS.cgConstructor

export default {
  // CRUD
  list(params)            { return api.get(E.list, { params }) },
  getDetail(id)           { return api.get(E.detail(id)) },
  create(data)            { return api.post(E.list, data) },
  update(id, data)        { return api.put(E.detail(id), data) },
  delete(id)              { return api.delete(E.detail(id)) },

  // Каскад: серия → модель → опции
  getModelLines()         { return api.get(E.modelLines) },
  getModelLineItems(mlId) { return api.get(E.modelLineItems(mlId)) },
  getOptions(params)      { return api.get(E.options, { params }) },

  // Превью без сохранения
  preview(data)           { return api.post(E.preview, data) },
}
