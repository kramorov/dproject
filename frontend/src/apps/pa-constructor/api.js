// pa-constructor/api.js
import api from '@/shared/api'
import { ENDPOINTS } from '@/shared/endpoints'

const E = ENDPOINTS.paConstructor

export default {
  create(data)           { return api.post(E.list, data) },

  // Options & preview
  getOptions(mliId)      { return api.get(E.options, { params: { model_line_item_id: mliId } }) },
  preview(data)          { return api.post(E.preview, data) },
  createSku(data)        { return api.post(E.createSku, data) },

  // Cascading selects
  getModelLines()        { return api.get(E.modelLines) },
  getModelLineItems(mlId, variety){ return api.get(E.modelLineItems(mlId, variety)) },
}
