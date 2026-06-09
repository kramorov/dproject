<!-- price-catalog/components/EaPriceJournal.vue — журнал документов конфигуратора ЭП -->
<template>
  <div>
    <div class="fl">
      <button class="btn" @click="showCreate=true">+ Документ</button>
    </div>

    <!-- Создание -->
    <div v-if="showCreate" class="card">
      <h4>Новый документ конфигуратора ЭП</h4>
      <input v-model="form.name" placeholder="Название" class="fi" />
      <select v-model="form.priceVariety" class="fi"><option :value="null">Тип цены</option>
        <option v-for="v in opts.varieties" :key="v.id" :value="v.id">{{ v.name }}</option></select>
      <select v-model="form.currency" class="fi"><option :value="null">Валюта</option>
        <option v-for="c in opts.currencies" :key="c.id" :value="c.id">{{ c.code }}</option></select>
      <select v-model="form.mlId" @change="onSeriesChange" class="fi">
        <option :value="null">— серия —</option>
        <option v-for="ml in modelLines" :key="ml.id" :value="ml.id">{{ ml.name }} ({{ ml.code }})</option>
      </select>
      <select v-model="form.psId" class="fi" :disabled="!form.mlId">
        <option :value="null">— напряжение —</option>
        <option v-for="ps in powerSupplies" :key="ps.id" :value="ps.id">{{ ps.name }} ({{ ps.encoding }})</option>
      </select>
      <button class="btn" @click="doCreate" :disabled="!form.name||!form.psId">Создать и заполнить</button>
      <button class="btn-c" @click="showCreate=false">Отмена</button>
      <div v-if="err" class="er">{{ err }}</div>
    </div>

    <div v-if="loading" class="st">Загрузка...</div>
    <table v-else-if="docs.length" class="tb">
      <thead><tr><th>Название</th><th>Дата</th><th>Серия</th><th>Напряжение</th><th>Строк</th><th>Статус</th><th></th></tr></thead>
      <tbody>
        <tr v-for="d in docs" :key="d.id">
          <td class="lnk" @click="$emit('open', { id: d.id })">{{ d.name }}</td>
          <td>{{ d.document_date?.slice(0,10)||'—' }}</td>
          <td>{{ d.model_line?.name || '—' }}</td>
          <td>{{ d.power_supply?.name || '—' }}</td>
          <td>{{ d.rows_count }}</td>
          <td><span :class="badge(d.status)">{{ d.status_label||'—' }}</span></td>
          <td class="act-col">
            <button v-if="d.status==='draft'" class="btn-s btn-sm" @click="doPost(d.id)">Провести</button>
            <button v-if="d.status==='posted'" class="btn-w btn-sm" @click="doUnpost(d.id)">Отмена</button>
            <button class="btn-d btn-sm" @click="doDelete(d.id)">✕</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else-if="!loading" class="st">Нет документов</div>
  </div>
</template>

<script setup>
import { ref, reactive, inject, onMounted } from 'vue'
import priceApi from '../api'

const emit = defineEmits(['open'])
const opts = inject('opts')

const docs = ref([])
const loading = ref(false)
const showCreate = ref(false)
const form = reactive({ name: '', priceVariety: null, currency: null, mlId: null, psId: null })
const err = ref(null)
const modelLines = ref([])
const powerSupplies = ref([])

function badge(s) {
  const map = { draft: 'badge-draft', on_approval: 'badge-approval', posted: 'badge-posted' }
  return 'badge ' + (map[s] || '')
}

async function load() {
  loading.value = true
  try {
    const r = await priceApi.getEaConfigDocs()
    docs.value = r.data || []
  } catch (e) { err.value = e?.displayMessage }
  finally { loading.value = false }
}

async function doCreate() {
  if (!form.name) { err.value = 'Название обязательно'; return }
  err.value = null
  try {
    const r = await priceApi.createEaConfigDoc({
      name: form.name,
      price_variety_id: form.priceVariety || undefined,
      currency_id: form.currency || undefined,
      model_line_id: form.mlId,
      power_supply_id: form.psId,
    })
    form.name = ''; form.priceVariety = null; form.currency = null
    showCreate.value = false
    emit('open', { id: r.data.id, isNew: true })
  } catch (e) { err.value = e?.displayMessage }
}

async function doPost(id) {
  try {
    await priceApi.postEaConfigDoc(id)
    load()
  } catch (e) { err.value = e?.displayMessage }
}

async function doUnpost(id) {
  if (!confirm('Отменить проведение?')) return
  try {
    await priceApi.unpostEaConfigDoc(id)
    load()
  } catch (e) { err.value = e?.displayMessage }
}

async function doDelete(id) {
  if (!confirm('Удалить документ?')) return
  try { await priceApi.deleteEaConfigDoc(id); load() } catch (e) { err.value = e?.displayMessage }
}

onMounted(async () => { load(); await loadModelLines() })

async function loadModelLines() {
  try {
    const r = await fetch('/api/electric_actuators/constructor/model_lines/')
    modelLines.value = await r.json()
  } catch (e) { console.error(e) }
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
    powerSupplies.value = opts.power_supply_options || []
  } catch (e) { console.error(e) }
}
</script>

<style scoped>
.fl{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;align-items:center}
.fi{padding:5px 8px;border:1px solid #d1d5db;border-radius:5px;font-size:13px}
.tb{width:100%;border-collapse:collapse;font-size:13px}
.tb th{text-align:left;padding:6px 10px;background:#f9fafb;border-bottom:2px solid #e5e7eb;color:#6b7280;font-weight:500}
.tb td{padding:6px 10px;border-bottom:1px solid #f3f4f6}
.lnk{cursor:pointer;color:#2563eb}
.st{text-align:center;padding:40px;color:#6b7280}
.er{color:#dc2626;font-size:12px;margin-top:4px}
.card{margin-bottom:12px;padding:12px;border:1px solid #e5e7eb;border-radius:6px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.card h4{margin:0;font-size:14px}
.btn,.btn-s,.btn-d,.btn-c,.btn-w{padding:4px 12px;border:none;border-radius:4px;font-size:12px;cursor:pointer}
.btn{background:#2563eb;color:#fff}
.btn-s{background:#059669;color:#fff}
.btn-d{background:#dc2626;color:#fff}
.btn-c{background:#e5e7eb;color:#374151}
.btn-w{background:#9333ea;color:#fff}
.btn-sm{padding:2px 8px;font-size:11px}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:500}
.badge-draft{background:#e5e7eb;color:#374151}
.badge-approval{background:#fef3c7;color:#92400e}
.badge-posted{background:#d1fae5;color:#065f46}
.act-col{display:flex;gap:4px}
</style>
