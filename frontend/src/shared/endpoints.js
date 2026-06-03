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
}