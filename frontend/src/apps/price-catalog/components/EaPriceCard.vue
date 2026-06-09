<!-- price-catalog/components/EaPriceCard.vue — редактор документа конфигуратора ЭП -->
<template>
  <div>
    <div class="fl">
      <button class="btn-c" @click="$emit('close')">← К списку</button>
      <span class="lbl" v-if="doc">{{ doc.name }} | {{ doc.status_label }}</span>
    </div>

    <div v-if="loading" class="st">Загрузка... {{ modelLines.length }} серий</div>

    <!-- Фильтры -->
    <div class="card">
      <div class="new-form">
        <input v-model="form.name" placeholder="Название" class="fi" />
        <select v-model="form.mlId" @change="onSeriesChange" class="fi">
          <option :value="null">— серия —</option>
          <option v-for="ml in modelLines" :key="ml.id" :value="ml.id">{{ ml.name }} ({{ ml.code }})</option>
        </select>
        <select v-model="form.psId" class="fi" :disabled="!form.mlId">
          <option :value="null">— напряжение —</option>
          <option v-for="ps in powerSupplies" :key="ps.id" :value="ps.id">{{ ps.name }} ({{ ps.encoding }})</option>
        </select>
        <button class="btn" @click="startNew" :disabled="!form.psId">Загрузить модели</button>
      </div>
    </div>

    <div v-if="err" class="er">{{ err }}</div>
    <div v-if="msg" class="msg">{{ msg }}</div>

    <!-- Матрица -->
    <div v-if="matrix.length" class="matrix-wrap">
      <div class="fl" style="margin-bottom:8px">
        <button class="btn" @click="save" :disabled="saving">{{ saving ? 'Сохранение...' : 'Сохранить' }}</button>
      </div>
      <table class="mtx">
        <thead>
          <tr>
            <th class="rown">Модель</th>
            <th class="col-base">Базовая цена</th>
            <th v-for="col in columns" :key="col.key" class="col-opt">{{ col.label }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in matrix" :key="row.id">
            <td class="rown">
              <strong>{{ row.code }}</strong>
              <div class="sub">{{ row.name }}</div>
            </td>
            <td class="col-base">
              <input v-model.number="row.basePrice" type="number" step="0.01" class="ci" />
            </td>
            <td v-for="col in columns" :key="col.key" class="col-opt">
              <input v-model.number="row.options[col.key]" type="number" step="0.01" class="ci" placeholder="0" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import priceApi from '../api'

const props = defineProps({
  docId: { type: [Number, String], default: null },
  isNew: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'changed'])

const doc = ref(null)
const loading = ref(false)
const saving = ref(false)
const err = ref(null)
const msg = ref(null)
const modelLines = ref([])
const powerSupplies = ref([])
const matrix = ref([])
const columns = ref([])

const form = reactive({ name: '', mlId: null, psId: null })

onMounted(async () => {
  await loadModelLines()
  if (props.docId && !props.isNew) await loadDoc()
})

async function loadModelLines() {
  try {
    const r = await fetch('/api/electric_actuators/constructor/model_lines/')
    const data = await r.json()
    modelLines.value = data || []
    console.log('modelLines loaded:', modelLines.value.length)
  } catch (e) { console.error('loadModelLines:', e) }
}

async function loadDoc() {
  loading.value = true
  try {
    const r = await priceApi.getEaConfigDoc(props.docId)
    doc.value = r.data
    form.name = r.data.name || ''
    form.mlId = r.data.model_line?.id || null
    form.psId = r.data.power_supply?.id || null
    if (form.mlId) await onSeriesChange()
    if (form.psId) await buildMatrix()
    fillSaved(r.data.rows || [])
  } catch (e) { err.value = 'Ошибка загрузки'; console.error(e) }
  finally { loading.value = false }
}

async function onSeriesChange() {
  powerSupplies.value = []
  form.psId = null
  if (!form.mlId) return
  try {
    const r1 = await fetch(`/api/electric_actuators/constructor/model-lines/${form.mlId}/items/`)
    const items = await r1.json()
    if (!items.length) return
    const r2 = await fetch(`/api/electric_actuators/constructor/options/?model_line_item_id=${items[0].id}`)
    const opts = await r2.json()
    if (opts.power_supply_options?.length) {
      powerSupplies.value = opts.power_supply_options
    }
    console.log('powerSupplies loaded:', powerSupplies.value.length)
  } catch (e) { console.error('onSeriesChange:', e) }
}

async function startNew() {
  if (!form.psId) return
  await buildMatrix()
}

async function buildMatrix() {
  loading.value = true; err.value = null
  try {
    const r = await priceApi.getEaConfigOptions(form.psId)
    const items = r.data.model_items || []
    const colMap = new Map()
    for (const item of items) {
      for (const grp of item.option_groups || []) {
        for (const opt of grp.items || []) {
          if (opt.is_default) continue
          const key = `${grp.field}_${opt.option_id}`
          if (!colMap.has(key)) {
            colMap.set(key, { key, label: opt.encoding || opt.name?.substring(0, 6) || key })
          }
        }
      }
    }
    columns.value = [...colMap.values()]
    matrix.value = items.map(item => {
      const opts = {}
      for (const grp of item.option_groups || []) {
        for (const opt of grp.items || []) {
          if (opt.is_default) continue
          opts[`${grp.field}_${opt.option_id}`] = 0
        }
      }
      return { id: item.id, name: item.name, code: item.code, basePrice: 0, options: opts }
    })
  } catch (e) { err.value = 'Ошибка загрузки'; console.error(e) }
  finally { loading.value = false }
}

function fillSaved(rows) {
  for (const row of rows) {
    const idx = matrix.value.findIndex(m => m.id === row.model_line_item?.id)
    if (idx >= 0) {
      matrix.value[idx].basePrice = row.base_price || 0
      for (const [key, val] of Object.entries(row.options || {})) {
        if (matrix.value[idx].options.hasOwnProperty(key)) {
          matrix.value[idx].options[key] = val
        }
      }
    }
  }
}

async function save() {
  saving.value = true; err.value = null; msg.value = null
  try {
    const data = {
      name: form.name || doc.value?.name || 'Конфигуратор цен',
      price_variety_id: doc.value?.price_variety?.id,
      currency_id: doc.value?.currency?.id,
      model_line_id: form.mlId,
      power_supply_id: form.psId,
      rows: matrix.value.map(row => ({
        model_line_item_id: row.id,
        base_price: row.basePrice || 0,
        options: Object.fromEntries(
          Object.entries(row.options).filter(([k, v]) => v > 0)
        ),
      })),
    }
    const r = await priceApi.createEaConfigDoc(data)
    msg.value = `Сохранено: ${r.data.name} (${r.data.rows_created} строк)`
    emit('changed')
  } catch (e) { err.value = 'Ошибка сохранения'; console.error(e) }
  finally { saving.value = false }
}
</script>

<style scoped>
.lbl { font-size: 13px; color: #6b7280 }
.card { margin-bottom: 12px; padding: 12px; border: 1px solid #e5e7eb; border-radius: 6px }
.new-form { display: flex; gap: 8px; flex-wrap: wrap; align-items: center }
.fl { display: flex; gap: 8px; align-items: center; margin-bottom: 8px }
.fi { padding: 5px 8px; border: 1px solid #d1d5db; border-radius: 5px; font-size: 13px }
.btn { padding: 4px 12px; border: none; border-radius: 4px; font-size: 12px; cursor: pointer; background: #2563eb; color: #fff }
.btn-c { padding: 4px 12px; border: none; border-radius: 4px; font-size: 12px; cursor: pointer; background: #e5e7eb; color: #374151 }
.er { color: #dc2626; font-size: 12px; margin: 4px 0 }
.msg { color: #059669; font-size: 13px; margin: 4px 0 }
.st { text-align: center; padding: 40px; color: #6b7280 }
.matrix-wrap { overflow-x: auto; max-height: 70vh; overflow-y: auto }
.mtx { border-collapse: collapse; font-size: 12px; min-width: 100% }
.mtx th { position: sticky; top: 0; background: #f1f5f9; padding: 6px 4px; border: 1px solid #d1d5db; font-weight: 500; white-space: nowrap; z-index: 1 }
.mtx td { padding: 4px; border: 1px solid #e5e7eb }
.rown { min-width: 140px; max-width: 160px }
.rown strong { display: block; font-size: 13px }
.rown .sub { font-size: 10px; color: #6b7280; white-space: nowrap; overflow: hidden; text-overflow: ellipsis }
.col-base { min-width: 90px }
.col-opt { min-width: 70px }
.ci { width: 100%; padding: 4px; border: 1px solid transparent; border-radius: 3px; font-size: 12px; text-align: right; box-sizing: border-box }
.ci:focus { border-color: #2563eb; outline: none; background: #fff }
.ci:hover { border-color: #d1d5db }
.ci::placeholder { color: #d1d5db }
</style>
