<!-- posi-constructor/App.vue — двухпанельный конструктор позиционеров -->
<template>
  <div class="constructor-app">
    <!-- Левая панель: список конфигураций + фильтры -->
    <aside class="panel-left">
      <h2>Сохранённые конфигурации</h2>

      <div class="filter-bar">
        <input v-model="filters.search" placeholder="Поиск по коду/названию..." class="filter-input" />
        <select v-model="filters.acting_type" @change="onFilterTypeChange">
          <option :value="null">Все типы</option>
          <option v-for="at in actingTypes" :key="at.id" :value="at.id">{{ at.name }}</option>
        </select>
        <select v-model="filters.model_line" @change="onFilterChange" :disabled="!filters.acting_type">
          <option :value="null">Все серии</option>
          <option v-for="ml in filterModelLines" :key="ml.id" :value="ml.id">{{ ml.name }}</option>
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
          <div class="card-model">{{ item.model_line?.name || '' }}</div>
          <div class="card-desc">{{ (item.description || '').substring(0, 80) }}</div>
          <button class="btn-icon delete" @click.stop="deleteItem(item.id)" title="Удалить">×</button>
        </div>
      </div>
    </aside>

    <!-- Правая панель: форма конструктора -->
    <main class="panel-right">
      <div class="builder-header">
        <h2>Новый позиционер</h2>
      </div>

      <div class="form-row-inline">
        <div class="form-row" style="flex:0.6">
          <label>Тип позиционера</label>
          <select v-model="form.acting_type" @change="onTypeChange">
            <option :value="null">— выберите тип —</option>
            <option v-for="at in actingTypes" :key="at.id" :value="at.id">{{ at.name }}</option>
          </select>
        </div>
        <div class="form-row" style="flex:1" v-if="form.acting_type">
          <label>Серия позиционеров</label>
          <select v-model="form.selected_model_line" @change="onModelLineChange">
            <option :value="null">— выберите серию —</option>
            <option v-for="ml in modelLines" :key="ml.id" :value="ml.id">
              {{ ml.name }} ({{ ml.code }})
            </option>
          </select>
        </div>
      </div>

      <template v-if="form.selected_model_line && options">
        <h3>Опции серии</h3>
        <div class="options-grid">
          <div class="form-row" v-for="opt in optionFields" :key="opt.key">
            <label>{{ opt.label }}</label>
            <select v-model="form[opt.key]" :disabled="opt.disabled">
              <option v-for="o in opt.items" :key="o.id" :value="o[opt.valueKey]">
                {{ optionLabel(opt, o) }}{{ o.is_default ? ' (стандарт)' : '' }}
              </option>
            </select>
          </div>

          <!-- Взрывозащита: строка-кодировка (варианты Exd — внутри опции) -->
          <div class="form-row" v-if="exdRows.length">
            <label>Взрывозащита</label>
            <select v-model="form.selected_exd_row" :disabled="exdRows.length <= 1" @change="onExdRowChange">
              <option v-for="row in exdRows" :key="row.id" :value="row.id">
                {{ row.name }}{{ row.is_default ? ' (стандарт)' : '' }}
              </option>
            </select>
          </div>
        </div>
      </template>

      <!-- Предупреждения (only_non_ex при выборе Ex) -->
      <div class="warnings" v-if="previewWarnings.length">
        <div v-for="(w, i) in previewWarnings" :key="i" class="warning">
          ⚠ {{ w.message }}
        </div>
      </div>

      <!-- Карточка товара (live preview) -->
      <div class="preview" v-if="previewData">
        <h3>Превью: <span class="preview-code">{{ previewData.code }}</span></h3>
        <PaProductCard :preview="previewData" />
      </div>

      <div class="actions">
        <button class="btn primary" @click="save" :disabled="!canSave || saving">
          {{ saving ? 'Сохранение...' : 'Сохранить' }}
        </button>
        <button class="btn secondary" @click="resetForm">Сбросить</button>
      </div>

      <div class="message" :class="message?.type" v-if="message">{{ message.text }}</div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import api from './api'
import PaProductCard from '@/shared/components/catalog/PaProductCard.vue'

const actingTypes = ref([])
const modelLines = ref([])
const filterModelLines = ref([])
const savedList = ref([])
const loadingList = ref(false)
const options = ref(null)
const message = ref(null)
const previewData = ref(null)
const previewWarnings = ref([])
const saving = ref(false)

// Единый маппинг опций: ключ формы → ключ ответа options + какой id использовать
// (option_id — реальная опция; id — through-строка для профилей сигналов и температуры)
const OPTION_MAP = {
  selected_body_connection:     { label: 'Присоединения корпуса', apiKey: 'body_connections', valueKey: 'option_id' },
  selected_lever:               { label: 'Рычаг', apiKey: 'levers', valueKey: 'option_id' },
  selected_temperature:         { label: 'Температурное исполнение', apiKey: 'temperature_options', valueKey: 'option_id' },
  selected_signal_profile_option: { label: 'Профиль сигналов (обратная связь)', apiKey: 'signal_profiles', valueKey: 'id' },
  selected_alarm:               { label: 'Сигнал тревоги', apiKey: 'alarms', valueKey: 'option_id' },
}

const filters = reactive({ search: '', acting_type: null, model_line: null })

const defaultForm = () => ({
  acting_type: null,
  selected_model_line: null,
  selected_body_connection: null,
  selected_lever: null,
  selected_temperature: null,
  selected_signal_profile_option: null,
  selected_alarm: null,
  selected_exd_row: null,
  selected_exd: null,
})

const form = reactive(defaultForm())

const canSave = computed(() => !!form.selected_model_line)

const filteredList = computed(() => {
  let list = savedList.value
  const s = (filters.search || '').toLowerCase()
  if (s) {
    list = list.filter(item =>
      (item.code || '').toLowerCase().includes(s) ||
      (item.name || '').toLowerCase().includes(s) ||
      (item.description || '').toLowerCase().includes(s))
  }
  return list
})

const optionFields = computed(() => {
  if (!options.value) return []
  return Object.entries(OPTION_MAP).map(([key, cfg]) => ({
    key, label: cfg.label,
    items: options.value[cfg.apiKey] || [],
    valueKey: cfg.valueKey,
    disabled: (options.value[cfg.apiKey] || []).length <= 1,
  }))
})

const exdRows = computed(() => options.value?.exd_options || [])

const selectedExdRow = computed(() =>
  exdRows.value.find(r => r.id === form.selected_exd_row) || null)

// Ex-режим: выбран вид Exd с непустым code (общепром — пустой code / нет варианта)
const isExMode = computed(() => {
  if (!form.selected_exd || !selectedExdRow.value) return false
  const variant = selectedExdRow.value.variants.find(v => v.option_id === form.selected_exd)
  return !!variant?.code
})

function optionLabel(opt, o) {
  let label = o.name
  if (opt.apiKey === 'signal_profiles') {
    if (o.encoding) label += ` [${o.encoding}]`
    if (o.capabilities_display) label += ` · ${o.capabilities_display}`
  } else if (o.encoding) {
    label += ` [${o.encoding}]`
  }
  if (o.only_non_ex && isExMode.value) label += ' ⛔ (только общепром)'
  return label
}

onMounted(async () => {
  try {
    actingTypes.value = (await api.getActingTypes()).data
    await loadList()
  } catch (e) { showMessage('Ошибка загрузки', 'error') }
})

async function loadList() {
  loadingList.value = true
  try {
    const params = {}
    if (filters.acting_type) params.acting_type_id = filters.acting_type
    if (filters.model_line) params.model_line_id = filters.model_line
    savedList.value = (await api.list(params)).data
  } catch (e) { /* */ }
  finally { loadingList.value = false }
}

async function onFilterTypeChange() {
  filters.model_line = null
  filterModelLines.value = []
  if (filters.acting_type) {
    try { filterModelLines.value = (await api.getModelLines({ acting_type: filters.acting_type })).data }
    catch (e) { filterModelLines.value = [] }
  }
  await loadList()
}

async function onFilterChange() {
  await loadList()
}

async function deleteItem(id) {
  if (!confirm('Удалить конфигурацию?')) return
  try { await api.delete(id); await loadList(); showMessage('Удалено', 'success') }
  catch (e) { showMessage('Ошибка удаления', 'error') }
}

async function loadItem(item) {
  try {
    const d = (await api.getDetail(item.id)).data
    form.acting_type = d.acting_type?.id || null
    modelLines.value = []
    if (form.acting_type) {
      modelLines.value = (await api.getModelLines({ acting_type: form.acting_type })).data
    }
    form.selected_model_line = d.model_line?.id || null
    if (form.selected_model_line) {
      options.value = (await api.getOptions(form.selected_model_line)).data
    }
    form.selected_body_connection = d.selected_body_connection?.id || null
    form.selected_lever = d.selected_lever?.id || null
    form.selected_temperature = d.selected_temperature?.id || null
    form.selected_signal_profile_option = d.selected_signal_profile_option?.id || null
    form.selected_alarm = d.selected_alarm?.id || null
    form.selected_exd_row = d.selected_exd_row?.id || null
    form.selected_exd = d.selected_exd?.id || null
    previewWarnings.value = []
    previewData.value = d.item ? { ...d.item, sku: d.sku, tech_description: null } : null
  } catch (e) { showMessage('Ошибка загрузки', 'error') }
}

// --- каскад ---

async function onTypeChange() {
  clearOptions()
  form.selected_model_line = null
  modelLines.value = []
  if (!form.acting_type) return
  try {
    modelLines.value = (await api.getModelLines({ acting_type: form.acting_type })).data
  } catch (e) { showMessage('Ошибка загрузки серий', 'error') }
}

async function onModelLineChange() {
  clearOptions()
  if (!form.selected_model_line) return
  try {
    options.value = (await api.getOptions(form.selected_model_line)).data
    autoFillDefaults()
  } catch (e) { showMessage('Ошибка загрузки опций', 'error') }
}

function onExdRowChange() {
  const row = selectedExdRow.value
  form.selected_exd = row?.variants?.[0]?.option_id || null
}

function clearOptions() {
  options.value = null
  previewData.value = null
  previewWarnings.value = []
  form.selected_body_connection = null
  form.selected_lever = null
  form.selected_temperature = null
  form.selected_signal_profile_option = null
  form.selected_alarm = null
  form.selected_exd_row = null
  form.selected_exd = null
}

function autoFillDefaults() {
  if (!options.value) return
  for (const [key, cfg] of Object.entries(OPTION_MAP)) {
    const items = options.value[cfg.apiKey]
    if (!items?.length) continue
    if (items.length === 1) form[key] = items[0][cfg.valueKey]
    else if (form[key] == null) {
      const def = items.find(o => o.is_default)
      if (def) form[key] = def[cfg.valueKey]
    }
  }
  // Взрывозащита: строка + первый вариант (или null для общепром)
  if (exdRows.value.length) {
    let row = exdRows.value.find(r => r.id === form.selected_exd_row)
    if (!row) {
      row = exdRows.value.find(r => r.is_default) || exdRows.value[0]
      form.selected_exd_row = row.id
    }
    if (form.selected_exd == null) {
      form.selected_exd = row.variants?.[0]?.option_id || null
    }
  }
}

// --- сохранение ---

async function save() {
  saving.value = true
  try {
    const res = await api.create({ ...form })
    const sku = res.data?.sku
    const base = res.status === 201
      ? 'Создано: ' + (res.data.name || res.data.code || '')
      : 'Конфигурация уже существует: ' + (res.data.code || '')
    showMessage(base + (sku ? ' | SKU: ' + sku.code : ''), 'success')
    previewData.value = res.data.item ? { ...res.data.item, sku: res.data.sku } : null
    previewWarnings.value = []
    await loadList()
  } catch (e) {
    const detail = e.response?.data?.error || e.displayMessage || 'Ошибка сохранения'
    showMessage(detail, 'error')
  } finally { saving.value = false }
}

function resetForm() {
  Object.assign(form, defaultForm())
  clearOptions()
  modelLines.value = []
}

// --- live preview ---
let previewTimer = null
watch(() => ({ ...form }), () => {
  if (!form.selected_model_line) { previewData.value = null; return }
  clearTimeout(previewTimer)
  previewTimer = setTimeout(async () => {
    try {
      const res = await api.preview({ ...form })
      previewData.value = res.data
      previewWarnings.value = res.data.warnings || []
    } catch (e) { /* */ }
  }, 300)
}, { deep: true })

function showMessage(text, type = 'info') {
  message.value = { text, type }
  setTimeout(() => { message.value = null }, 4000)
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
.builder-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.builder-header h2 { font-size: 18px; margin: 0; }
h3 { font-size: 15px; color: #555; margin: 16px 0 8px; }
.options-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 16px; }
.form-row-inline { display: flex; gap: 12px; align-items: flex-end; margin-bottom: 12px; }
.form-row { margin-bottom: 12px; }
.form-row label { display: block; font-size: 13px; color: #555; margin-bottom: 4px; }
.form-row select { width: 100%; padding: 8px 10px; font-size: 14px; border: 1px solid #ccc; border-radius: 6px; background: #fff; }
.form-row select:focus { outline: none; border-color: #4a6cf7; }
.form-row select:disabled { background: #f3f3f5; color: #555; cursor: not-allowed; border-color: #ddd; }
.warnings { margin-top: 12px; display: flex; flex-direction: column; gap: 6px; }
.warning { background: #fff7e6; border: 1px solid #f0d9a0; color: #8a6d1a; border-radius: 6px; padding: 8px 12px; font-size: 13px; }
.preview { margin-top: 20px; }
.preview h3 { display: flex; align-items: center; gap: 10px; }
.preview-code { font-family: monospace; color: #4a6cf7; }
.actions { margin-top: 20px; display: flex; gap: 10px; }
.btn { padding: 10px 24px; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; }
.btn.primary { background: #4a6cf7; color: #fff; }
.btn.primary:disabled { background: #a0b4f7; cursor: not-allowed; }
.btn.secondary { background: #eee; color: #333; }
.message { margin-top: 12px; padding: 8px 12px; border-radius: 6px; font-size: 13px; }
.message.success { background: #e6f7e6; color: #2a7a2a; }
.message.error { background: #fde6e6; color: #a33; }
.message.info { background: #e8f0fe; color: #2a5db0; }
</style>
