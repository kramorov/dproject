<!-- ConfiguratorRulesPage.vue — Админ-страница параметров типов оборудования -->
<template>
  <div class="rules-admin">
    <h2>⚙️ Параметры типов оборудования</h2>

    <div class="tabs">
      <button v-for="t in tabs" :key="t.key" :class="['tab', { active: activeTab === t.key }]"
              @click="activeTab = t.key">{{ t.label }}</button>
    </div>

    <!-- EquipmentTypeParameter — moved to Pipeline Config -->
    <div v-if="activeTab === 'etp'" class="section">
      <p>Редактирование параметров типов оборудования перенесено в <strong>AI Pipeline Config</strong>.</p>
      <p>Там же настраиваются промпты, JSON-схемы и семантика сравнения.</p>
      <div class="actions">
        <a href="/admin/pipeline-config" class="btn btn-link">🔗 Открыть AI Pipeline Config → вкладка Equipment Types</a>
      </div>
    </div>

    <!-- ParameterSources (read-only) -->
    <div v-if="activeTab === 'sources'" class="table-wrap">
      <div class="toolbar">
        <span class="count">{{ sources.length }} источников</span>
      </div>
      <table>
        <thead><tr><th>Code</th><th>Название</th><th>Описание</th></tr></thead>
        <tbody>
          <tr v-for="s in sources" :key="s.id">
            <td><code>{{ s.code }}</code></td>
            <td>{{ s.name }}</td>
            <td style="font-size:0.8rem;color:#666">{{ s.description }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- AI Pipeline -->
    <div v-if="activeTab === 'ai'" class="section">
      <p>AI Pipeline настраивает промпты и JSON-схемы для каждого шага и типа оборудования.</p>
      <div class="actions">
        <a href="/admin/pipeline-config" class="btn btn-link">🔗 Открыть AI Pipeline Config</a>
      </div>
      <hr />
      <h3>Сгенерировать JSON Schema из ETP</h3>
      <div class="field-row">
        <label>Тип оборудования:</label>
        <select v-model="schemaEqType" style="width:200px">
          <option :value="null">— выберите —</option>
          <option v-for="et in uniqueEqTypes" :key="et.id" :value="et.id">{{ et.code }}</option>
        </select>
        <button @click="generateSchema" :disabled="!schemaEqType" class="btn btn-gen">
          {{ generating ? '...' : 'Сгенерировать' }}
        </button>
      </div>
      <pre v-if="generatedSchema" class="schema-preview">{{ generatedSchema }}</pre>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>
  </div>
</template>

<script>
import api from '@/shared/api'

const ENDPOINTS = {
  etp: '/configurator/admin/equipment-type-parameters/',
  sources: '/configurator/admin/parameter-sources/',
}

export default {
  name: 'ConfiguratorRulesPage',
  data() {
    return {
      activeTab: 'etp',
      tabs: [
        { key: 'etp', label: 'Параметры' },
        { key: 'sources', label: 'Источники' },
        { key: 'ai', label: 'AI Pipeline' },
      ],
      redirectToPipeline: true,
      etpList: [],
      sources: [],
      schemaEqType: null,
      generatedSchema: '',
      generating: false,
      loading: false,
      error: '',
    }
  },
  computed: {
    uniqueEqTypes() {
      const seen = new Map()
      for (const p of this.etpList) {
        if (p.equipment_type_code && !seen.has(p.equipment_type_code)) {
          seen.set(p.equipment_type_code, { id: p.equipment_type, code: p.equipment_type_code })
        }
      }
      return [...seen.values()]
    },
  },
  async mounted() {
    await this.loadAll()
  },
  methods: {
    async generateSchema() {
      if (!this.schemaEqType) return
      this.generating = true
      try {
        const { data } = await api.get(
          `/configurator/admin/equipment-type-parameters/schema/?equipment_type=${this.schemaEqType}`
        )
        this.generatedSchema = JSON.stringify(data.schema, null, 2)
      } catch (e) {
        this.generatedSchema = 'Ошибка генерации: ' + (e.response?.data?.error || e.message)
      } finally { this.generating = false }
    },
    async loadAll() {
      this.loading = true
      try {
        const [etpRes, srcRes] = await Promise.all([
          api.get(ENDPOINTS.etp),
          api.get(ENDPOINTS.sources),
        ])
        this.etpList = etpRes.data.results || etpRes.data
        this.sources = srcRes.data.results || srcRes.data
      } catch (e) { this.error = 'Ошибка загрузки' }
      finally { this.loading = false }
    },

    async save(type, item) {
      try {
        await api.patch(ENDPOINTS[type] + item.id + '/', {
          param_name: item.param_name,
          field_path: item.field_path,
          param_type: item.param_type,
          unit: item.unit,
          compare_direction: item.compare_direction,
          compare_label: item.compare_label,
          is_required: item.is_required,
          is_active: item.is_active,
        })
      } catch (e) { console.warn('Save failed', e) }
    },

    async addParam() {
      try {
        const { data } = await api.post(ENDPOINTS.etp, {
          equipment_type: null,
          param_name: 'new_param',
          field_path: 'new_param',
          is_active: true,
        })
        this.etpList.push(data)
      } catch (e) {
        this.error = 'Ошибка создания: ' + (e.response?.data?.detail || e.message)
      }
    },

    async del(type, item) {
      if (!confirm('Удалить?')) return
      try {
        await api.delete(ENDPOINTS[type] + item.id + '/')
        if (type === 'etp') this.etpList = this.etpList.filter(p => p.id !== item.id)
      } catch (e) { console.warn('Delete failed', e) }
    },
  },
}
</script>

<style scoped>
.rules-admin { max-width: 1200px; margin: 0 auto; padding: 16px; font-family: system-ui, sans-serif; }
h2 { font-size: 1.3rem; margin-bottom: 12px; }
.tabs { display: flex; gap: 4px; margin-bottom: 12px; }
.tab { padding: 6px 14px; border: 1px solid #ccc; border-radius: 4px 4px 0 0; background: #f0f0f0; cursor: pointer; font-size: 0.85rem; }
.tab.active { background: #fff; border-bottom-color: #fff; font-weight: 600; }
.toolbar { display: flex; gap: 12px; align-items: center; margin-bottom: 8px; }
.count { color: #888; font-size: 0.8rem; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
th, td { padding: 5px 8px; border: 1px solid #e0e0e0; text-align: left; }
th { background: #f8f8f8; font-weight: 600; }
tr:hover { background: #f4f4ff; }
select { font-size: 0.82rem; }
.btn { padding: 4px 10px; border: 1px solid #ccc; border-radius: 3px; cursor: pointer; font-size: 0.8rem; }
.btn-add { background: #e8f5e9; text-decoration: none; color: inherit; }
.btn-del { background: #ffebee; color: #c00; }
.error-msg { background: #fee; color: #c00; padding: 8px 12px; border-radius: 4px; margin: 12px 0; }
.spinner { color: #888; }
.info-hint { background: #e3f2fd; color: #1565c0; padding: 8px 12px; border-radius: 4px; font-size: 0.78rem; margin-bottom: 8px; display: block; }

.section { background: #fafafa; border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; }
.field-row { display: flex; gap: 12px; align-items: center; margin: 12px 0; }
.schema-preview { background: #1e1e1e; color: #d4d4d4; padding: 12px; border-radius: 4px; font-size: 0.78rem; overflow-x: auto; max-height: 400px; white-space: pre-wrap; }
.btn-link { background: #e3f2fd; color: #1565c0; display: inline-block; }
.btn-gen { background: #e8f5e9; }
hr { margin: 16px 0; border: none; border-top: 1px solid #e0e0e0; }
</style>
