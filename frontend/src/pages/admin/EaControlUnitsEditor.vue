<template>
  <div class="units-editor">
    <!-- ЛЕВАЯ ПАНЕЛЬ: фильтры -->
    <div class="left-pane">
      <div class="pane-head"><h3>Фильтры</h3></div>
      <label class="filter"><span>Бренд</span>
        <select v-model="filters.brand">
          <option :value="null">Все</option>
          <option v-for="b in brands" :key="b.id" :value="b.id">{{ b.name }}</option>
        </select>
      </label>
      <label class="filter"><span>Класс БУ</span>
        <select v-model="filters.kind">
          <option :value="null">Все</option>
          <option v-for="k in kinds" :key="k.id" :value="k.id">{{ k.name }}</option>
        </select>
      </label>
      <div class="count">{{ filtered.length }} из {{ units.length }}</div>
      <div v-if="error" class="error">{{ error }}</div>

      <div class="pane-head nodes-head"><h3>Узлы</h3></div>
      <div class="node-list">
        <div v-for="n in nodeTree" :key="n.id" class="node-item"
             :class="{ active: selectedNodeId === n.id }"
             :style="{ paddingLeft: (n.depth * 12) + 'px' }"
             @click="selectedNodeId = n.id">
          <span class="label">{{ n.name || n.code }}</span>
          <span class="code">{{ n.code }}</span>
        </div>
        <div v-if="!nodeTree.length" class="hint">Узлов нет.</div>
      </div>
    </div>

    <!-- ПРАВАЯ ПАНЕЛЬ: сверху список, снизу редактор -->
    <div class="right-pane">
      <div class="top-area">
        <div class="toolbar">
          <EditorActions align="start" :buttons="toolbarButtons" @action="onToolbar" />
        </div>
        <div class="list-scroll">
          <div v-for="u in filtered" :key="u.id" class="unit-row"
               :class="{ active: form && form.id === u.id }" @click="openEdit(u)">
            <span class="label">{{ u.name }} <i class="code">{{ u.code }}</i></span>
            <span class="meta">{{ kindLabel(u.kind) }} · {{ brandName(u.brand) }}</span>
            <span class="row-actions">
              <button title="Копировать (с матрицей и правилами)" @click.stop="copyUnit(u)">⧉</button>
              <button title="Удалить" @click.stop="removeUnit(u)">✕</button>
            </span>
          </div>
          <p v-if="!filtered.length" class="empty">Блоков нет.</p>
        </div>
      </div>

      <!-- РЕДАКТОР -->
      <div v-if="form" class="edit-area">
        <div class="edit-head">
          <h3>{{ form.id ? 'Изменить' : 'Создать' }} — блок управления</h3>
          <button v-if="form && form.id" class="export-btn" @click="exportSettings">Экспорт настроек в Excel</button>
        </div>

        <div class="sub-tabs">
          <button :class="{ active: tab === 'basic' }" @click="tab = 'basic'">Основное</button>
          <button :class="{ active: tab === 'options' }" @click="openOptionsTab()">Редактор доступных опций</button>
          <button :class="{ active: tab === 'bindings' }" @click="openBindingsTab()">Привязки</button>
        </div>

        <!-- ОСНОВНОЕ -->
        <div v-if="tab === 'basic'">
          <div class="edit-form" @input="dirty = true" @change="dirty = true">
            <div class="form-row">
              <label class="field"><span>Код</span><input v-model="form.code" /></label>
              <label class="field"><span>Название</span><input v-model="form.name" /></label>
            </div>
            <div class="form-row">
              <label class="field"><span>Бренд</span>
                <select v-model="form.brand">
                  <option :value="null">— —</option>
                  <option v-for="b in brands" :key="b.id" :value="b.id">{{ b.name }}</option>
                </select>
              </label>
              <label class="field"><span>Класс БУ</span>
                <select v-model="form.kind">
                  <option v-for="k in kinds" :key="k.id" :value="k.id">{{ k.name }}</option>
                </select>
              </label>
            </div>
            <div class="form-row">
              <label class="field"><span>Сортировка</span>
                <input type="number" v-model.number="form.sorting_order" /></label>
              <label class="field chk"><span>Активно</span>
                <input type="checkbox" v-model="form.is_active" /></label>
            </div>
          </div>

          <div class="templates" @input="dirty = true" @change="dirty = true">
            <label class="field wide"><span>Описание</span>
              <textarea v-model="form.description" rows="2"></textarea></label>
            <label class="field wide"><span>Шаблон названия</span>
              <textarea v-model="form.name_template" rows="2"></textarea></label>
            <label class="field wide"><span>Шаблон описания</span>
              <textarea v-model="form.description_template" rows="3"></textarea></label>
            <label class="field wide"><span>Шаблон спецификации (JSON)</span>
              <textarea v-model="form.spec_template" rows="4"
                        placeholder="{'Раздел': {'Поле': 'ключ'}}"></textarea></label>
          </div>
        </div>

        <!-- РЕДАКТОР ДОСТУПНЫХ ОПЦИЙ -->
        <div v-else-if="tab === 'options'" class="options-editor">
          <div class="matrix-toolbar">
            <label class="mfield"><span>Напряжение</span>
              <select v-model="matrixPowerSupply" @change="onVoltageChange">
                <option :value="null">— любое напряжение —</option>
                <option v-for="p in powerSupplies" :key="p.id" :value="p.id">{{ p.label }}</option>
              </select>
            </label>
            <span class="hint">std — стандарт · opt — опция · na — недоступно · насл. — наследовать от «любое напряжение»</span>
          </div>
          <div class="rules-legend hint">
            <span>Правило слота:</span>
            <b>Показать</b> — слот отображается в конфигураторе ·
            <b>Скрыть</b> — слот не отображается (убирается из раздела) ·
            <b>Заблокировать</b> — слот виден, но опции выбрать нельзя ·
            <b>Обязать</b> — метка «обязателен» ·
            <b>Дефолт</b> — опция подставляется по умолчанию (при выполнении условия)
          </div>
          <div class="rules-legend hint">
            <span>Оператор:</span>
            <b>только этот БУ</b> — точное условие ·
            <b>несколько БУ</b> — список БУ ·
            <b>все, кроме</b> — список исключений (пусто = все БУ)
          </div>
          <div v-if="!form.id" class="hint">Сначала сохраните блок управления, затем настраивайте опции.</div>
          <template v-else>
            <div v-if="!selectedNode" class="hint">Выберите узел слева.</div>
            <div v-else class="tree-editor">
              <div class="node-block">
                <div class="node-head" :class="{ off: selectedNodeAllNa }">
                  <strong>{{ selectedNode.name }}</strong>
                  <span class="code">{{ selectedNode.code }}</span>
                  <span v-if="selectedNodeAllNa" class="off-mark">Раздел выключен</span>
                </div>
                <div v-for="s in selectedNodeSlots" :key="s.code" class="mslot">
                  <div class="mslot-head">
                    <strong>{{ s.name }}</strong>
                    <span class="code">{{ s.code }}</span>
                    <span v-if="s.required" class="req">обязателен</span>
                  </div>
                  <div v-for="o in s.options" :key="o.id" class="mopt"
                       :class="optionRowClass(o)"
                       :title="o.has_voltage_diff ? 'Есть отличия по напряжениям' : null">
                    <span class="oname">{{ o.name }}</span>
                    <span v-if="o.inherited" class="inh-val">{{ o.availability }}</span>
                    <div class="seg">
                      <button :class="{ on: o.availability === 'std' && !o.inherited }" @click="setAvail(o, 'std')">std</button>
                      <button :class="{ on: o.availability === 'opt' && !o.inherited }" @click="setAvail(o, 'opt')">opt</button>
                      <button :class="{ on: o.availability === 'na' && !o.inherited }" @click="setAvail(o, 'na')">na</button>
                      <button v-if="matrixPowerSupply !== null"
                              :class="{ on: o.inherited }"
                              :title="o.inherited ? 'наследуется от «любое напряжение»' : 'наследовать от «любое напряжение»'"
                              @click="setInherit(o)">насл.</button>
                    </div>
                  </div>
                  <div class="mrule">
                    <span>Правило</span>
                    <select v-model="s.rule.action" @change="onRuleActionChange(s)">
                      <option :value="null">— нет —</option>
                      <option value="show">Показать</option>
                      <option value="hide">Скрыть</option>
                      <option value="block">Заблокировать</option>
                      <option value="require">Обязать</option>
                      <option value="set_default">Дефолт</option>
                    </select>
                    <select v-if="s.rule.action" v-model="s.rule.operator" @change="onRuleOperatorChange(s)">
                      <option value="exact">только этот БУ</option>
                      <option value="in">несколько БУ</option>
                      <option value="not_in">все, кроме</option>
                    </select>
                    <template v-if="s.rule.action && (s.rule.operator === 'in' || s.rule.operator === 'not_in')">
                      <label v-for="cu in (matrix?.control_unit_options || [])" :key="cu.code" class="cu-chk"
                             :title="cu.code === (matrix?.unit?.option_code) ? 'текущий БУ (фиксирован)' : ''">
                        <input type="checkbox"
                               :checked="ruleCodeChecked(s.rule, cu.code)"
                               :disabled="cu.code === (matrix?.unit?.option_code)"
                               @change="toggleRuleCode(s.rule, cu.code)" />
                        {{ cu.name }}
                      </label>
                    </template>
                    <select v-if="s.rule.action === 'set_default'" v-model="s.rule.action_value" @change="matrixDirty = true">
                      <option :value="null">— —</option>
                      <option v-for="o in s.options" :key="o.code" :value="o.code">{{ o.name }}</option>
                    </select>
                    <span class="rule-desc">{{ ruleDesc(s.rule.action) }}</span>
                  </div>
                </div>
                <p v-if="!selectedNodeSlots.length" class="empty">В узле нет слотов.</p>
              </div>
            </div>
          </template>
        </div>

        <!-- ПРИВЯЗКИ -->
        <div v-else class="bindings-editor">
          <div v-if="!form.id" class="hint">Сначала сохраните блок управления, затем настраивайте привязки.</div>
          <template v-else>
            <div class="bind-add">
              <label class="mfield"><span>Серия</span>
                <select v-model="addSeriesId">
                  <option :value="null">— выберите серию —</option>
                  <option v-for="s in bindingSeries" :key="s.id" :value="s.id">
                    {{ s.name }}<template v-if="s.code"> ({{ s.code }})</template>
                  </option>
                </select>
              </label>
              <button class="btn-ghost" :disabled="!addSeries" @click="addWholeSeries">Вся серия</button>
            </div>
            <div v-if="addSeries" class="bind-models">
              <div class="bind-models-head">
                <span class="hint">Модели серии — отметьте и добавьте выборочно:</span>
                <button class="btn-ghost" @click="toggleAllModels">Выбрать все</button>
                <button class="btn-ghost" :disabled="!selectedModels.size" @click="addSelectedModels">Добавить выбранные</button>
              </div>
              <div class="bind-model-list">
                <label v-for="it in addSeries.items" :key="it.id" class="bind-model-chk">
                  <input type="checkbox" :checked="selectedModels.has(it.id)" @change="toggleModel(it.id)" />
                  <span>{{ it.name }} <i class="code">{{ it.code }}</i></span>
                </label>
                <p v-if="!addSeries.items.length" class="hint">В серии нет моделей.</p>
              </div>
            </div>

            <div class="bind-groups">
              <div v-for="g in bindingGroups" :key="g.model_line" class="bind-group">
                <div class="bind-group-head">
                  <strong>{{ g.model_line_name }}</strong>
                  <span class="code">{{ g.model_line_code }}</span>
                  <span v-if="g.whole" class="whole">Вся серия ({{ g.bindings.length }})</span>
                  <button class="btn-ghost" @click="removeSeries(g)">Убрать серию</button>
                </div>
                <div class="bind-items">
                  <div v-for="b in g.bindings" :key="b.id || b.model_line_item" class="bind-item">
                    <span>{{ b.item_name }} <i class="code">{{ b.item_code }}</i></span>
                    <button title="Убрать модель" @click="removeBinding(b)">✕</button>
                  </div>
                </div>
              </div>
              <p v-if="!bindingGroups.length" class="empty">Привязок нет.</p>
            </div>
          </template>
        </div>

        <div class="edit-actions">
          <EditorActions :buttons="editButtons" @action="onEdit" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * «Блоки управления» — редактор типов БУ в макете «слева фильтры, справа
 * список/редактор». Копирование БУ копирует профильные строки матрицы и
 * правила выбора БУ (бэкенд, control-units/<id>/copy/); удаление снимает
 * опцию слота control_unit и чистит правила (delete-unit/). Вкладка
 * «Редактор доступных опций» — слоты выбранного узла (слева «Узлы»)
 * с пометкой std/opt/na (GET/PUT /api/ea-control/unit-matrix/). Узел, у
 * которого во всех слотах все опции «na», помечается «Раздел выключен».
 */
import { computed, onMounted, reactive, ref } from 'vue'
import api from '@/shared/api'
import { t } from '@/shared/i18n'
import EditorActions from '@/components/EditorActions.vue'

// Классы БУ приходят с API (справочник control-unit-kinds вместо хардкода).
const kinds = ref([])

const units = ref([])
const brands = ref([])
const powerSupplies = ref([])
const nodes = ref([])
const error = ref('')
// матрица профиля выбранного БУ (вкладка «Редактор доступных опций»)
const matrix = ref(null)
const matrixPowerSupply = ref(null)
const lastVoltage = ref(null)
const matrixOriginals = new Map() // option id -> availability
const matrixInheritedOriginals = new Map() // option id -> inherited(bool)
const ruleOriginals = new Map() // slot id -> {action, action_value}
const matrixDirty = ref(false)

const filters = reactive({ brand: null, kind: null })
const form = ref(null)
const dirty = ref(false)
const tab = ref('basic')
const selectedNodeId = ref(null)
// привязки БУ к моделям ЭП (вкладка «Привязки»)
const bindingData = ref(null)   // {bindings, series}
const addSeriesId = ref(null)
const selectedModels = ref(new Set())
const bindingsDirty = ref(false)

const filtered = computed(() => units.value.filter(u =>
  (!filters.brand || u.brand === filters.brand)
  && (!filters.kind || u.kind === filters.kind)))

// Дерево узлов (секций) для левой панели «Узлы» — тот же вид, что на
// закладке «Конфигуратор опций» (вложенность через parent).
const nodeTree = computed(() => {
  const byParent = {}
  for (const n of nodes.value) {
    const key = n.parent || 0
    if (!byParent[key]) byParent[key] = []
    byParent[key].push(n)
  }
  const out = []
  const seen = new Set()
  const walk = (pid, depth) => {
    const kids = (byParent[pid] || []).slice()
      .sort((a, b) => (a.sorting_order || 0) - (b.sorting_order || 0))
    for (const n of kids) {
      if (seen.has(n.id)) continue
      seen.add(n.id)
      out.push({ ...n, depth })
      walk(n.id, depth + 1)
    }
  }
  walk(0, 0)
  // узлы с битой цепочкой parent (недостижимые из корня) — в корень
  for (const n of nodes.value) {
    if (!seen.has(n.id)) {
      out.push({ ...n, depth: 0 })
      seen.add(n.id)
    }
  }
  return out
})

const selectedNode = computed(() => {
  if (selectedNodeId.value == null) return null
  return nodes.value.find(n => n.id === selectedNodeId.value) || null
})

// Слоты выбранного узла из загруженной матрицы профиля (по section_id).
const selectedNodeSlots = computed(() => {
  if (!matrix.value || selectedNodeId.value == null) return []
  return (matrix.value.slots || []).filter(s => s.section_id === selectedNodeId.value)
})

const selectedNodeAllNa = computed(() => {
  const slots = selectedNodeSlots.value
  return slots.length > 0 && slots.every(s =>
    (s.options || []).length > 0 && (s.options || []).every(o => o.availability === 'na'))
})

// ── Привязки ────────────────────────────────────────────────────────────
const bindingSeries = computed(() => bindingData.value?.series || [])

const addSeries = computed(() => {
  if (addSeriesId.value == null) return null
  return bindingSeries.value.find(s => s.id === addSeriesId.value) || null
})

// Группировка привязок по сериям; whole = привязаны все текущие модели серии.
const bindingGroups = computed(() => {
  const data = bindingData.value
  if (!data) return []
  const byLine = new Map()
  for (const b of data.bindings || []) {
    const key = b.model_line
    if (!byLine.has(key)) {
      const s = bindingSeries.value.find(x => x.id === key)
      byLine.set(key, {
        model_line: key,
        model_line_code: b.model_line_code || '',
        model_line_name: b.model_line_name || '',
        series: s || null,
        bindings: [],
      })
    }
    byLine.get(key).bindings.push(b)
  }
  const out = []
  for (const g of byLine.values()) {
    g.bindings.sort((a, b) => (a.sorting_order || 0) - (b.sorting_order || 0))
    const allIds = new Set((g.series?.items || []).map(i => i.id))
    const boundIds = new Set(g.bindings.map(b => b.model_line_item))
    g.whole = allIds.size > 0 && boundIds.size === allIds.size
    out.push(g)
  }
  out.sort((a, b) => (a.model_line_name || '').localeCompare(b.model_line_name || ''))
  return out
})

const toolbarButtons = computed(() => [
  { key: 'create', label: t('eaControl.add'), kind: 'primary' },
  { key: 'refresh', label: t('eaControl.refresh') },
])

const editButtons = computed(() => [
  { key: 'save', label: t('eaControl.save'), kind: 'primary', disabled: !(dirty.value || matrixDirty.value || bindingsDirty.value) },
  { key: 'cancel', label: t('eaControl.cancel') },
])

function kindLabel(k) {
  const o = kinds.value.find(x => x.id === k)
  return o ? o.name : (k ?? '')
}

function brandName(id) {
  const b = brands.value.find(x => x.id === id)
  return b ? b.name : ''
}

// Фон строки опции: наследуемое (конкретное напряжение) — светло-зелёный,
// отличие по напряжениям (вид «любое напряжение») — светло-оранжевый,
// иначе — по доступности std/opt/na.
function optionRowClass(o) {
  if (o.inherited) return 'mopt-inh'
  if (o.has_voltage_diff) return 'mopt-diff'
  return 'av-' + o.availability
}

function ruleDesc(action) {
  switch (action) {
    case 'show': return 'слот отображается'
    case 'hide': return 'слот не отображается'
    case 'block': return 'слот виден, опции выбрать нельзя'
    case 'require': return 'метка «обязателен»'
    case 'set_default': return 'опция по умолчанию'
    default: return 'без правила'
  }
}

function onRuleActionChange(s) {
  const r = s.rule
  if (r.action && !r.operator) {
    r.operator = 'exact'
    r.when_value = null
  }
  matrixDirty.value = true
}

function onRuleOperatorChange(s) {
  const r = s.rule
  if (r.operator === 'exact') {
    r.when_value = null
  } else if (!Array.isArray(r.when_value)) {
    r.when_value = []
  }
  matrixDirty.value = true
}

function ruleHasCode(rule, code) {
  return Array.isArray(rule.when_value) && rule.when_value.includes(code)
}

function ruleCodeChecked(rule, code) {
  const self = matrix.value?.unit?.option_code
  if (code === self) return rule.operator === 'in'
  return Array.isArray(rule.when_value) && rule.when_value.includes(code)
}

function toggleRuleCode(rule, code) {
  if (code === matrix.value?.unit?.option_code) return
  const list = Array.isArray(rule.when_value) ? [...rule.when_value] : []
  const i = list.indexOf(code)
  if (i >= 0) list.splice(i, 1)
  else list.push(code)
  rule.when_value = list
  matrixDirty.value = true
}

async function loadUnits() {
  error.value = ''
  try {
    const { data } = await api.get('/ea-control/control-units/')
    units.value = Array.isArray(data) ? data : data.results || []
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка загрузки БУ'
  }
}

async function loadMeta() {
  const [meta, sections] = await Promise.all([
    api.get('/ea-control/meta/'),
    api.get('/ea-control/sections/'),
  ])
  brands.value = meta.data.brands || []
  powerSupplies.value = (meta.data.power_supplies || []).map(o => ({
    id: o.id, label: o.code ? `${o.name} (${o.code})` : o.name }))
  nodes.value = sections.data.results || sections.data || []
}

function openEdit(u) {
  if (dirty.value || matrixDirty.value || bindingsDirty.value) {
    if (!confirm('Есть несохранённые изменения. Отменить их?')) return
  }
  form.value = {
    id: u.id, code: u.code, name: u.name, brand: u.brand, kind: u.kind,
    sorting_order: u.sorting_order || 0,
    is_active: u.is_active, description: u.description || '',
    name_template: u.name_template || '',
    description_template: u.description_template || '',
    spec_template: typeof u.spec_template === 'string'
      ? u.spec_template : JSON.stringify(u.spec_template || {}, null, 2),
  }
  dirty.value = false
  matrix.value = null
  matrixDirty.value = false
  bindingData.value = null
  bindingsDirty.value = false
  addSeriesId.value = null
  selectedModels.value = new Set()
  tab.value = 'basic'
}

function openCreate() {
  if (dirty.value || matrixDirty.value || bindingsDirty.value) {
    if (!confirm('Есть несохранённые изменения. Отменить их?')) return
  }
  form.value = {
    id: null, code: '', name: '', brand: null, kind: defaultKindId(),
    sorting_order: 0, is_active: true, description: '',
    name_template: '', description_template: '', spec_template: '',
  }
  dirty.value = false
  matrix.value = null
  matrixDirty.value = false
  bindingData.value = null
  bindingsDirty.value = false
  addSeriesId.value = null
  selectedModels.value = new Set()
  tab.value = 'basic'
}

function onToolbar(b) {
  if (b.key === 'create') openCreate()
  else if (b.key === 'refresh') loadUnits()
}

async function copyUnit(u) {
  error.value = ''
  const copyBindings = confirm('Копировать привязки к сериям/моделям вместе с БУ?')
  try {
    await api.post(`/ea-control/control-units/${u.id}/copy/`, { copy_bindings: copyBindings })
    await loadUnits()
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка копирования'
  }
}

async function removeUnit(u) {
  if (!confirm(`Удалить БУ «${u.name}»? Связанные правила и опция выбора будут удалены, строки матрицы — каскадом.`)) return
  error.value = ''
  try {
    await api.delete(`/ea-control/control-units/${u.id}/delete-unit/`)
    if (form.value && form.value.id === u.id) form.value = null
    await loadUnits()
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка удаления'
  }
}

async function loadMatrix() {
  if (!form.value || !form.value.id) { matrix.value = null; return }
  error.value = ''
  try {
    const { data } = await api.get('/ea-control/unit-matrix/', {
      params: { unit: form.value.id, power_supply: matrixPowerSupply.value || undefined },
    })
    matrix.value = data
    lastVoltage.value = matrixPowerSupply.value
    matrixOriginals.clear()
    matrixInheritedOriginals.clear()
    ruleOriginals.clear()
    for (const s of data.slots || []) {
      for (const o of s.options || []) {
        matrixOriginals.set(o.id, o.availability)
        matrixInheritedOriginals.set(o.id, !!o.inherited)
      }
      ruleOriginals.set(s.id, {
        action: s.rule?.action || null,
        action_value: s.rule?.action_value || null,
        operator: s.rule?.operator || null,
        when_value: s.rule?.when_value || null,
      })
    }
    matrixDirty.value = false
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка загрузки матрицы'
  }
}

function setAvail(o, avail) {
  if (!o.inherited && o.availability === avail) return
  o.availability = avail
  o.inherited = false
  matrixDirty.value = true
}

function setInherit(o) {
  if (o.inherited) return
  o.inherited = true
  matrixDirty.value = true
}

async function saveMatrix() {
  if (!form.value || !form.value.id) return
  const changes = []
  const ruleChanges = []
  for (const s of (matrix.value?.slots || [])) {
    for (const o of s.options || []) {
      const orig = matrixOriginals.get(o.id)
      const origInh = matrixInheritedOriginals.get(o.id)
      if (o.inherited) {
        if (origInh === false) {
          changes.push({ slot_id: s.id, option_id: o.id, availability: 'inherit' })
        }
      } else if (origInh || orig !== o.availability) {
        changes.push({ slot_id: s.id, option_id: o.id, availability: o.availability })
      }
    }
    const rOrig = ruleOriginals.get(s.id)
    const curAction = s.rule?.action || null
    const curValue = s.rule?.action_value || null
    const curOp = s.rule?.operator || null
    const curWv = s.rule?.when_value || null
    if (rOrig && (rOrig.action !== curAction || rOrig.action_value !== curValue
        || rOrig.operator !== curOp
        || JSON.stringify(rOrig.when_value) !== JSON.stringify(curWv))) {
      ruleChanges.push({ slot_id: s.id, action: curAction, action_value: curValue,
                         operator: curOp, when_value: curWv })
    }
  }
  if (!changes.length && !ruleChanges.length) return
  await api.put('/ea-control/unit-matrix/save/', {
    unit: form.value.id,
    power_supply: matrixPowerSupply.value || null,
    changes,
    rule_changes: ruleChanges,
  })
}

async function openOptionsTab() {
  tab.value = 'options'
  await loadMatrix()
  // Узел не сбрасывается при смене напряжения; выбираем первый, только
  // если выбора нет или выбранный узел больше не существует.
  if (selectedNodeId.value == null || !nodeTree.value.some(n => n.id === selectedNodeId.value)) {
    selectedNodeId.value = nodeTree.value.length ? nodeTree.value[0].id : null
  }
}

// ── Привязки ────────────────────────────────────────────────────────────
async function openBindingsTab() {
  tab.value = 'bindings'
  if (bindingData.value === null) await loadBindings()
}

async function loadBindings() {
  if (!form.value || !form.value.id) { bindingData.value = null; return }
  error.value = ''
  try {
    const { data } = await api.get('/ea-control/unit-bindings/', {
      params: { unit: form.value.id },
    })
    bindingData.value = data
    addSeriesId.value = null
    selectedModels.value = new Set()
    bindingsDirty.value = false
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка загрузки привязок'
  }
}

function makeBindingEntry(line, item, idx) {
  return {
    id: null,
    model_line: line.id,
    model_line_code: line.code || '',
    model_line_name: line.name || '',
    model_line_item: item.id,
    item_code: item.code || '',
    item_name: item.name || '',
    is_active: true,
    sorting_order: idx,
  }
}

function addWholeSeries() {
  const s = addSeries.value
  if (!s || !bindingData.value) return
  const kept = (bindingData.value.bindings || []).filter(b => b.model_line !== s.id)
  const added = s.items.map((it, idx) => makeBindingEntry(s, it, kept.length + idx))
  bindingData.value.bindings = kept.concat(added)
  selectedModels.value = new Set()
  bindingsDirty.value = true
}

function addSelectedModels() {
  const s = addSeries.value
  if (!s || !bindingData.value || !selectedModels.value.size) return
  const list = bindingData.value.bindings || []
  const existing = new Set(list.filter(b => b.model_line === s.id).map(b => b.model_line_item))
  const add = []
  for (const it of s.items) {
    if (selectedModels.value.has(it.id) && !existing.has(it.id)) {
      add.push(makeBindingEntry(s, it, list.length + add.length))
    }
  }
  if (add.length) {
    bindingData.value.bindings = list.concat(add)
    bindingsDirty.value = true
  }
  selectedModels.value = new Set()
}

function removeBinding(b) {
  if (!bindingData.value) return
  bindingData.value.bindings = (bindingData.value.bindings || []).filter(x => x !== b)
  bindingsDirty.value = true
}

function removeSeries(g) {
  if (!bindingData.value) return
  bindingData.value.bindings = (bindingData.value.bindings || []).filter(x => x.model_line !== g.model_line)
  bindingsDirty.value = true
}

function toggleModel(id) {
  const s = selectedModels.value
  if (s.has(id)) s.delete(id)
  else s.add(id)
}

function toggleAllModels() {
  const s = addSeries.value
  if (!s) return
  const all = s.items.map(i => i.id)
  const cur = selectedModels.value
  if (all.length && all.every(id => cur.has(id))) {
    selectedModels.value = new Set()
  } else {
    selectedModels.value = new Set(all)
  }
}

async function saveBindings() {
  if (!form.value || !form.value.id) return
  const bindings = (bindingData.value?.bindings || []).map((b, idx) => ({
    model_line_item: b.model_line_item,
    sorting_order: b.sorting_order ?? idx,
    is_active: b.is_active ?? true,
  }))
  await api.put('/ea-control/unit-bindings/save/', {
    unit: form.value.id,
    bindings,
  })
}

function onVoltageChange() {
  if (matrixDirty.value
      && !confirm('Есть несохранённые изменения матрицы. Отменить их и переключить напряжение?')) {
    matrixPowerSupply.value = lastVoltage.value
    return
  }
  loadMatrix()
}

function onEdit(b) {
  if (b.key === 'save') save()
  else if (b.key === 'cancel') cancelEdit()
}

async function save() {
  error.value = ''
  if (!form.value.code || !form.value.name) {
    error.value = 'Заполните код и название'
    return
  }
  const f = form.value
  let spec = null
  if (typeof f.spec_template === 'string' && f.spec_template.trim()) {
    try {
      spec = JSON.parse(f.spec_template)
    } catch {
      error.value = 'Шаблон спецификации: невалидный JSON'
      return
    }
  }
  const payload = {
    code: f.code, name: f.name, brand: f.brand, kind: f.kind,
    sorting_order: f.sorting_order || 0,
    is_active: f.is_active, description: f.description || '',
    name_template: f.name_template || '',
    description_template: f.description_template || '',
    spec_template: spec,
  }
  try {
    if (f.id) {
      await api.put(`/ea-control/control-units/${f.id}/`, payload)
    } else {
      const r = await api.post('/ea-control/control-units/', payload)
      f.id = r.data.id
    }
    if (matrixDirty.value) {
      await saveMatrix()
      await loadMatrix()
    }
    if (bindingsDirty.value && f.id) {
      await saveBindings()
      await loadBindings()
    }
    dirty.value = false
    matrixDirty.value = false
    bindingsDirty.value = false
    await loadUnits()
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка сохранения'
  }
}

function cancelEdit() {
  if (dirty.value || matrixDirty.value || bindingsDirty.value) {
    if (!confirm('Есть несохранённые изменения. Отменить их?')) return
  }
  form.value = null
  matrix.value = null
  bindingData.value = null
  dirty.value = false
  matrixDirty.value = false
  bindingsDirty.value = false
  addSeriesId.value = null
  selectedModels.value = new Set()
}

async function exportSettings() {
  if (!form.value || !form.value.id) return
  error.value = ''
  try {
    const r = await api.get('/ea-control/export-settings/', {
      params: { unit: form.value.id },
      responseType: 'blob',
    })
    let filename = `cu_settings_${form.value.code || form.value.id}.xlsx`
    const disposition = r.headers['content-disposition'] || ''
    const m = /filename="?([^";]+)"?/.exec(disposition)
    if (m) filename = m[1]
    const url = URL.createObjectURL(r.data)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка экспорта'
  }
}

async function loadKinds() {
  try {
    const { data } = await api.get('/ea-control/control-unit-kinds/')
    const list = Array.isArray(data) ? data : data.results || []
    kinds.value = list.map(o => ({ id: o.id, code: o.code, name: o.name }))
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка загрузки классов БУ'
  }
}

function defaultKindId() {
  const o = kinds.value.find(x => x.code === 'INTEGRATED')
  return o ? o.id : null
}

onMounted(async () => {
  try {
    await loadMeta()
    await loadKinds()
    await loadUnits()
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка инициализации'
  }
})
</script>

<style scoped>
.units-editor { display: flex; height: calc(100vh - 80px); border: 1px solid #ddd; border-radius: 4px; overflow: hidden; }
.left-pane { width: 260px; flex-shrink: 0; border-right: 1px solid #ddd; overflow: auto; padding: 12px; }
.right-pane { flex: 1; overflow: auto; padding: 12px; }
.pane-head h3 { margin: 0 0 10px; font-size: 18px; }
.filter { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.filter span { flex: 0 0 70px; text-align: right; color: #444; font-size: 13px; }
.filter select { flex: 1; min-width: 0; padding: 4px 6px; border: 1px solid #ccc; border-radius: 3px; }
.count { color: #666; font-size: 12px; margin-top: 8px; }
.error { color: #c00; margin-top: 8px; font-size: 13px; }
.nodes-head { margin-top: 18px; }
.node-list { display: flex; flex-direction: column; gap: 2px; }
.node-item { display: flex; gap: 6px; padding: 5px 8px; cursor: pointer; border-radius: 3px; font-size: 13px; }
.node-item:hover { background: #f0f0f0; }
.node-item.active { background: #2c6fb0; color: #fff; }
.node-item .label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.node-item .code { color: #888; font-size: 11px; }
.node-item.active .code { color: #dbe7f3; }
.toolbar { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
.list-scroll { overflow-y: auto; max-height: 260px; border: 1px solid #eee; border-radius: 3px; }
.unit-row { display: flex; align-items: center; gap: 8px; padding: 7px 10px; cursor: pointer; border-bottom: 1px solid #f0f0f0; }
.unit-row:hover { background: #f5f8fc; }
.unit-row.active { background: #e8f0fa; }
.unit-row .label { flex: 1; font-size: 13px; }
.unit-row .code { color: #888; font-size: 11px; font-style: normal; }
.unit-row .meta { color: #666; font-size: 12px; }
.row-actions { display: flex; gap: 4px; }
.row-actions button { cursor: pointer; }
.empty { color: #999; padding: 10px; }
.edit-area { border-top: 2px solid #2c6fb0; margin-top: 12px; padding-top: 10px; }
.edit-head { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.edit-head h3 { margin: 0 0 8px; font-size: 15px; }
.export-btn {
  padding: 5px 12px; border: 1px solid #2c6fb0; background: #fff;
  color: #2c6fb0; border-radius: 4px; cursor: pointer; font-size: 13px;
}
.export-btn:hover { background: #eef4fb; }
.sub-tabs { display: flex; gap: 4px; margin: 8px 0 12px; }
.sub-tabs button { padding: 6px 12px; border: 1px solid #ccc; background: #f5f5f5; cursor: pointer; }
.sub-tabs button.active { background: #2c6fb0; color: #fff; border-color: #2c6fb0; }
.edit-form { display: flex; flex-direction: column; gap: 8px; max-width: 900px; }
.form-row { display: flex; gap: 12px; }
.field { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; }
.field > span { flex: 0 0 110px; text-align: right; color: #444; font-size: 13px; }
.field > input, .field > select, .field > textarea {
  flex: 1; min-width: 0; padding: 4px 6px; border: 1px solid #ccc; border-radius: 3px; box-sizing: border-box;
}
.field.chk > input { flex: 0 0 auto; }
.field.wide { align-items: flex-start; }
.field.wide > span { padding-top: 4px; }
.templates { display: flex; flex-direction: column; gap: 8px; max-width: 900px; margin-top: 12px; }
.options-editor { max-width: 960px; }
.matrix-toolbar { display: flex; gap: 14px; align-items: center; margin-bottom: 8px; flex-wrap: wrap; }
.mfield { display: flex; align-items: center; gap: 8px; }
.mfield span { color: #444; font-size: 13px; }
.mfield select { padding: 4px 6px; border: 1px solid #ccc; border-radius: 3px; }
.hint { color: #888; font-size: 12px; }
.rules-legend { display: flex; gap: 6px; align-items: baseline; margin: 6px 0; flex-wrap: wrap; }
.rules-legend b { color: #2c6fb0; font-weight: 600; }
.tree-editor { border: 1px solid #e0e0e0; border-radius: 4px; padding: 8px; }
.node-block { margin-bottom: 12px; }
.node-head { display: flex; gap: 8px; align-items: baseline; margin-bottom: 4px; }
.node-head .code { color: #888; font-size: 11px; }
.node-head.off { opacity: .55; }
.off-mark { color: #b60; font-size: 12px; }
.mslot { margin-bottom: 12px; }
.mslot-head { display: flex; gap: 8px; align-items: baseline; margin-bottom: 4px; }
.mslot-head .code { color: #888; font-size: 11px; }
.mslot-head .req { color: #b60; font-size: 12px; }
.mopt { display: flex; align-items: center; gap: 10px; padding: 4px 6px; border-top: 1px solid #f0f0f0; }
.mopt .oname { flex: 1; font-size: 13px; }
.mopt.av-std { background: #f2faf2; }
.mopt.av-opt { background: #fffdf4; }
.mopt.av-na { background: #fafafa; opacity: .6; }
.mopt.mopt-inh { background: #e8f5e9; }
.mopt.mopt-diff { background: #fff3e0; }
.inh-val { flex: 0 0 auto; color: #5a7d5a; font-size: 11px; font-style: italic; }
.inh { color: #2c6fb0; font-size: 11px; cursor: help; }
.seg { display: flex; border: 1px solid #ccc; border-radius: 4px; overflow: hidden; }
.seg button { border: none; background: #fff; padding: 3px 10px; font-size: 12px; cursor: pointer; border-left: 1px solid #eee; }
.seg button:first-child { border-left: none; }
.seg button.on { background: #2c6fb0; color: #fff; }
.mrule { display: flex; align-items: center; gap: 8px; padding: 4px 6px; border-top: 1px dashed #e0e0e0; }
.mrule > span { color: #666; font-size: 12px; flex: 0 0 auto; }
.mrule select { padding: 3px 6px; border: 1px solid #ccc; border-radius: 3px; }
.rule-desc { color: #666; font-size: 12px; }
.cu-chk { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; color: #444; }
.cu-chk input { margin: 0; }
.edit-actions { margin-top: 12px; }

/* Привязки */
.bindings-editor { max-width: 960px; }
.bind-add { display: flex; gap: 14px; align-items: center; margin-bottom: 8px; flex-wrap: wrap; }
.btn-ghost { padding: 5px 12px; border: 1px solid #ccc; background: #fff; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-ghost:disabled { opacity: .45; cursor: not-allowed; }
.btn-ghost:hover:not(:disabled) { background: #eef4fb; border-color: #2c6fb0; }
.bind-models { border: 1px solid #e0e0e0; border-radius: 4px; padding: 8px; margin-bottom: 12px; }
.bind-models-head { display: flex; gap: 10px; align-items: center; margin-bottom: 6px; flex-wrap: wrap; }
.bind-model-list { display: flex; flex-direction: column; gap: 2px; max-height: 200px; overflow-y: auto; }
.bind-model-chk { display: flex; align-items: center; gap: 6px; font-size: 13px; cursor: pointer; }
.bind-model-chk .code { color: #888; font-size: 11px; font-style: normal; }
.bind-groups { display: flex; flex-direction: column; gap: 10px; }
.bind-group { border: 1px solid #e0e0e0; border-radius: 4px; padding: 8px; }
.bind-group-head { display: flex; gap: 8px; align-items: baseline; margin-bottom: 4px; flex-wrap: wrap; }
.bind-group-head .code { color: #888; font-size: 11px; }
.bind-group-head .whole { color: #2c6fb0; font-size: 12px; }
.bind-items { display: flex; flex-direction: column; gap: 2px; }
.bind-item { display: flex; align-items: center; gap: 8px; padding: 3px 6px; border-top: 1px solid #f0f0f0; font-size: 13px; }
.bind-item span { flex: 1; }
.bind-item .code { color: #888; font-size: 11px; font-style: normal; }
.bind-item button { cursor: pointer; border: none; background: none; color: #a00; }
</style>
