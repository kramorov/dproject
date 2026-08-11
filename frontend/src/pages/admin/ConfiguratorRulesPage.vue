<!-- ConfiguratorRulesPage.vue — Админ-страница правил конфигуратора -->
<template>
  <div class="rules-admin">
    <h2>⚙️ Правила конфигуратора</h2>

    <!-- Tabs -->
    <div class="tabs">
      <button v-for="t in tabs" :key="t.key" :class="['tab', { active: activeTab === t.key }]"
              @click="activeTab = t.key">{{ t.label }}</button>
    </div>

    <!-- Таблица PropagationRules -->
    <div v-if="activeTab === 'propagation'" class="table-wrap">
      <div class="toolbar">
        <span class="count">{{ propagationRules.length }} правил</span>
        <a :href="djangoAdminUrl('propagationrule')" target="_blank" class="btn btn-add">+ Добавить (Django admin)</a>
        <span v-if="loading" class="spinner">⏳</span>
      </div>
      <table>
        <thead><tr>
          <th>Code</th><th>Equipment Type</th><th>Param</th><th>Source</th>
          <th>Mandatory</th><th>Override</th><th>Priority</th><th>Active</th><th></th>
        </tr></thead>
        <tbody>
          <tr v-for="r in propagationRules" :key="r.id">
            <td><code>{{ r.code }}</code></td>
            <td><code>{{ r.equipment_type_code }}</code></td>
            <td><input v-model="r.param_name" @change="save('propagation', r)" class="edit-inline" /></td>
            <td><select v-model="r.source" @change="save('propagation', r)">
              <option v-for="s in sources" :key="s" :value="s">{{ s }}</option>
            </select></td>
            <td><input type="checkbox" v-model="r.is_mandatory" @change="save('propagation', r)" /></td>
            <td><input type="checkbox" v-model="r.allow_override" @change="save('propagation', r)" /></td>
            <td><input type="number" v-model.number="r.priority" @change="save('propagation', r)" style="width:60px" /></td>
            <td><input type="checkbox" v-model="r.is_active" @change="save('propagation', r)" /></td>
            <td><button class="btn btn-del" @click="del('propagation', r)">✕</button></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Таблица ParameterBindings -->
    <div v-if="activeTab === 'bindings'" class="table-wrap">
      <div class="toolbar">
        <span class="count">{{ bindings.length }} привязок</span>
        <a :href="djangoAdminUrl('parameterbinding')" target="_blank" class="btn btn-add">+ Добавить (Django admin)</a>
      </div>
      <table>
        <thead><tr>
          <th>Equipment Type</th><th>Param Name</th><th>Rule</th><th>Active</th><th></th>
        </tr></thead>
        <tbody>
          <tr v-for="b in bindings" :key="b.id">
            <td><code>{{ b.equipment_type_code }}</code></td>
            <td><input v-model="b.param_name" @change="save('bindings', b)" class="edit-inline" /></td>
            <td><code>{{ b.rule_code }}</code></td>
            <td><input type="checkbox" v-model="b.is_active" @change="save('bindings', b)" /></td>
            <td><button class="btn btn-del" @click="del('bindings', b)">✕</button></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Таблица ParameterRules -->
    <div v-if="activeTab === 'parameter_rules'" class="table-wrap">
      <div class="toolbar">
        <span class="count">{{ parameterRules.length }} правил</span>
      </div>
      <table>
        <thead><tr>
          <th>Code</th><th>Name</th><th>Match Type</th><th>Hardness</th>
          <th>Relaxation</th><th>Active</th>
        </tr></thead>
        <tbody>
          <tr v-for="r in parameterRules" :key="r.id">
            <td><code>{{ r.code }}</code></td>
            <td>{{ r.name }}</td>
            <td>{{ r.match_type }}</td>
            <td>{{ r.hardness }}</td>
            <td>{{ r.relaxation_strategy }}</td>
            <td><input type="checkbox" v-model="r.is_active" @change="save('parameter_rules', r)" /></td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>
  </div>
</template>

<script>
import api from '@/shared/api'

const ENDPOINTS = {
  propagation: '/configurator/admin/equipment-type-parameters/',
  parameter_rules: '/configurator/admin/parameter-rules/',
  bindings: '/configurator/admin/parameter-bindings/',
}

export default {
  name: 'ConfiguratorRulesPage',
  data() {
    return {
      activeTab: 'propagation',
      tabs: [
        { key: 'propagation', label: 'PropagationRules' },
        { key: 'bindings', label: 'ParameterBindings' },
        { key: 'parameter_rules', label: 'ParameterRules' },
      ],
      sources: ['user', 'global', 'parent', 'derived'],
      propagationRules: [],
      bindings: [],
      parameterRules: [],
      loading: false,
      error: '',
    }
  },
  async mounted() {
    await this.loadAll()
  },
  methods: {
    async loadAll() {
      this.loading = true
      try {
        const [pr, pb, prule] = await Promise.all([
          api.get(ENDPOINTS.propagation),
          api.get(ENDPOINTS.bindings),
          api.get(ENDPOINTS.parameter_rules),
        ])
        this.propagationRules = pr.data.results || pr.data
        this.bindings = pb.data.results || pb.data
        this.parameterRules = prule.data.results || prule.data
      } catch (e) { this.error = 'Ошибка загрузки' }
      finally { this.loading = false }
    },

    async save(type, item) {
      try {
        const ep = ENDPOINTS[type] + item.id + '/'
        await api.patch(ep, item)
      } catch (e) { console.warn('Save failed', e) }
    },

    djangoAdminUrl(model) {
      return `/admin/configurator/${model}/add/`
    },

    async del(type, item) {
      if (!confirm('Удалить?')) return
      try {
        const ep = ENDPOINTS[type] + item.id + '/'
        await api.delete(ep)
        if (type === 'propagation') {
          this.propagationRules = this.propagationRules.filter(r => r.id !== item.id)
        } else if (type === 'bindings') {
          this.bindings = this.bindings.filter(b => b.id !== item.id)
        }
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

.edit-inline { border: 1px solid #ddd; padding: 2px 4px; border-radius: 2px; width: 100%; box-sizing: border-box; font-size: 0.82rem; }
select { font-size: 0.82rem; }

.btn { padding: 4px 10px; border: 1px solid #ccc; border-radius: 3px; cursor: pointer; font-size: 0.8rem; }
.btn-add { background: #e8f5e9; }
.btn-del { background: #ffebee; color: #c00; }

.error-msg { background: #fee; color: #c00; padding: 8px 12px; border-radius: 4px; margin: 12px 0; }
.spinner { color: #888; }
</style>
