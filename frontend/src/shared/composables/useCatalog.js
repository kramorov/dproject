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
 * @param {string}   [opts.mode]         'engineer' — getEngineer/getEngineerFilters вместо list/getFilters
 */
export function useCatalog(api, opts = {}) {
  const {
    limit: defaultLimit = 24,
    debounceMs = 300,
    fixedParams = null,
    filterScope = null,
    onData = null,
    withSearch = true,
    mode = null,
  } = opts

  const items = ref([])
  const compatibleData = ref([])
  const total = ref(0)
  const exactTotal = ref(0)
  const compatibleTotal = ref(0)
  const splitFilter = ref(null)
  const loading = ref(false)
  const limit = ref(defaultLimit)
  const offset = ref(0)

  const filterData = reactive({})
  const filtersLoaded = ref(false)
  const showCompatibleAvailable = ref(false)
  const showCompatible = ref(false)
  const activeFilters = reactive({})
  const search = ref('')

  let searchTimer = null

  // --- Фильтры ---
  async function loadFilters() {
    try {
      const params = filterScope ? { scope: filterScope } : undefined
      const r = await (mode === 'engineer' ? api.getEngineerFilters(params) : api.getFilters(params))
      const body = r.data || {}

      // Clear stale keys from previous scope before assigning new ones
      for (const k of Object.keys(filterData)) {
        delete filterData[k]
      }

      // New CatalogConfig format: { filters: {...}, show_compatible: bool }
      if (body.filters) {
        Object.assign(filterData, body.filters)
        showCompatibleAvailable.value = !!body.show_compatible
      } else {
        // Old format: { param_name: { label, order, options } }
        Object.assign(filterData, body)
      }
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

  function toggleCompatible(val) {
    showCompatible.value = val
    offset.value = 0
    fetchData()
  }

  function resetFilters() {
    for (const k of Object.keys(activeFilters)) {
      activeFilters[k] = ''
    }
    search.value = ''
    showCompatible.value = false
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

      // show_compatible
      if (showCompatible.value) {
        params.show_compatible = 'true'
      }

      // Активные фильтры
      for (const [k, v] of Object.entries(activeFilters)) {
        if (v !== '' && v != null) params[k] = v
      }

      const r = await (mode === 'engineer' ? api.getEngineer(params) : api.list(params))
      const body = r.data || {}

      items.value = body.data || []
      total.value = body.total || 0

      // Compatible split (from apply_filters_and_split)
      compatibleData.value = body.compatible_data || []
      exactTotal.value = body.exact_count ?? items.value.length
      compatibleTotal.value = body.compatible_count ?? 0
      splitFilter.value = body.split_filter || null

      if (onData) onData(items.value)
    } catch (e) {
      console.error('[useCatalog] Failed to load data', e)
      items.value = []
      compatibleData.value = []
      total.value = 0
    }
    loading.value = false
  }

  return {
    // State
    items, compatibleData, total, exactTotal, compatibleTotal,
    splitFilter, loading, limit, offset,
    filterData, filtersLoaded, showCompatibleAvailable,
    showCompatible, activeFilters, search,

    // Actions
    loadFilters, fetchData,
    onFilterChange, toggleCompatible, resetFilters,
    onSearchInput, goPage,
  }
}