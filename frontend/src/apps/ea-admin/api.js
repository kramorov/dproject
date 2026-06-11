import api from '@/shared/api'
import { ENDPOINTS } from '@/shared/endpoints'

const B = ENDPOINTS.eaAdmin

export default {
  /** GET матрица: модели × напряжения */
  async getMatrix(modelLineId) {
    const r = await api.get(B.matrix, { params: { model_line_id: modelLineId } })
    return r.data
  },
  /** POST сохранить матрицу */
  async saveMatrix(payload) {
    const r = await api.post(B.matrix, payload)
    return r.data
  },
  /** Список серий */
  async getModelLines() {
    const r = await api.get(ENDPOINTS.eaConstructor.modelLines)
    return r.data
  },
  /** Экспорт в Excel — скачать Blob */
  async exportMatrix(modelLineId) {
    const r = await api.get(B.exportMatrix, {
      params: { model_line_id: modelLineId },
      responseType: 'blob',
    })
    return r.data
  },
  /** GET: список моделей с ControlUnit + SafetyPosition */
  async getControlUnits(modelLineId, powerSupplyId) {
    const r = await api.get(B.copyControlUnits, {
      params: { model_line_id: modelLineId, power_supply_id: powerSupplyId },
    })
    return r.data
  },
  /** PATCH: обновить CU/SP для одной модели (источник) */
  async updateSourceOptions(mliId, powerSupplyId, controlUnits, safetyPositions) {
    const r = await api.patch(B.copyControlUnits, {
      model_line_item_id: mliId,
      power_supply_id: powerSupplyId,
      control_units: controlUnits,
      safety_positions: safetyPositions,
    })
    return r.data
  },
  /** POST: копировать опции от модели к моделям */
  async copyControlUnits(sourceMliId, targetMliIds, powerSupplyId) {
    const r = await api.post(B.copyControlUnits, {
      source_mli_id: sourceMliId,
      target_mli_ids: targetMliIds,
      power_supply_id: powerSupplyId,
    })
    return r.data
  },
  /** Импорт из Excel */
  async importMatrix(modelLineId, file) {
    const formData = new FormData()
    formData.append('model_line_id', modelLineId)
    formData.append('file', file)
    const r = await api.post(B.importMatrix, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return r.data
  },
}
