import api from '@/shared/api'
import { ENDPOINTS } from '@/shared/endpoints'

export default {
  async getSwitchesData(modelLineId) {
    const r = await api.get(ENDPOINTS.eaAdmin.copySwitches, {
      params: { model_line_id: modelLineId },
    })
    return r.data
  },
  async copySwitches(sourceMliId, targetMliIds) {
    const r = await api.post(ENDPOINTS.eaAdmin.copySwitches, {
      source_mli_id: sourceMliId,
      target_mli_ids: targetMliIds,
    })
    return r.data
  },
  async updateSwitches(mliId, waySwitches, endSwitches, torqueSwitches) {
    const r = await api.patch(ENDPOINTS.eaAdmin.copySwitches, {
      model_line_item_id: mliId,
      way_switches: waySwitches,
      end_switches: endSwitches,
      torque_switches: torqueSwitches,
    })
    return r.data
  },
  async getModelLines() {
    const r = await api.get(ENDPOINTS.eaConstructor.modelLines)
    return r.data
  },
}
