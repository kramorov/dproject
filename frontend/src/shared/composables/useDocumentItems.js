// shared/composables/useDocumentItems.js
// Универсальный composable для табличной части документа.
// Строки, reorder (вверх/вниз), добавление, удаление.

import { ref, computed } from 'vue'

/**
 * @param {Object}   api — { getItems(docId), addItem(docId, data), updateItem(docId, itemId, data), deleteItem(docId, itemId) }
 * @param {Object}   [opts]
 * @param {Function} [opts.newItemDefaults] — () => поля по умолчанию для новой строки
 */
export function useDocumentItems(api, opts = {}) {
  const items = ref([])
  const loading = ref(false)
  const error = ref('')

  const itemCount = computed(() => items.value.length)

  // ── Загрузка ──
  async function loadItems(docId) {
    currentDocId = docId
    loading.value = true
    error.value = ''
    try {
      const r = await api.getItems(docId)
      items.value = (r.data || []).sort((a, b) => (a.sorting_order || 0) - (b.sorting_order || 0))
    } catch (e) {
      error.value = 'Ошибка загрузки строк'
    } finally {
      loading.value = false
    }
  }

  // ── Добавление ──
  async function addItem(docId) {
    const defaults = opts.newItemDefaults ? opts.newItemDefaults() : {}
    const data = { ...defaults, sorting_order: items.value.length + 1 }
    try {
      const r = await api.addItem(docId, data)
      items.value.push(r.data)
    } catch (e) {
      error.value = 'Ошибка добавления строки'
    }
  }

  // ── Удаление (soft delete — is_active=False) ──
  async function removeItem(docId, itemId) {
    try {
      await api.deleteItem(docId, itemId)
      items.value = items.value.filter(item => item.id !== itemId)
    } catch (e) {
      error.value = 'Ошибка удаления строки'
    }
  }

  // ── Обновление строки ──
  async function updateItem(docId, itemId, data) {
    try {
      const r = await api.updateItem(docId, itemId, data)
      const idx = items.value.findIndex(item => item.id === itemId)
      if (idx >= 0) items.value[idx] = r.data
    } catch (e) {
      error.value = 'Ошибка обновления строки'
    }
  }

  // ── Reorder (с сохранением порядка на сервер) ──
  let currentDocId = null

  function reorderItems(docId, fromIndex, toIndex) {
    const arr = [...items.value]
    const [moved] = arr.splice(fromIndex, 1)
    arr.splice(toIndex, 0, moved)
    arr.forEach((item, i) => { item.sorting_order = i + 1 })
    items.value = arr
    // Сохраняем новый порядок для всех строк
    arr.forEach(item => {
      api.updateItem(docId, item.id, { sorting_order: item.sorting_order }).catch(() => {})
    })
  }

  function moveUp(index) {
    if (index <= 0 || !currentDocId) return
    reorderItems(currentDocId, index, index - 1)
  }

  function moveDown(index) {
    if (index >= items.value.length - 1 || !currentDocId) return
    reorderItems(currentDocId, index, index + 1)
  }

  return {
    items, loading, error, itemCount, currentDocId,
    loadItems, addItem, removeItem, updateItem,
    moveUp, moveDown,
  }
}
