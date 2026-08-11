<!-- ConfiguratorPaKitPage.vue — Конфигуратор сборки с чекбоксами и зависимостями -->
<template>
  <div class="configurator">
    <h1>🔧 Конфигуратор сборки</h1>

    <!-- Выбор типа сборки -->
    <div v-if="!assembly" class="section start-screen">
      <h2>Выберите тип оборудования</h2>
      <div class="cg-list">
        <button v-for="cg in compositionGroups" :key="cg.id"
                class="cg-card" @click="createAssembly(cg.id)">
          <strong>{{ cg.name || cg.code }}</strong>
          <small>{{ cg.code }}</small>
        </button>
      </div>
      <div v-if="creating" class="hint">Создание сборки...</div>
      <div v-if="error" class="error-msg">{{ error }}</div>
    </div>

    <!-- Основной интерфейс -->
    <div class="layout" v-else>
      <!-- Левая панель: дерево -->
      <aside class="tree-panel">
        <h3>Состав сборки</h3>
        <ul class="tree">
          <li v-for="node in flatTree" :key="node.id"
              :class="{
                active: selectedComponentId === node.id,
                virtual: !node.equipment_type_code,
                disabled: isNodeDisabled(node),
                skipped: node.status === 'skipped'
              }"
              :style="{ paddingLeft: (node.level * 14) + 'px' }"
              @click="selectComponent(node)">
            <!-- Чекбокс -->
            <input type="checkbox"
                   :checked="node.status !== 'skipped'"
                   :disabled="isNodeDisabled(node)"
                   @click.stop
                   @change="toggleComponent(node, $event)" />
            <span class="status-dot" :class="node.status"></span>
            <span class="node-label">{{ nodeLabel(node) }}</span>
            <span v-if="node.selected_product_id" class="selected-badge">✓</span>
          </li>
        </ul>
        <div class="actions" style="margin-top:12px">
          <button class="btn-primary btn-small" @click="refreshAssembly">🔄 Обновить</button>
        </div>
      </aside>

      <!-- Правая панель: детали -->
      <main class="detail-panel">
        <!-- Глобальные требования -->
        <section class="section">
          <h2>🌍 Глобальные требования</h2>
          <div class="global-grid">
            <div class="global-col">
              <ExdFilter :all-options="[]" @update:modelValue="onExdChange" />
            </div>
            <div class="global-col">
              <ClimateFilter @update:temps="onClimateChange" />
            </div>
          </div>
        </section>

        <!-- Выбранный компонент -->
        <section class="section" v-if="selectedComponent && selectedComponent.status !== 'skipped'">
          <h2>
            📋 {{ nodeLabel(selectedComponent) }}
            <span class="badge" v-if="selectedComponent.status === 'selected'">выбран</span>
            <span class="badge badge-filtered" v-if="selectedComponent.status === 'filtered'">кандидаты</span>
          </h2>

          <!-- Виртуальный узел -->
          <div v-if="!selectedComponent.equipment_type_code" class="hint">
            Это группа без оборудования. Выберите дочерний компонент.
          </div>

          <!-- Компонент с оборудованием -->
          <div v-else>
            <!-- Предупреждение: сначала выберите родителя -->
            <div v-if="needsParentFirst(selectedComponent)" class="relaxed-note">
              ⚠️ Сначала выберите продукт для родительского компонента.
            </div>

            <!-- Форма требований -->
            <div v-else>
              <div v-if="loadingSchema" class="hint">Загрузка полей...</div>
              <div v-else-if="filterSchema && filterSchema.fields && filterSchema.fields.length">
                <div class="grid-3">
                  <div class="field" v-for="field in visibleFields" :key="field.param_name">
                    <label>{{ field.label }}</label>
                    <select v-if="field.options && field.options.length"
                            v-model="ownReqs[field.param_name]"
                            @change="saveOwnReqs">
                      <option :value="null">— Не указано —</option>
                      <option v-for="opt in field.options" :key="opt.id" :value="opt.id">{{ opt.name }}</option>
                    </select>
                    <input v-else type="text" v-model="ownReqs[field.param_name]"
                           @change="saveOwnReqs" />
                  </div>
                </div>

                <div class="actions">
                  <button class="btn-primary" @click="runFilter" :disabled="filtering">
                    {{ filtering ? 'Подбор...' : '🔍 Подобрать' }}
                  </button>
                </div>
              </div>
              <div v-else class="hint">Нет полей требований для этого типа.</div>
            </div>

            <!-- Результаты -->
            <div v-if="filterResults" class="results">
              <p v-if="filterResults.relaxed" class="relaxed-note">
                ⚠️ Точных совпадений нет. {{ filterResults.relaxation_detail }}
              </p>
              <div v-if="filterResults.relaxation_detail && !filterResults.relaxed" class="hint">
                {{ filterResults.relaxation_detail }}
              </div>
              <div v-if="filterResults.candidates && filterResults.candidates.length" class="candidates">
                <div v-for="c in filterResults.candidates" :key="c.id"
                     class="candidate-card"
                     :class="{ selected: selectedComponent.selected_product_id === c.id }">
                  <div>
                    <strong>{{ c.name || c.code }}</strong>
                    <code>{{ c.code }}</code>
                    <div v-if="c.score != null" class="candidate-meta">
                      ⭐ Score: {{ Number(c.score).toFixed(1) }}
                      <span v-if="c.spring_margin != null">| 📊 Запас: {{ Number(c.spring_margin).toFixed(0) }} Нм</span>
                    </div>
                  </div>
                  <button class="btn-select" @click="selectProduct(c.id)"
                          :disabled="selecting === c.id">
                    {{ selectedComponent.selected_product_id === c.id ? '✓ Выбран' : 'Выбрать' }}
                  </button>
                </div>
              </div>
              <p v-else class="hint">Нет подходящих вариантов</p>
            </div>
          </div>
        </section>

        <!-- Ничего не выбрано -->
        <section class="section hint" v-else>
          Выберите компонент в дереве слева.
        </section>
      </main>
    </div>
  </div>
</template>

<script>
import api from '@/shared/api'
import ClimateFilter from '@/shared/components/ClimateFilter.vue'
import ExdFilter from '@/shared/components/ExdFilter.vue'

export default {
  name: 'ConfiguratorPaKitPage',
  components: { ClimateFilter, ExdFilter },
  data() {
    return {
      compositionGroups: [],
      assembly: null,
      selectedComponentId: null,
      globalReqs: { temp_min: null, temp_max: null, exd: null, pressure: 6 },
      ownReqs: {},
      filterSchema: null,
      filterResults: null,
      loadingSchema: false,
      creating: false,
      filtering: false,
      selecting: null,
      error: '',
    }
  },
  computed: {
    flatTree() {
      if (!this.assembly || !this.assembly.components) return []
      return this._flatten(this.assembly.components, 1)
    },
    selectedComponent() {
      if (!this.flatTree.length || !this.selectedComponentId) return null
      return this.flatTree.find(n => n.id === this.selectedComponentId) || null
    },
    visibleFields() {
      if (!this.filterSchema || !this.filterSchema.fields) return []
      // Показываем все поля — пользователь может переопределить наследуемые значения
      return this.filterSchema.fields
    },
  },
  async mounted() {
    await this._loadCompositionGroups()
  },
  methods: {
    async _loadCompositionGroups() {
      try {
        const { data } = await api.get('/ai-assistant/composition-groups/?group_type=required')
        this.compositionGroups = Array.isArray(data) ? data : (data.results || [])
      } catch (e) { console.warn('Failed to load CGs', e) }
    },

    nodeLabel(node) {
      if (node.equipment_type_name) return node.equipment_type_name
      if (node.label) return node.label
      return 'Группа'
    },

    isNodeDisabled(node) {
      // Skipped можно выбрать (чекбокс активен)
      if (node.status === 'skipped') return false
      // Если есть родитель с equipment_type и он не selected — disabled
      // Виртуальные родители (без ET) тоже блокируют, т.к. никогда не станут selected
      if (node.parent && this.flatTree.length) {
        const parent = this.flatTree.find(n => n.id === node.parent)
        if (parent && parent.status !== 'selected') {
          return true
        }
      }
      return false
    },

    needsParentFirst(node) {
      if (!node.equipment_type_code) return false
      if (node.parent && this.flatTree.length) {
        const parent = this.flatTree.find(n => n.id === node.parent)
        return parent && parent.equipment_type_code && parent.status !== 'selected'
      }
      return false
    },

    _flatten(nodes, level) {
      let result = []
      for (const n of nodes) {
        result.push({ ...n, level })
        if (n.children && n.children.length) {
          result = result.concat(this._flatten(n.children, level + 1))
        }
      }
      return result
    },

    // ── Сборка ──
    async createAssembly(cgId) {
      this.creating = true; this.error = ''
      try {
        const { data } = await api.post('/configurator/assemblies/', {
          composition_group_id: cgId,
          name: 'Сборка',
          global_requirements: this.globalReqs,
        })
        this.assembly = data
      } catch (e) {
        this.error = e.response?.data?.error || e.displayMessage || 'Ошибка'
      } finally { this.creating = false }
    },

    async refreshAssembly() {
      if (!this.assembly) return
      try {
        const { data } = await api.get(`/configurator/assemblies/${this.assembly.id}/`)
        this.assembly = data
      } catch (e) { console.warn('Refresh failed', e) }
    },

    // ── Глобальные требования ──
    onClimateChange(temps) {
      if (temps) {
        this.globalReqs.temp_min = temps.min_temp ?? null
        this.globalReqs.temp_max = temps.max_temp ?? null
        this.globalReqs.climate_designation = temps.designation || null
      } else {
        this.globalReqs.temp_min = null
        this.globalReqs.temp_max = null
      }
      this.saveGlobalReqs()
    },
    onExdChange(exdIds) {
      this.globalReqs.exd = exdIds && exdIds.length ? exdIds : null
      this.saveGlobalReqs()
    },
    async saveGlobalReqs() {
      if (!this.assembly) return
      try {
        await api.patch(`/configurator/assemblies/${this.assembly.id}/`, {
          global_requirements: this.globalReqs,
        })
      } catch (e) { console.warn('Save global', e) }
    },

    // ── Компонент ──
    selectComponent(node) {
      this.selectedComponentId = node.id
      this.ownReqs = { ...(node.own_requirements || {}) }
      this.filterResults = node.filter_results || null
      this.filterSchema = null
      if (node.equipment_type && node.status !== 'skipped' && !this.needsParentFirst(node)) {
        this._loadFilterSchema(node.equipment_type)
      }
    },

    async toggleComponent(node, event) {
      const newStatus = event.target.checked ? 'pending' : 'skipped'
      try {
        await api.patch(`/configurator/components/${node.id}/requirements/`, { status: newStatus })
        node.status = newStatus
        if (newStatus === 'skipped') {
          this.filterResults = null
          this.filterSchema = null
        }
      } catch (e) { console.warn('Toggle failed', e) }
    },

    async _loadFilterSchema(etId) {
      this.loadingSchema = true
      try {
        const { data } = await api.get(`/configurator/equipment-types/${etId}/filter-schema/`)
        this.filterSchema = data
      } catch (e) { console.warn('Schema', e) }
      finally { this.loadingSchema = false }
    },

    async saveOwnReqs() {
      if (!this.selectedComponentId) return
      const clean = {}
      for (const [k, v] of Object.entries(this.ownReqs)) {
        if (v !== null && v !== '' && v !== undefined) clean[k] = v
      }
      try {
        const { data } = await api.patch(
          `/configurator/components/${this.selectedComponentId}/requirements/`,
          { own_requirements: clean }
        )
        this._updateNode(this.assembly.components, data)
      } catch (e) { console.warn('Save reqs', e) }
    },

    async runFilter() {
      if (!this.selectedComponentId) return
      this.filtering = true; this.error = ''
      try {
        const { data } = await api.post(`/configurator/components/${this.selectedComponentId}/filter/`)
        this.filterResults = data
      } catch (e) {
        this.error = e.response?.data?.error || e.displayMessage || 'Ошибка'
      } finally { this.filtering = false }
    },

    async selectProduct(productId) {
      if (!this.selectedComponentId) return
      this.selecting = productId; this.error = ''
      try {
        const { data } = await api.post(`/configurator/components/${this.selectedComponentId}/select/`, {
          product_id: productId,
        })
        this._updateNode(this.assembly.components, {
          id: this.selectedComponentId,
          selected_product_id: productId,
          selected_product_specs: data.selected_product,
          status: 'selected',
        })
        await this.refreshAssembly()
      } catch (e) {
        this.error = e.response?.data?.error || e.displayMessage || 'Ошибка'
      } finally { this.selecting = null }
    },

    _updateNode(nodes, update) {
      for (let i = 0; i < nodes.length; i++) {
        if (nodes[i].id === update.id) { Object.assign(nodes[i], update); return true }
        if (nodes[i].children && nodes[i].children.length) {
          if (this._updateNode(nodes[i].children, update)) return true
        }
      }
      return false
    },
  },
}
</script>

<style scoped>
.configurator { max-width: 1200px; margin: 0 auto; padding: 16px; font-family: system-ui, sans-serif; }
h1 { font-size: 1.4rem; margin-bottom: 16px; }
h2 { font-size: 1.1rem; color: #555; margin: 12px 0 8px; display: flex; align-items: center; gap: 8px; }
h3 { margin: 0 0 8px; font-size: 1rem; }

.start-screen { text-align: center; padding: 40px; }
.cg-list { display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; margin: 16px 0; }
.cg-card {
  padding: 16px 24px; border: 1px solid #d0d0d0; border-radius: 8px;
  background: #fff; cursor: pointer; text-align: left; min-width: 180px;
}
.cg-card:hover { border-color: #2563eb; background: #f0f4ff; }
.cg-card strong { display: block; }
.cg-card small { color: #888; }

.layout { display: flex; gap: 16px; min-height: 70vh; }
.tree-panel {
  width: 280px; min-width: 220px; background: #f8f8f8; border: 1px solid #e0e0e0;
  border-radius: 8px; padding: 12px; overflow-y: auto;
}
.detail-panel { flex: 1; min-width: 0; }

.tree { list-style: none; padding: 0; margin: 0; }
.tree li {
  padding: 5px 6px; cursor: pointer; border-radius: 4px; font-size: 0.82rem;
  display: flex; align-items: center; gap: 5px;
}
.tree li:hover { background: #e8e8ff; }
.tree li.active { background: #d0d0ff; font-weight: 600; }
.tree li.virtual { font-style: italic; color: #888; }
.tree li.disabled { opacity: 0.5; pointer-events: none; }
.tree li.skipped { opacity: 0.4; }
.tree li.skipped input[type=checkbox] { pointer-events: auto; }
.tree li input[type=checkbox] { margin: 0; flex-shrink: 0; }

.status-dot {
  width: 7px; height: 7px; border-radius: 50%; background: #ccc; flex-shrink: 0;
}
.status-dot.pending { background: #ccc; }
.status-dot.requirements_filled { background: #f0ad4e; }
.status-dot.filtered { background: #5bc0de; }
.status-dot.selected { background: #5cb85c; }
.status-dot.skipped { background: #e0e0e0; }

.selected-badge { color: #5cb85c; font-weight: bold; margin-left: auto; }
.badge { font-size: 0.7rem; padding: 1px 6px; border-radius: 8px; background: #5cb85c; color: #fff; }
.badge-filtered { background: #5bc0de; }

.section { background: #fafafa; border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px; margin-bottom: 12px; }
.global-grid { display: grid; grid-template-columns: 1fr 1fr auto; gap: 16px; align-items: start; }
.global-col { min-width: 0; }
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.field { display: flex; flex-direction: column; }
.field label { font-size: 0.75rem; color: #666; margin-bottom: 3px; }
.field select, .field input { padding: 6px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 0.85rem; }

.actions { margin: 12px 0; display: flex; gap: 8px; }
.btn-primary { padding: 8px 20px; background: #2563eb; color: #fff; border: none; border-radius: 5px; cursor: pointer; font-size: 0.9rem; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-small { padding: 5px 12px; font-size: 0.8rem; }
.btn-select { padding: 4px 12px; background: #eee; border: 1px solid #ccc; border-radius: 4px; cursor: pointer; font-size: 0.8rem; }
.btn-select:hover { background: #d0ffd0; }

.candidates { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
.candidate-card {
  border: 1px solid #e0e0e0; border-radius: 6px; padding: 10px;
  display: flex; justify-content: space-between; align-items: center; background: #fff;
}
.candidate-card.selected { border-color: #5cb85c; background: #f0fff0; }
.candidate-meta { font-size: 0.78rem; color: #666; margin-top: 4px; }

.hint { color: #888; font-size: 0.85rem; padding: 12px 0; }
.relaxed-note { background: #fff3cd; padding: 8px 12px; border-radius: 4px; font-size: 0.85rem; margin: 8px 0; }
.error-msg { background: #fee; color: #c00; padding: 10px 16px; border-radius: 6px; margin: 12px 0; }
</style>
