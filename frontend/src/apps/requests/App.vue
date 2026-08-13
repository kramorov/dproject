<template>
  <div class="app">
    <h1>📋 Заявки клиентов</h1>

    <div class="toolbar">
      <button @click="openCreate">+ Новая заявка</button>
      <button class="ghost" @click="load">↻</button>
    </div>

    <!-- Список -->
    <div v-if="!current">
      <table class="list">
        <thead>
          <tr><th>Код</th><th>Название</th><th>Клиент</th><th>Статус</th><th>Дата</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="r in items" :key="r.id">
            <td>{{ r.code || '—' }}</td>
            <td>{{ r.name || r.client_request_number || '—' }}</td>
            <td>{{ r.end_customer || '—' }}</td>
            <td>{{ r.status_code || '—' }}</td>
            <td>{{ r.request_date || '—' }}</td>
            <td>
              <button class="ghost" @click="open(r.id)">Открыть</button>
              <button class="ghost danger" @click="remove(r)">✕</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!items.length" class="empty">Нет заявок.</p>
    </div>

    <!-- Деталь -->
    <div v-else>
      <button class="ghost" @click="current=null">← К списку</button>
      <h2>{{ current.name || current.code }} <span class="badge">{{ current.status_code || '—' }}</span></h2>
      <div class="meta">
        <span>клиент: {{ current.end_customer || '—' }}</span>
        <span>дата: {{ current.request_date || '—' }}</span>
      </div>
      <p class="text">{{ current.request_text || '' }}</p>

      <h3>Позиции</h3>
      <table class="list">
        <thead><tr><th>№</th><th>Тип</th><th>Текст</th><th>Статус</th><th>v</th></tr></thead>
        <tbody>
          <tr v-for="it in currentItems" :key="it.id">
            <td>{{ it.item_no }}</td>
            <td>{{ it.item_type_code || '—' }}</td>
            <td>{{ it.request_line_text || '—' }}</td>
            <td>{{ it.status }}</td>
            <td>{{ it.version }}</td>
          </tr>
        </tbody>
      </table>

      <div class="toolbar">
        <label>Тип: <select v-model="newItem.item_type"><option v-for="t in itemTypes" :key="t.id" :value="t.id">{{ t.symbolic_code }}</option></select></label>
        <input v-model="newItem.request_line_text" placeholder="Текст позиции" />
        <button @click="addItem">+ Позиция</button>
      </div>
    </div>

    <!-- Модалка создания -->
    <div v-if="showCreate" class="modal-backdrop" @click.self="showCreate=false">
      <div class="modal">
        <h3>Новая заявка</h3>
        <label>Название: <input v-model="form.name" /></label>
        <label>Номер клиента: <input v-model="form.client_request_number" /></label>
        <label>Конечный заказчик: <input v-model="form.end_customer" /></label>
        <label>Дата: <input type="date" v-model="form.request_date" /></label>
        <label>Текст: <textarea v-model="form.request_text" rows="3"></textarea></label>
        <div class="modal-actions">
          <button @click="create">Создать</button>
          <button class="ghost" @click="showCreate=false">Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import requestsApi from './api'

const items = ref([])
const current = ref(null)
const currentItems = ref([])
const itemTypes = ref([])
const showCreate = ref(false)
const newItem = ref({ item_type: null, request_line_text: '' })
const form = ref({ name: '', client_request_number: '', end_customer: '', request_date: '', request_text: '' })

onMounted(() => { load(); loadItemTypes() })

async function load() {
  const r = await requestsApi.listRequests()
  items.value = r.data
}

async function loadItemTypes() {
  try {
    const r = await requestsApi.itemTypes()
    itemTypes.value = r.data || []
    newItem.value.item_type = itemTypes.value[0]?.id || null
  } catch (e) { console.error('item types error', e) }
}

async function open(id) {
  const r = await requestsApi.getRequest(id)
  current.value = r.data
  await loadCurrentItems(id)
}

async function loadCurrentItems(requestId) {
  const r = await requestsApi.listItems({ request_parent: requestId })
  currentItems.value = r.data
}

function openCreate() {
  form.value = { name: '', client_request_number: '', end_customer: '', request_date: new Date().toISOString().slice(0, 10), request_text: '' }
  showCreate.value = true
}

async function create() {
  await requestsApi.createRequest(form.value)
  showCreate.value = false
  await load()
}

async function remove(r) {
  if (!confirm(`Удалить заявку #${r.code || r.id}?`)) return
  await requestsApi.deleteRequest(r.id)
  await load()
}

async function addItem() {
  if (!current.value) return
  await requestsApi.createItem({
    request_parent: current.value.id,
    item_type: newItem.value.item_type,
    request_line_text: newItem.value.request_line_text,
  })
  newItem.value.request_line_text = ''
  await loadCurrentItems(current.value.id)
}
</script>

<style scoped>
.app{max-width:1400px;margin:0 auto;padding:20px;font-family:-apple-system,BlinkMacSystemFont,sans-serif}
h1{margin:0 0 12px;font-size:24px}
.toolbar{display:flex;gap:8px;align-items:center;margin:12px 0}
.toolbar button{padding:6px 14px;border:1px solid #d1d5db;border-radius:4px;background:#2563eb;color:#fff;cursor:pointer;font-size:14px}
.toolbar button.ghost{background:#fff;color:#111}
.toolbar button.danger{color:#dc2626}
.toolbar input{padding:6px;border:1px solid #d1d5db;border-radius:4px;font-size:14px}
.toolbar select{padding:6px;border:1px solid #d1d5db;border-radius:4px;font-size:14px}
.list{width:100%;border-collapse:collapse;font-size:14px}
.list th,.list td{border:1px solid #e5e7eb;padding:6px 10px;text-align:left}
.list th{background:#f9fafb}
.badge{padding:2px 8px;border-radius:10px;font-size:12px;background:#e0f2fe;color:#075985}
.meta{display:flex;gap:16px;color:#555;font-size:14px;margin-bottom:8px}
.text{color:#333;font-size:14px}
.empty{color:#999;padding:20px}
.modal-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.35);display:flex;align-items:center;justify-content:center;z-index:50}
.modal{background:#fff;padding:20px;border-radius:8px;min-width:400px;display:flex;flex-direction:column;gap:12px}
.modal label{display:flex;flex-direction:column;gap:4px;font-size:14px}
.modal input,.modal textarea{padding:6px;border:1px solid #d1d5db;border-radius:4px;font-size:14px}
.modal-actions{display:flex;gap:8px;justify-content:flex-end}
.modal-actions button{padding:6px 14px;border-radius:4px;border:1px solid #d1d5db;background:#2563eb;color:#fff;cursor:pointer}
.modal-actions button.ghost{background:#fff;color:#111}
</style>
