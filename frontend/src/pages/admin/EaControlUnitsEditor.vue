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
          <option v-for="k in KIND_CHOICES" :key="k[0]" :value="k[0]">{{ k[1] }}</option>
        </select>
      </label>
      <div class="count">{{ filtered.length }} из {{ units.length }}</div>
      <div v-if="error" class="error">{{ error }}</div>
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
        </div>

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
                <option v-for="k in KIND_CHOICES" :key="k[0]" :value="k[0]">{{ k[1] }}</option>
              </select>
            </label>
            <label class="field"><span>Размещение</span>
              <select v-model="form.location">
                <option :value="null">— —</option>
                <option v-for="o in locations" :key="o.id" :value="o.id">{{ o.label }}</option>
              </select>
            </label>
          </div>
          <div class="form-row">
            <label class="field"><span>Напряжение цепей</span>
              <select v-model="form.control_voltage">
                <option :value="null">— —</option>
                <option v-for="p in powerSupplies" :key="p.id" :value="p.id">{{ p.label }}</option>
              </select>
            </label>
            <label class="field"><span>Питание цепей</span>
              <select v-model="form.signal_power">
                <option :value="null">— —</option>
                <option v-for="o in signalPowers" :key="o.id" :value="o.id">{{ o.label }}</option>
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

        <div class="sub-tabs">
          <button :class="{ active: tab === 'templates' }" @click="tab = 'templates'">Шаблоны и описания</button>
          <button :class="{ active: tab === 'settings' }" @click="openSettingsTab()">Настройки</button>
        </div>

        <div v-if="tab === 'templates'" class="templates"
             @input="dirty = true" @change="dirty = true">
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

        <div v-else class="settings">
          <div class="matrix-toolbar">
            <label class="mfield"><span>Напряжение</span>
              <select v-model="matrixPowerSupply" @change="onVoltageChange">
                <option :value="null">— любое напряжение —</option>
                <option v-for="p in powerSupplies" :key="p.id" :value="p.id">{{ p.label }}</option>
              </select>
            </label>
            <span class="hint">std — стандарт · opt — опция · na — недоступно; на конкретном напряжении na снимает переопределение</span>
          </div>
          <div v-if="!form.id" class="hint">Сначала сохраните блок управления, затем настраивайте опции.</div>
          <template v-else>
            <div class="node-tabs">
              <button v-for="n in nodeTree" :key="n.id"
                      :class="{ active: nodeId === n.id }"
                      :style="{ paddingLeft: (6 + n.depth * 10) + 'px' }"
                      @click="nodeId = n.id">{{ n.name }}</button>
            </div>
            <div v-if="nodeId" class="matrix-editor">
              <div v-for="s in matrixSlotsOfNode" :key="s.code" class="mslot">
                <div class="mslot-head">
                  <strong>{{ s.name }}</strong>
                  <span class="code">{{ s.code }}</span>
                  <span v-if="s.required" class="req">обязателен</span>
                </div>
                <div v-for="o in s.options" :key="o.id" class="mopt"
                     :class="'av-' + o.availability">
                  <span class="oname">{{ o.name }}</span>
                  <span v-if="o.inherited" class="inh" title="наследуется от «любое напряжение»">насл.</span>
                  <div class="seg">
                    <button :class="{ on: o.availability === 'std' }" @click="setAvail(o, 'std')">std</button>
                    <button :class="{ on: o.availability === 'opt' }" @click="setAvail(o, 'opt')">opt</button>
                    <button :class="{ on: o.availability === 'na' }" @click="setAvail(o, 'na')">na</button>
                  </div>
                </div>
              </div>
              <p v-if="!matrixSlotsOfNode.length" class="empty">В узле нет слотов.</p>
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
 * «Настройки» редактирует профильную матрицу выбранного БУ: слоты → опции
 * с пометкой std/opt/na (GET/PUT /api/ea-control/unit-matrix/).
 */
import { computed, onMounted, reactive, ref } from 'vue'
import api from '@/shared/api'
import { t } from '@/shared/i18n'
import EditorActions from '@/components/EditorActions.vue'

const KIND_CHOICES = [
  ['NONE', 'Без БУ'], ['BASIC', 'Базовый'],
  ['INTEGRATED', 'Интеллектуальный'], ['POSITIONER', 'Позиционер'],
]

const units = ref([])
const brands = ref([])
const powerSupplies = ref([])
const locations = ref([])
const signalPowers = ref([])
const nodes = ref([])
const error = ref('')
// матрица профиля выбранного БУ (вкладка «Настройки»)
const matrix = ref(null)
const matrixPowerSupply = ref(null)
const lastVoltage = ref(null)
const matrixOriginals = new Map() // option id -> availability
const matrixDirty = ref(false)

const filters = reactive({ brand: null, kind: null })
const form = ref(null)
const dirty = ref(false)
const tab = ref('templates')
const nodeId = ref(null)

const filtered = computed(() => units.value.filter(u =>
  (!filters.brand || u.brand === filters.brand)
  && (!filters.kind || u.kind === filters.kind)))

const nodeTree = computed(() => {
  const byParent = {}
  for (const n of nodes.value) {
    const key = n.parent || 0
    if (!byParent[key]) byParent[key] = []
    byParent[key].push(n)
  }
  const out = []
  const walk = (pid, depth) => {
    for (const n of (byParent[pid] || [])) {
      out.push({ ...n, depth })
      walk(n.id, depth + 1)
    }
  }
  walk(0, 0)
  return out
})

const matrixSlotsOfNode = computed(() =>
  (matrix.value?.slots || []).filter(s => s.section_id === nodeId.value))

const toolbarButtons = computed(() => [
  { key: 'create', label: t('eaControl.add'), kind: 'primary' },
  { key: 'refresh', label: t('eaControl.refresh') },
])

const editButtons = computed(() => [
  { key: 'save', label: t('eaControl.save'), kind: 'primary', disabled: !(dirty.value || matrixDirty.value) },
  { key: 'cancel', label: t('eaControl.cancel') },
])

function kindLabel(k) {
  const o = KIND_CHOICES.find(([id]) => id === k)
  return o ? o[1] : k
}

function brandName(id) {
  const b = brands.value.find(x => x.id === id)
  return b ? b.name : ''
}

function dictList(rows) {
  return rows.map(o => ({ id: o.id, label: o.name || o.code || String(o.id) }))
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
  const [meta, loc, sp, sections] = await Promise.all([
    api.get('/ea-control/meta/'),
    api.get('/ea-control/location-options/'),
    api.get('/ea-control/signal-powers/'),
    api.get('/ea-control/sections/'),
  ])
  brands.value = meta.data.brands || []
  powerSupplies.value = (meta.data.power_supplies || []).map(o => ({
    id: o.id, label: o.code ? `${o.name} (${o.code})` : o.name }))
  locations.value = dictList(loc.data.results || loc.data || [])
  signalPowers.value = dictList(sp.data.results || sp.data || [])
  nodes.value = sections.data.results || sections.data || []
}

function openEdit(u) {
  if (dirty.value || matrixDirty.value) {
    if (!confirm('Есть несохранённые изменения. Отменить их?')) return
  }
  form.value = {
    id: u.id, code: u.code, name: u.name, brand: u.brand, kind: u.kind,
    location: u.location, control_voltage: u.control_voltage,
    signal_power: u.signal_power, sorting_order: u.sorting_order || 0,
    is_active: u.is_active, description: u.description || '',
    name_template: u.name_template || '',
    description_template: u.description_template || '',
    spec_template: typeof u.spec_template === 'string'
      ? u.spec_template : JSON.stringify(u.spec_template || {}, null, 2),
  }
  dirty.value = false
  matrix.value = null
  matrixDirty.value = false
  tab.value = 'templates'
}

function openCreate() {
  if (dirty.value || matrixDirty.value) {
    if (!confirm('Есть несохранённые изменения. Отменить их?')) return
  }
  form.value = {
    id: null, code: '', name: '', brand: null, kind: 'INTEGRATED',
    location: null, control_voltage: null, signal_power: null,
    sorting_order: 0, is_active: true, description: '',
    name_template: '', description_template: '', spec_template: '',
  }
  dirty.value = false
  matrix.value = null
  matrixDirty.value = false
  tab.value = 'templates'
}

function onToolbar(b) {
  if (b.key === 'create') openCreate()
  else if (b.key === 'refresh') loadUnits()
}

async function copyUnit(u) {
  error.value = ''
  try {
    await api.post(`/ea-control/control-units/${u.id}/copy/`)
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
    for (const s of data.slots || []) {
      for (const o of s.options || []) matrixOriginals.set(o.id, o.availability)
    }
    matrixDirty.value = false
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка загрузки матрицы'
  }
}

function setAvail(o, avail) {
  if (o.availability === avail) return
  o.availability = avail
  matrixDirty.value = true
}

async function saveMatrix() {
  if (!form.value || !form.value.id) return
  const changes = []
  for (const s of (matrix.value?.slots || [])) {
    for (const o of s.options || []) {
      const orig = matrixOriginals.get(o.id)
      if (orig !== undefined && orig !== o.availability) {
        changes.push({ slot_id: s.id, option_id: o.id, availability: o.availability })
      }
    }
  }
  if (!changes.length) return
  await api.put('/ea-control/unit-matrix/save/', {
    unit: form.value.id,
    power_supply: matrixPowerSupply.value || null,
    changes,
  })
}

function openSettingsTab() {
  tab.value = 'settings'
  if (nodeId.value == null && nodeTree.value.length) nodeId.value = nodeTree.value[0].id
  loadMatrix()
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
    location: f.location, control_voltage: f.control_voltage,
    signal_power: f.signal_power, sorting_order: f.sorting_order || 0,
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
    dirty.value = false
    matrixDirty.value = false
    await loadUnits()
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка сохранения'
  }
}

function cancelEdit() {
  form.value = null
  matrix.value = null
  dirty.value = false
  matrixDirty.value = false
}

onMounted(async () => {
  try {
    await loadMeta()
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
.edit-head h3 { margin: 0 0 8px; font-size: 15px; }
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
.sub-tabs { display: flex; gap: 4px; margin: 14px 0 8px; }
.sub-tabs button { padding: 6px 12px; border: 1px solid #ccc; background: #f5f5f5; cursor: pointer; }
.sub-tabs button.active { background: #2c6fb0; color: #fff; border-color: #2c6fb0; }
.templates { display: flex; flex-direction: column; gap: 8px; max-width: 900px; }
.node-tabs { display: flex; flex-wrap: wrap; gap: 2px; margin-bottom: 8px; max-height: 120px; overflow: auto; }
.node-tabs button { padding: 4px 8px; border: 1px solid #ccc; background: #fff; cursor: pointer; font-size: 12px; text-align: left; }
.node-tabs button.active { background: #2c6fb0; color: #fff; }
.matrix-toolbar { display: flex; gap: 14px; align-items: center; margin-bottom: 8px; flex-wrap: wrap; }
.mfield { display: flex; align-items: center; gap: 8px; }
.mfield span { color: #444; font-size: 13px; }
.mfield select { padding: 4px 6px; border: 1px solid #ccc; border-radius: 3px; }
.hint { color: #888; font-size: 12px; }
.matrix-editor { border: 1px solid #e0e0e0; border-radius: 4px; padding: 8px; max-width: 960px; }
.mslot { margin-bottom: 12px; }
.mslot-head { display: flex; gap: 8px; align-items: baseline; margin-bottom: 4px; }
.mslot-head .code { color: #888; font-size: 11px; }
.mslot-head .req { color: #b60; font-size: 12px; }
.mopt { display: flex; align-items: center; gap: 10px; padding: 4px 6px; border-top: 1px solid #f0f0f0; }
.mopt .oname { flex: 1; font-size: 13px; }
.mopt.av-std { background: #f2faf2; }
.mopt.av-opt { background: #fffdf4; }
.mopt.av-na { background: #fafafa; opacity: .6; }
.inh { color: #2c6fb0; font-size: 11px; cursor: help; }
.seg { display: flex; border: 1px solid #ccc; border-radius: 4px; overflow: hidden; }
.seg button { border: none; background: #fff; padding: 3px 10px; font-size: 12px; cursor: pointer; border-left: 1px solid #eee; }
.seg button:first-child { border-left: none; }
.seg button.on { background: #2c6fb0; color: #fff; }
.edit-actions { margin-top: 12px; }
</style>
