<!-- shared/components/catalog/PaQuickSelect.vue -->
<!-- QuickSelect-конфигуратор пневмоприводов: серия → DA/SR → модель → опции → карточка -->
<template>
  <div class="pa-qs">
    <PageTitle :title="pageTitle" />

    <!-- Серия + Тип привода + Модель в одну строку -->
    <div class="chip-group" v-if="modelLines.length">
      <div class="chip-row-inline">
        <div class="chip-col" style="flex:1">
          <div class="chip-label">Серия</div>
          <div class="chip-row">
            <button v-for="ml in modelLines" :key="ml.id" class="chip" :class="{active:form.model_line_id===ml.id}" @click="selectML(ml.id)">{{ ml.name }}</button>
          </div>
        </div>
        <div class="chip-col" style="flex:0 0 auto" v-if="form.model_line_id">
          <div class="chip-label">Тип привода</div>
          <div class="chip-row">
            <button class="chip" :class="{active:form.variety==='DA'}" @click="selectVariety('DA')">DA</button>
            <button class="chip" :class="{active:form.variety==='SR'}" @click="selectVariety('SR')">SR</button>
          </div>
        </div>
        <div class="chip-col" style="flex:2" v-if="form.variety && modelItems.length">
          <div class="chip-label">Модель</div>
          <div class="chip-row">
            <button v-for="item in modelItems" :key="item.id" class="chip" :class="{active:form.model_line_item_id===item.id}" @click="selectItem(item.id)">{{ item.name }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Опции: дропдауны в одну строку -->
    <div class="chip-group" v-if="allOptions.length">
      <div class="chip-row-inline">
        <div class="chip-col" v-for="opt in allOptions" :key="opt.key">
          <div class="chip-label">{{ opt.label }}</div>
          <select class="chip-select" :value="form[opt.key]" @change="toggleOption(opt.key, $event.target.value)">
            <option :value="null">—</option>
            <option v-for="o in opt.items" :key="o.id" :value="o.id">{{ o.name }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Карточка результата -->
    <div v-if="preview" class="pa-card-result">
      <PaProductCard :preview="preview" @add-to-cart="$emit('addToCart', {model_line_item_id: form.model_line_item_id, options: buildOptionsPayload()})" />
    </div>

    <Spinner v-else-if="loading" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import PageTitle from '@/shared/components/PageTitle.vue'
import Spinner from '@/shared/components/Spinner.vue'
import PaProductCard from './PaProductCard.vue'

const props = defineProps({
  api: { type: Object, required: true },
  labels: { type: Object, default: () => ({}) },
})
defineEmits(['addToCart', 'navigate'])

const pageTitle = computed(() => props.labels.title || 'Быстрый подбор пневмопривода')

const modelLines = ref([])
const modelItems = ref([])
const optionFields = ref([])
const preview = ref(null)
const loading = ref(false)

// Computed: split optionFields into specific groups for layout
const allOptions = computed(() => optionFields.value.filter(o => !['model_line_id', 'variety', 'model_line_item_id'].includes(o.key)))

const form = reactive({
  model_line_id: null,
  variety: null,
  model_line_item_id: null,
  springs_qty: null, temperature: null, safety_position: null,
  ip: null, exd: null, body_coating: null, hand_wheel: null,
})

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await props.api.getModelLines()
    modelLines.value = data || []
  } catch (e) { console.error(e) }
  loading.value = false
})

async function selectML(id) {
  if (form.model_line_id === id) return
  resetAfter('model_line_id')
  form.model_line_id = id
  form.variety = null
}

async function selectVariety(v) {
  if (form.variety === v) return
  resetAfter('variety')
  form.variety = v
  loading.value = true
  try {
    const { data } = await props.api.getModelLineItems(form.model_line_id, v)
    modelItems.value = data || []
  } catch (e) { console.error(e) }
  loading.value = false
}

async function selectItem(id) {
  if (form.model_line_item_id === id) return
  form.model_line_item_id = id
  form.springs_qty = null; form.temperature = null; form.safety_position = null
  form.ip = null; form.exd = null; form.body_coating = null; form.hand_wheel = null
  optionFields.value = []
  preview.value = null

  loading.value = true
  try {
    const { data } = await props.api.getOptions(id)
    // API returns flat keys: {safety_positions: [...], springs_qty_options: [...], ...}
    const keyMap = {
      safety_positions: 'safety_position', springs_qty_options: 'springs_qty',
      temperature_options: 'temperature', ip_options: 'ip', exd_options: 'exd',
      body_coating_options: 'body_coating', hand_wheel_options: 'hand_wheel',
    }
    const fields = []
    for (const [apiKey, items] of Object.entries(data)) {
      if (!Array.isArray(items) || !items.length) continue
      const formKey = keyMap[apiKey] || apiKey
      const label = optionLabels[formKey] || formKey
      const mapped = items.map(o => ({ id: o.option_id || o.id, name: o.name, is_default: o.is_default }))
      fields.push({ key: formKey, label, items: mapped })
      const def = mapped.find(o => o.is_default) || mapped[0]
      if (def && form[formKey] === null) form[formKey] = def.id
    }
    optionFields.value = fields
    await fetchPreview()
  } catch (e) { console.error(e) }
  loading.value = false
}

function toggleOption(key, value) {
  const v = value === '' || value === null ? null : Number(value)
  if (form[key] === v) return
  form[key] = v
  fetchPreview()
}

async function fetchPreview() {
  if (!form.model_line_item_id) return
  try {
    const { data } = await props.api.preview({
      selected_model_line_item: form.model_line_item_id,
      selected_safety_position: form.safety_position,
      selected_springs_qty: form.springs_qty,
      selected_temperature: form.temperature,
      selected_ip: form.ip,
      selected_exd: form.exd,
      selected_body_coating: form.body_coating,
      selected_hand_wheel: form.hand_wheel,
    })
    preview.value = data
  } catch (e) { /* ignore */ }
}

function resetAfter(field) {
  const order = ['model_line_id', 'variety', 'model_line_item_id']
  const idx = order.indexOf(field)
  for (let i = idx + 1; i < order.length; i++) form[order[i]] = null
  modelItems.value = []
  optionFields.value = []
  preview.value = null
}

function buildOptionsPayload() {
  const keys = ['springs_qty', 'temperature', 'safety_position', 'ip', 'exd', 'body_coating', 'hand_wheel']
  const opts = {}
  for (const k of keys) { if (form[k] != null) opts[k] = form[k] }
  return opts
}

const optionLabels = {
  safety_position: 'Положение безопасности',
  springs_qty: 'Количество пружин',
  temperature: 'Температурное исполнение',
  ip: 'Степень защиты IP',
  exd: 'Взрывозащита',
  body_coating: 'Покрытие корпуса',
  hand_wheel: 'Ручной дублёр',
}
</script>

<style scoped>
.pa-qs { max-width: 1200px; margin: 0 auto; padding: 16px; }
.chip-group { margin-bottom: 12px; }
.chip-label { font-weight: 500; font-size: 13px; margin-bottom: 4px; color: #374151; }
.chip-row { display: flex; flex-wrap: wrap; gap: 4px; }
.chip-row-inline { display: flex; gap: 24px; flex-wrap: wrap; }
.chip-col { min-width: 0; }
.chip { padding: 4px 12px; font-size: 12px; border: 1px solid #d1d5db; border-radius: 16px; background: #fff; cursor: pointer; transition: all .12s; white-space: nowrap; color: #1f2937; }
.chip:hover { border-color: #2563eb; color: #2563eb; }
.chip.active { background: #2563eb; color: #fff; border-color: #2563eb; }
.chip-select { padding: 4px 8px; font-size: 12px; border: 1px solid #d1d5db; border-radius: 8px; background: #fff; color: #1f2937; min-width: 100px; }
.pa-card-result { margin-top: 20px; }
</style>
