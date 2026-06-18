import api from '@/shared/api'
import { ENDPOINTS } from '@/shared/endpoints'

const B = ENDPOINTS.eaModelAdmin

export default {
  async getModelLines() {
    const r = await api.get(B.modelLines)
    return r.data
  },
  async getItems(modelLineId) {
    const r = await api.get(B.items, { params: { model_line_id: modelLineId } })
    return r.data
  },
  async getItem(id) {
    const r = await api.get(B.itemDetail(id))
    return r.data
  },
  async saveItem(id, payload) {
    const r = await api.put(B.itemDetail(id), payload)
    return r.data
  },
  async getWirings() {
    const r = await api.get(B.wirings)
    return r.data
  },
}
