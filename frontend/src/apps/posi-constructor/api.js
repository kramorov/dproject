// posi-constructor/api.js
import api from '@/shared/api'
import { ENDPOINTS } from '@/shared/endpoints'

const E = ENDPOINTS.posiConstructor

export default {
  // CRUD
  list(params)           { return api.get(E.list, { params }) },
  getDetail(id)          { return api.get(E.detail(id)) },
  create(data)           { return api.post(E.list, data) },
  update(id, data)       { return api.put(E.detail(id), data) },
  delete(id)             { return api.delete(E.detail(id)) },

  // Каскад: тип → серия → опции
  getActingTypes()       { return api.get(E.actingTypes) },
  getModelLines(params)  { return api.get(E.modelLines, { params }) },
  getOptions(mlId)       { return api.get(E.options, { params: { model_line: mlId } }) },

  // Превью без сохранения
  preview(data)          { return api.post(E.preview, data) },
}
