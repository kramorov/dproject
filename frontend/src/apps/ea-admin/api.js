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
  /** Импорт из Excel */
  async importMatrix(modelLineId, file) {
    const formData = new FormData()
    formData.append('model_line_id', modelLineId)
    formData.append('file', file)
    const r = await api.post(B.importMatrix, formData)
    return r.data
  },
}
