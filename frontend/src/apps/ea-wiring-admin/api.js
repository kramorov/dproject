import api from '@/shared/api'
import { ENDPOINTS } from '@/shared/endpoints'

const B = {
  list: '/electric_actuators/admin/wirings/',
  detail: (id) => `/electric_actuators/admin/wirings/${id}/`,
}

export default {
  async list() {
    const r = await api.get(B.list)
    return r.data
  },
  async get(id) {
    const r = await api.get(B.detail(id))
    return r.data
  },
  async create(payload) {
    const r = await api.post(B.list, payload)
    return r.data
  },
  async update(id, payload) {
    const r = await api.put(B.detail(id), payload)
    return r.data
  },
  async remove(id) {
    const r = await api.delete(B.detail(id))
    return r.data
  },
  async copy(id) {
    const r = await api.post(B.detail(id))
    return r.data
  },
  async getModelLines() {
    const r = await api.get(ENDPOINTS.eaConstructor.modelLines)
    return r.data
  },
}
