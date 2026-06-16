<template>
  <div class="ea-admin">
    <div class="toolbar">
      <label class="ml-label">Серия:</label>
      <select v-model="selectedMlId" @change="loadData" class="ml-select">
        <option :value="null">— выберите серию —</option>
        <option v-for="ml in modelLines" :key="ml.id" :value="ml.id">{{ ml.name }}</option>
      </select>
      <span v-if="loading" class="spinner">⏳</span>
      <span v-if="msg" class="msg" :class="msgType">{{ msg }}</span>
    </div>

    <div v-if="!selectedMlId" class="placeholder">Выберите серию электроприводов.</div>

    <div v-else-if="models.length" class="copy-panel">
      <!-- Источник -->
      <div class="copy-section">
        <h4>Источник:
          <select v-model="sourceMliId" class="ml-select inline" @change="onSourceChange">
            <option :value="null">— выберите модель —</option>
            <option v-for="m in models" :key="m.id" :value="m.id">{{ m.name }}</option>
          </select>
        </h4>

        <table v-if="sourceMliId" class="matrix copy-ref">
          <thead>
            <tr>
              <th class="col-model">Опция</th>
              <th>Код</th>
              <th class="col-enc">Encoding</th>
              <th>Есть</th>
              <th>Default</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in sourceRows" :key="row.key" :class="{ 'row-missing': !sourceEdit[row.key]?.has }">
              <td class="col-model">{{ row.groupIcon }} {{ row.group }}: {{ row.name }}</td>
              <td class="mono">{{ row.code }}</td>
              <td>
                <input v-if="sourceEdit[row.key]?.has" v-model="sourceEdit[row.key].encoding"
                  class="enc-inp" size="6" maxlength="20" />
                <span v-else class="mono">{{ row.encoding }}</span>
              </td>
              <td><input type="checkbox" :checked="sourceEdit[row.key]?.has" @change="toggleSourceOpt(row)"></td>
              <td><input type="checkbox" :checked="sourceEdit[row.key]?.isDefault"
                :disabled="!sourceEdit[row.key]?.has" @change="toggleSourceDefault(row)"></td>
            </tr>
          </tbody>
        </table>
        <div v-if="sourceMliId" style="margin-top:6px">
          <button class="btn btn-sm" @click="saveSource" :disabled="savingSource">💾 Сохранить источник</button>
          <span v-if="sourceDirty" class="hint">есть изменения</span>
        </div>
        <div v-else class="hint">← выберите модель-источник</div>
      </div>

      <!-- Цели -->
      <div class="copy-section">
        <h4>Цели:
          <label class="check-all"><input type="checkbox" :checked="allSelected" @change="toggleAll"> все</label>
          <button class="btn btn-sm" :disabled="!sourceMliId || !targetMliIds.length || copying" @click="doCopy">
            {{ copying ? 'Копирование...' : '📋 Копировать опции' }}
          </button>
        </h4>
        <table v-if="models.length" class="matrix copy-target-table">
          <thead>
            <tr><th class="col-check">⇨</th><th class="col-model">Модель</th>
              <th v-for="p in palette" :key="p.key" class="col-opt">{{ p.groupIcon }} {{ GROUP_LABELS[p.type] || '' }} {{ p.code || p.name }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in models" :key="m.id" :class="{ 'row-source': m.id === sourceMliId }">
              <td class="col-check">
                <label v-if="m.id !== sourceMliId" class="target-check">
                  <input type="checkbox" :value="m.id" v-model="targetMliIds">
                </label>
              </td>
              <td class="col-model">{{ m.name }}</td>
              <td v-for="p in palette" :key="p.key" :class="cellMarkClass(m, p)">{{ cellMark(m, p) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from './api'

const modelLines = ref([])
const selectedMlId = ref(null)
const loading = ref(false)
const msg = ref('')
const msgType = ref('ok')
const models = ref([])
const palette = ref([])
const sourceMliId = ref(null)
const targetMliIds = ref([])
const copying = ref(false)
const savingSource = ref(false)

const sourceEdit = reactive({})
const sourceDirty = computed(() => Object.keys(sourceEdit).length > 0 && sourceRows.value.some(r => {
  const e = sourceEdit[r.key]; if (!e) return false
  return e.has !== r.has || e.isDefault !== r.isDefault || e.encoding !== r.encoding
}))

const allSelected = computed(() => {
  const el = models.value.filter(m => m.id !== sourceMliId.value)
  return el.length > 0 && el.every(m => targetMliIds.value.includes(m.id))
})

const GROUP_LABELS = { way: 'Путевые', end: 'Концевые', torque: 'Моментные' }
const GROUP_ICONS = { way: '🔹', end: '🔸', torque: '🔺', ref: '⬜' }

const sourceRows = computed(() => {
  const m = models.value.find(x => x.id === sourceMliId.value)
  if (!m) return []
  const rows = []
  for (const p of palette.value) {
    const set = m[p.type]
    const opt = set?.[p.id]
    rows.push({
      key: p.type + '-' + p.id,
      groupIcon: GROUP_ICONS[p.type] || '⬜',
      group: GROUP_LABELS[p.type] || p.type,
      name: p.name,
      code: p.code,
      encoding: opt?.encoding || '',
      has: !!opt,
      isDefault: opt?.is_default || false,
      type: p.type,
      optId: p.id,
    })
  }
  return rows
})

function initSourceEdit() {
  Object.keys(sourceEdit).forEach(k => delete sourceEdit[k])
  for (const r of sourceRows.value) {
    sourceEdit[r.key] = { has: r.has, isDefault: r.isDefault, encoding: r.encoding }
  }
}

function toggleSourceOpt(row) {
  if (!sourceEdit[row.key]) sourceEdit[row.key] = { has: false, isDefault: false, encoding: row.encoding }
  sourceEdit[row.key].has = !sourceEdit[row.key].has
  if (!sourceEdit[row.key].has) sourceEdit[row.key].isDefault = false
}

function toggleSourceDefault(row) {
  if (!sourceEdit[row.key]) sourceEdit[row.key] = { has: false, isDefault: false, encoding: row.encoding }
  sourceEdit[row.key].isDefault = !sourceEdit[row.key].isDefault
}

function cellMarkClass(m, p) {
  const set = m[p.type]
  const opt = set?.[p.id]
  if (!opt) return 'cell-missing'
  if (opt.is_default) return 'cell-default'
  return 'cell-has-data'
}

function cellMark(m, p) {
  const set = m[p.type]
  const opt = set?.[p.id]
  if (!opt) return '✗'
  if (opt.is_default) return '✓d'
  return '✓'
}

function onSourceChange() {
  targetMliIds.value = []
  initSourceEdit()
}

function toggleAll(e) {
  const el = models.value.filter(m => m.id !== sourceMliId.value)
  targetMliIds.value = e.target.checked ? el.map(m => m.id) : []
}

async function loadData() {
  if (!selectedMlId.value) { models.value = []; palette.value = []; return }
  loading.value = true; msg.value = ''
  try {
    const d = await api.getSwitchesData(selectedMlId.value)
    models.value = d.models || []
    palette.value = d.palette || []
    sourceMliId.value = null
    targetMliIds.value = []
  } catch (e) {
    msg.value = 'Ошибка: ' + (e.response?.data?.error || e.message)
    msgType.value = 'err'
  } finally { loading.value = false }
}

async function saveSource() {
  savingSource.value = true; msg.value = ''
  const way = []; const end = []; const torque = []
  for (const r of sourceRows.value) {
    const e = sourceEdit[r.key]; if (!e || !e.has) continue
    const item = { switches_parameter_id: r.optId, encoding: e.encoding || '', is_default: e.isDefault || false }
    if (r.type === 'way') way.push(item)
    else if (r.type === 'end') end.push(item)
    else if (r.type === 'torque') torque.push(item)
  }
  try {
    await api.updateSwitches(sourceMliId.value, way, end, torque)
    msg.value = 'Источник сохранён'; msgType.value = 'ok'
    const savedId = sourceMliId.value
    await loadData()
    sourceMliId.value = savedId
    initSourceEdit()
  } catch (e) {
    msg.value = 'Ошибка: ' + (e.response?.data?.error || e.message)
    msgType.value = 'err'
  } finally { savingSource.value = false }
}

async function doCopy() {
  if (!sourceMliId.value || !targetMliIds.value.length) return
  copying.value = true; msg.value = ''
  try {
    const d = await api.copySwitches(sourceMliId.value, targetMliIds.value)
    msg.value = `Скопировано: ${d.created_way} путевых, ${d.created_end} концевых, ${d.created_torque} моментных`
    msgType.value = 'ok'
    await loadData()
    sourceMliId.value = null
  } catch (e) {
    msg.value = 'Ошибка: ' + (e.response?.data?.error || e.message)
    msgType.value = 'err'
  } finally { copying.value = false }
}

onMounted(async () => {
  try { modelLines.value = await api.getModelLines() } catch (e) { console.error(e) }
})
</script>

<style scoped>
.ea-admin { padding: 20px; font-family: var(--cat-font, 'Segoe UI', sans-serif); color: var(--cat-text, #1f2937); }
.toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.ml-label { font-weight: 600; font-size: 14px; }
.ml-select { padding: 6px 10px; border: 1px solid var(--cat-border, #d1d5db); border-radius: 6px; font-size: 14px; min-width: 180px; background: var(--cat-surface, #fff); color: var(--cat-text, #1f2937); }
.ml-select.inline { min-width: 200px; }
.spinner { font-size: 16px; }
.msg { font-size: 13px; padding: 4px 10px; border-radius: 4px; } .msg.ok { color: #065f46; background: #d1fae5; } .msg.err { color: #991b1b; background: #fee2e2; }
.btn { padding: 6px 14px; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; font-weight: 500; background: #2563eb; color: #fff; }
.btn:disabled { opacity: .5; cursor: not-allowed; }
.btn-sm { padding: 4px 10px; font-size: 12px; }
.placeholder { text-align: center; color: var(--cat-text-muted, #6b7280); padding: 60px 20px; font-size: 15px; }
.hint { color: #9ca3af; font-size: 13px; padding: 0 8px; }

.copy-panel { margin-top: 12px; display: flex; flex-direction: column; gap: 24px; }
.copy-section h4 { font-size: 14px; margin: 0 0 8px; display: flex; align-items: center; gap: 10px; }
.matrix { border-collapse: collapse; font-size: 12px; }
.matrix th, .matrix td { border: 1px solid var(--cat-border, #e5e7eb); padding: 3px 6px; text-align: center; }
.col-model { text-align: left; min-width: 170px; font-weight: 500; }
.col-check { min-width: 32px; }
.col-enc { min-width: 80px; }
.col-opt { min-width: 50px; max-width: 90px; font-size: 11px; white-space: nowrap; }
.mono { font-family: monospace; font-size: 11px; }
.enc-inp { width: 70px; padding: 2px 3px; border: 1px solid #d1d5db; border-radius: 3px; font-size: 11px; font-family: monospace; text-align: center; }
.check-all { font-weight: 400; font-size: 12px; cursor: pointer; }
.target-check { cursor: pointer; }
.row-source { opacity: 0.5; }
.row-missing { opacity: 0.4; }
.cell-has-data { background: #f0fdf4; }
.cell-default { background: #dbeafe; }
.cell-missing { background: #fef2f2; }
.copy-ref { width: auto; }
.copy-target-table { width: auto; }
</style>
