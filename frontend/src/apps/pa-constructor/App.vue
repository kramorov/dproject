<!-- pa-constructor/App.vue — двухпанельный конструктор пневмопривода -->
<template>
  <div class="constructor-app">
    <!-- Левая панель: список конфигураций + фильтры -->
    <aside class="panel-left">
      <h2>Сохранённые конфигурации</h2>

      <div class="filter-bar">
        <input v-model="filters.search" placeholder="Поиск по коду/названию..." class="filter-input" />
        <select v-model="filters.model_line" @change="onFilterChange">
          <option :value="null">Все серии</option>
          <option v-for="ml in modelLines" :key="ml.id" :value="ml.id">{{ ml.name }}</option>
        </select>
        <select v-model="filters.model_line_item" @change="onFilterChange" :disabled="!filters.model_line">
          <option :value="null">Все модели</option>
          <option v-for="mli in filterModelLineItems" :key="mli.id" :value="mli.id">{{ mli.name }}</option>
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
        <label>Серия пневмоприводов</label>
        <select v-model="form.selected_model_line" @change="onModelLineChange">
          <option :value="null">— выберите серию —</option>
          <option v-for="ml in modelLines" :key="ml.id" :value="ml.id">{{ ml.name }} ({{ ml.code }})</option>
        </select>
      </div>

      <div class="form-row" v-if="form.selected_model_line">
        <label>Вид привода</label>
        <select v-model="form.selected_variety" @change="onVarietyChange">
          <option :value="null">— выберите вид —</option>
          <option value="DA">DA — двойного действия</option>
          <option value="SR">SR — с возвратной пружиной</option>
        </select>
      </div>

      <div class="form-row" v-if="form.selected_variety">
        <label>Модель</label>
        <select v-model="form.selected_model_line_item" @change="onModelLineItemChange">
          <option :value="null">— выберите модель —</option>
          <option v-for="item in modelLineItems" :key="item.id" :value="item.id">{{ item.name }}</option>
        </select>
      </div>

      <template v-if="form.selected_model_line_item && options">
        <h3>Опции</h3>
        <div class="options-grid">
          <div class="form-row" v-for="opt in optionFields" :key="opt.key">
            <label>{{ opt.label }}</label>
            <select v-model="form[opt.key]" :disabled="opt.disabled">
              <option v-for="o in opt.items" :key="o.option_id" :value="o.option_id">
                {{ o.name }}{{ o.is_default ? ' (стандарт)' : '' }}
              </option>
            </select>
          </div>
        </div>
      </template>

      <div class="preview" v-if="previewText">
        <h3>Предпросмотр
          <button class="btn small" @click="showTechModal = true" v-if="techDescription">📄 Просмотр</button>
        </h3>
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

    <!-- Модалка -->
    <Teleport to="body">
      <div class="modal-overlay" v-if="showTechModal" @click.self="showTechModal = false">
        <div class="modal-content">
          <div class="modal-header">
            <h3>Техническое описание</h3>
            <button class="btn-icon close" @click="showTechModal = false">×</button>
          </div>
          <div class="modal-body" v-html="techDescription"></div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import api from './api'

const modelLines = ref([])
const modelLineItems = ref([])
const filterModelLineItems = ref([])
const savedList = ref([])
const loadingList = ref(false)
const options = ref(null)
const message = ref(null)
const previewText = ref('')
const techDescription = ref('')
const showTechModal = ref(false)
const saving = ref(false)

// Единый маппинг опций: ключ формы → ключ в ответе API
const OPTION_MAP = {
  selected_safety_position: { label: 'Положение безопасности', apiKey: 'safety_positions' },
  selected_springs_qty:      { label: 'Количество пружин',     apiKey: 'springs_qty_options' },
  selected_temperature:      { label: 'Температурное исполнение', apiKey: 'temperature_options' },
  selected_ip:               { label: 'IP защита',             apiKey: 'ip_options' },
  selected_exd:              { label: 'Взрывозащита',          apiKey: 'exd_options' },
  selected_body_coating:     { label: 'Покрытие корпуса',      apiKey: 'body_coating_options' },
  selected_hand_wheel:       { label: 'Ручной дублер',         apiKey: 'hand_wheel_options' },
}

const filters = reactive({ search: '', model_line: null, model_line_item: null })

const defaultForm = () => ({
  selected_model_line: null,
  selected_variety: null,
  selected_model_line_item: null,
  selected_safety_position: null,
  selected_springs_qty: null,
  selected_temperature: null,
  selected_ip: null,
  selected_exd: null,
  selected_body_coating: null,
  selected_hand_wheel: null,
})

const form = reactive(defaultForm())
const canSave = computed(() => form.selected_model_line_item)

const filteredList = computed(() => {
  let list = savedList.value
  const s = (filters.search || '').toLowerCase()
  if (s) list = list.filter(item => (item.code || '').toLowerCase().includes(s) || (item.name || '').toLowerCase().includes(s))
  return list
})

const optionFields = computed(() => {
  if (!options.value) return []
  return Object.entries(OPTION_MAP).map(([key, cfg]) => ({
    key, label: cfg.label,
    items: options.value[cfg.apiKey] || [],
    disabled: (options.value[cfg.apiKey] || []).length <= 1,
  }))
})

onMounted(async () => {
  try { modelLines.value = (await api.getModelLines()).data; await loadList() }
  catch (e) { showMessage('Ошибка загрузки', 'error') }
})

async function loadList() {
  loadingList.value = true
  try {
    const params = {}
    if (filters.model_line) params.model_line_id = filters.model_line
    if (filters.model_line_item) params.model_line_item_id = filters.model_line_item
    savedList.value = (await api.list(params)).data
  } catch (e) { /* */ }
  finally { loadingList.value = false }
}

async function onFilterChange() {
  // Поиск — клиентский, API не дёргаем
  if (filters.model_line) {
    try { filterModelLineItems.value = (await api.getModelLineItems(filters.model_line)).data }
    catch (e) { filterModelLineItems.value = [] }
    if (!filterModelLineItems.value.find(m => m.id === filters.model_line_item)) filters.model_line_item = null
  } else { filterModelLineItems.value = []; filters.model_line_item = null }
  // При смене серии/модели грузим список с серверными фильтрами
  if (filters.model_line || filters.model_line_item) await loadList()
}

async function deleteItem(id) {
  if (!confirm('Удалить конфигурацию?')) return
  try { await api.delete(id); await loadList(); showMessage('Удалено', 'success') }
  catch (e) { showMessage('Ошибка удаления', 'error') }
}

async function loadItem(item) {
  try {
    const d = (await api.getDetail(item.id)).data
    form.selected_model_line = d.model_line?.id || null
    form.selected_variety = null

    if (form.selected_model_line) {
      const items = (await api.getModelLineItems(form.selected_model_line)).data
      modelLineItems.value = items
      const mli = items.find(i => i.id === d.model_line_item?.id)
      if (mli?.variety) {
        form.selected_variety = mli.variety
        modelLineItems.value = (await api.getModelLineItems(form.selected_model_line, mli.variety)).data
      }
    }

    form.selected_model_line_item = d.model_line_item?.id || null
    for (const key of Object.keys(OPTION_MAP)) {
      if (d[key]?.id) form[key] = d[key].id
    }

    options.value = (await api.getOptions(form.selected_model_line_item)).data
    previewText.value = d.description || ''
  } catch (e) { showMessage('Ошибка загрузки', 'error') }
}

// --- cascade (no draft creation) ---
async function onModelLineChange() {
  form.selected_variety = null; form.selected_model_line_item = null
  modelLineItems.value = []; options.value = null; previewText.value = ''
}
async function onVarietyChange() {
  form.selected_model_line_item = null; modelLineItems.value = []; options.value = null; previewText.value = ''
  if (!form.selected_variety || !form.selected_model_line) return
  try { modelLineItems.value = (await api.getModelLineItems(form.selected_model_line, form.selected_variety)).data }
  catch (e) { showMessage('Ошибка загрузки моделей', 'error') }
}
async function onModelLineItemChange() {
  options.value = null; previewText.value = ''
  if (!form.selected_model_line_item) return
  try {
    options.value = (await api.getOptions(form.selected_model_line_item)).data
    autoFillDefaults()
  } catch (e) { showMessage('Ошибка загрузки опций', 'error') }
}

function autoFillDefaults() {
  if (!options.value) return
  for (const [key, cfg] of Object.entries(OPTION_MAP)) {
    const items = options.value[cfg.apiKey]
    if (!items?.length) continue
    if (items.length === 1) form[key] = items[0].option_id
    else if (form[key] == null) {
      const def = items.find(o => o.is_default)
      if (def) form[key] = def.option_id
    }
  }
}

// --- save: always POST (create new), never PUT ---
async function save() {
  saving.value = true
  try {
    const res = await api.create({ ...form })
    showMessage(res.status === 201 ? 'Создано: ' + res.data.name : 'Найдена существующая: ' + res.data.name, 'success')
    previewText.value = res.data.description || ''
    await loadList()
  } catch (e) {
    const msg = e.response?.data?.detail || 'Ошибка сохранения'
    showMessage(msg, 'error')
  }
  finally { saving.value = false }
}

function resetForm() {
  Object.assign(form, defaultForm())
  options.value = null; modelLineItems.value = []
  previewText.value = ''; techDescription.value = ''
}

// --- live preview ---
let previewTimer = null
watch(() => ({ ...form }), () => {
  if (!form.selected_model_line_item) return
  clearTimeout(previewTimer)
  previewTimer = setTimeout(async () => {
    try {
      const res = await api.preview({ ...form })
      previewText.value = `${res.data.name}\n${res.data.description}`
      techDescription.value = res.data.tech_description || ''
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
.builder-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.builder-header h2 { font-size: 18px; margin: 0; }
h3 { font-size: 15px; color: #555; margin: 16px 0 8px; }
.options-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 16px; }
.form-row { margin-bottom: 12px; }
.form-row label { display: block; font-size: 13px; color: #555; margin-bottom: 4px; }
.form-row select { width: 100%; padding: 8px 10px; font-size: 14px; border: 1px solid #ccc; border-radius: 6px; background: #fff; }
.form-row select:focus { outline: none; border-color: #4a6cf7; }
.form-row select:disabled { background: #f3f3f5; color: #555; cursor: not-allowed; border-color: #ddd; }
.preview { margin-top: 20px; }
.preview h3 { display: flex; align-items: center; gap: 10px; }
.preview-text { background: #f7f7f9; border: 1px solid #e0e0e6; border-radius: 6px; padding: 12px; font-size: 13px; white-space: pre-wrap; word-break: break-word; max-height: 200px; overflow-y: auto; }
.actions { margin-top: 20px; display: flex; gap: 10px; }
.btn { padding: 10px 24px; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; }
.btn.primary { background: #4a6cf7; color: #fff; }
.btn.primary:disabled { background: #a0b4f7; cursor: not-allowed; }
.btn.secondary { background: #eee; color: #333; }
.btn.small { padding: 4px 12px; font-size: 12px; }
.message { margin-top: 12px; padding: 8px 12px; border-radius: 6px; font-size: 13px; }
.message.success { background: #e6f7e6; color: #2a7a2a; }
.message.error { background: #fde6e6; color: #a33; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: #fff; border-radius: 10px; max-width: 780px; width: 92%; max-height: 85vh; display: flex; flex-direction: column; box-shadow: 0 8px 40px rgba(0,0,0,.2); }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #eee; }
.modal-header h3 { margin: 0; font-size: 16px; }
.modal-header .close { font-size: 22px; border: none; background: none; cursor: pointer; color: #888; }
.modal-body { padding: 20px; overflow-y: auto; font-size: 13px; line-height: 1.6; flex: 1; }
</style>
