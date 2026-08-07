<template>
  <div class="qg-admin">
    <h1>Графы вопросов-ответов</h1>

    <!-- Список -->
    <section class="qg-section" v-if="!editing">
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
      <div class="qg-editor-header">
        <h2>{{ isNew ? 'Новый граф' : 'Редактирование: ' + form.name }}</h2>
        <div class="qg-editor-tabs">
          <button class="qg-tab" :class="{ active: editorTab === 'visual' }" @click="editorTab = 'visual'">🎨 Визуальный</button>
          <button class="qg-tab" :class="{ active: editorTab === 'json' }" @click="editorTab = 'json'">{ } JSON</button>
        </div>
      </div>

      <!-- Meta -->
      <div class="qg-meta-row">
        <div class="qg-form-group qg-inline">
          <label>Код</label><input v-model="form.code" class="qg-input" />
        </div>
        <div class="qg-form-group qg-inline">
          <label>Название</label><input v-model="form.name" class="qg-input" />
        </div>
        <div class="qg-form-group qg-inline">
          <label>Тип оборудования</label>
          <select v-model="form.equipment_type_id" class="qg-input">
            <option :value="null">— выберите —</option>
            <option v-for="et in equipmentTypes" :key="et.id" :value="et.id">{{ et.name }}</option>
          </select>
        </div>
        <div class="qg-form-group qg-inline qg-checkbox">
          <label><input type="checkbox" v-model="form.is_active" /> Активен</label>
        </div>
      </div>

      <!-- Visual editor -->
      <div v-if="editorTab === 'visual'" class="qg-flow-wrap">
        <QuestionGraphFlow
          :graph-json="liveGraphJson"
          :graph-code="form.code"
          @update:graph-json="onGraphUpdate"
          @save="saveGraph"
          @close="cancelEdit"
        />
      </div>

      <!-- JSON fallback -->
      <div v-else class="qg-json-fallback">
        <textarea v-model="graphJsonText" class="qg-json-editor" rows="20" placeholder='{"entry_node": "...", "nodes": {...}, "edges": [...]}'></textarea>
        <div v-if="jsonError" class="qg-error">{{ jsonError }}</div>
        <div class="qg-actions">
          <button class="qg-btn-primary" @click="saveFromJson">💾 Сохранить</button>
          <button class="qg-btn-accent" v-if="!isNew" @click="convertToWizard(form.code)">⚙ Сгенерировать мастера</button>
          <button @click="cancelEdit">Отмена</button>
        </div>
      </div>

      <div v-if="saveMsg" class="qg-msg" :class="{ error: saveError }">{{ saveMsg }}</div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/shared/api'
import QuestionGraphFlow from '@/shared/components/catalog/QuestionGraphFlow.vue'

const graphs = ref([])
const equipmentTypes = ref([])
const editing = ref(false)
const isNew = ref(true)
const saveMsg = ref('')
const saveError = ref(false)
const jsonError = ref('')
const editorTab = ref('visual')

const form = ref({
  id: null, code: '', name: '', equipment_type_id: null, is_active: true,
})
const graphJsonText = ref('{}')
const liveGraphJson = ref({ nodes: {}, edges: [], entry_node: '' })

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
  liveGraphJson.value = { entry_node: '', nodes: {}, edges: [] }
  graphJsonText.value = JSON.stringify(liveGraphJson.value, null, 2)
  isNew.value = true
  editing.value = true
  editorTab.value = 'visual'
  saveMsg.value = ''
}

async function editGraph(g) {
  try {
    const { data } = await api.get(`/core/question-graph/admin/${g.id}/`)
    form.value = {
      id: data.id, code: data.code, name: data.name,
      equipment_type_id: data.equipment_type_id, is_active: data.is_active,
    }
    liveGraphJson.value = data.graph_json || { nodes: {}, edges: [], entry_node: '' }
    graphJsonText.value = JSON.stringify(liveGraphJson.value, null, 2)
    isNew.value = false
    editing.value = true
    editorTab.value = 'visual'
    saveMsg.value = ''
  } catch (e) { console.error(e) }
}

function cancelEdit() {
  editing.value = false
  saveMsg.value = ''
}

function onGraphUpdate(gj) {
  liveGraphJson.value = gj
  graphJsonText.value = JSON.stringify(gj, null, 2)
}

async function saveGraph(gj) {
  saveMsg.value = ''
  saveError.value = false
  const payload = {
    ...form.value,
    graph_json: gj || liveGraphJson.value,
  }
  try {
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

async function saveFromJson() {
  try {
    const gj = JSON.parse(graphJsonText.value)
    jsonError.value = ''
    liveGraphJson.value = gj
    await saveGraph(gj)
  } catch (e) {
    jsonError.value = 'Ошибка JSON: ' + e.message
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
.qg-admin { max-width: 1400px; margin: 0 auto; padding: 24px; }
h1 { font-size: 22px; margin: 0 0 20px; }
.qg-section { margin-bottom: 32px; }
.qg-table { width: 100%; border-collapse: collapse; margin-bottom: 16px; }
.qg-table th, .qg-table td { padding: 8px 12px; border-bottom: 1px solid #e2e8f0; text-align: left; font-size: 14px; }
.qg-table th { background: #f8fafc; font-weight: 600; }
.qg-empty { color: #94a3b8; padding: 24px 0; }
.qg-btn-primary { background: #2563eb; color: #fff; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; }
.qg-btn-danger { background: #dc2626; color: #fff; border: none; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 12px; margin-left: 4px; }
.qg-btn-accent { background: #7c3aed; color: #fff; border: none; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 12px; margin-left: 4px; }
.qg-editor-header { display: flex; align-items: center; gap: 24px; margin-bottom: 16px; }
.qg-editor-header h2 { margin: 0; font-size: 18px; }
.qg-editor-tabs { display: flex; gap: 4px; }
.qg-tab { padding: 6px 14px; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 6px; cursor: pointer; font-size: 13px; }
.qg-tab.active { background: #2563eb; color: #fff; border-color: #2563eb; }
.qg-meta-row { display: flex; gap: 16px; align-items: flex-end; flex-wrap: wrap; margin-bottom: 16px; }
.qg-form-group { display: flex; flex-direction: column; gap: 4px; }
.qg-form-group label { font-size: 12px; font-weight: 600; color: #475569; }
.qg-form-group.qg-inline { flex-direction: column; }
.qg-form-group.qg-checkbox { flex-direction: row; align-items: center; margin-top: 8px; }
.qg-input { padding: 7px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; min-width: 160px; }
.qg-input:focus { border-color: #2563eb; outline: none; }
.qg-flow-wrap { height: 650px; border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden; }
.qg-json-fallback { margin-top: 12px; }
.qg-json-editor { width: 100%; font-family: monospace; font-size: 13px; padding: 12px; border: 1px solid #d1d5db; border-radius: 8px; box-sizing: border-box; }
.qg-error { color: #dc2626; font-size: 13px; margin-top: 4px; }
.qg-msg { font-size: 14px; padding: 8px 12px; border-radius: 6px; margin-top: 8px; }
.qg-msg:not(.error) { background: #dcfce7; color: #166534; }
.qg-msg.error { background: #fee2e2; color: #991b1b; }
.qg-actions { display: flex; gap: 8px; margin-top: 12px; }
button { font-size: 13px; padding: 6px 12px; border-radius: 5px; cursor: pointer; border: 1px solid #d1d5db; background: #fff; }
</style>
