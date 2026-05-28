// src/apps/limit-switch-admin/api.js
// CRUD через UniversalAPIView /api/core/
import api from '@/shared/api'

const CORE = '/core/'

// ── Утилиты ──
function extractIds(arr) {
  if (!arr) return []
  return arr.map(v => (typeof v === 'object' ? v.id : v))
}

function listResponse(res) {
  const data = res.data?.data
  if (Array.isArray(data)) return data
  if (Array.isArray(res.data)) return res.data
  return []
}

// ── LimitSwitchModelLine (Серии БКВ) ──
export const modelLineApi = {
  list(params = {}) {
    return api.get(CORE, { params: { model: 'pa_controls.LimitSwitchModelLine', fmt: 'compact', ...params } })
  },
  get(id) {
    return api.get(CORE, { params: { model: 'pa_controls.LimitSwitchModelLine', id } })
  },
  create(data) {
    return api.post(CORE, { model: 'pa_controls.LimitSwitchModelLine', ...data })
  },
  update(id, data) {
    return api.put(CORE, { model: 'pa_controls.LimitSwitchModelLine', id, ...data })
  },
  remove(id) {
    return api.delete(CORE, { params: { model: 'pa_controls.LimitSwitchModelLine', id } })
  },
}

// ── LimitSwitchBox (Блоки БКВ) ──
export const limitSwitchApi = {
  list(params = {}) {
    return api.get(CORE, { params: { model: 'pa_controls.LimitSwitchBox', fmt: 'compact', ...params } })
  },
  get(id) {
    return api.get(CORE, { params: { model: 'pa_controls.LimitSwitchBox', id } })
  },
  create(data) {
    return api.post(CORE, { model: 'pa_controls.LimitSwitchBox', ...data })
  },
  update(id, data) {
    return api.put(CORE, { model: 'pa_controls.LimitSwitchBox', id, ...data })
  },
  remove(id) {
    return api.delete(CORE, { params: { model: 'pa_controls.LimitSwitchBox', id } })
  },
}

// ── Справочники (для FK/M2M select-ов) ──
function fetchAll(model, extraParams = {}) {
  return api.get(CORE, { params: { model, fmt: 'compact', limit: 500, ...extraParams } })
    .then(res => {
      const data = listResponse(res)
      return data.map(item => ({ id: item.id, name: item.name || item.code || String(item.id) }))
    })
    .catch(() => [])
}

export const refsApi = {
  async modelLines()     { return fetchAll('pa_controls.LimitSwitchModelLine') },
  async bodies()         { return fetchAll('pa_controls.LimitSwitchBody') },
  async sensorVarieties(){ return fetchAll('pa_controls.LimitSwitchSensorVariety') },
  async sensors()        { return fetchAll('pa_controls.SensorComponent') },
  async signalTypes()    { return fetchAll('pa_controls.SignalType') },
  async ipOptions()      { return fetchAll('params.IpOption') },
  async exdOptions()     { return fetchAll('params.ExdOption') },
  async bodyMaterials()  { return fetchAll('materials.MaterialGeneral') },
  async specifiedMaterials() { return fetchAll('materials.MaterialSpecified') },
  async producers()      { return fetchAll('producers.Producer') },
  async brands()         { return fetchAll('producers.Brands') },
  async equipmentTypes() { return fetchAll('core.EquipmentType') },
  async certVarieties()  { return fetchAll('cert_doc.CertVariety') },
}

export { extractIds, listResponse }