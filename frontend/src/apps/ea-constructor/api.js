// ea-constructor/api.js
import api from '@/shared/api'
import { ENDPOINTS } from '@/shared/endpoints'

const E = ENDPOINTS.eaConstructor

export default {
  // CRUD
  list(params)           { return api.get(E.list, { params }) },
  getDetail(id)          { return api.get(E.detail(id)) },
  create(data)           { return api.post(E.list, data) },
  update(id, data)       { return api.put(E.detail(id), data) },
  delete(id)             { return api.delete(E.detail(id)) },

  // Options & preview
  getOptions(mliId, psId) {
    const params = { model_line_item_id: mliId }
    if (psId) params.power_supply_id = psId
    return api.get(E.options, { params })
  },
  preview(data)          { return api.post(E.preview, data) },

  // Cascading selects
  getModelLines()        { return api.get(E.modelLines) },
  getModelLineItems(mlId){ return api.get(E.modelLineItems(mlId)) },
}
