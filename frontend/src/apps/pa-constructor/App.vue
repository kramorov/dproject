<!-- pa-constructor/App.vue — конструктор пневмопривода (без списка сохранённых) -->
<template>
  <div class="constructor-app">
    <!-- Форма конструктора -->
    <main class="panel-right">
      <div class="builder-header">
        <h2>{{ t('paCtor.newConfig') }}</h2>
      </div>

      <div class="form-row-inline">
        <div class="form-row" style="flex:0.7">
          <label>{{ t('paCtor.series') }}</label>
          <select v-model="form.selected_model_line" @change="onModelLineChange">
            <option :value="null">{{ t('paCtor.chooseSeries') }}</option>
            <option v-for="ml in modelLines" :key="ml.id" :value="ml.id">{{ ml.name }} ({{ ml.code }})</option>
          </select>
        </div>
        <div class="form-row" style="flex:1" v-if="form.selected_model_line">
          <label>{{ t('paCtor.variety') }}</label>
          <select v-model="form.selected_variety" @change="onVarietyChange">
            <option :value="null">{{ t('paCtor.chooseVariety') }}</option>
            <option v-for="v in varieties" :key="v.id" :value="v.code">
              {{ v.name }} — {{ v.description }}
            </option>
          </select>
        </div>
        <div class="form-row" style="flex:0.7" v-if="form.selected_variety">
          <label>{{ t('paCtor.model') }}</label>
          <select v-model="form.selected_model_line_item" @change="onModelLineItemChange">
            <option :value="null">{{ t('paCtor.chooseModel') }}</option>
            <option v-for="item in modelLineItems" :key="item.id" :value="item.id">{{ item.name }}</option>
          </select>
        </div>
      </div>

      <template v-if="form.selected_model_line_item && options">
        <h3>{{ t('paCtor.options') }}</h3>
        <div class="options-grid">
          <div class="form-row" v-for="opt in optionFields" :key="opt.key">
            <label>{{ opt.label }}</label>
            <select v-model="form[opt.key]" :disabled="opt.disabled">
              <option v-for="o in opt.items" :key="o.option_id" :value="o.option_id">
                {{ o.name }}
              </option>
            </select>
          </div>
        </div>
      </template>

      <!-- Карточка товара -->
      <div class="preview" v-if="previewData">
        <PaProductCard :preview="previewData" @add-to-cart="onAddToCart" />
      </div>

      <div class="actions">
        <button class="btn primary" @click="save" :disabled="!canSave || saving">
          {{ saving ? t('paCtor.saving') : t('paCtor.create') }}
        </button>
        <button class="btn secondary" @click="resetForm">{{ t('paCtor.reset') }}</button>
      </div>

      <div class="message" v-if="message" :class="message.type">{{ message.text }}</div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useI18n } from '@/shared/i18n'
import api from './api'
import PaProductCard from '@/shared/components/catalog/PaProductCard.vue'

const { t } = useI18n()

const modelLines = ref([])
const modelLineItems = ref([])
const varieties = ref([])
const options = ref(null)
const message = ref(null)
const previewData = ref(null)
const saving = ref(false)

// Единый маппинг опций: ключ формы → ключ в ответе API
const OPTION_MAP = {
  selected_safety_position: { label: 'paCtor.lbl.safetyPosition', apiKey: 'safety_positions' },
  selected_springs_qty:      { label: 'paCtor.lbl.springsQty',     apiKey: 'springs_qty_options' },
  selected_temperature:      { label: 'paCtor.lbl.temperature',   apiKey: 'temperature_options' },
  selected_ip:               { label: 'paCtor.lbl.ip',            apiKey: 'ip_options' },
  selected_exd:              { label: 'paCtor.lbl.exd',           apiKey: 'exd_options' },
  selected_body_coating:     { label: 'paCtor.lbl.coating',       apiKey: 'body_coating_options' },
  selected_body_color:       { label: 'paCtor.lbl.color',         apiKey: 'body_color_options' },
  selected_manual_override:       { label: 'paCtor.lbl.manualOverride', apiKey: 'manual_override_options' },
}

// Ключи формы → ключи опций для create-sku (sku_service ждёт springs_qty, temperature, ...)
const SKU_OPTION_KEYS = {
  selected_safety_position: 'safety_position',
  selected_springs_qty: 'springs_qty',
  selected_temperature: 'temperature',
  selected_ip: 'ip',
  selected_exd: 'exd',
  selected_body_coating: 'body_coating',
  selected_body_color: 'body_color',
  selected_manual_override: 'manual_override',
}
function buildSkuOptionsPayload() {
  const opts = {}
  for (const [formKey, apiKey] of Object.entries(SKU_OPTION_KEYS)) {
    if (form[formKey] != null) opts[apiKey] = form[formKey]
  }
  return opts
}

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
  selected_body_color: null,
  selected_manual_override: null,
})

const form = reactive(defaultForm())
const canSave = computed(() => form.selected_model_line_item)

const optionFields = computed(() => {
  if (!options.value) return []
  return Object.entries(OPTION_MAP).map(([key, cfg]) => ({
    key, label: t(cfg.label),
    items: options.value[cfg.apiKey] || [],
    disabled: (options.value[cfg.apiKey] || []).length <= 1,
  }))
})

onMounted(async () => {
  try {
    modelLines.value = (await api.getModelLines()).data
    varieties.value = (await api.getVarieties()).data
  }
  catch (e) { showMessage(t('paCtor.errLoad'), 'error') }
})

// --- cascade (no draft creation) ---
async function onModelLineChange() {
  form.selected_variety = null; form.selected_model_line_item = null
  modelLineItems.value = []; options.value = null; previewData.value = null
}
async function onVarietyChange() {
  form.selected_model_line_item = null; modelLineItems.value = []; options.value = null; previewData.value = null
  if (!form.selected_variety || !form.selected_model_line) return
  try { modelLineItems.value = (await api.getModelLineItems(form.selected_model_line, form.selected_variety)).data }
  catch (e) { showMessage(t('paCtor.errLoadModels'), 'error') }
}
async function onModelLineItemChange() {
  options.value = null; previewData.value = null
  if (!form.selected_model_line_item) return
  try {
    options.value = (await api.getOptions(form.selected_model_line_item)).data
    autoFillDefaults()
  } catch (e) { showMessage(t('paCtor.errLoadOptions'), 'error') }
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

// --- save: POST (создать карточку каталога через хэш-дедуп) ---
async function save() {
  saving.value = true
  try {
    const res = await api.create({ ...form })
    const sku = res.data?.sku
    const verb = res.data?.created === false ? t('paCtor.updated') : t('paCtor.created')
    const msg = sku
      ? verb + ': ' + (res.data.name || '') + ' | SKU: ' + sku.code
      : verb + ': ' + (res.data.name || '')
    showMessage(msg, 'success')
    // Refresh preview from API to get full to_dict() data
    try { const pr = await api.preview({ ...form }); previewData.value = pr.data } catch (e) { /* ignore */ }
  } catch (e) {
    const msg = e.response?.data?.detail || e.response?.data?.error || t('paCtor.errSave')
    showMessage(msg, 'error')
  }
  finally { saving.value = false }
}

function resetForm() {
  Object.assign(form, defaultForm())
  options.value = null; modelLineItems.value = []
  previewData.value = null
}

// --- live preview ---
let previewTimer = null
watch(() => ({ ...form }), () => {
  if (!form.selected_model_line_item) return
  clearTimeout(previewTimer)
  previewTimer = setTimeout(async () => {
    try {
      const res = await api.preview({ ...form })
      previewData.value = res.data
    } catch (e) { /* */ }
  }, 300)
}, { deep: true })

async function onAddToCart() {
  if (!form.selected_model_line_item) return
  try {
    const { data } = await api.createSku({
      model_line_item_id: form.selected_model_line_item,
      options: buildSkuOptionsPayload(),
    })
    showMessage(t('paCtor.skuCreated') + (data.code || data.name), 'success')
  } catch (e) {
    showMessage(t('paCtor.err') + (e.response?.data?.error || e.message), 'error')
  }
}

function showMessage(text, type = 'info') {
  message.value = { text, type }
  setTimeout(() => { message.value = null }, 3000)
}
</script>

<style scoped>
.constructor-app { max-width: 1200px; margin: 0 auto; padding: 20px 32px; }
.panel-right { }
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
.preview { margin-top: 20px; }
.actions { margin-top: 20px; display: flex; gap: 10px; }
.btn { padding: 10px 24px; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; }
.btn.primary { background: #4a6cf7; color: #fff; }
.btn.primary:disabled { background: #a0b4f7; cursor: not-allowed; }
.btn.secondary { background: #eee; color: #333; }
.message { margin-top: 12px; padding: 8px 12px; border-radius: 6px; font-size: 13px; }
.message.success { background: #e6f7e6; color: #2a7a2a; }
.message.error { background: #fde6e6; color: #a33; }
</style>
