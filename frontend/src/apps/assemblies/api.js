import api from '@/shared/api'

const B = '/configurator/assemblies'

export default {
  list(params = {}) { return api.get(`${B}/`, { params }) },
  get(id) { return api.get(`${B}/${id}/`) },
  create(data) { return api.post(`${B}/`, data) },
  update(id, data) { return api.patch(`${B}/${id}/`, data) },
  expand(id) { return api.post(`${B}/${id}/expand/`) },
  fork(id, data = {}) { return api.post(`${B}/${id}/fork/`, data) },
  fixate(id, data = {}) { return api.post(`${B}/${id}/fixate/`, data) },
  bom(id) { return api.get(`${B}/${id}/bom/`) },

  // Компоненты
  updateComponent(id, data) { return api.patch(`/configurator/components/${id}/requirements/`, data) },
  filterComponent(id) { return api.post(`/configurator/components/${id}/filter/`) },

  // Справочники
  compositionGroups() { return api.get('/ai-assistant/composition-groups/') },
}
