// shared/endpoints.js
// Единый источник URL API для всех каталогов.
// Используется с @/shared/api, который уже содержит baseURL (API_URL + API_PREFIX).
// Все пути — БЕЗ префикса /api, т.к. baseURL его добавляет.

export const ENDPOINTS = {
  gearbox: {
    catalog: '/gearbox/catalog/',
    detail: (id) => `/gearbox/catalog/${id}/`,
    filters: '/gearbox/filters/',
    quickselect: '/gearbox/quickselect/',
  },

  filterRegulator: {
    catalog: '/filter-regulator/catalog/',
    detail: (id) => `/filter-regulator/catalog/${id}/`,
    filters: '/filter-regulator/filters/',
    quickselect: '/filter-regulator/quickselect/',
    meta: '/filter-regulator/meta/',
  },

  limitSwitch: {
    catalog: '/pa-controls/catalog/',
    detail: (id) => `/pa-controls/catalog/${id}/`,
    filters: '/pa-controls/filters/',
    quickselect: '/pa-controls/quickselect/',
    meta: '/pa-controls/meta/',
  },

  admin: {
    pricesSnapshot: '/admin/prices/snapshot/',
  },
}
