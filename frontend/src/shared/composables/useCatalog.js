// shared/composables/useCatalog.js
// Универсальный composable для каталогов: fetchData, пагинация, фильтры, поиск.
// Заменяет дублирующуюся логику в GearboxList/FrList/LsbList и GearboxBrand/FrBrand/LsbBrand.

import { ref, reactive } from 'vue'

/**
 * @param {Object}   api           API-модуль каталога ({ list, getFilters, getDetail })
 * @param {Object}   [opts]
 * @param {number}   [opts.limit=24]
 * @param {number}   [opts.debounceMs=300]
 * @param {Object}   [opts.fixedParams]    Параметры, всегда добавляемые к запросу (напр. { brand_id } в Brand)
 * @param {Function} [opts.onData]         Callback после загрузки (напр. установить brandName из первого элемента)
 * @param {boolean}  [opts.withSearch=true] Показывать строку поиска
 */
export function useCatalog(api, opts = {}) {
  const {
    limit: defaultLimit = 24,
    debounceMs = 300,
    fixedParams = null,
    onData = null,
    withSearch = true,
  } = opts

  const items = ref([])
  const total = ref(0)
  const loading = ref(false)
  const limit = ref(defaultLimit)
  const offset = ref(0)

  const filterData = reactive({})
  const filtersLoaded = ref(false)
  const activeFilters = reactive({})
  const search = ref('')

  let searchTimer = null

  // --- Фильтры ---
  async function loadFilters() {
    try {
      const r = await api.getFilters()
      Object.assign(filterData, r.data || {})
    } catch (e) {
      console.error('[useCatalog] Failed to load filters', e)
    }
    filtersLoaded.value = true
  }

  function onFilterChange(key, value) {
    activeFilters[key] = value
    offset.value = 0
    fetchData()
  }

  function resetFilters() {
    for (const k of Object.keys(activeFilters)) {
      activeFilters[k] = ''
    }
    search.value = ''
    offset.value = 0
    fetchData()
  }

  // --- Поиск ---
  function onSearchInput() {
    clearTimeout(searchTimer)
    searchTimer = setTimeout(() => {
      offset.value = 0
      fetchData()
    }, debounceMs)
  }

  // --- Пагинация ---
  function goPage(n) {
    offset.value = Math.max(0, n)
    fetchData()
    if (typeof window !== 'undefined') {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  // --- Загрузка ---
  async function fetchData() {
    loading.value = true
    try {
      const params = { limit: limit.value, offset: offset.value }

      // Фиксированные параметры (brand_id, model_line_id и т.д.)
      if (fixedParams) {
        Object.assign(params, typeof fixedParams === 'function' ? fixedParams() : fixedParams)
      }

      // Поиск
      if (withSearch && search.value) {
        params.search = search.value
      }

      // Активные фильтры
      for (const [k, v] of Object.entries(activeFilters)) {
        if (v !== '' && v != null) params[k] = v
      }

      const r = await api.list(params)
      items.value = r.data?.data || []
      total.value = r.data?.total || 0

      if (onData) onData(items.value)
    } catch (e) {
      console.error('[useCatalog] Failed to load data', e)
      items.value = []
      total.value = 0
    }
    loading.value = false
  }

  return {
    // State
    items, total, loading, limit, offset,
    filterData, filtersLoaded, activeFilters, search,

    // Actions
    loadFilters, fetchData,
    onFilterChange, resetFilters,
    onSearchInput, goPage,
  }
}
