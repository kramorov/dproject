<script setup>
/**
 * Универсальный CRUD-редактор модели по конфигу MODEL_CONFIGS
 * (endpoint, label, columns, fields). Используется вкладкой «Справочники»
 * (variant=inline) и «Редактором БУ» (variant=modal) страницы
 * /admin/ea-control. Формы — общий FieldInput; кнопки — общий EditorActions.
 *
 * Копирование записи: кнопка «Копировать» (только у моделей с полем code) —
 * создаёт копию текущей записи с кодом `<code>_Copy` (уникальность — суффиксы).
 */
import { computed, reactive, ref, watch } from 'vue'
import api from '@/shared/api'
import { guardedDelete } from '@/shared/guardedDelete'
import { uniqueCode } from '@/shared/uniqueCode'
import EditorActions from '@/components/EditorActions.vue'
import FieldInput from '@/components/admin/FieldInput.vue'
import { t } from '@/shared/i18n'

const props = defineProps({
  config: { type: Object, required: true },
  optionsMap: { type: Object, required: true },
  variant: { type: String, default: 'inline' }, // inline | modal
})

const rows = ref([])
const loading = ref(false)
const error = ref('')
const editing = ref(null)
const form = reactive({})
const dirty = ref(false)
const deletePending = ref(false)

const columns = computed(() => props.config.columns)
const copyable = computed(() =>
  props.config.fields.some(f => f.name === 'code'))

const toolbarButtons = computed(() => [
  { key: 'create', label: t('eaControl.add'), kind: 'primary' },
  { key: 'refresh', label: t('eaControl.refresh'), disabled: loading.value },
])

const editButtons = computed(() => {
  const buttons = [
    { key: 'save', label: t('eaControl.save'), kind: 'primary',
      disabled: !(dirty.value || deletePending.value) },
    { key: 'delete',
      label: deletePending.value ? t('eaControl.cancelDelete')
                                  : (editing.value && editing.value.id == null
                                     ? t('eaControl.cancelCreate')
                                     : t('eaControl.deleteValue')),
      kind: deletePending.value ? 'danger' : 'default' },
  ]
  if (copyable.value && editing.value && editing.value.id) {
    buttons.push({ key: 'copy', label: t('eaControl.copy'), kind: 'default' })
  }
  return buttons
})

const modalButtons = computed(() => {
  const buttons = [
    { key: 'save', label: t('eaControl.save'), kind: 'primary' },
    { key: 'cancel', label: t('eaControl.cancel') },
  ]
  if (copyable.value && editing.value && editing.value.id) {
    buttons.push({ key: 'copy', label: t('eaControl.copy'), kind: 'default' })
  }
  return buttons
})

function colLabel(c) {
  const f = props.config.fields.find(x => x.name === c)
  return f ? f.label : c
}

function display(row, c) {
  const v = row[c]
  if (v === null || v === undefined || v === '') return ''
  if (typeof v === 'boolean') return v ? '✓' : ''
  const f = props.config.fields.find(x => x.name === c)
  if (f) {
    if (f.choices) {
      const o = f.choices.find(([id]) => id === v)
      if (o) return o[1]
    }
    if (f.source && props.optionsMap[f.source]) {
      const o = props.optionsMap[f.source].find(o => o.id === v)
      if (o) return o.label
    }
  }
  return String(v)
}

function selectOptions(f) {
  if (f.choices) return f.choices.map(([id, label]) => ({ id, label }))
  return props.optionsMap[f.source] || []
}

function toggleMs(name, id) {
  const arr = form[name] || []
  const i = arr.indexOf(id)
  if (i >= 0) arr.splice(i, 1)
  else arr.push(id)
  form[name] = arr
  dirty.value = true
}

function markDirty() {
  dirty.value = true
}

function confirmUnsaved() {
  if (!editing.value || !dirty.value) return true
  return confirm('Есть несохранённые изменения. Отменить их и переключиться?')
}

function onRowClick(row) {
  if (editing.value && editing.value.id === row.id) return
  if (!confirmUnsaved()) return
  openEdit(row)
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get(`/ea-control/${props.config.endpoint}/`)
    rows.value = Array.isArray(data) ? data : data.results || []
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка загрузки'
  } finally {
    loading.value = false
  }
}

function onToolbarAction(b) {
  if (b.key === 'create') openCreate()
  else if (b.key === 'refresh') load()
}

function onEditAction(b) {
  if (b.key === 'save') save()
  else if (b.key === 'delete') toggleDelete()
  else if (b.key === 'copy') copyRecord()
  else if (b.key === 'cancel') closeEdit()
}

function openCreate() {
  if (!confirmUnsaved()) return
  const f = {}
  for (const field of props.config.fields) {
    f[field.name] = field.type === 'bool' ? true
      : field.type === 'multiselect' ? [] : (field.type === 'json' ? '' : null)
  }
  editing.value = { id: null }
  deletePending.value = false
  dirty.value = false
  Object.assign(form, f)
}

function openEdit(row) {
  const f = {}
  for (const field of props.config.fields) {
    let v = row[field.name]
    if (field.type === 'json' && v !== null && v !== undefined) {
      v = JSON.stringify(v, null, 2)
    }
    f[field.name] = v
  }
  editing.value = row
  deletePending.value = false
  dirty.value = false
  Object.assign(form, f)
}

function closeEdit() {
  editing.value = null
  deletePending.value = false
  dirty.value = false
}

function toggleDelete() {
  if (!editing.value) return
  if (editing.value.id == null) {
    closeEdit()
    return
  }
  deletePending.value = !deletePending.value
}

// Общая нормализация формы → payload (save и copy): json-парсинг,
// пустые значения → null, обязательные скаляры → ''/0
function normalizePayload() {
  const payload = {}
  for (const field of props.config.fields) {
    let v = form[field.name]
    if (field.type === 'json' && typeof v === 'string' && v.trim()) {
      try { v = JSON.parse(v) } catch { v = null }
    }
    if (v === '' || v === undefined) v = null
    if (v === null) {
      if (field.type === 'text' || field.type === 'textarea') v = ''
      else if (field.type === 'number' && !field.nullable) v = 0
    }
    payload[field.name] = v
  }
  return payload
}

async function save() {
  error.value = ''
  if (deletePending.value) {
    try {
      if (editing.value && editing.value.id) {
        await guardedDelete(`/ea-control/${props.config.endpoint}/${editing.value.id}/`)
      }
      closeEdit()
      await load()
    } catch (e) {
      if (e && e.cancelled) return
      error.value = e.displayMessage || 'Ошибка удаления'
    }
    return
  }
  const payload = normalizePayload()
  try {
    if (editing.value && editing.value.id) {
      await api.put(`/ea-control/${props.config.endpoint}/${editing.value.id}/`, payload)
    } else {
      await api.post(`/ea-control/${props.config.endpoint}/`, payload)
    }
    closeEdit()
    await load()
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка сохранения'
  }
}

async function copyRecord() {
  error.value = ''
  if (!editing.value || !editing.value.id) return
  const payload = normalizePayload()
  const taken = new Set(rows.value.map(r => r.code))
  const base = `${(payload.code || 'copy').trim()}_Copy`
  payload.code = uniqueCode(base, taken)
  try {
    const { data } = await api.post(`/ea-control/${props.config.endpoint}/`, payload)
    deletePending.value = false
    dirty.value = false
    await load()
    if (data && data.id) openEdit(data)
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка копирования'
  }
}

async function remove(row) {
  if (!confirm(`Удалить запись #${row.id}?`)) return
  try {
    await guardedDelete(`/ea-control/${props.config.endpoint}/${row.id}/`)
    if (editing.value && editing.value.id === row.id) closeEdit()
    await load()
  } catch (e) {
    if (e && e.cancelled) return
    error.value = e.displayMessage || 'Ошибка удаления'
  }
}

load()

// смена модели (выбор другого справочника) — перезагрузка списка
watch(() => props.config.endpoint, () => {
  closeEdit()
  load()
})

defineExpose({ confirmUnsaved })
</script>

<template>
  <div class="dict-editor">
    <div v-if="error" class="error-banner">{{ error }}</div>

    <div class="toolbar">
      <EditorActions align="start" :buttons="toolbarButtons" @action="onToolbarAction" />
      <span class="count">{{ rows.length }} записей</span>
    </div>

    <div class="table-scroll">
      <table v-if="rows.length" class="grid">
        <thead>
          <tr>
            <th v-for="c in columns" :key="c">{{ colLabel(c) }}</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.id" class="row"
              :class="{ editing: editing && editing.id === row.id }"
              @click="variant === 'inline' ? onRowClick(row) : openEdit(row)">
            <td v-for="c in columns" :key="c">{{ display(row, c) }}</td>
            <td class="actions">
              <button v-if="variant === 'modal'" title="Изменить" @click.stop="openEdit(row)">✎</button>
              <button title="Удалить" @click.stop="remove(row)">✕</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">Записей нет.</p>
    </div>

    <!-- Встроенная форма (вариант «Справочники») -->
    <div v-if="variant === 'inline' && editing" class="edit-area">
      <div class="edit-head">
        <h3>{{ editing.id ? 'Изменить' : 'Создать' }} — {{ config.label }}</h3>
        <EditorActions :buttons="editButtons" @action="onEditAction" />
      </div>
      <div v-if="deletePending" class="del-banner">Запись будет удалена при сохранении.</div>
      <div class="edit-form" @input="markDirty" @change="markDirty">
        <FieldInput v-for="f in config.fields" :key="f.name"
                    :field="f" :model-value="form[f.name]"
                    :options="selectOptions(f)"
                    @update:model-value="v => { form[f.name] = v }"
                    @toggle-ms="id => toggleMs(f.name, id)" />
      </div>
    </div>

    <!-- Модальная форма (вариант «Редактор БУ») -->
    <div v-if="variant === 'modal' && editing" class="modal-backdrop" @click.self="closeEdit">
      <div class="modal">
        <h3>{{ editing.id ? 'Изменить' : 'Создать' }} — {{ config.label }}</h3>
        <div class="edit-form" @input="markDirty" @change="markDirty">
          <FieldInput v-for="f in config.fields" :key="f.name"
                      :field="f" :model-value="form[f.name]"
                      :options="selectOptions(f)"
                      @update:model-value="v => { form[f.name] = v }"
                      @toggle-ms="id => toggleMs(f.name, id)" />
        </div>
        <div class="modal-actions">
          <EditorActions :buttons="modalButtons" @action="onEditAction" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.error-banner { background: #fdecea; color: #c62828; padding: 8px 10px; border-radius: 4px; margin-bottom: 10px; }
.toolbar { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
.count { color: #666; }
.empty { color: #999; }
.grid { width: 100%; border-collapse: collapse; font-size: 13px; }
.grid th, .grid td { border: 1px solid #ddd; padding: 4px 8px; text-align: left; }
.grid th { background: #f0f0f0; position: sticky; top: 0; }
.grid tbody tr.row { cursor: pointer; }
.grid tbody tr.row:hover { background: #f5f8fc; }
.grid tbody tr.row.editing { background: #e8f0fa; }
.actions { white-space: nowrap; }
.actions button { margin-right: 4px; cursor: pointer; }
.table-scroll { overflow-y: auto; max-height: 320px; }
.edit-area { border-top: 2px solid #2c6fb0; margin-top: 12px; padding-top: 10px; }
.edit-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.edit-head h3 { margin: 0; font-size: 15px; }
.del-banner { background: #fdecea; color: #c62828; padding: 6px 8px; border-radius: 3px; margin-bottom: 8px; font-size: 13px; }
.edit-form { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 12px; max-width: 900px; }
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,.4);
  display: flex; align-items: flex-start; justify-content: center; padding-top: 40px; z-index: 100;
}
.modal { background: #fff; padding: 16px; width: 720px; max-height: 85vh; overflow: auto; border-radius: 6px; }
.modal h3 { margin: 0 0 12px; }
.modal-actions { margin-top: 14px; display: flex; gap: 8px; justify-content: flex-end; }
</style>
