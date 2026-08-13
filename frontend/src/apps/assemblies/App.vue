<template>
  <div class="app">
    <h1>🧩 Сборки (Assemblies)</h1>

    <!-- Панель действий -->
    <div class="toolbar">
      <button @click="openCreate">+ Новая сборка</button>
      <label class="filter">
        Статус:
        <select v-model="statusFilter" @change="load">
          <option value="">Все</option>
          <option value="draft">draft</option>
          <option value="fixed">fixed</option>
        </select>
      </label>
      <button @click="load" class="ghost">↻</button>
    </div>

    <!-- Список -->
    <div v-if="!current">
      <table class="list">
        <thead>
          <tr><th>ID</th><th>Название</th><th>Статус</th><th>Rev</th><th>Шаблон</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="a in items" :key="a.id">
            <td>{{ a.id }}</td>
            <td>{{ a.name || '—' }}</td>
            <td><span class="badge" :class="a.status">{{ a.status }}</span></td>
            <td>{{ a.revision ?? '—' }}</td>
            <td>{{ a.is_template ? '📦' : '' }}</td>
            <td><button class="ghost" @click="open(a.id)">Открыть</button></td>
          </tr>
        </tbody>
      </table>
      <p v-if="!items.length" class="empty">Нет сборок. Создайте первую.</p>
    </div>

    <!-- Деталь -->
    <div v-else>
      <button class="ghost" @click="closeDetail">← К списку</button>
      <h2>Сборка #{{ current.id }} — {{ current.status }}</h2>
      <div class="meta">
        <span>rev: {{ current.revision ?? '—' }}</span>
        <span>шаблон: {{ current.is_template ? 'да' : 'нет' }}</span>
        <span>требования: {{ current.requirement_version || '—' }}</span>
      </div>
      <div class="toolbar">
        <button @click="doFork(false)">Fork (состав)</button>
        <button @click="doFork(true)">Fork (новая версия требований)</button>
        <button @click="doFixate">Закрепить (fixate)</button>
        <button class="ghost" @click="doExpand">Переразвернуть</button>
      </div>

      <h3>Компоненты</h3>
      <table class="list">
        <thead>
          <tr><th>Вкл</th><th>Тип</th><th>Статус</th><th>SKU</th><th>path</th></tr>
        </thead>
        <tbody>
          <tr v-for="c in flatComponents" :key="c.id">
            <td><input type="checkbox" :checked="c.included" @change="toggleIncluded(c)" /></td>
            <td :style="{paddingLeft: (c.level * 14) + 'px'}">{{ c.equipment_type_code || '?' }}</td>
            <td><span class="badge" :class="c.status">{{ c.status }}</span></td>
            <td>{{ c.selected_sku || '—' }}</td>
            <td>{{ c.path }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Модалка создания -->
    <div v-if="showCreate" class="modal-backdrop" @click.self="showCreate=false">
      <div class="modal">
        <h3>Новая сборка</h3>
        <label>CompositionGroup:
          <select v-model="newAssembly.cg">
            <option v-for="g in cgs" :key="g.id" :value="g.id">{{ g.code || g.name }}</option>
          </select>
        </label>
        <label>Название: <input v-model="newAssembly.name" /></label>
        <div class="modal-actions">
          <button @click="createAssembly">Создать</button>
          <button class="ghost" @click="showCreate=false">Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import assembliesApi from './api'

const items = ref([])
const current = ref(null)
const cgs = ref([])
const statusFilter = ref('')
const showCreate = ref(false)
const newAssembly = ref({ cg: null, name: '' })

onMounted(() => {
  load()
  loadCgs()
})

async function load() {
  const params = {}
  if (statusFilter.value) params.status = statusFilter.value
  const r = await assembliesApi.list(params)
  items.value = r.data
}

async function loadCgs() {
  try {
    const r = await assembliesApi.compositionGroups()
    cgs.value = r.data || []
  } catch (e) {
    console.error('CG load error', e)
  }
}

async function open(id) {
  const r = await assembliesApi.get(id)
  current.value = r.data
}

function closeDetail() { current.value = null }

function openCreate() {
  newAssembly.value = { cg: cgs.value[0]?.id || null, name: '' }
  showCreate.value = true
}

async function createAssembly() {
  await assembliesApi.create({ composition_group_id: newAssembly.value.cg, name: newAssembly.value.name })
  showCreate.value = false
  await load()
}

async function doFork(forRequirementsChange) {
  const payload = { for_requirements_change: forRequirementsChange }
  const r = await assembliesApi.fork(current.value.id, payload)
  current.value = r.data
  await load()
}

async function doFixate() {
  try {
    const r = await assembliesApi.fixate(current.value.id, {})
    current.value = r.data
  } catch (e) {
    alert(e.response?.data?.error || 'Ошибка закрепления')
  }
}

async function doExpand() {
  const r = await assembliesApi.expand(current.value.id)
  current.value = r.data
}

const flatComponents = computed(() => {
  const out = []
  const walk = (nodes) => {
    for (const n of nodes || []) {
      out.push(n)
      walk(n.children)
    }
  }
  walk(current.value?.components || [])
  return out
})

async function toggleIncluded(c) {
  c.included = !c.included
  if (!c.included) c.status = 'skipped'
  else if (c.status === 'skipped') c.status = 'pending'
  await assembliesApi.updateComponent(c.id, { included: c.included, status: c.status })
}
</script>

<style scoped>
.app{max-width:1400px;margin:0 auto;padding:20px;font-family:-apple-system,BlinkMacSystemFont,sans-serif}
h1{margin:0 0 12px;font-size:24px}
.toolbar{display:flex;gap:8px;align-items:center;margin:12px 0}
.toolbar button{padding:6px 14px;border:1px solid #d1d5db;border-radius:4px;background:#2563eb;color:#fff;cursor:pointer;font-size:14px}
.toolbar button.ghost{background:#fff;color:#111}
.filter{display:flex;gap:6px;align-items:center;font-size:14px}
.list{width:100%;border-collapse:collapse;font-size:14px}
.list th,.list td{border:1px solid #e5e7eb;padding:6px 10px;text-align:left}
.list th{background:#f9fafb}
.badge{padding:2px 8px;border-radius:10px;font-size:12px}
.badge.draft{background:#fef3c7;color:#92400e}
.badge.fixed{background:#dcfce7;color:#166534}
.badge.selected{background:#dcfce7;color:#166534}
.badge.skipped{background:#f3f4f6;color:#6b7280}
.badge.pending{background:#e0f2fe;color:#075985}
.meta{display:flex;gap:16px;color:#555;font-size:14px;margin-bottom:8px}
.empty{color:#999;padding:20px}
.modal-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.35);display:flex;align-items:center;justify-content:center;z-index:50}
.modal{background:#fff;padding:20px;border-radius:8px;min-width:360px;display:flex;flex-direction:column;gap:12px}
.modal label{display:flex;flex-direction:column;gap:4px;font-size:14px}
.modal-actions{display:flex;gap:8px;justify-content:flex-end}
.modal-actions button{padding:6px 14px;border-radius:4px;border:1px solid #d1d5db;background:#2563eb;color:#fff;cursor:pointer}
.modal-actions button.ghost{background:#fff;color:#111}
</style>
