// shared/composables/useCatalog.js
// Универсальный composable для каталогов: fetchData, пагинация, фильтры, поиск.

import { ref, reactive, unref } from 'vue'

/**
 * @param {Object}   api           API-модуль каталога ({ list, getFilters, getDetail })
 * @param {Object}   [opts]
 * @param {number}   [opts.limit=24]
 * @param {number}   [opts.debounceMs=300]
 * @param {Object|Function|import('vue').Ref} [opts.fixedParams]  Параметры, всегда добавляемые к запросу
 * @param {string}   [opts.filterScope]  ?scope= для getFilters (model_line — без model_line_id/brand_id)
 * @param {Function} [opts.onData]       Callback после загрузки
 * @param {boolean}  [opts.withSearch=true]
 */
export function useCatalog(api, opts = {}) {
  const {
    limit: defaultLimit = 24,
    debounceMs = 300,
    fixedParams = null,
    filterScope = null,
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
      const params = filterScope ? { scope: filterScope } : undefined
      const r = await api.getFilters(params)
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
      const fp = unref(fixedParams)
      if (fp) {
        Object.assign(params, typeof fp === 'function' ? fp() : fp)
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
