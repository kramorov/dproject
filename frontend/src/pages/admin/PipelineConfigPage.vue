<template>
  <div class="pipeline-config">
    <h1>Pipeline Configurator</h1>
    <nav class="tabs">
      <button v-for="t in tabs" :key="t.id" :class="{ active: activeTab === t.id }" @click="activeTab = t.id">{{ t.label }}</button>
    </nav>

    <!-- Pipeline Skills -->
    <section v-show="activeTab === 'skills'" class="section">
      <h2>Pipeline Skills <button class="btn-add" @click="addSkill">+ Add</button></h2>
      <table>
        <thead><tr><th>Code</th><th>Step</th><th>Equipment</th><th>Prompt</th><th>Schema</th><th>Model</th><th>Avg Latency</th><th></th></tr></thead>
        <tbody>
          <tr v-for="(s, i) in skills" :key="i">
            <td><input v-model="s.code" class="cell-input" /></td>
            <td><select v-model="s.step"><option v-for="sc in STEP_CHOICES" :key="sc[0]" :value="sc[0]">{{ sc[1] }}</option></select></td>
            <td><select v-model="s.equipment_type"><option :value="null">* (общий)</option><option v-for="et in equipmentTypes" :key="et.id" :value="et.id">{{ et.name }}</option></select></td>
            <td><select v-model="s.prompt_template"><option :value="null">—</option><option v-for="pt in promptTemplates" :key="pt.id" :value="pt.id">{{ pt.code || pt.name }} v{{ pt.version }}</option></select></td>
            <td><select v-model="s.output_schema"><option :value="null">—</option><option v-for="sc in schemas" :key="sc.id" :value="sc.id">{{ sc.name }} v{{ sc.version }}</option></select></td>
            <td><select v-model="s.model_role"><option v-for="r in modelRoles" :key="r" :value="r">{{ r }}</option></select></td>
            <td>{{ s.avg_latency_ms ? s.avg_latency_ms + ' ms' : '—' }}</td>
            <td><button class="btn-save-sm" @click="saveSkill(s)">💾</button><button class="btn-del" @click="deleteSkill(s.id)">✕</button></td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- Skill Overrides -->
    <section v-show="activeTab === 'overrides'" class="section">
      <h2>Skill Overrides <button class="btn-add" @click="addOverride">+ Add</button></h2>
      <table>
        <thead><tr><th>Customer</th><th>Skill</th><th>Model Role</th><th>Suffix</th><th></th></tr></thead>
        <tbody>
          <tr v-for="(o, i) in overrides" :key="i">
            <td><select v-model="o.customer"><option v-for="c in customers" :key="c.id" :value="c.id">{{ c.name }}</option></select></td>
            <td><select v-model="o.step_config"><option v-for="s in skills" :key="s.id" :value="s.id">{{ s.code || (s.step + ' / ' + (s.equipment_type_name || '*')) }}</option></select></td>
            <td><input v-model="o.model_role" class="cell-input" placeholder="default" /></td>
            <td><input v-model="o.prompt_suffix" class="cell-input" /></td>
            <td><button class="btn-save-sm" @click="saveOverride(o)">💾</button><button class="btn-del" @click="deleteOverride(o.id)">✕</button></td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- Prompt Templates -->
    <section v-show="activeTab === 'prompts'" class="section">
      <h2>Prompt Templates <button class="btn-add" @click="addPrompt">+ Add</button></h2>
      <table>
        <thead><tr><th>#</th><th>Code</th><th>Name</th><th>Version</th><th>Active</th><th></th></tr></thead>
        <tbody>
          <tr v-for="(p, i) in promptTemplates" :key="i">
            <td><input v-model="p.sorting_order" class="cell-input" size="3" /></td>
            <td><input v-model="p.code" class="cell-input" /></td>
            <td><input v-model="p.name" class="cell-input" /></td>
            <td><input v-model="p.version" class="cell-input" size="6" /></td>
            <td><input type="checkbox" v-model="p.is_active" /></td>
            <td>
              <button class="btn-edit" @click="editingPrompt = p">Edit text</button>
              <button class="btn-save-sm" @click="savePrompt(p)">💾</button>
              <button class="btn-del" @click="deletePrompt(p.id)">✕</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="editingPrompt" class="modal-overlay" @click.self="editingPrompt = null">
        <div class="modal">
          <h3>{{ editingPrompt.code || editingPrompt.name }} v{{ editingPrompt.version }}</h3>
          <textarea v-model="editingPrompt.template_text" rows="20" class="prompt-editor"></textarea>
          <div class="modal-actions"><button class="btn-save" @click="savePrompt(editingPrompt); editingPrompt = null">Save</button><button @click="editingPrompt = null">Cancel</button></div>
        </div>
      </div>
    </section>

    <!-- JSON Schemas -->
    <section v-show="activeTab === 'schemas'" class="section">
      <h2>JSON Schemas <button class="btn-add" @click="addSchema">+ Add</button></h2>
      <table>
        <thead><tr><th>#</th><th>Name</th><th>Version</th><th>Active</th><th></th></tr></thead>
        <tbody>
          <tr v-for="(s, i) in schemas" :key="i">
            <td><input v-model="s.sorting_order" class="cell-input" size="3" /></td>
            <td><input v-model="s.name" class="cell-input" /></td>
            <td><input v-model="s.version" class="cell-input" size="6" /></td>
            <td><input type="checkbox" v-model="s.is_active" /></td>
            <td>
              <button class="btn-edit" @click="editingSchema = s">Edit JSON</button>
              <button class="btn-save-sm" @click="saveSchema(s)">💾</button>
              <button class="btn-del" @click="deleteSchema(s.id)">✕</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="editingSchema" class="modal-overlay" @click.self="editingSchema = null">
        <div class="modal modal-wide">
          <h3>{{ editingSchema.name }} v{{ editingSchema.version }}</h3>
          <div v-if="(editingSchema._viewMode || 'tree') === 'tree'" class="json-tree-view">
            <vue-json-pretty :data="safeParseJSON(editingSchema.schema_json_text)" :deep="3" showLineNumber />
          </div>
          <div v-else-if="editingSchema._viewMode === 'table'" class="json-tree-view">
            <JsonTableViewer :data="safeParseJSON(editingSchema.schema_json_text)" />
          </div>
          <div v-else>
            <textarea v-model="editingSchema.schema_json_text" rows="18" class="prompt-editor" :class="{ invalid: editingSchema._jsonError }"></textarea>
            <div v-if="editingSchema._jsonError" class="json-error">{{ editingSchema._jsonError }}</div>
          </div>
          <div class="modal-actions" style="justify-content: space-between">
            <div>
              <button class="btn-mode" :class="{ active: (editingSchema._viewMode || 'tree') === 'tree' }" @click="editingSchema._viewMode = 'tree'">Tree</button>
              <button class="btn-mode" :class="{ active: editingSchema._viewMode === 'table' }" @click="editingSchema._viewMode = 'table'">Table</button>
              <button class="btn-mode" :class="{ active: editingSchema._viewMode === 'raw' }" @click="editingSchema._viewMode = 'raw'">Raw</button>
              <button class="btn-edit" @click="formatJSON(editingSchema, 'schema_json_text')">Format</button>
            </div>
            <div>
              <button class="btn-save" @click="saveSchema(editingSchema); editingSchema = null">Save</button>
              <button @click="editingSchema = null">Cancel</button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Equipment Types -->
    <section v-show="activeTab === 'equipment'" class="section">
      <h2>Equipment Types — AI Settings</h2>
      <table>
        <thead><tr><th>Code</th><th>Name</th><th>Filter Endpoint</th><th>Param Semantics</th><th></th></tr></thead>
        <tbody>
          <tr v-for="(et, i) in equipmentTypes" :key="i">
            <td>{{ et.code }}</td><td>{{ et.name }}</td>
            <td><input v-model="et.filter_endpoint" class="cell-input" /></td>
            <td><button class="btn-edit" @click="editingEquipSemantics = et">Edit</button></td>
            <td><button class="btn-save-sm" @click="saveEquipment(et)">💾</button></td>
          </tr>
        </tbody>
      </table>
      <div v-if="editingEquipSemantics" class="modal-overlay" @click.self="editingEquipSemantics = null">
        <div class="modal modal-wide">
          <h3>{{ editingEquipSemantics.name }} — param_semantics</h3>
          <div v-if="!editingEquipSemantics._showRaw" class="json-tree-view">
            <JsonTableViewer :data="safeParseJSON(editingEquipSemantics.param_semantics_text)" />
          </div>
          <div v-else>
            <textarea v-model="editingEquipSemantics.param_semantics_text" rows="14" class="prompt-editor" :class="{ invalid: editingEquipSemantics._jsonError }"></textarea>
            <div v-if="editingEquipSemantics._jsonError" class="json-error">{{ editingEquipSemantics._jsonError }}</div>
          </div>
          <div v-if="editingEquipSemantics._jsonError" class="json-error">{{ editingEquipSemantics._jsonError }}</div>
          <div class="modal-actions" style="justify-content: space-between">
            <button class="btn-edit" @click="editingEquipSemantics._showRaw = !editingEquipSemantics._showRaw">{{ editingEquipSemantics._showRaw ? 'Tree view' : 'Edit raw' }}</button>
              <button class="btn-edit" @click="formatJSON(editingEquipSemantics, 'param_semantics_text')">Format JSON</button>
            <div>
              <button class="btn-save" @click="saveEquipment(editingEquipSemantics); editingEquipSemantics = null">Save</button>
              <button @click="editingEquipSemantics = null">Cancel</button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Estimated Latency -->
    <section v-show="activeTab === 'skills'" class="section latency-section">
      <h3>Estimated Response Times</h3>
      <div v-for="s in skills.filter(x => x.avg_latency_ms)" :key="'lat-' + s.id" class="latency-row">
        <strong>{{ s.step }}{{ s.equipment_type_name ? ' / ' + s.equipment_type_name : '' }}:</strong> {{ s.avg_latency_ms }} ms ({{ s.latency_sample_count }} samples)
      </div>
      <div v-if="!skills.some(s => s.avg_latency_ms)" class="empty">No data yet.</div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/shared/api'
import JsonTableViewer from '@/components/JsonTableViewer.vue'
import VueJsonPretty from 'vue-json-pretty'
import 'vue-json-pretty/lib/styles.css'

const activeTab = ref('skills')
const tabs = [
  { id: 'skills', label: 'Pipeline Skills' }, { id: 'overrides', label: 'Overrides' },
  { id: 'prompts', label: 'Prompt Templates' }, { id: 'schemas', label: 'JSON Schemas' },
  { id: 'equipment', label: 'Equipment Types' },
]

const STEP_CHOICES = [['decompose','Decompose'],['extract','Extract'],['filter','Filter'],['select','Select'],['compare','Compare'],['format','Format']]

const skills = ref([]); const overrides = ref([]); const promptTemplates = ref([])
const schemas = ref([]); const equipmentTypes = ref([]); const modelRoles = ref([]); const customers = ref([])
const editingPrompt = ref(null); const editingSchema = ref(null); const editingEquipSemantics = ref(null)

onMounted(async () => {
  const safe = p => p.then(r => {
  const d = r.data
  if (Array.isArray(d)) return d
  if (d && Array.isArray(d.results)) return d.results
  return []
}).catch(() => [])
  const [skillsRaw, overridesRaw, promptsRaw, schemasRaw, equipmentRaw, customersRaw, rolesResp] = await Promise.all([
    safe(api.get('/ai-assistant/skills/')), safe(api.get('/ai-assistant/overrides/')),
    safe(api.get('/ai-assistant/prompts/')), safe(api.get('/ai-assistant/schemas/')),
    safe(api.get('/ai-assistant/equipment-types/')), safe(api.get('/ai-assistant/customers/')),
    safe(api.get('/ai-assistant/model-roles/')),
  ])
  skills.value = skillsRaw.map(sk => ({ ...sk, equipment_type: sk.equipment_type || null, equipment_type_name: sk.equipment_type_detail?.name || null, prompt_template: sk.prompt_template || null }))
  overrides.value = overridesRaw
  promptTemplates.value = promptsRaw
  schemas.value = schemasRaw.map(s => ({ ...s, schema_json_text: JSON.stringify(s.schema_json, null, 2) }))
  equipmentTypes.value = equipmentRaw.map(e => ({ ...e, param_semantics_text: JSON.stringify(e.param_semantics || {}, null, 2) }))
  modelRoles.value = rolesResp; customers.value = customersRaw
})

async function saveSkill(s) {
  const p = { ...s, equipment_type: s.equipment_type || null, prompt_template: s.prompt_template || null, output_schema: s.output_schema || null }
  s.id ? await api.patch(`/ai-assistant/skills/${s.id}/`, p) : (await api.post('/ai-assistant/skills/', p)).data.id && (s.id = (await api.post('/ai-assistant/skills/', p)).data.id)
}
async function addSkill() { skills.value.push({ step: 'decompose', equipment_type: null, model_role: 'debug', priority: 10, is_active: true }) }
async function deleteSkill(id) { if (confirm('Delete?')) { await api.delete(`/ai-assistant/skills/${id}/`); skills.value = skills.value.filter(s => s.id !== id) } }

async function saveOverride(o) { o.id ? await api.patch(`/ai-assistant/overrides/${o.id}/`, o) : (await api.post('/ai-assistant/overrides/', o)).data.id && (o.id = (await api.post('/ai-assistant/overrides/', o)).data.id) }
async function addOverride() { overrides.value.push({ step_config: null, customer: null, is_active: true }) }
async function deleteOverride(id) { if (confirm('Delete?')) { await api.delete(`/ai-assistant/overrides/${id}/`); overrides.value = overrides.value.filter(o => o.id !== id) } }

async function savePrompt(p) { p.id ? await api.patch(`/ai-assistant/prompts/${p.id}/`, p) : (await api.post('/ai-assistant/prompts/', p)).data.id && (p.id = (await api.post('/ai-assistant/prompts/', p)).data.id) }
async function addPrompt() { promptTemplates.value.push({ name: 'new', version: '1', code: '', template_text: '', is_active: true }) }
async function deletePrompt(id) { if (confirm('Delete?')) { await api.delete(`/ai-assistant/prompts/${id}/`); promptTemplates.value = promptTemplates.value.filter(p => p.id !== id) } }

async function saveSchema(s) {
  try { s.schema_json = JSON.parse(s.schema_json_text) } catch (e) { alert('Invalid JSON'); return }
  const p = { name: s.name, version: s.version, schema_json: s.schema_json, is_active: s.is_active, sorting_order: s.sorting_order }
  s.id ? await api.patch(`/ai-assistant/schemas/${s.id}/`, p) : (await api.post('/ai-assistant/schemas/', p)).data.id && (s.id = (await api.post('/ai-assistant/schemas/', p)).data.id)
}
async function addSchema() { schemas.value.push({ name: 'new', version: '1', schema_json_text: '{}', schema_json: {}, is_active: true }) }
async function deleteSchema(id) { if (confirm('Delete?')) { await api.delete(`/ai-assistant/schemas/${id}/`); schemas.value = schemas.value.filter(s => s.id !== id) } }

async function saveEquipment(et) {
  try { et.param_semantics = JSON.parse(et.param_semantics_text) } catch (e) { alert('Invalid JSON'); return }
  await api.patch(`/ai-assistant/equipment-types/${et.id}/`, { param_semantics: et.param_semantics, filter_endpoint: et.filter_endpoint })
}

function safeParseJSON(text) { try { return JSON.parse(text) } catch { return {} } }

function formatJSON(obj, field) {
  try {
    const parsed = JSON.parse(obj[field])
    obj[field] = JSON.stringify(parsed, null, 2)
    obj._jsonError = null
  } catch (e) {
    obj._jsonError = e.message
  }
}
</script>

<style scoped>
.pipeline-config { padding: 24px; max-width: 1400px; margin: 0 auto; font-family: system-ui; }
h1 { margin-bottom: 20px; font-size: 24px; }
.tabs { display: flex; gap: 4px; margin-bottom: 20px; border-bottom: 2px solid #e0e0e0; }
.tabs button { padding: 10px 20px; border: none; background: none; cursor: pointer; font-size: 14px; color: #666; border-bottom: 2px solid transparent; margin-bottom: -2px; }
.tabs button.active { color: #1976d2; border-bottom-color: #1976d2; font-weight: 600; }
.section { background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,.1); }
.section h2 { font-size: 18px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; font-size: 13px; }
th { font-weight: 600; color: #666; background: #fafafa; }
.cell-input { border: 1px solid #ddd; padding: 4px 8px; border-radius: 4px; font-size: 13px; width: 100%; box-sizing: border-box; }
select { padding: 4px 8px; border-radius: 4px; border: 1px solid #ddd; font-size: 13px; max-width: 200px; }
.btn-add { background: #1976d2; color: #fff; border: none; padding: 6px 14px; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-del { background: none; border: none; color: #e53935; cursor: pointer; font-size: 16px; padding: 0 4px; }
.btn-mode { background: none; border: 1px solid #999; color: #666; padding: 3px 10px; border-radius: 3px; cursor: pointer; font-size: 12px; margin-right: 2px; }
.btn-mode.active { background: #1976d2; color: #fff; border-color: #1976d2; }
.btn-edit { background: none; border: 1px solid #1976d2; color: #1976d2; padding: 2px 8px; border-radius: 3px; cursor: pointer; font-size: 12px; margin-right: 4px; }
.btn-save-sm { background: none; border: none; cursor: pointer; font-size: 14px; padding: 0 4px; }
.btn-save { background: #2e7d32; color: #fff; border: none; padding: 8px 20px; border-radius: 4px; cursor: pointer; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: #fff; padding: 24px; border-radius: 8px; width: 800px; }
.modal-wide { width: 1000px; max-height: 80vh; overflow-y: auto; }
.modal h3 { margin-bottom: 12px; }
.modal-actions { display: flex; gap: 10px; margin-top: 12px; justify-content: flex-end; }
.prompt-editor { width: 100%; font-family: 'Courier New', monospace; font-size: 13px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
.latency-section { background: #f5f5f5; }
.latency-row { padding: 4px 0; font-size: 13px; }
.empty { color: #999; font-style: italic; }
.json-tree-view { max-height: 60vh; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; padding: 8px; background: #fafafa; }
.json-error { color: #e53935; font-size: 12px; margin-top: -8px; margin-bottom: 8px; padding: 4px 8px; background: #ffebee; border-radius: 3px; }
.prompt-editor.invalid { border-color: #e53935; background: #fff8f8; }
</style>
