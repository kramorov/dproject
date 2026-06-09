// shared/composables/useDocumentJournal.js
// Универсальный composable для журналов документов.
// Список, фильтры (даты, статус, поиск), пагинация, batch-операции.

import { ref, reactive, computed } from 'vue'

const STATUS_LABELS = {
  draft: 'Черновик',
  on_approval: 'На согласовании',
  posted: 'Проведён',
  deleted: 'Удалён',
}

const STATUS_ICONS = {
  draft: '✎',
  on_approval: '⟳',
  posted: '✓',
  deleted: '✕',
}

/**
 * Composable для журнала документов.
 *
 * Родительский компонент должен:
 *   - Передать возвращаемые refs/reactive как props в DocumentJournal
 *   - Слушать @filter-change для обновления filters
 *   - Слушать @sort-by, @batch-*, @open-card, @create-new
 *
 * @param {Object} api — API-модуль журнала:
 *   { list(params), create(data), register(id), unregister(id), markDeleted(id) }
 * @param {Object} [opts]
 * @param {number} [opts.limit=25]
 * @param {Function} [opts.onCreateFields] — (data) => поля для POST
 */
export function useDocumentJournal(api, opts = {}) {
  const { limit: defaultLimit = 25 } = opts

  // ── State ──
  const items = ref([])
  const total = ref(0)
  const loading = ref(false)
  const limit = ref(defaultLimit)
  const offset = ref(0)

  // Сортировка
  const sortField = ref('document_date')
  const sortDir = ref('desc')

  // Фильтры
  const filters = reactive({
    search: '',
    status: '',
    date_from: '',
    date_to: '',
  })

  // Выбранные строки (чекбоксы)
  const selectedIds = ref(new Set())
  const allSelected = ref(false)

  // ── Computed ──
  const hasFilters = computed(() => {
    return filters.search || filters.status || filters.date_from || filters.date_to
  })

  const selectedCount = computed(() => selectedIds.value.size)

  // ── Загрузка ──
  async function fetchList() {
    loading.value = true
    try {
      const params = {
        limit: limit.value,
        offset: offset.value,
      }
      if (filters.search) params.search = filters.search
      if (filters.status) params.status = filters.status
      if (filters.date_from) params.date_from = filters.date_from
      if (filters.date_to) params.date_to = filters.date_to
      if (sortField.value) params.ordering = (sortDir.value === 'desc' ? '-' : '') + sortField.value

      const r = await api.list(params)
      const body = r.data || {}
      items.value = body.data || []
      total.value = body.total || 0
    } catch (e) {
      console.error('[DocumentJournal] fetchList error:', e)
    } finally {
      loading.value = false
      selectedIds.value = new Set()
      allSelected.value = false
    }
  }

  // Пагинация
  function goPage(n) {
    offset.value = (n - 1) * limit.value
    fetchList()
  }

  // Поиск с debounce
  let searchTimer = null
  function onSearchInput(val) {
    filters.search = val
    clearTimeout(searchTimer)
    searchTimer = setTimeout(() => {
      offset.value = 0
      fetchList()
    }, 300)
  }

  function applyFilters() {
    offset.value = 0
    fetchList()
  }

  function sortBy(field) {
    if (sortField.value === field) {
      sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortField.value = field
      sortDir.value = 'asc'
    }
    offset.value = 0
    fetchList()
  }

  function resetFilters() {
    filters.search = ''
    filters.status = ''
    filters.date_from = ''
    filters.date_to = ''
    offset.value = 0
    fetchList()
  }

  // ── Чекбоксы ──
  function toggleSelect(id) {
    const s = new Set(selectedIds.value)
    if (s.has(id)) s.delete(id)
    else s.add(id)
    selectedIds.value = s
    allSelected.value = s.size === items.value.length
  }

  function toggleAll() {
    if (allSelected.value) {
      selectedIds.value = new Set()
      allSelected.value = false
    } else {
      selectedIds.value = new Set(items.value.map(item => item.id))
      allSelected.value = true
    }
  }

  // ── Batch-операции ──
  async function batchRegister() {
    if (!selectedCount.value) return
    loading.value = true
    let ok = 0, err = 0
    for (const id of selectedIds.value) {
      try {
        await api.register(id)
        ok++
      } catch { err++ }
    }
    loading.value = false
    await fetchList()
    return { ok, err }
  }

  async function batchUnregister() {
    if (!selectedCount.value) return
    loading.value = true
    let ok = 0, err = 0
    for (const id of selectedIds.value) {
      try {
        await api.unregister(id)
        ok++
      } catch { err++ }
    }
    loading.value = false
    await fetchList()
    return { ok, err }
  }

  async function batchMarkDeleted() {
    if (!selectedCount.value) return
    loading.value = true
    let ok = 0, err = 0
    for (const id of selectedIds.value) {
      try {
        await api.markDeleted(id)
        ok++
      } catch { err++ }
    }
    loading.value = false
    await fetchList()
    return { ok, err }
  }

  // ── Создание ──
  async function createDocument(data) {
    const fields = opts.onCreateFields ? opts.onCreateFields(data) : data
    const r = await api.create(fields)
    await fetchList()
    return r.data
  }

  return {
    // State
    items, total, loading, limit, offset,
    filters, hasFilters,
    selectedIds, selectedCount, allSelected,
    sortField, sortDir,

    // Methods
    fetchList, goPage, onSearchInput, applyFilters, resetFilters, sortBy,
    toggleSelect, toggleAll,
    batchRegister, batchUnregister, batchMarkDeleted,
    createDocument,

    // Constants
    STATUS_LABELS, STATUS_ICONS,
  }
}
