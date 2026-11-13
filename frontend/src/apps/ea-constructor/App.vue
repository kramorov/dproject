<!-- ea-constructor/App.vue — двухпанельный конструктор электропривода -->
<template>
  <div class="constructor-app">
    <!-- Левая панель: список конфигураций + фильтры -->
    <aside class="panel-left">
      <h2>{{ t('eaCtor.saved') }}</h2>

      <div class="filter-bar">
        <input v-model="filters.search" :placeholder="t('eaCtor.searchPlaceholder')" class="filter-input" />
        <select v-model="filters.model_line" @change="onFilterChange">
          <option :value="null">{{ t('eaCtor.allSeries') }}</option>
          <option v-for="ml in modelLines" :key="ml.id" :value="ml.id">{{ ml.name }}</option>
        </select>
        <select v-model="filters.model_line_item" @change="onFilterChange" :disabled="!filters.model_line">
          <option :value="null">{{ t('eaCtor.allModels') }}</option>
          <option v-for="mli in filterModelLineItems" :key="mli.id" :value="mli.id">{{ mli.name }}</option>
        </select>
      </div>

      <div class="saved-list">
        <div v-if="loadingList" class="list-status">{{ t('eaCtor.loading') }}</div>
        <div v-else-if="!filteredList.length" class="list-status">{{ t('eaCtor.noSaved') }}</div>
        <div
          v-for="item in filteredList" :key="item.id"
          class="saved-card"
          @click="loadItem(item)"
        >
          <div class="card-code">{{ item.code || '—' }}</div>
          <div class="card-model">{{ item.model_line_item?.name || '' }}</div>
          <div class="card-desc">{{ item.description?.substring(0, 80) || '' }}</div>
          <button class="btn-icon delete" @click.stop="deleteItem(item.id)" :title="t('eaCtor.delete')">×</button>
        </div>
      </div>
    </aside>

    <!-- Правая панель: форма конструктора -->
    <main class="panel-right">
      <div class="builder-header">
        <h2>{{ t('eaCtor.newConfig') }}</h2>
      </div>

      <div class="form-row">
        <label>{{ t('eaCtor.series') }}</label>
        <select v-model="form.selected_model_line" @change="onModelLineChange">
          <option :value="null">{{ t('eaCtor.chooseSeries') }}</option>
          <option v-for="ml in modelLines" :key="ml.id" :value="ml.id">{{ ml.name }} ({{ ml.code }})</option>
        </select>
      </div>

      <div class="form-row" v-if="form.selected_model_line">
        <label>{{ t('eaCtor.model') }}</label>
        <select v-model="form.selected_model_line_item" @change="onModelLineItemChange" :disabled="!modelLineItems.length">
          <option :value="null">{{ t('eaCtor.chooseModel') }}</option>
          <option v-for="item in modelLineItems" :key="item.id" :value="item.id">{{ item.name }}</option>
        </select>
      </div>

      <!-- Напряжение питания — появляется после выбора модели -->
      <div class="form-row" v-if="form.selected_model_line_item && powerSupplyOptions.length">
        <label>{{ t('eaCtor.powerSupply') }}</label>
        <select v-model="form.selected_power_supply" @change="onPowerSupplyChange">
          <option :value="null">{{ t('eaCtor.choosePowerSupply') }}</option>
          <option v-for="ps in powerSupplyOptions" :key="ps.option_id" :value="ps.option_id">{{ ps.name }}</option>
        </select>
      </div>

      <template v-if="form.selected_model_line_item && options">
        <h3>{{ t('eaCtor.options') }}</h3>
        <div class="options-grid">
          <div class="form-row" v-for="opt in standardOptionFields" :key="opt.key">
            <label>{{ opt.label }}</label>
            <select v-model="form[opt.key]" :disabled="opt.disabled">
              <option v-for="o in opt.items" :key="o.option_id" :value="o.option_id">
                {{ o.name }}
              </option>
            </select>
          </div>
        </div>

        <!-- Зависимые от напряжения опции -->
        <template v-if="powerDependentOptions.length">
          <h3>{{ t('eaCtor.powerDependent') }}</h3>
          <div class="options-grid">
            <div class="form-row" v-for="opt in powerDependentOptions" :key="opt.key">
              <label>{{ opt.label }}</label>
              <select v-model="form[opt.key]" :disabled="opt.disabled">
                <option v-for="o in opt.items" :key="o.option_id" :value="o.option_id">
                  {{ o.name }}
                </option>
              </select>
            </div>
          </div>
        </template>

        <!-- Блок управления (слотовая модель) -->
        <div class="form-row" v-if="controlUnitOptions.length">
          <label>{{ t('eaCtor.lbl.controlUnit') }}</label>
          <select v-model="form.selected_control_unit" @change="onControlUnitChange">
            <option :value="null">{{ t('eaCtor.choose') }}</option>
            <option v-for="o in controlUnitOptions" :key="o.option_id" :value="o.option_id">
              {{ o.name }}<template v-if="o.code"> ({{ o.code }})</template>
            </option>
          </select>
        </div>

        <!-- Слоты выбранного БУ -->
        <div v-if="controlUnitPackage" class="cu-package">
          <h3>{{ t('eaCtor.controlUnitOptions') }}</h3>
          <CuSlotConfigurator :key="form.selected_control_unit" :pkg="controlUnitPackage" v-model="form.control_unit_snapshot" />
        </div>
      </template>

      <div class="preview" v-if="previewText">
        <h3>{{ t('eaCtor.preview') }}
          <button class="btn small" @click="showTechModal = true" v-if="techDescription">{{ t('eaCtor.view') }}</button>
        </h3>
        <pre class="preview-text">{{ previewText }}</pre>
      </div>

      <div class="actions">
        <button class="btn primary" @click="save" :disabled="!canSave || saving">
          {{ saving ? t('eaCtor.saving') : t('eaCtor.create') }}
        </button>
        <button class="btn secondary" @click="resetForm">{{ t('eaCtor.reset') }}</button>
      </div>

      <div class="message" v-if="message" :class="message.type">{{ message.text }}</div>
    </main>

    <!-- Модалка -->
    <Teleport to="body">
      <div class="modal-overlay" v-if="showTechModal" @click.self="showTechModal = false">
        <div class="modal-content">
          <div class="modal-header">
            <h3>{{ t('eaCtor.specification') }}</h3>
            <button class="btn small" @click="downloadSpec" :disabled="downloadingSpec">
              {{ downloadingSpec ? t('eaCtor.downloading') : t('eaCtor.downloadSpec') }}
            </button>
            <button class="btn-icon close" @click="showTechModal = false">×</button>
          </div>
          <div class="modal-body">
            <div v-if="spec" class="spec">
              <div v-for="(group, gtitle) in spec" :key="gtitle" class="spec-group">
                <h4 class="spec-group-title">{{ gtitle }}</h4>
                <div v-for="(value, label) in group" :key="label" class="spec-row">
                  <span class="spec-label">{{ label }}</span>
                  <span class="spec-value">{{ value }}</span>
                </div>
              </div>
            </div>
            <div v-else v-html="techDescription"></div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useI18n } from '@/shared/i18n'
import api from './api'
import CuSlotConfigurator from '@/components/admin/CuSlotConfigurator.vue'

const { t } = useI18n()

const modelLines = ref([])
const modelLineItems = ref([])
const filterModelLineItems = ref([])
const savedList = ref([])
const loadingList = ref(false)
const options = ref(null)
const message = ref(null)
const previewText = ref('')
const techDescription = ref('')
const spec = ref(null)
const showTechModal = ref(false)
const downloadingSpec = ref(false)
const saving = ref(false)

// Опции, не зависящие от напряжения (model_line + model_line_item + model_body)
const STANDARD_OPTIONS = {
  selected_temperature:              { label: 'eaCtor.lbl.temperature',   apiKey: 'temperature_options' },
  selected_ip:                       { label: 'eaCtor.lbl.ip',            apiKey: 'ip_options' },
  selected_exd:                      { label: 'eaCtor.lbl.exd',           apiKey: 'exd_options' },
  selected_body_coating:             { label: 'eaCtor.lbl.coating',       apiKey: 'body_coating_options' },
  selected_body_color_option:        { label: 'eaCtor.lbl.color',         apiKey: 'body_color_options' },
  selected_hand_wheel:               { label: 'eaCtor.lbl.handWheel',     apiKey: 'hand_wheel_options' },
  selected_turn_angle_option:        { label: 'eaCtor.lbl.turnAngle',     apiKey: 'turn_angle_options' },
  selected_cable_glands_holes:       { label: 'eaCtor.lbl.cableGlands',   apiKey: 'cable_glands_holes_options' },
}

// Опции, зависящие от выбранного напряжения
const POWER_DEPENDENT = {
  selected_safety_position:      { label: 'eaCtor.lbl.safetyPosition', apiKey: 'safety_position_options' },
}

const filters = reactive({ search: '', model_line: null, model_line_item: null })

const defaultForm = () => ({
  selected_model_line: null,
  selected_model_line_item: null,
  selected_power_supply: null,
  selected_safety_position: null,
  selected_control_unit: null,
  control_unit_snapshot: {},
  selected_temperature: null,
  selected_ip: null,
  selected_exd: null,
  selected_body_coating: null,
  selected_body_color_option: null,
  selected_hand_wheel: null,
  selected_turn_angle_option: null,
  selected_cable_glands_holes: null,
})

const form = reactive(defaultForm())
const canSave = computed(() => form.selected_model_line_item && form.selected_power_supply && form.selected_control_unit)

const filteredList = computed(() => {
  let list = savedList.value
  const s = (filters.search || '').toLowerCase()
  if (s) list = list.filter(item => (item.code || '').toLowerCase().includes(s) || (item.name || '').toLowerCase().includes(s))
  return list
})

const powerSupplyOptions = computed(() => {
  if (!options.value) return []
  return options.value.power_supply_options || []
})

const standardOptionFields = computed(() => {
  if (!options.value) return []
  return Object.entries(STANDARD_OPTIONS).map(([key, cfg]) => ({
    key, label: t(cfg.label),
    items: options.value[cfg.apiKey] || [],
    disabled: (options.value[cfg.apiKey] || []).length <= 1,
  }))
})

const powerDependentOptions = computed(() => {
  if (!options.value || !form.selected_power_supply) return []
  return Object.entries(POWER_DEPENDENT).map(([key, cfg]) => ({
    key, label: t(cfg.label),
    items: options.value[cfg.apiKey] || [],
    disabled: (options.value[cfg.apiKey] || []).length <= 1,
  }))
})

const controlUnitOptions = computed(() => options.value?.control_unit_options || [])
const controlUnitPackage = computed(() => options.value?.control_unit_package || null)

function autoFillControlUnit() {
  const items = controlUnitOptions.value
  if (!items?.length) { form.selected_control_unit = null; return }
  if (items.length === 1) { form.selected_control_unit = items[0].option_id; return }
  // Текущее значение не в списке (другая модель) — сбрасываем
  if (form.selected_control_unit != null
      && !items.some(o => o.option_id === form.selected_control_unit)) {
    form.selected_control_unit = null
  }
  if (form.selected_control_unit == null) {
    const def = items.find(o => o.is_default) || items[0]
    form.selected_control_unit = def.option_id
  }
}

async function onControlUnitChange() {
  form.control_unit_snapshot = {}
  if (!form.selected_model_line_item || !form.selected_control_unit) return
  try {
    options.value = (await loadOptions()).data
  } catch (e) { showMessage(t('eaCtor.errLoadOptions'), 'error') }
}

onMounted(async () => {
  try { modelLines.value = (await api.getModelLines()).data; await loadList() }
  catch (e) { showMessage(t('eaCtor.errLoad'), 'error') }
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
  if (filters.model_line) {
    try { filterModelLineItems.value = (await api.getModelLineItems(filters.model_line)).data }
    catch (e) { filterModelLineItems.value = [] }
    if (!filterModelLineItems.value.find(m => m.id === filters.model_line_item)) filters.model_line_item = null
  } else { filterModelLineItems.value = []; filters.model_line_item = null }
  if (filters.model_line || filters.model_line_item) await loadList()
}

async function deleteItem(id) {
  if (!confirm(t('eaCtor.deleteConfirm'))) return
  try { await api.delete(id); await loadList(); showMessage(t('eaCtor.deleted'), 'success') }
  catch (e) { showMessage(t('eaCtor.errDelete'), 'error') }
}

async function loadItem(item) {
  try {
    const d = (await api.getDetail(item.id)).data
    form.selected_model_line = d.model_line?.id || null
    form.selected_model_line_item = null
    form.selected_power_supply = null

    if (form.selected_model_line) {
      modelLineItems.value = (await api.getModelLineItems(form.selected_model_line)).data
    }

    form.selected_model_line_item = d.model_line_item?.id || null

    if (d.selected_power_supply?.id) form.selected_power_supply = d.selected_power_supply.id
    if (d.selected_safety_position?.id) form.selected_safety_position = d.selected_safety_position.id
    if (d.selected_control_unit?.id) form.selected_control_unit = d.selected_control_unit.id
    if (d.control_unit_snapshot) form.control_unit_snapshot = { ...d.control_unit_snapshot }

    // Загружаем опции (с power_supply_id и control_unit_id)
    if (form.selected_model_line_item) {
      options.value = (await loadOptions()).data
      autoFillFromData(d)
    }

    previewText.value = d.description || ''
  } catch (e) { showMessage(t('eaCtor.errLoad'), 'error') }
}

function autoFillFromData(d) {
  if (d.control_unit_snapshot && typeof d.control_unit_snapshot === 'object') {
    form.control_unit_snapshot = { ...d.control_unit_snapshot }
  }

  // Заполняем стандартные опции
  for (const key of Object.keys(STANDARD_OPTIONS)) {
    if (d[key]?.id) form[key] = d[key].id
  }
}

// --- cascade ---
async function onModelLineChange() {
  form.selected_model_line_item = null; form.selected_power_supply = null
  form.selected_control_unit = null; form.control_unit_snapshot = {}
  modelLineItems.value = []; options.value = null; previewText.value = ''
  if (!form.selected_model_line) return
  try { modelLineItems.value = (await api.getModelLineItems(form.selected_model_line)).data }
  catch (e) { showMessage(t('eaCtor.errLoadModels'), 'error') }
}

async function onModelLineItemChange() {
  form.selected_power_supply = null
  form.selected_control_unit = null; form.control_unit_snapshot = {}
  options.value = null; previewText.value = ''
  if (!form.selected_model_line_item) return
  try {
    options.value = (await loadOptions()).data
    autoFillStandardDefaults()
    if (form.selected_power_supply) return  // одна опция — onPowerSupplyChange уже отработал
    autoFillControlUnit()
    if (form.selected_control_unit) {
      options.value = (await loadOptions()).data
    }
  } catch (e) { showMessage(t('eaCtor.errLoadOptions'), 'error') }
}

async function onPowerSupplyChange() {
  if (!form.selected_model_line_item || !form.selected_power_supply) return
  try {
    // Перезагружаем опции с power_supply_id — получаем safety_position
    options.value = (await loadOptions()).data
    autoFillPowerDependent()
    autoFillControlUnit()
    if (form.selected_control_unit) {
      options.value = (await loadOptions()).data
    }
  } catch (e) { showMessage(t('eaCtor.errLoadOptions'), 'error') }
}

async function loadOptions() {
  const mliId = form.selected_model_line_item
  const psId = form.selected_power_supply
  return api.getOptions(mliId, psId, form.selected_control_unit)
}

function autoFillStandardDefaults() {
  if (!options.value) return
  for (const [key, cfg] of Object.entries(STANDARD_OPTIONS)) {
    const items = options.value[cfg.apiKey]
    if (!items?.length) continue
    if (items.length === 1) form[key] = items[0].option_id
    else if (form[key] == null) {
      const def = items.find(o => o.is_default)
      if (def) form[key] = def.option_id
    }
  }
  // Автовыбор питания: если одна опция — сразу выбрана
  const psItems = options.value.power_supply_options
  if (psItems?.length === 1) {
    form.selected_power_supply = psItems[0].option_id
    onPowerSupplyChange()
  }
}

function autoFillPowerDependent() {
  if (!options.value) return
  for (const [key, cfg] of Object.entries(POWER_DEPENDENT)) {
    const items = options.value[cfg.apiKey]
    if (!items?.length) continue
    // Текущее значение не в списке (другое напряжение/серия) — сбрасываем
    if (form[key] != null && !items.some(o => o.option_id === form[key])) {
      form[key] = null
    }
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
    showMessage(res.status === 201 ? t('eaCtor.created') + res.data.name : t('eaCtor.foundExisting') + res.data.name, 'success')
    previewText.value = res.data.description || ''
    await loadList()
  } catch (e) {
    const msg = e.response?.data?.detail || t('eaCtor.errSave')
    showMessage(msg, 'error')
  }
  finally { saving.value = false }
}

function resetForm() {
  Object.assign(form, defaultForm())
  options.value = null; modelLineItems.value = []
  previewText.value = ''; techDescription.value = ''; spec.value = null
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
      spec.value = res.data.spec || null
    } catch (e) { /* */ }
  }, 300)
}, { deep: true })

function showMessage(text, type = 'info') {
  message.value = { text, type }
  setTimeout(() => { message.value = null }, 3000)
}

async function downloadSpec() {
  if (downloadingSpec.value) return
  downloadingSpec.value = true
  try {
    const res = await api.specDocx({ ...form })
    const blob = res.data
    const cd = res.headers?.['content-disposition'] || ''
    const m = cd.match(/filename\*?=(?:UTF-8''|")?([^;"]+)/i)
    const filename = m ? decodeURIComponent(m[1]) : 'Спецификация.docx'
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  } catch (e) {
    showMessage(e.displayMessage || t('eaCtor.errDownload'), 'error')
  } finally {
    downloadingSpec.value = false
  }
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
.cu-package { margin-top: 8px; }
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
.modal-header { display: flex; justify-content: space-between; align-items: center; gap: 10px; padding: 16px 20px; border-bottom: 1px solid #eee; }
.modal-header h3 { margin: 0; font-size: 16px; flex: 1; }
.modal-header .close { font-size: 22px; border: none; background: none; cursor: pointer; color: #888; }
.modal-body { padding: 20px; overflow-y: auto; font-size: 13px; line-height: 1.6; flex: 1; }
.spec-group { margin-bottom: 18px; }
.spec-group-title { margin: 0 0 8px; font-size: 14px; color: #1a1a2e; border-bottom: 1px solid #e5e7eb; padding-bottom: 4px; }
.spec-row { display: flex; gap: 12px; padding: 3px 0; }
.spec-label { flex: 0 0 46%; color: #666; }
.spec-value { flex: 1; color: #1a1a2e; word-break: break-word; }
</style>
