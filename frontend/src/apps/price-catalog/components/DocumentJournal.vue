<template>
  <div>
    <div class="fl">
      <input v-model="search" placeholder="Поиск..." @input="load" class="fi" />
      <select v-model="status" @change="load" class="fi">
        <option value="">Все статусы</option>
        <option value="draft">✎ Черновик</option>
        <option value="on_approval">⟳ На согласовании</option>
        <option value="posted">✓ Проведён</option>
      </select>
      <input v-model="dateFrom" type="date" @change="load" class="fi" />
      <input v-model="dateTo" type="date" @change="load" class="fi" />
      <button class="btn" @click="showCreate=true">+ Документ</button>
    </div>

    <!-- Создание -->
    <div v-if="showCreate" class="card">
      <h4>Новый документ</h4>
      <input v-model="form.name" placeholder="Название" class="fi" />
      <select v-model="form.ct" class="fi"><option :value="null">Тип оборудования</option>
        <option v-for="e in contentTypes" :key="e.id" :value="e.content_type_id">{{ e.name }}</option></select>
      <select v-model="form.priceVariety" class="fi"><option :value="null">Тип цены</option>
        <option v-for="v in opts.varieties" :key="v.id" :value="v.id">{{ v.name }}</option></select>
      <select v-model="form.currency" class="fi"><option :value="null">Валюта</option>
        <option v-for="c in opts.currencies" :key="c.id" :value="c.id">{{ c.code }}</option></select>
      <input v-model="form.date" type="date" class="fi" />
      <button class="btn" @click="doCreate">Создать</button>
      <button class="btn-c" @click="showCreate=false">Отмена</button>
      <div v-if="err" class="er">{{ err }}</div>
    </div>

    <div v-if="loading" class="st">Загрузка...</div>
    <table v-else class="tb">
      <thead><tr><th>Название</th><th>Тип</th><th>Дата</th><th>Позиций</th><th>Статус</th><th></th></tr></thead>
      <tbody>
        <tr v-for="d in docs" :key="d.id">
          <td class="lnk" @click="$emit('open', d.id)">{{ d.name }}</td>
          <td>{{ d.content_type_name||'—' }}</td>
          <td>{{ d.document_date?.slice(0,10)||'—' }}</td>
          <td>{{ d.items_count }}</td>
          <td><span :class="badge(d.status)">{{ d.status_label||'—' }}</span></td>
          <td class="act-col">
            <button v-if="d.status==='draft'" class="btn-s btn-sm" @click="doApply(d.id)">Провести</button>
            <button v-if="d.status==='posted'" class="btn-w btn-sm" @click="doUnapply(d.id)">Отмена</button>
            <button class="btn-d btn-sm" @click="doDelete(d.id)">✕</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, reactive, inject, onMounted } from 'vue'
import priceApi from '../api'

const emit = defineEmits(['open'])
const opts = inject('opts')
const contentTypes = inject('contentTypes')

function todayStr() { return new Date().toISOString().slice(0, 10) }

const docs = ref([])
const loading = ref(false)
const search = ref(''), status = ref(''), dateFrom = ref(''), dateTo = ref('')
const showCreate = ref(false)
const form = reactive({ name: '', ct: null, priceVariety: null, currency: null, date: todayStr() })
const err = ref(null)

function badge(s) {
  const map = { draft: 'badge-draft', on_approval: 'badge-approval', posted: 'badge-posted' }
  return 'badge ' + (map[s] || '')
}

async function load() {
  loading.value = true
  try {
    const params = {}
    if (search.value) params.search = search.value
    if (status.value) params.status = status.value
    if (dateFrom.value) params.date_from = dateFrom.value
    if (dateTo.value) params.date_to = dateTo.value
    const r = await priceApi.listDocuments(params)
    docs.value = r.data.data || []
  } catch (e) { err.value = e.displayMessage }
  finally { loading.value = false }
}

async function doCreate() {
  if (!form.name || !form.ct) { err.value = 'Название и тип обязательны'; return }
  err.value = null
  try {
    await priceApi.createDocument({
      name: form.name,
      item_content_type_id: form.ct,
      default_price_variety_id: form.priceVariety || undefined,
      default_currency_id: form.currency || undefined,
      document_date: form.date || undefined,
    })
    form.name = ''; form.ct = null; form.priceVariety = null; form.currency = null; form.date = todayStr()
    showCreate.value = false
    load()
  } catch (e) { err.value = e.displayMessage }
}

async function doApply(id) {
  try { await priceApi.applyDocument(id); load() } catch (e) { err.value = e.displayMessage }
}

async function doUnapply(id) {
  if (!confirm('Отменить проведение?')) return
  try { await priceApi.unapplyDocument(id); load() } catch (e) { err.value = e.displayMessage }
}

async function doDelete(id) {
  if (!confirm('Удалить документ?')) return
  try { await priceApi.deleteDocument(id); load() } catch (e) { err.value = e.displayMessage }
}

onMounted(load)
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
