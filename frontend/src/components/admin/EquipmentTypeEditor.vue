<!-- components/admin/EquipmentTypeEditor.vue -->
<!-- Редактор типа оборудования (EquipmentType) с разбивкой на под-вкладки.
     Вынесен из PipelineConfigPage (вкладка "Equipment Types"). -->
<template>
  <div class="split-layout">
    <!-- Left: equipment types list -->
    <div class="left-panel">
      <ul class="et-list">
        <li v-for="et in equipmentTypes" :key="et.id"
            :class="{ active: selectedEtId === et.id }"
            @click="selectEquipmentType(et)">
          <code>{{ et.code }}</code> {{ et.name }}
        </li>
      </ul>
    </div>

    <!-- Right: editor for selected type -->
    <div class="right-panel" v-if="selectedEt">
      <div class="et-info">
        <div class="et-info-title">
          <strong>{{ selectedEt.name }}</strong> <code>{{ selectedEt.code }}</code>
        </div>
        <div class="et-info-actions">
          <button class="btn-save" @click="saveEquipment(selectedEt)">💾 Сохранить</button>
          <span v-if="saveMessage" class="et-status" :class="{ error: saveError }">{{ saveMessage }}</span>
        </div>
      </div>

      <nav class="et-tabs">
        <button v-for="t in subTabs" :key="t.id" :class="{ active: subTab === t.id }" @click="subTab = t.id">{{ t.label }}</button>
      </nav>

      <div class="et-form">
        <!-- Основное -->
        <div v-show="subTab === 'basic'" class="et-tab">
          <div class="et-form-row">
            <label>Код</label><input v-model="selectedEt.code" class="cell-input" />
            <label>Сортировка</label><input v-model.number="selectedEt.sorting_order" type="number" class="cell-input" style="width:90px" />
          </div>
          <div class="et-form-row">
            <label>Название</label><input v-model="selectedEt.name" class="cell-input" />
            <label>Иконка</label><input v-model="selectedEt.icon" class="cell-input" style="width:120px" placeholder="emoji / css-class" />
          </div>
          <div class="et-form-row">
            <label>Filter Endpoint</label><input v-model="selectedEt.filter_endpoint" class="cell-input" placeholder="/api/.../selector/search/" />
          </div>
          <div class="et-form-col">
            <label>Описание</label><textarea v-model="selectedEt.description" class="cell-input" rows="2"></textarea>
          </div>
        </div>

        <!-- Шаблон названия (name_template) -->
        <div v-show="subTab === 'name'" class="et-tab">
          <div class="et-form-block">
            <label class="et-form-block-label">Шаблон названия (name_template)</label>
            <div class="et-chips">
              <button v-for="ph in placeholders" :key="ph" class="et-chip" type="button" @click="insertPlaceholder(ph, 'name_template', nameTemplateEl)">{{ ph }}</button>
            </div>
            <textarea ref="nameTemplateEl" v-model="selectedEt.name_template" class="cell-input" rows="4"></textarea>
          </div>
        </div>

        <!-- Шаблон описания (description_template) -->
        <div v-show="subTab === 'description'" class="et-tab">
          <div class="et-form-block">
            <label class="et-form-block-label">Шаблон описания (description_template)</label>
            <div class="et-chips">
              <button v-for="ph in placeholders" :key="ph" class="et-chip" type="button" @click="insertPlaceholder(ph, 'description_template', descriptionTemplateEl)">{{ ph }}</button>
            </div>
            <textarea ref="descriptionTemplateEl" v-model="selectedEt.description_template" class="cell-input" rows="4"></textarea>
          </div>
        </div>

        <!-- Шаблон заголовка (title_template) -->
        <div v-show="subTab === 'title'" class="et-tab">
          <div class="et-form-block">
            <label class="et-form-block-label">Шаблон заголовка (title_template)</label>
            <div class="et-chips">
              <button v-for="ph in placeholders" :key="ph" class="et-chip" type="button" @click="insertPlaceholder(ph, 'title_template', titleTemplateEl)">{{ ph }}</button>
            </div>
            <textarea ref="titleTemplateEl" v-model="selectedEt.title_template" class="cell-input" rows="4"></textarea>
          </div>
        </div>

        <!-- Шаблон спецификации (spec_template) -->
        <div v-show="subTab === 'spec'" class="et-tab">
          <div class="et-form-block">
            <label class="et-form-block-label">Шаблон спецификации (spec_template)</label>
            <SpecTemplateEditor :key="selectedEt.id" v-model="selectedEt.spec_template" :fields="templateFields" />
          </div>
        </div>

        <!-- Семантика параметров (param_semantics) -->
        <div v-show="subTab === 'semantics'" class="et-tab">
          <div class="et-form-block">
            <label class="et-form-block-label">Семантика параметров (param_semantics)</label>
            <SemanticsEditor :key="selectedEt.id" v-model="selectedEt.param_semantics" />
          </div>
        </div>

        <!-- AI Catalog Schema -->
        <div v-show="subTab === 'ai'" class="et-tab">
          <div class="et-form-block">
            <label class="et-form-block-label">AI Catalog Schema</label>
            <div class="et-form-row">
              <label>AI title</label><input v-model="selectedEt.ai_title" class="cell-input" />
              <label>AI placeholder</label><input v-model="selectedEt.ai_placeholder" class="cell-input" />
            </div>
            <div class="et-form-col">
              <label>AI description</label><textarea v-model="selectedEt.ai_description" class="cell-input" rows="2"></textarea>
            </div>
            <div class="et-form-col">
              <label>AI hints</label>
              <HintsEditor :key="selectedEt.id" v-model="selectedEt.ai_hints" />
            </div>
          </div>
        </div>
      </div>

      <!-- Конфигуратор: таблица параметров (EquipmentTypeParameter) -->
      <div class="param-section">
        <h4>Параметры конфигуратора ({{ filteredParams.length }})</h4>
        <div class="info-bar">
          ⓘ Редактируйте <strong>compare_direction</strong> и <strong>compare_label</strong> прямо в строках таблицы.
        </div>
        <table>
          <thead><tr>
            <th>Param</th><th>Path</th><th>Type</th><th>Unit</th>
            <th>Compare</th><th>Label</th>
            <th>Req</th><th>Act</th><th></th>
          </tr></thead>
          <tbody>
            <tr v-for="p in filteredParams" :key="p.id">
              <td><input v-model="p.param_name" class="cell-input" /></td>
              <td><input v-model="p.field_path" class="cell-input" /></td>
              <td><select v-model="p.param_type"><option value="">—</option><option value="integer">int</option><option value="decimal">dec</option><option value="choice">choice</option><option value="boolean">bool</option><option value="string">str</option></select></td>
              <td><input v-model="p.unit" class="cell-input" style="width:50px" /></td>
              <td><select v-model="p.compare_direction" @change="saveParam(p)">
                <option value="">—</option>
                <option value="min">Min ↑</option>
                <option value="max">Max ↓</option>
                <option value="exact">Exact =</option>
              </select></td>
              <td><input v-model="p.compare_label" class="cell-input" style="width:90px" placeholder="не менее" @change="saveParam(p)" /></td>
              <td><input type="checkbox" v-model="p.is_required" /></td>
              <td><input type="checkbox" v-model="p.is_active" /></td>
              <td><button class="btn-save-sm" @click="saveParam(p)">💾</button></td>
            </tr>
            <tr v-if="!filteredParams.length"><td colspan="9" class="empty">No parameters yet</td></tr>
          </tbody>
        </table>
        <button class="btn-add" @click="addParam()" style="margin-top:8px">+ Add Parameter</button>
      </div>
    </div>

    <!-- No type selected -->
    <div class="right-panel" v-else>
      <div class="empty">Выберите тип оборудования слева</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import api from '@/shared/api'
import SpecTemplateEditor from '@/components/admin/SpecTemplateEditor.vue'
import SemanticsEditor from '@/components/admin/SemanticsEditor.vue'
import HintsEditor from '@/components/admin/HintsEditor.vue'

const props = defineProps({
  equipmentTypes: { type: Array, default: () => [] },
})

const emit = defineEmits(['saved'])

const selectedEt = ref(null)
const selectedEtId = ref(null)
const subTab = ref('basic')
const templateFields = ref([])
const placeholders = ref([])
const titleTemplateEl = ref(null)
const nameTemplateEl = ref(null)
const descriptionTemplateEl = ref(null)
const saveMessage = ref('')
const saveError = ref(false)
const equipmentParams = ref([])

const subTabs = [
  { id: 'basic', label: 'Основное' },
  { id: 'name', label: 'Шаблон названия (name_template)' },
  { id: 'description', label: 'Шаблон описания (description_template)' },
  { id: 'title', label: 'Шаблон заголовка (title_template)' },
  { id: 'spec', label: 'Шаблон спецификации (spec_template)' },
  { id: 'semantics', label: 'Семантика параметров (param_semantics)' },
  { id: 'ai', label: 'AI Catalog Schema' },
]

const filteredParams = computed(() => {
  if (!selectedEtId.value) return []
  return equipmentParams.value.filter(p => p.equipment_type === selectedEtId.value)
})

onMounted(async () => {
  try {
    const { data } = await api.get('/configurator/admin/equipment-type-parameters/')
    equipmentParams.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e) {
    equipmentParams.value = []
  }
})

function cloneEquipmentType(et) {
  // Глубокая копия через JSON — данные типа оборудования приходят из DRF (plain JSON),
  // поэтому вложенные spec_template/param_semantics/ai_hints копируются без общих ссылок.
  return JSON.parse(JSON.stringify(et))
}

function selectEquipmentType(et) {
  saveMessage.value = ''
  saveError.value = false
  subTab.value = 'basic'
  templateFields.value = []
  placeholders.value = []
  const clone = cloneEquipmentType(et)
  if (clone.spec_template == null) clone.spec_template = {}
  if (clone.param_semantics == null) clone.param_semantics = {}
  if (!Array.isArray(clone.ai_hints)) clone.ai_hints = []
  if (clone.title_template == null) clone.title_template = ''
  if (clone.name_template == null) clone.name_template = ''
  if (clone.description_template == null) clone.description_template = ''
  if (clone.description == null) clone.description = ''
  if (clone.ai_title == null) clone.ai_title = ''
  if (clone.ai_description == null) clone.ai_description = ''
  if (clone.ai_placeholder == null) clone.ai_placeholder = ''
  if (clone.icon == null) clone.icon = ''
  selectedEt.value = clone
  selectedEtId.value = clone.id
  loadTemplateFields(clone.id)
}

async function loadTemplateFields(etId) {
  try {
    const { data } = await api.get('/ai-assistant/equipment-type-template-fields/', { params: { equipment_type: etId } })
    if (selectedEtId.value !== etId) return
    templateFields.value = data?.fields || []
    placeholders.value = data?.placeholders || []
  } catch (e) {
    if (selectedEtId.value !== etId) return
    templateFields.value = []
    placeholders.value = []
  }
}

function insertPlaceholder(ph, field, el) {
  if (!el || !selectedEt.value) return
  const start = el.selectionStart != null ? el.selectionStart : el.value.length
  const end = el.selectionEnd != null ? el.selectionEnd : start
  const text = selectedEt.value[field] || ''
  selectedEt.value[field] = text.slice(0, start) + ph + text.slice(end)
  nextTick(() => {
    const pos = start + ph.length
    el.focus()
    el.setSelectionRange(pos, pos)
  })
}

let statusTimer = null
function setSaveStatus(msg, isError) {
  saveMessage.value = msg
  saveError.value = isError
  if (statusTimer) clearTimeout(statusTimer)
  statusTimer = setTimeout(() => { saveMessage.value = ''; saveError.value = false }, 4000)
}

async function saveEquipment(et) {
  const p = {
    code: et.code, name: et.name, description: et.description || '',
    icon: et.icon || '', sorting_order: et.sorting_order || 0,
    filter_endpoint: et.filter_endpoint || null,
    name_template: et.name_template || null,
    description_template: et.description_template || null,
    title_template: et.title_template || null,
    spec_template: et.spec_template || {},
    param_semantics: et.param_semantics || {},
    ai_title: et.ai_title || '', ai_description: et.ai_description || '',
    ai_placeholder: et.ai_placeholder || '',
    ai_hints: Array.isArray(et.ai_hints) ? et.ai_hints : [],
  }
  try {
    await api.patch(`/ai-assistant/equipment-types/${et.id}/`, p)
    setSaveStatus('Сохранено', false)
    // Возвращаем сохранённое состояние в общий список (свежая копия, без общих ссылок)
    emit('saved', cloneEquipmentType(et))
  } catch (e) {
    const detail = e.response?.data?.detail
    const msg = typeof detail === 'string' ? detail : (e.response?.data?.non_field_errors?.[0] || e.message || 'Неизвестная ошибка')
    setSaveStatus('Ошибка сохранения: ' + msg, true)
  }
}

async function saveParam(p) { await api.patch(`/configurator/admin/equipment-type-parameters/${p.id}/`, p) }

async function addParam() {
  if (!selectedEtId.value) return
  const newP = {
    equipment_type: selectedEtId.value,
    param_name: 'new_param',
    field_path: 'new_param',
    field_type: 'choice',
    is_required: false,
    allow_override: true,
    is_active: true,
    sorting_order: filteredParams.value.length,
  }
  try {
    const { data } = await api.post('/configurator/admin/equipment-type-parameters/', newP)
    equipmentParams.value.push(data)
  } catch (e) { alert('Failed to create parameter: ' + (e.response?.data?.detail || e.message)) }
}
</script>

<style scoped>
.split-layout { display: flex; gap: 16px; min-height: 50vh; }
.left-panel { width: 220px; min-width: 180px; border-right: 1px solid #eee; padding-right: 12px; }
.right-panel { flex: 1; min-width: 0; overflow-y: auto; }

.et-list { list-style: none; padding: 0; margin: 0; }
.et-list li { padding: 8px 10px; cursor: pointer; border-radius: 4px; font-size: 13px; border-bottom: 1px solid #f0f0f0; }
.et-list li:hover { background: #f0f4ff; }
.et-list li.active { background: #e3edff; font-weight: 600; }
.et-list li code { font-size: 11px; color: #888; display: block; }

.et-info { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #eee; }
.et-info strong { font-size: 16px; display: block; margin-bottom: 4px; }
.et-info code { font-size: 12px; color: #888; }
.et-info-title { min-width: 0; }
.et-info-actions { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.et-status { font-size: 12px; color: #2e7d32; }
.et-status.error { color: #c62828; }

.et-tabs { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 12px; border-bottom: 2px solid #e0e0e0; }
.et-tabs button { padding: 8px 14px; border: none; background: none; cursor: pointer; font-size: 13px; color: #666; border-bottom: 2px solid transparent; margin-bottom: -2px; }
.et-tabs button.active { color: #1976d2; border-bottom-color: #1976d2; font-weight: 600; }

.et-form { display: flex; flex-direction: column; gap: 12px; }
.et-tab { display: flex; flex-direction: column; gap: 12px; }
.et-form-row { display: flex; gap: 12px; align-items: center; }
.et-form-row > label { flex: 0 0 110px; font-size: 12px; color: #666; }
.et-form-row .cell-input { flex: 1; }
.et-form-col { display: flex; flex-direction: column; gap: 4px; }
.et-form-col > label { font-size: 12px; color: #666; }
.et-form-block { border: 1px solid #e5e7eb; border-radius: 6px; padding: 10px 12px; background: #fafafa; display: flex; flex-direction: column; gap: 8px; }
.et-form-block-label { font-size: 13px; font-weight: 600; color: #374151; }
.et-chips { display: flex; flex-wrap: wrap; gap: 6px; max-height: 120px; overflow-y: auto; }
.et-chip { padding: 3px 8px; background: #e8f0fe; border: 1px solid #aecbfa; border-radius: 12px; font-family: monospace; font-size: 12px; color: #1a56b0; cursor: pointer; line-height: 1.3; }
.et-chip:hover { background: #d2e3fc; border-color: #7aa7f5; }

.param-section { margin-top: 16px; }
.param-section h4 { font-size: 14px; color: #555; margin-bottom: 8px; border-bottom: 1px solid #f0f0f0; padding-bottom: 4px; }
.info-bar { font-size: 12px; color: #888; margin-bottom: 8px; }

.cell-input { border: 1px solid #ddd; padding: 4px 8px; border-radius: 4px; font-size: 13px; width: 100%; box-sizing: border-box; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; font-size: 13px; }
th { font-weight: 600; color: #666; background: #fafafa; }
select { padding: 4px 8px; border-radius: 4px; border: 1px solid #ddd; font-size: 13px; max-width: 200px; }
.btn-add { background: #1976d2; color: #fff; border: none; padding: 6px 14px; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-save-sm { background: none; border: none; cursor: pointer; font-size: 14px; padding: 0 4px; }
.btn-save { background: #2e7d32; color: #fff; border: none; padding: 8px 20px; border-radius: 4px; cursor: pointer; }
.empty { color: #999; font-style: italic; }
</style>
