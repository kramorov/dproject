<!-- cg-constructor/App.vue — конструктор кабельных вводов -->
<template>
  <div class="constructor-app">
    <!-- Левая панель: сохранённые конфигурации -->
    <aside class="panel-left">
      <h2>Сохранённые конфигурации</h2>

      <div class="filter-bar">
        <input v-model="filters.search" placeholder="Поиск по коду/названию..." class="filter-input" />
        <select v-model="filters.model_line" @change="onFilterChange">
          <option :value="null">Все серии</option>
          <option v-for="ml in modelLines" :key="ml.id" :value="ml.id">{{ ml.name }}</option>
        </select>
      </div>

      <div class="saved-list">
        <div v-if="loadingList" class="list-status">Загрузка...</div>
        <div v-else-if="!filteredList.length" class="list-status">Нет сохранённых конфигураций</div>
        <div
          v-for="item in filteredList" :key="item.id"
          class="saved-card"
          @click="loadItem(item)"
        >
          <div class="card-code">{{ item.code || '—' }}</div>
          <div class="card-model">{{ item.model_line_item?.name || '' }}</div>
          <div class="card-desc">{{ item.description?.substring(0, 80) || '' }}</div>
          <button class="btn-icon delete" @click.stop="deleteItem(item.id)" title="Удалить">×</button>
        </div>
      </div>
    </aside>

    <!-- Правая панель: форма конструктора -->
    <main class="panel-right">
      <div class="builder-header">
        <h2>Новая конфигурация</h2>
      </div>

      <div class="form-row">
        <label>Серия кабельных вводов</label>
        <select v-model="form.selected_model_line" @change="onModelLineChange">
          <option :value="null">— выберите серию —</option>
          <option v-for="ml in modelLines" :key="ml.id" :value="ml.id">{{ ml.name }} ({{ ml.code }})</option>
        </select>
      </div>

      <div class="form-row" v-if="form.selected_model_line">
        <label>Модель</label>
        <select v-model="form.selected_model_line_item" @change="onModelLineItemChange" :disabled="!modelLineItems.length">
          <option :value="null">— выберите модель —</option>
          <option v-for="item in modelLineItems" :key="item.id" :value="item.id">{{ item.name }}</option>
        </select>
      </div>

      <template v-if="options">
        <h3>Опции</h3>

        <div class="form-row">
          <label>Резьба</label>
          <select v-model="form.selected_thread_option" :disabled="(options.thread_options || []).length <= 1">
            <option :value="null">— выберите резьбу —</option>
            <option v-for="o in options.thread_options" :key="o.id" :value="o.id">
              {{ o.name }}{{ o.is_default ? ' (стандарт)' : '' }}
            </option>
          </select>
        </div>

        <div class="form-row">
          <label>Материал корпуса</label>
          <select v-model="form.selected_body_material_option" :disabled="(options.body_material_options || []).length <= 1">
            <option :value="null">— выберите материал —</option>
            <option v-for="o in options.body_material_options" :key="o.id" :value="o.id">
              {{ o.name }}{{ o.is_default ? ' (стандарт)' : '' }}
            </option>
          </select>
        </div>

        <div class="form-row">
          <label>Взрывозащита</label>
          <select v-model="form.selected_exd_option" :disabled="(options.exd_options || []).length <= 1">
            <option :value="null">— по умолчанию серии —</option>
            <option v-for="o in options.exd_options" :key="o.id" :value="o.id">
              {{ exdLabel(o) }}{{ o.is_default ? ' (стандарт)' : '' }}
            </option>
          </select>
        </div>
      </template>

      <div class="preview" v-if="previewText">
        <h3>Превью</h3>
        <pre class="preview-text">{{ previewText }}</pre>
      </div>

      <div class="actions">
        <button class="btn primary" @click="save" :disabled="!canSave || saving">
          {{ saving ? 'Сохранение...' : 'Создать' }}
        </button>
        <button class="btn secondary" @click="resetForm">Сбросить</button>
      </div>

      <div class="message" v-if="message" :class="message.type">{{ message.text }}</div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import api from './api'

const modelLines = ref([])
const modelLineItems = ref([])
const savedList = ref([])
const loadingList = ref(false)
const options = ref(null)
const message = ref(null)
const previewText = ref('')
const saving = ref(false)

const filters = reactive({ search: '', model_line: null })

const defaultForm = () => ({
  selected_model_line: null,
  selected_model_line_item: null,
  selected_thread_option: null,
  selected_body_material_option: null,
  selected_exd_option: null,
})

const form = reactive(defaultForm())
const canSave = computed(() => !!form.selected_model_line_item)

const filteredList = computed(() => {
  const s = (filters.search || '').toLowerCase()
  if (!s) return savedList.value
  return savedList.value.filter(item =>
    (item.code || '').toLowerCase().includes(s) || (item.name || '').toLowerCase().includes(s)
  )
})

function exdLabel(o) {
  if (o.encoding) return o.encoding
  const codes = (o.variants || []).map(v => v.code).filter(Boolean)
  return codes.length ? codes.join(' / ') : (o.id || '')
}

onMounted(async () => {
  try {
    modelLines.value = (await api.getModelLines()).data
    await loadList()
  } catch (e) { /* */ }
})

async function loadList() {
  loadingList.value = true
  try {
    const params = {}
    if (filters.model_line) params.model_line_id = filters.model_line
    savedList.value = (await api.list(params)).data
  } catch (e) { /* */ } finally { loadingList.value = false }
}

async function onFilterChange() {
  await loadList()
}

async function deleteItem(id) {
  if (!confirm('Удалить конфигурацию?')) return
  try {
    await api.delete(id)
    await loadList()
    showMessage('Удалено', 'success')
  } catch (e) { showMessage('Ошибка удаления', 'error') }
}

async function loadItem(item) {
  try {
    const d = (await api.getDetail(item.id)).data
    form.selected_model_line = d.model_line?.id || null
    form.selected_model_line_item = d.model_line_item?.id || null
    form.selected_thread_option = d.selected_thread_option?.id || null
    form.selected_body_material_option = d.selected_body_material_option?.id || null
    form.selected_exd_option = d.selected_exd_option?.id || null
    if (form.selected_model_line) {
      modelLineItems.value = (await api.getModelLineItems(form.selected_model_line)).data
    }
    if (form.selected_model_line_item) {
      options.value = (await loadOptions()).data
    }
    previewText.value = d.description || ''
  } catch (e) { showMessage('Ошибка загрузки', 'error') }
}

async function onModelLineChange() {
  form.selected_model_line_item = null
  form.selected_thread_option = null
  form.selected_body_material_option = null
  form.selected_exd_option = null
  modelLineItems.value = []
  options.value = null
  previewText.value = ''
  if (!form.selected_model_line) return
  try { modelLineItems.value = (await api.getModelLineItems(form.selected_model_line)).data }
  catch (e) { showMessage('Ошибка загрузки моделей', 'error') }
}

async function onModelLineItemChange() {
  form.selected_thread_option = null
  form.selected_body_material_option = null
  form.selected_exd_option = null
  options.value = null
  previewText.value = ''
  if (!form.selected_model_line_item) return
  try {
    options.value = (await loadOptions()).data
    autoFillDefaults()
  } catch (e) { showMessage('Ошибка загрузки опций', 'error') }
}

async function loadOptions() {
  return api.getOptions({
    model_line: form.selected_model_line,
    model_line_item: form.selected_model_line_item,
  })
}

function autoFillDefaults() {
  if (!options.value) return
  const def = (items) => {
    if (!items?.length) return null
    if (items.length === 1) return items[0].id
    return (items.find(o => o.is_default) || items[0]).id
  }
  form.selected_thread_option = def(options.value.thread_options)
  form.selected_body_material_option = def(options.value.body_material_options)
  form.selected_exd_option = def(options.value.exd_options)
}

async function save() {
  saving.value = true
  try {
    const res = await api.create({ ...form })
    showMessage(res.status === 201 ? 'Создано: ' + res.data.name : 'Найдена существующая: ' + res.data.name, 'success')
    previewText.value = res.data.description || ''
    await loadList()
  } catch (e) {
    const msg = e.response?.data?.error || e.response?.data?.detail || 'Ошибка сохранения'
    showMessage(msg, 'error')
  } finally { saving.value = false }
}

function resetForm() {
  Object.assign(form, defaultForm())
  options.value = null
  modelLineItems.value = []
  previewText.value = ''
}

let previewTimer = null
watch(() => ({ ...form }), () => {
  if (!form.selected_model_line_item) return
  clearTimeout(previewTimer)
  previewTimer = setTimeout(async () => {
    try {
      const res = await api.preview({ ...form })
      previewText.value = `${res.data.name}\n${res.data.description}`
    } catch (e) { /* */ }
  }, 300)
}, { deep: true })

function showMessage(text, type = 'info') {
  message.value = { text, type }
  setTimeout(() => { message.value = null }, 3000)
}
</script>

<style scoped>
.constructor-app {
  display: flex; gap: 0; height: calc(100vh - 60px);
  font-family: system-ui, -apple-system, sans-serif; color: #1a1a2e;
}
.panel-left {
  width: 360px; min-width: 300px; flex-shrink: 0;
  border-right: 1px solid #e5e7eb; padding: 20px;
  display: flex; flex-direction: column; overflow: hidden;
}
.panel-left h2 { font-size: 16px; margin: 0 0 12px; }
.filter-bar { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.filter-input { padding: 7px 10px; font-size: 13px; border: 1px solid #ccc; border-radius: 6px; }
.filter-input:focus { outline: none; border-color: #4a6cf7; }
.filter-bar select { padding: 7px 10px; font-size: 13px; border: 1px solid #ccc; border-radius: 6px; background: #fff; }
.saved-list { flex: 1; overflow-y: auto; }
.list-status { color: #999; font-size: 13px; padding: 12px 0; }
.saved-card {
  position: relative; padding: 10px 12px; margin-bottom: 6px;
  border: 1px solid #e5e7eb; border-radius: 8px; cursor: pointer;
  transition: border-color .15s, background .15s;
}
.saved-card:hover { border-color: #a0b4f7; background: #f8f9ff; }
.card-code { font-weight: 700; font-size: 14px; margin-bottom: 2px; }
.card-model { font-size: 12px; color: #666; margin-bottom: 2px; }
.card-desc { font-size: 11px; color: #999; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.saved-card .delete {
  position: absolute; top: 6px; right: 8px;
  border: none; background: none; font-size: 18px; color: #c44;
  cursor: pointer; line-height: 1; padding: 0 4px; opacity: 0; transition: opacity .15s;
}
.saved-card:hover .delete { opacity: 1; }

.panel-right { flex: 1; padding: 20px 32px; overflow-y: auto; }
.builder-header { margin-bottom: 16px; }
.builder-header h2 { font-size: 18px; margin: 0; }
h3 { font-size: 15px; color: #555; margin: 16px 0 8px; }
.form-row { margin-bottom: 12px; }
.form-row label { display: block; font-size: 13px; color: #555; margin-bottom: 4px; }
.form-row select { width: 100%; padding: 8px 10px; font-size: 14px; border: 1px solid #ccc; border-radius: 6px; background: #fff; }
.form-row select:focus { outline: none; border-color: #4a6cf7; }
.form-row select:disabled { background: #f3f3f5; color: #555; cursor: not-allowed; border-color: #ddd; }
.preview { margin-top: 20px; }
.preview-text { background: #f7f7f9; border: 1px solid #e0e0e6; border-radius: 6px; padding: 12px; font-size: 13px; white-space: pre-wrap; word-break: break-word; max-height: 200px; overflow-y: auto; }
.actions { margin-top: 20px; display: flex; gap: 10px; }
.btn { padding: 10px 24px; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; }
.btn.primary { background: #4a6cf7; color: #fff; }
.btn.primary:disabled { background: #a0b4f7; cursor: not-allowed; }
.btn.secondary { background: #eee; color: #333; }
.message { margin-top: 12px; padding: 8px 12px; border-radius: 6px; font-size: 13px; }
.message.success { background: #e6f7e6; color: #2a7a2a; }
.message.error { background: #fde6e6; color: #a33; }
</style>
