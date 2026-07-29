// pa-catalog/api.js
import api from '@/shared/api'
import { ENDPOINTS } from '@/shared/endpoints'

const E = ENDPOINTS.paCatalog

export default {
  // Model lines (series)
  getModelLines() { return api.get(E.modelLines) },
  // Model line items (body+variety)
  getModelLineItems(mlId, variety) {
    const params = {}
    if (variety) params.variety = variety
    return api.get(E.modelLineItems(mlId), { params })
  },
  // Available options for a model_line_item
  getOptions(mliId) { return api.get(E.options, { params: { model_line_item_id: mliId } }) },
  // Preview code/description from options
  preview(payload) { return api.post(E.preview, payload) },
  // Search (selector)
  search(payload) { return api.post(E.search, payload) },
  // Create SKU (add to cart)
  createSku(payload) { return api.post(E.createSku, payload) },
  // Initial data (pressures, etc.)
  getInitialData() { return api.get('/pneumatic_actuators/selector/initial-data/') },
}
