// shared/composables/useDocumentCard.js
// Универсальный composable для карточки документа.
// Загрузка, сохранение, проведение/отмена, print/export/import.

import { ref, reactive, computed, watch } from 'vue'

/**
 * @param {Object}   api — API-модуль:
 *   { getDetail(id), update(id, data), register(id), unregister(id),
 *     markDeleted(id), print(id), exportDoc(id, fmt), importFile(id, file) }
 * @param {Object}   [opts]
 * @param {Function} [opts.onSave]      — кастомное сохранение (иначе api.update)
 * @param {Function} [opts.onCreate]    — кастомное создание (иначе api.create)
 */
export function useDocumentCard(api, opts = {}) {
  // ── State ──
  const doc = ref(null)
  const loading = ref(false)
  const saving = ref(false)
  const error = ref('')

  // Форма
  const form = reactive({
    name: '',
    document_date: '',
    description: '',
  })
  const isDirty = ref(false)

  // ── Computed ──
  const isDraft = computed(() => doc.value?.status === 'draft')
  const isPosted = computed(() => doc.value?.is_posted)
  const isDeleted = computed(() => doc.value?.is_deleted)
  const features = computed(() => doc.value?.features || {})

  const canSave = computed(() => isDraft.value && isDirty.value)
  const canRegister = computed(() => isDraft.value && !isDeleted.value)
  const canUnregister = computed(() => isPosted.value)
  const canMarkDeleted = computed(() => !isDeleted.value)
  const canRestore = computed(() => isDeleted.value)

  // Доступные export-форматы (только те, что реализованы)
  const availableExports = computed(() => {
    const f = features.value
    return [
      f.export_word && { key: 'word', label: 'Word' },
      f.export_excel && { key: 'excel', label: 'Excel' },
      f.export_pdf && { key: 'pdf', label: 'PDF' },
    ].filter(Boolean)
  })

  // ── Загрузка ──
  async function loadDocument(id) {
    loading.value = true
    error.value = ''
    try {
      const r = await api.getDetail(id)
      doc.value = r.data
      fillForm(r.data)
    } catch (e) {
      error.value = 'Ошибка загрузки документа'
      console.error('[DocumentCard] load error:', e)
    } finally {
      loading.value = false
      isDirty.value = false
    }
  }

  function fillForm(data) {
    form.name = data.name || ''
    form.document_date = data.document_date || ''
    form.description = data.description || ''
  }

  // Отслеживаем изменения формы
  watch([() => form.name, () => form.document_date, () => form.description], () => {
    if (doc.value) {
      isDirty.value =
        form.name !== (doc.value.name || '') ||
        form.document_date !== (doc.value.document_date || '') ||
        form.description !== (doc.value.description || '')
    }
  })

  // ── Сохранение ──
  async function save() {
    if (!canSave.value || !doc.value) return
    saving.value = true
    error.value = ''
    try {
      const data = {
        name: form.name,
        document_date: form.document_date,
        description: form.description,
      }
      if (opts.onSave) {
        await opts.onSave(doc.value.id, data)
      } else {
        await api.update(doc.value.id, data)
      }
      isDirty.value = false
      await loadDocument(doc.value.id) // перечитать
    } catch (e) {
      error.value = 'Ошибка сохранения'
      console.error('[DocumentCard] save error:', e)
    } finally {
      saving.value = false
    }
  }

  // ── Статусные действия ──
  async function register() {
    if (!doc.value) return
    saving.value = true
    error.value = ''
    try {
      await api.register(doc.value.id)
      await loadDocument(doc.value.id)
    } catch (e) {
      error.value = 'Ошибка проведения'
    } finally {
      saving.value = false
    }
  }

  async function unregister() {
    if (!doc.value) return
    saving.value = true
    error.value = ''
    try {
      await api.unregister(doc.value.id)
      await loadDocument(doc.value.id)
    } catch (e) {
      error.value = 'Ошибка отмены проведения'
    } finally {
      saving.value = false
    }
  }

  async function markDeleted() {
    if (!doc.value) return
    saving.value = true
    error.value = ''
    try {
      await api.markDeleted(doc.value.id)
      await loadDocument(doc.value.id)
    } catch (e) {
      error.value = 'Ошибка пометки на удаление'
    } finally {
      saving.value = false
    }
  }

  // ── Восстановление ──
  async function restore() {
    if (!doc.value) return
    saving.value = true
    error.value = ''
    try {
      await api.update(doc.value.id, { status: 'draft' })
      await loadDocument(doc.value.id)
    } catch (e) {
      error.value = 'Ошибка восстановления'
    } finally {
      saving.value = false
    }
  }

  // ── Печать ──
  async function printDocument() {
    if (!doc.value) return
    try {
      const r = await api.print(doc.value.id)
      const html = typeof r.data === 'string' ? r.data : r.data?.html || ''
      const w = window.open('', '_blank', 'width=800,height=600')
      if (w) {
        w.document.write(html)
        w.document.close()
      }
    } catch (e) {
      error.value = 'Ошибка печати'
    }
  }

  // ── Экспорт ──
  function exportDocument(fmt) {
    if (!doc.value) return
    const url = api.exportUrl
      ? api.exportUrl(doc.value.id, fmt)
      : `/api/documents/${doc.value.id}/export/${fmt}/`
    // POST для скачивания файла (с CSRF-токеном)
    const form = document.createElement('form')
    form.method = 'POST'
    form.action = url
    form.target = '_blank'
    // CSRF-токен из cookie
    const csrf = document.cookie.split('; ').find(r => r.startsWith('csrftoken='))
    if (csrf) {
      const input = document.createElement('input')
      input.type = 'hidden'
      input.name = 'csrfmiddlewaretoken'
      input.value = csrf.split('=')[1]
      form.appendChild(input)
    }
    document.body.appendChild(form)
    form.submit()
    document.body.removeChild(form)
  }

  // ── Импорт ──
  async function importFile(file) {
    if (!doc.value) return
    saving.value = true
    error.value = ''
    try {
      const formData = new FormData()
      formData.append('file', file)
      const r = await api.importFile(doc.value.id, formData)
      await loadDocument(doc.value.id)
      return r.data
    } catch (e) {
      error.value = 'Ошибка импорта'
    } finally {
      saving.value = false
    }
  }

  return {
    // State
    doc, loading, saving, error,
    form, isDirty,

    // Computed
    isDraft, isPosted, isDeleted, features,
    canSave, canRegister, canUnregister, canMarkDeleted, canRestore,
    availableExports,

    // Methods
    loadDocument, save,
    register, unregister, markDeleted, restore,
    printDocument, exportDocument, importFile,
  }
}
