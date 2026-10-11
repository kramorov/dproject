// pa-catalog-browse/api.js
// API-клиент каталога готовых артикулов пневмоприводов (браузинг сгенерированных
// карточек PneumaticActuatorCatalogItem по общему паттерну каталога).
import api from '@/shared/api'
import { ENDPOINTS } from '@/shared/endpoints'

const E = ENDPOINTS.paCatalog

export default {
  // Список карточек (пагинированный контракт {data, total, ...})
  list(params) { return api.get(E.items, { params }) },
  // Деталка карточки
  getDetail(id) { return api.get(E.itemDetail(id)) },
  // Серии (CatalogSection)
  getSections(params = {}) { return api.get(E.modelLines, { params }) },
  // Опции фильтров сайдбара серии (?model_line_id=)
  getFilters(params = {}) { return api.get(E.filters, { params }) },
  // Инженерный подбор: все карточки + фильтры
  getEngineer(params) { return api.get(E.items, { params }) },
  getEngineerFilters(params = {}) { return api.get(E.filters, { params }) },
}
