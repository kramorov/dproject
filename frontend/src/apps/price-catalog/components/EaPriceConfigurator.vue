<!-- price-catalog/components/EaPriceConfigurator.vue -->
<template>
  <div>
    <h3>Конфигуратор цен электроприводов</h3>

    <!-- Блок 1: Создание нового документа ИЛИ список существующих -->
    <div class="card">
      <!-- Существующие документы -->
      <div v-if="docs.length" class="docs-bar">
        <span class="lbl">Документы:</span>
        <select v-model="docId" @change="loadDoc" class="fi" style="flex:1">
          <option :value="null">+ Новый документ</option>
          <option v-for="d in docs" :key="d.id" :value="d.id">
            {{ d.name }} ({{ d.power_supply?.name || '?' }}, {{ d.status_label }})
          </option>
        </select>
        <button v-if="docId" class="btn-d btn-sm" @click="doDelete">✕</button>
      </div>

      <!-- Форма нового документа -->
      <div v-if="mode==='new'" class="new-form">
        <input v-model="form.name" placeholder="Название документа" class="fi" />
        <select v-model="form.priceType" class="fi">
          <option :value="null">— тип цены —</option>
          <option v-for="v in opts.varieties" :key="v.id" :value="v.id">{{ v.name }}</option>
        </select>
        <select v-model="form.currency" class="fi">
          <option :value="null">— валюта —</option>
          <option v-for="c in opts.currencies" :key="c.id" :value="c.id">{{ c.code }}</option>
        </select>
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

    <!-- Блок 2: Матрица -->
    <div v-if="loading" class="st">Загрузка...</div>
    <div v-else-if="mode==='matrix'" class="matrix-wrap">
      <div class="fl" style="margin-bottom:8px">
        <button class="btn" @click="save" :disabled="saving">{{ saving ? 'Сохранение...' : 'Сохранить' }}</button>
        <span class="lbl">{{ form.name || 'Новый документ' }} | {{ form.priceType }} | {{ form.currency }}</span>
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
    <div v-else-if="mode==='new'" class="st">Выберите напряжение и нажмите «Загрузить модели»</div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, inject } from 'vue'
import priceApi from '../api'

const opts = inject('opts')

const mode = ref('new')  // 'new' | 'matrix'
const docId = ref(null)
const saving = ref(false)
const loading = ref(false)
const err = ref(null)
const msg = ref(null)
const docs = ref([])
const modelLines = ref([])
const powerSupplies = ref([])
const matrix = ref([])
const columns = ref([])

const form = reactive({
  name: '',
  priceType: null,
  currency: null,
  mlId: null,
  psId: null,
})

onMounted(async () => {
  try {
    const r = await priceApi.getEaConfigDocs()
    docs.value = r.data || []
    await loadModelLines()
  } catch {}
})

async function loadModelLines() {
  try {
    const axios = (await import('@/shared/api')).default
    modelLines.value = (await axios.get('/electric_actuators/constructor/model_lines/')).data || []
  } catch {}
}

async function onSeriesChange() {
  powerSupplies.value = []
  form.psId = null
  if (!form.mlId) return
  try {
    const axios = (await import('@/shared/api')).default
    const items = (await axios.get(`/electric_actuators/constructor/model-lines/${form.mlId}/items/`)).data || []
    if (!items.length) return
    const opts = (await axios.get('/electric_actuators/constructor/options/', {
      params: { model_line_item_id: items[0].id }
    })).data
    if (opts.power_supply_options?.length) {
      powerSupplies.value = opts.power_supply_options
    }
  } catch {}
}

async function startNew() {
  if (!form.psId) return
  loading.value = true; err.value = null; mode.value = 'matrix'
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
            colMap.set(key, { key, label: opt.encoding || opt.name?.substring(0, 6) || key, group: grp.field })
          }
        }
      }
    }
    columns.value = [...colMap.values()]

    matrix.value = items.map(item => {
      const opts = {}
      for (const grp of item.option_groups || []) {
        for (const opt of grp.items || []) {
          opts[`${grp.field}_${opt.option_id}`] = 0
        }
      }
      return { id: item.id, name: item.name, code: item.code, basePrice: 0, options: opts }
    })
  } catch (e) { err.value = 'Ошибка загрузки'; mode.value = 'new' }
  finally { loading.value = false }
}

async function loadDoc() {
  if (!docId.value) { mode.value = 'new'; return }
  loading.value = true; err.value = null
  try {
    const r = await priceApi.getEaConfigDoc(docId.value)
    const doc = r.data
    form.name = doc.name
    form.priceType = doc.price_type
    form.currency = doc.currency
    form.psId = doc.power_supply?.id
    mode.value = 'matrix'

    await startNewInternal()

    const rows = doc.rows || []
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
  } catch (e) { err.value = 'Ошибка загрузки документа' }
  finally { loading.value = false }
}

async function startNewInternal() {
  loading.value = true
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
            colMap.set(key, { key, label: opt.encoding || opt.name?.substring(0, 6) || key, group: grp.field })
          }
        }
      }
    }
    columns.value = [...colMap.values()]
    matrix.value = items.map(item => {
      const opts = {}
      for (const grp of item.option_groups || []) {
        for (const opt of grp.items || []) {
          opts[`${grp.field}_${opt.option_id}`] = 0
        }
      }
      return { id: item.id, name: item.name, code: item.code, basePrice: 0, options: opts }
    })
  } catch (e) { err.value = 'Ошибка загрузки' }
  finally { loading.value = false }
}

async function save() {
  saving.value = true; err.value = null; msg.value = null
  try {
    const data = {
      name: form.name || 'Конфигуратор цен ' + new Date().toLocaleDateString('ru'),
      price_variety_id: form.priceType,
      currency_id: form.currency,
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
    docId.value = r.data.id
    msg.value = `Сохранено: ${r.data.name} (${r.data.rows_created} строк)`
    docs.value = (await priceApi.getEaConfigDocs()).data || []
  } catch (e) { err.value = 'Ошибка сохранения' }
  finally { saving.value = false }
}

async function doDelete() {
  if (!confirm('Удалить документ?')) return
  try {
    await priceApi.deleteEaConfigDoc(docId.value)
    docId.value = null; mode.value = 'new'
    msg.value = 'Документ удалён'
    docs.value = (await priceApi.getEaConfigDocs()).data || []
  } catch (e) { err.value = 'Ошибка удаления' }
}
</script>

<style scoped>
h3 { margin: 0 0 12px }
.lbl { font-size: 13px; color: #6b7280 }
.card { margin-bottom: 12px; padding: 12px; border: 1px solid #e5e7eb; border-radius: 6px }
.docs-bar { display: flex; gap: 8px; align-items: center; margin-bottom: 10px }
.new-form { display: flex; gap: 8px; flex-wrap: wrap; align-items: center }
.fl { display: flex; gap: 8px; align-items: center }
.fi { padding: 5px 8px; border: 1px solid #d1d5db; border-radius: 5px; font-size: 13px }
.btn { padding: 4px 12px; border: none; border-radius: 4px; font-size: 12px; cursor: pointer; background: #2563eb; color: #fff }
.btn-d { background: #dc2626; color: #fff }
.btn-sm { padding: 2px 8px; font-size: 11px }
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
