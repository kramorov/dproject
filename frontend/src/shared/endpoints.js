// shared/endpoints.js
// Единый источник URL API для всех каталогов.
// Используется с @/shared/api, который уже содержит baseURL (API_URL + API_PREFIX).
// Все пути — БЕЗ префикса /api, т.к. baseURL его добавляет.

export const ENDPOINTS = {
  gearbox: {
    catalog: '/gearbox/catalog/',
    detail: (id) => `/gearbox/catalog/${id}/`,
    filters: '/gearbox/filters/',
    engineer: '/gearbox/engineer/',
    engineerFilters: '/gearbox/engineer/filters/',
    quickselect: '/gearbox/quickselect/',
  },

  filterRegulator: {
    catalog: '/filter-regulator/catalog/',
    detail: (id) => `/filter-regulator/catalog/${id}/`,
    filters: '/filter-regulator/filters/',
    engineer: '/filter-regulator/engineer/',
    engineerFilters: '/filter-regulator/engineer/filters/',
    quickselect: '/filter-regulator/quickselect/',
    meta: '/filter-regulator/meta/',
  },

  solenoidValves: {
    catalog: '/solenoid-valves/catalog/',
    detail: (id) => `/solenoid-valves/catalog/${id}/`,
    filters: '/solenoid-valves/filters/',
    engineer: '/solenoid-valves/engineer/',
    engineerFilters: '/solenoid-valves/engineer/filters/',
    quickselect: '/solenoid-valves/quickselect/',
    meta: '/solenoid-valves/meta/',
  },

  pneumaticFittings: {
    catalog: '/pneumatic-fittings/catalog/',
    detail: (id) => `/pneumatic-fittings/catalog/${id}/`,
    filters: '/pneumatic-fittings/filters/',
    engineer: '/pneumatic-fittings/engineer/',
    engineerFilters: '/pneumatic-fittings/engineer/filters/',
    quickselect: '/pneumatic-fittings/quickselect/',
    meta: '/pneumatic-fittings/meta/',
  },

  limitSwitch: {
    sections: '/pa-controls/sections/',
    catalog: '/pa-controls/catalog/',
    detail: (id) => `/pa-controls/catalog/${id}/`,
    filters: '/pa-controls/filters/',
    engineer: '/pa-controls/engineer/',
    engineerFilters: '/pa-controls/engineer/filters/',
    quickselect: '/pa-controls/quickselect/',
    meta: '/pa-controls/meta/',
  },

  admin: {
    pricesSnapshot: '/admin/prices/snapshot/',
  },

  paConstructor: {
    list: '/pneumatic_actuators/constructor/',
    detail: (id) => `/pneumatic_actuators/constructor/${id}/`,
    options: '/pneumatic_actuators/constructor/options/',
    preview: '/pneumatic_actuators/constructor/preview/',
    modelLines: '/pneumatic_actuators/constructor/model_lines/',
    modelLineItems: (mlId, variety) => {
      let url = `/pneumatic_actuators/constructor/model-lines/${mlId}/items/`
      if (variety) url += `?variety=${variety}`
      return url
    },
  },

  eaConstructor: {
    list: '/electric_actuators/constructor/',
    detail: (id) => `/electric_actuators/constructor/${id}/`,
    options: '/electric_actuators/constructor/options/',
    preview: '/electric_actuators/constructor/preview/',
    modelLines: '/electric_actuators/constructor/model_lines/',
    modelLineItems: (mlId) => `/electric_actuators/constructor/model-lines/${mlId}/items/`,
  },
}