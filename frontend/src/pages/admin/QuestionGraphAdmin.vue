<template>
  <div class="qg-admin">
    <h1>Графы вопросов-ответов</h1>

    <!-- Список -->
    <section class="qg-section">
      <table class="qg-table" v-if="graphs.length">
        <thead><tr><th>Код</th><th>Название</th><th>Тип оборудования</th><th>Активен</th><th></th></tr></thead>
        <tbody>
          <tr v-for="g in graphs" :key="g.id">
            <td>{{ g.code }}</td>
            <td>{{ g.name }}</td>
            <td>{{ g.equipment_type_name || '-' }}</td>
            <td>{{ g.is_active ? '✓' : '—' }}</td>
            <td>
              <button @click="editGraph(g)">Ред.</button>
              <button @click="deleteGraph(g.id)" class="qg-btn-danger">Уд.</button>
              <button @click="convertToWizard(g.code)" class="qg-btn-accent" title="Сгенерировать мастера подбора из графа">⚙→Шаги</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="qg-empty">Нет графов. Создайте новый.</div>
      <button class="qg-btn-primary" @click="newGraph">+ Новый граф</button>
    </section>

    <!-- Редактор -->
    <section class="qg-section" v-if="editing">
      <h2>{{ isNew ? 'Новый граф' : 'Редактирование' }}</h2>
      <div class="qg-form-group">
        <label>Код</label><input v-model="form.code" class="qg-input" />
      </div>
      <div class="qg-form-group">
        <label>Название</label><input v-model="form.name" class="qg-input" />
      </div>
      <div class="qg-form-group">
        <label>Тип оборудования</label>
        <select v-model="form.equipment_type_id" class="qg-input">
          <option :value="null">— выберите —</option>
          <option v-for="et in equipmentTypes" :key="et.id" :value="et.id">{{ et.name }}</option>
        </select>
      </div>
      <div class="qg-form-group">
        <label><input type="checkbox" v-model="form.is_active" /> Активен</label>
      </div>

      <!-- Graph JSON editor -->
      <h3>Граф (JSON)</h3>
      <textarea v-model="graphJsonText" class="qg-json-editor" rows="20" placeholder='{"entry_node": "...", "nodes": {...}, "edges": [...]}'></textarea>
      <div v-if="jsonError" class="qg-error">{{ jsonError }}</div>

      <!-- Preview -->
      <div v-if="parsedGraph" class="qg-preview">
        <h4>Узлы:</h4>
        <div v-for="(node, nid) in parsedGraph.nodes" :key="nid" class="qg-node-card">
          <strong>{{ nid }}</strong>
          <span class="qg-node-question">{{ node.question }}</span>
          <span v-if="node.param_name">param: {{ node.param_name }}</span>
          <span v-if="node.param_names">params: {{ node.param_names.join(', ') }}</span>
          <span v-if="node.pages">страниц: {{ node.pages.length }}</span>
          <span v-if="node.branches">веток: {{ Object.keys(node.branches).length }}</span>
        </div>
        <h4>Рёбра:</h4>
        <div v-for="(e, ei) in parsedGraph.edges" :key="ei" class="qg-edge">
          {{ e.from }} → {{ e.to }}
        </div>
      </div>

      <div class="qg-actions">
        <button class="qg-btn-primary" @click="saveGraph">💾 Сохранить</button>
        <button class="qg-btn-accent" v-if="!isNew" @click="convertToWizard(form.code)">⚙ Сгенерировать мастера</button>
        <button @click="cancelEdit">Отмена</button>
      </div>
      <div v-if="saveMsg" class="qg-msg" :class="{ error: saveError }">{{ saveMsg }}</div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/shared/api'

const graphs = ref([])
const equipmentTypes = ref([])
const editing = ref(false)
const isNew = ref(true)
const saveMsg = ref('')
const saveError = ref(false)
const jsonError = ref('')

const form = ref({
  id: null, code: '', name: '', equipment_type_id: null, is_active: true,
})
const graphJsonText = ref('{}')

const parsedGraph = computed(() => {
  try {
    const g = JSON.parse(graphJsonText.value)
    jsonError.value = ''
    return g
  } catch (e) {
    jsonError.value = e.message
    return null
  }
})

onMounted(async () => {
  await loadGraphs()
  await loadEquipmentTypes()
})

async function loadGraphs() {
  try {
    const { data } = await api.get('/core/question-graph/admin/')
    graphs.value = data
  } catch (e) { console.error(e) }
}

async function loadEquipmentTypes() {
  try {
    const { data } = await api.get('/core/wizard/model-filters/equipment-types/')
    equipmentTypes.value = data.data || []
  } catch (e) { console.error(e) }
}

function newGraph() {
  form.value = { id: null, code: '', name: '', equipment_type_id: null, is_active: true }
  graphJsonText.value = JSON.stringify({
    entry_node: '', nodes: {}, edges: []
  }, null, 2)
  isNew.value = true
  editing.value = true
  saveMsg.value = ''
}

async function editGraph(g) {
  try {
    const { data } = await api.get(`/core/question-graph/admin/${g.id}/`)
    form.value = {
      id: data.id, code: data.code, name: data.name,
      equipment_type_id: data.equipment_type_id, is_active: data.is_active,
    }
    graphJsonText.value = JSON.stringify(data.graph_json || {}, null, 2)
    isNew.value = false
    editing.value = true
    saveMsg.value = ''
  } catch (e) { console.error(e) }
}

function cancelEdit() {
  editing.value = false
  saveMsg.value = ''
}

async function saveGraph() {
  if (!parsedGraph.value) return
  saveMsg.value = ''
  saveError.value = false
  try {
    const payload = {
      ...form.value,
      graph_json: parsedGraph.value,
    }
    if (isNew.value) {
      const { data } = await api.post('/core/question-graph/admin/', payload)
      form.value.id = data.id
      isNew.value = false
    } else {
      await api.put(`/core/question-graph/admin/${form.value.id}/`, payload)
    }
    saveMsg.value = 'Сохранено'
    await loadGraphs()
  } catch (e) {
    saveMsg.value = 'Ошибка: ' + (e.response?.data?.error || e.message)
    saveError.value = true
  }
}

async function deleteGraph(id) {
  if (!confirm('Удалить?')) return
  try {
    await api.delete(`/core/question-graph/admin/${id}/`)
    await loadGraphs()
    if (form.value.id === id) cancelEdit()
  } catch (e) { console.error(e) }
}

async function convertToWizard(code) {
  try {
    const { data } = await api.post(`/core/question-graph/${code}/to-wizard/`)
    saveMsg.value = `Мастер ${data.created ? 'создан' : 'обновлён'} (ID: ${data.wizard_id}), ${data.pages.length} страниц, ${data.filters.length} фильтров`
    saveError.value = false
  } catch (e) {
    saveMsg.value = 'Ошибка конвертации: ' + (e.response?.data?.error || e.message)
    saveError.value = true
  }
}
</script>

<style scoped>
.qg-admin { max-width: 900px; margin: 0 auto; padding: 1rem; }
.qg-section { margin-bottom: 2rem; }
.qg-table { width: 100%; border-collapse: collapse; }
.qg-table th, .qg-table td { padding: 0.5rem; border: 1px solid #ddd; text-align: left; }
.qg-empty { color: #999; padding: 1rem 0; }
.qg-form-group { margin-bottom: 1rem; }
.qg-form-group label { display: block; margin-bottom: 0.25rem; font-weight: 600; }
.qg-input { width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 6px; font-size: 1rem; }
.qg-json-editor { width: 100%; font-family: monospace; font-size: 0.85rem; border: 1px solid #ddd; border-radius: 6px; padding: 0.75rem; }
.qg-node-card { background: #f8f9fa; border-radius: 6px; padding: 0.5rem; margin: 0.25rem 0; }
.qg-node-card strong { margin-right: 1rem; color: #2563eb; }
.qg-node-question { color: #555; }
.qg-node-card span { margin-right: 1rem; font-size: 0.85rem; color: #888; }
.qg-edge { padding: 0.25rem 0.5rem; color: #666; font-size: 0.9rem; }
.qg-preview { margin-top: 1rem; background: #fafafa; border-radius: 8px; padding: 1rem; }
.qg-actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
.qg-btn-primary { background: #2563eb; color: #fff; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; }
.qg-btn-danger { color: #dc2626; }
.qg-btn-accent { background: #059669; color: #fff; border: none; padding: 0.25rem 0.75rem; border-radius: 4px; cursor: pointer; }
.qg-msg { padding: 0.5rem; margin-top: 0.5rem; border-radius: 6px; background: #dcfce7; color: #166534; }
.qg-msg.error { background: #fee2e2; color: #991b1b; }
.qg-error { color: #dc2626; font-size: 0.9rem; }
button { padding: 0.25rem 0.75rem; border: 1px solid #ddd; border-radius: 4px; background: #fff; cursor: pointer; margin-right: 0.25rem; }
button:hover { background: #f0f0f0; }
</style>
