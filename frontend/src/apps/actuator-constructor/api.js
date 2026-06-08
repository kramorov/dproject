// actuator-constructor/api.js
import api from '@/shared/api'
import { ENDPOINTS } from '@/shared/endpoints'

const E = ENDPOINTS.actuatorConstructor

export default {
  // CRUD
  list(params)           { return api.get(E.list, { params }) },
  getDetail(id)          { return api.get(E.detail(id)) },
  create(data)           { return api.post(E.list, data) },
  update(id, data)       { return api.put(E.detail(id), data) },
  delete(id)             { return api.delete(E.detail(id)) },

  // Options & preview
  getOptions(mliId)      { return api.get(E.options, { params: { model_line_item_id: mliId } }) },
  preview(data)          { return api.post(E.preview, data) },

  // Cascading selects
  getModelLines()        { return api.get(E.modelLines) },
  getModelLineItems(mlId, variety){ return api.get(E.modelLineItems(mlId, variety)) },
}
