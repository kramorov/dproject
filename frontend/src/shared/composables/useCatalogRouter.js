// shared/composables/useCatalogRouter.js
// Универсальный composable для App.vue каталогов.
// Управляет: текущая страница (section/list/detail/brand/engineer), навигация, предзагрузка фильтров.

import { ref, reactive, onMounted } from 'vue'

/**
 * @param {Object}   api           API-модуль каталога
 * @param {Object}   [opts]
 * @param {string}   [opts.initialPage='section']
 * @param {Object}   [opts.hashMap]  Карта hash → page (напр. { '#engineer': 'engineer' })
 * @param {string}   [opts.idProp='brandId']  Название параметра для Brand-страницы ('brandId' | 'modelLineId')
 * @param {boolean}  [opts.preloadFilters=true]
 */
export function useCatalogRouter(api, opts = {}) {
  const {
    initialPage = 'section',
    hashMap = {},
    idProp = 'brandId',
    preloadFilters = true,
  } = opts

  const page = ref(initialPage)
  const selectedId = ref(null)
  const idValue = ref(null) // значение для brandId/modelLineId
  const filters = reactive({ loaded: false, data: {} })

  function goToList() { page.value = 'list' }
  function goToBrand(id) { idValue.value = id; page.value = 'brand' }
  function goToEngineer() { page.value = 'engineer' }

  function onSelectItem(id) {
    selectedId.value = id
    page.value = 'detail'
  }

  // Предзагрузка фильтров + проверка hash
  if (preloadFilters) {
    onMounted(async () => {
      // Хеш-роутинг
      for (const [hash, targetPage] of Object.entries(hashMap)) {
        if (typeof window !== 'undefined' && window.location.hash === hash) {
          page.value = targetPage
          break
        }
      }

      // Загрузка фильтров
      try {
        const r = await api.getFilters()
        filters.data = r.data || {}
        filters.loaded = true
      } catch (e) {
        console.error('[useCatalogRouter] Failed to load filters', e)
        filters.loaded = true
      }
    })
  }

  return {
    page, selectedId, idValue, filters,
    goToList, goToBrand, goToEngineer, onSelectItem,
    // expose idProp for template binding
    idProp,
  }
}
