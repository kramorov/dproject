<template>
  <div class="ea-admin">
    <div class="toolbar">
      <label class="ml-label">Серия:</label>
      <select v-model="selectedMlId" @change="onSeriesChange" class="ml-select">
        <option :value="null">— выберите серию —</option>
        <option v-for="ml in modelLines" :key="ml.id" :value="ml.id">{{ ml.name }}</option>
      </select>
      <span v-if="loading" class="spinner">⏳</span>
      <span v-if="msg" class="msg" :class="msgType">{{ msg }}</span>
      <div class="spacer"></div>
      <button v-if="selectedMlId && tab==='matrix'" class="btn btn-export" @click="doExport">📥 Экспорт</button>
      <label v-if="selectedMlId && tab==='matrix'" class="btn btn-import">📤 Импорт<input type="file" accept=".xlsx" hidden @change="doImport"></label>
      <button v-if="dirty" class="btn btn-save" @click="save" :disabled="saving">💾 Сохранить</button>
      <button v-if="dirty" class="btn btn-cancel" @click="loadMatrix">↩ Отменить</button>
    </div>

    <div v-if="selectedMlId" class="tabs">
      <button :class="['tab', { active: tab === 'matrix' }]" @click="tab = 'matrix'">📊 Матрица</button>
      <button :class="['tab', { active: tab === 'copy' }]" @click="tab = 'copy'; loadCopyData()">📋 Копирование опций</button>
    </div>

    <div v-if="!selectedMlId" class="placeholder">Выберите серию электроприводов.</div>

    <!-- TAB: Матрица -->
    <div v-if="selectedMlId && tab === 'matrix' && modelItems.length" class="table-wrap">
      <table class="matrix">
        <thead><tr><th class="col-model" rowspan="2">Модель</th><th v-for="ps in powerSupplies" :key="ps.id" :colspan="FIELDS.length" class="col-ps-header">{{ ps.name }}</th></tr>
        <tr><template v-for="ps in powerSupplies" :key="'s'+ps.id"><th v-for="f in FIELDS" :key="f.key" class="col-sub">{{ f.label }}</th></template></tr></thead>
        <tbody><tr v-for="(m,mi) in modelItems" :key="m.id"><td class="col-model">{{ m.name }}</td><template v-for="(v,vi) in m.voltages" :key="v.power_supply_id"><td v-for="f in FIELDS" :key="f.key" :class="cellClass(mi,vi,f.key)"><input type="number" :step="f.step" min="0" :value="displayValue(v[f.key])" @input="onInput(mi,vi,f.key,$event)" @focus="onFocus(mi,vi)" placeholder="0"></td></template></tr></tbody>
      </table>
    </div>

    <!-- TAB: Копирование опций -->
    <div v-if="selectedMlId && tab === 'copy'" class="copy-panel">
      <div class="copy-controls">
        <label>Напряжение:</label>
        <select v-model="copyPsId" @change="fetchCopyModels" class="ml-select">
          <option :value="null">— выберите —</option>
          <option v-for="ps in copyVoltages" :key="ps.id" :value="ps.id">{{ ps.name }}</option>
        </select>
        <span v-if="totalOpts" class="palette-summary">Опций: {{ totalOpts }} (БУ: {{ copyPalette.cu.length }}, ПБ: {{ copyPalette.sp.length }})</span>
        <span v-if="!copyPsId && copyVoltages.length" class="hint">← выберите напряжение</span>
      </div>

      <div v-if="copyPsId && copyModels.length" class="copy-matrix">
        <div class="copy-section">
          <h4>Источник:
            <select v-model="sourceMliId" class="ml-select inline" @change="onSourceChange">
              <option :value="null">— выберите модель —</option>
              <option v-for="m in copyModels" :key="m.id" :value="m.id">{{ m.name }}</option>
            </select>
          </h4>
          <table v-if="sourceMliId" class="matrix copy-ref">
            <thead><tr><th class="col-model">Опция</th><th>Enc</th><th>Есть</th><th>Default</th></tr></thead>
            <tbody>
              <tr v-for="row in sourceRows" :key="row.key">
                <td class="col-model">{{ row.icon }} {{ row.name }}</td>
                <td>{{ row.encoding }}</td>
                <td><input type="checkbox" :checked="sourceEdit[row.key]?.has" @change="toggleSourceOpt(row)"></td>
                <td><input type="checkbox" :checked="sourceEdit[row.key]?.isDefault" :disabled="!sourceEdit[row.key]?.has" @change="toggleSourceDefault(row)"></td>
              </tr>
            </tbody>
          </table>
          <div v-if="sourceMliId" style="margin-top:6px">
            <button class="btn btn-save btn-sm" @click="saveSource" :disabled="savingSource">💾 Сохранить источник</button>
            <span v-if="sourceDirty" class="hint" style="padding:0 8px">есть изменения</span>
          </div>
          <div v-else class="hint">← выберите модель-источник</div>
        </div>

        <div class="copy-section">
          <h4>Получатели
            <label class="check-all"><input type="checkbox" @change="toggleAll" :checked="allSelected"> Все</label>
            <button class="btn btn-save btn-sm" @click="doCopy" :disabled="!sourceMliId || !targetMliIds.length || copying">{{ copying?'⏳':'📋' }} Скопировать</button>
          </h4>
          <table v-if="paletteColumns.length" class="matrix copy-target-table">
            <thead><tr><th class="col-model" style="min-width:80px">Модель</th><th v-for="col in paletteColumns" :key="col.key" class="col-sub">{{ col.label }}</th></tr></thead>
            <tbody>
              <tr v-for="m in copyModels" :key="m.id" :class="{ 'row-source': m.id===sourceMliId, 'row-no-ps': !m.has_power_supply }">
                <td class="col-model" style="min-width:80px"><label class="target-check"><input type="checkbox" :value="m.id" v-model="targetMliIds" :disabled="m.id===sourceMliId||!m.has_power_supply"> {{ m.name }}</label></td>
                <td v-for="col in paletteColumns" :key="col.key" :class="cellClassCopy(m,col)">{{ cellMarkCopy(m,col) }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="hint">Нет опций для отображения</div>
        </div>
      </div>
      <div v-else-if="copyPsId && !copyModels.length" class="hint">Нет моделей с этим напряжением</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import eaApi from './api'

const FIELDS = [
  { key: 'current_rated', label: 'I ном, А', step: '0.01' },
  { key: 'current_starting', label: 'I пуск, А', step: '0.01' },
  { key: 'motor_power', label: 'P, кВт', step: '0.001' },
  { key: 'time_to_open', label: 't откр, с', step: '0.01' },
  { key: 'time_to_close', label: 't закр, с', step: '0.01' },
  { key: 'torque_min', label: 'M мин, Нм', step: '1' },
  { key: 'torque_max', label: 'M макс, Нм', step: '1' },
]

const modelLines = ref([])
const selectedMlId = ref(null)
const powerSupplies = ref([])
const modelItems = ref([])
const loading = ref(false)
const saving = ref(false)
const dirty = ref(false)
const msg = ref('')
const msgType = ref('ok')
const tab = ref('matrix')
const touched = reactive({})

// Copy state
const copyVoltages = ref([])
const copyPsId = ref(null)
const copyModels = ref([])
const copyPalette = ref({ cu: [], sp: [] })
const sourceMliId = ref(null)
const targetMliIds = ref([])
const copying = ref(false)
const savingSource = ref(false)
const sourceEdit = reactive({})
const sourceDirty = computed(() => Object.keys(sourceEdit).length > 0 && sourceRows.value.some(r => {
  const e = sourceEdit[r.key]; if (!e) return false
  return e.has !== r.has || e.isDefault !== r.isDefault
}))

const totalOpts = computed(() => copyPalette.value.cu.length + copyPalette.value.sp.length)
const allSelected = computed(() => {
  const el = copyModels.value.filter(m => m.id !== sourceMliId.value && m.has_power_supply)
  return el.length > 0 && el.every(m => targetMliIds.value.includes(m.id))
})
const paletteColumns = computed(() => {
  const cols = []
  copyPalette.value.cu.forEach(o => cols.push({ key: 'cu-'+o.id, label: o.name, type: 'cu', optId: o.id }))
  copyPalette.value.sp.forEach(o => cols.push({ key: 'sp-'+o.id, label: o.name, type: 'sp', optId: o.id }))
  return cols
})

function sourceCu(cuId) { const m = copyModels.value.find(x => x.id === sourceMliId.value); return m?.cu?.[cuId] }
function sourceSp(spId) { const m = copyModels.value.find(x => x.id === sourceMliId.value); return m?.sp?.[spId] }

const sourceRows = computed(() => {
  const rows = []
  for (const opt of copyPalette.value.cu) {
    const cu = sourceCu(opt.id)
    rows.push({ key: 'cu-'+opt.id, icon: '🔹', name: opt.name, encoding: opt.encoding, has: !!cu, isDefault: cu?.is_default || false, optId: opt.id })
  }
  for (const opt of copyPalette.value.sp) {
    const sp = sourceSp(opt.id)
    rows.push({ key: 'sp-'+opt.id, icon: '🔸', name: opt.name, encoding: opt.encoding, has: !!sp, isDefault: sp?.is_default || false, optId: opt.id })
  }
  return rows
})

function initSourceEdit() {
  Object.keys(sourceEdit).forEach(k => delete sourceEdit[k])
  for (const r of sourceRows.value) {
    sourceEdit[r.key] = { has: r.has, isDefault: r.isDefault }
  }
}
function toggleSourceOpt(row) {
  if (!sourceEdit[row.key]) sourceEdit[row.key] = { has: false, isDefault: false }
  sourceEdit[row.key].has = !sourceEdit[row.key].has
  if (!sourceEdit[row.key].has) sourceEdit[row.key].isDefault = false
}
function toggleSourceDefault(row) {
  if (!sourceEdit[row.key]) sourceEdit[row.key] = { has: false, isDefault: false }
  sourceEdit[row.key].isDefault = !sourceEdit[row.key].isDefault
}
async function saveSource() {
  savingSource.value = true; msg.value = ''
  const cus = []; const sps = []
  for (const r of sourceRows.value) {
    const e = sourceEdit[r.key]; if (!e || !e.has) continue
    const item = { encoding: r.encoding, is_default: e.isDefault || false }
    if (r.key.startsWith('cu-')) { item.control_unit_id = r.optId; cus.push(item) }
    else { item.safety_position_id = r.optId; sps.push(item) }
  }
  try {
    await eaApi.updateSourceOptions(sourceMliId.value, copyPsId.value, cus, sps)
    msg.value = 'Источник сохранён'; msgType.value = 'ok'
    const savedId = sourceMliId.value
    await fetchCopyModels()
    sourceMliId.value = savedId
    initSourceEdit()
  } catch(e) { msg.value = 'Ошибка: ' + (e.response?.data?.error || e.message); msgType.value = 'err' }
  finally { savingSource.value = false }
}

function cellClassCopy(m, col) {
  if (!m.has_power_supply) return 'cell-empty'
  const set = col.type === 'cu' ? m.cu : m.sp
  const opt = set?.[col.optId]
  if (!opt) return 'cell-missing'
  if (opt.is_default) return 'cell-default'
  return 'cell-has-data'
}
function cellMarkCopy(m, col) {
  if (!m.has_power_supply) return '—'
  const set = col.type === 'cu' ? m.cu : m.sp
  const opt = set?.[col.optId]
  if (!opt) return '✗'
  if (opt.is_default) return '✓d'
  return '✓'
}

onMounted(async () => { try { modelLines.value = await eaApi.getModelLines() } catch(e) { console.error(e) } })

function onSeriesChange() { loadMatrix(); if (tab.value === 'copy') loadCopyData() }

// ── Matrix tab ──
async function loadMatrix() {
  if (!selectedMlId.value) { modelItems.value = []; powerSupplies.value = []; return }
  loading.value = true; dirty.value = false; Object.keys(touched).forEach(k => delete touched[k]); msg.value = ''
  try {
    const d = await eaApi.getMatrix(selectedMlId.value)
    powerSupplies.value = d.power_supplies || []
    modelItems.value = (d.models || []).map(m => ({ ...m, voltages: m.voltages.map(v => ({ ...v })) }))
  } catch(e) { msg.value = 'Ошибка: ' + (e.response?.data?.error || e.message); msgType.value = 'err' }
  finally { loading.value = false }
}
function onFocus(mi, vi) { touched[`${mi}-${vi}`] = true; dirty.value = true }
function onInput(mi, vi, field, event) {
  const raw = event.target.value; modelItems.value[mi].voltages[vi][field] = raw === '' ? '' : (isNaN(parseFloat(raw)) ? raw : parseFloat(raw)); dirty.value = true
}
function displayValue(v) { return (v === '' || v === null || v === undefined || typeof v === 'string') ? '' : v }
function cellClass(mi, vi, field) { const v = modelItems.value[mi].voltages[vi]; return FIELDS.some(f => v[f.key]) ? 'cell-has-data' : (touched[`${mi}-${vi}`] ? 'cell-touched' : 'cell-empty') }

async function save() {
  saving.value = true; msg.value = ''; const rows = []
  for (const m of modelItems.value) for (const v of m.voltages) {
    const row = { model_line_item_id: m.id, power_supply_id: v.power_supply_id }
    for (const f of FIELDS) { const raw = v[f.key]; row[f.key] = (raw === '' || raw === null || isNaN(raw)) ? 0 : raw }
    rows.push(row)
  }
  try { const d = await eaApi.saveMatrix({ model_line_id: selectedMlId.value, rows }); msg.value = `Сохранено: +${d.created} ~${d.updated} -${d.deleted}`; msgType.value = 'ok'; dirty.value = false; await loadMatrix() }
  catch(e) { msg.value = 'Ошибка: ' + (e.response?.data?.error || e.message); msgType.value = 'err' }
  finally { saving.value = false }
}
async function doExport() { try { const blob = await eaApi.exportMatrix(selectedMlId.value); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `ea_ps_${selectedMlId.value}.xlsx`; a.click(); URL.revokeObjectURL(url); msg.value = 'Готово'; msgType.value = 'ok' } catch(e) { msg.value = 'Ошибка экспорта'; msgType.value = 'err' } }
async function doImport(e) { const f = e.target.files[0]; if (!f) return; saving.value = true; try { const d = await eaApi.importMatrix(selectedMlId.value, f); msg.value = `Импорт: +${d.created} ~${d.updated} деактивировано ${d.deleted}`; msgType.value = 'ok'; await loadMatrix() } catch(ex) { msg.value = 'Ошибка импорта: ' + (ex.response?.data?.error || ex.message); msgType.value = 'err' } finally { saving.value = false; e.target.value = '' } }

// ── Copy tab ──
async function loadCopyData() { if (!selectedMlId.value) return; copyPsId.value = null; sourceMliId.value = null; targetMliIds.value = []; copyModels.value = []; try { const d = await eaApi.getMatrix(selectedMlId.value); copyVoltages.value = d.power_supplies || [] } catch(e) { console.error(e) } }
async function fetchCopyModels() { if (!copyPsId.value) { copyModels.value = []; copyPalette.value = { cu: [], sp: [] }; return }; loading.value = true; try { const r = await eaApi.getControlUnits(selectedMlId.value, copyPsId.value); copyModels.value = r.models || []; const p = r.palette || {}; copyPalette.value = { cu: p.control_units || [], sp: p.safety_positions || [] }; sourceMliId.value = null; targetMliIds.value = [] } catch(e) { msg.value = 'Ошибка: ' + (e.response?.data?.error || e.message); msgType.value = 'err' } finally { loading.value = false } }
function onSourceChange() { targetMliIds.value = []; initSourceEdit() }
function toggleAll(e) { const el = copyModels.value.filter(m => m.id !== sourceMliId.value && m.has_power_supply); targetMliIds.value = e.target.checked ? el.map(m => m.id) : [] }

async function doCopy() {
  if (!sourceMliId.value || !targetMliIds.value.length || !copyPsId.value) return
  copying.value = true; msg.value = ''
  try { const d = await eaApi.copyControlUnits(sourceMliId.value, targetMliIds.value, copyPsId.value); msg.value = `Скопировано: ${d.created_control_units} БУ, ${d.created_safety_positions} ПБ`; if (d.skipped_no_power_supply) msg.value += ` (пропущено: ${d.skipped_no_power_supply})`; msgType.value = 'ok'; await fetchCopyModels() }
  catch(e) { msg.value = 'Ошибка: ' + (e.response?.data?.error || e.message); msgType.value = 'err' }
  finally { copying.value = false }
}
</script>

<style scoped>
.ea-admin { padding: 20px; font-family: var(--cat-font, 'Segoe UI', sans-serif); color: var(--cat-text, #1f2937); }
.toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.ml-label { font-weight: 600; font-size: 14px; }
.ml-select { padding: 6px 10px; border: 1px solid var(--cat-border, #d1d5db); border-radius: 6px; font-size: 14px; min-width: 180px; background: var(--cat-surface, #fff); color: var(--cat-text, #1f2937); }
.ml-select.inline { min-width: 200px; }
.spacer { flex: 1; } .spinner { font-size: 16px; }
.msg { font-size: 13px; padding: 4px 10px; border-radius: 4px; } .msg.ok { color: #065f46; background: #d1fae5; } .msg.err { color: #991b1b; background: #fee2e2; }
.btn { padding: 6px 14px; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; font-weight: 500; }
.btn-save { background: #2563eb; color: #fff; } .btn-save:disabled { opacity: .5; cursor: not-allowed; }
.btn-cancel { background: var(--cat-bg, #f3f4f6); color: var(--cat-text, #1f2937); border: 1px solid var(--cat-border, #d1d5db); }
.btn-export { background: #059669; color: #fff; } .btn-import { background: #7c3aed; color: #fff; display: inline-flex; align-items: center; }
.btn-sm { padding: 4px 10px; font-size: 12px; }
.placeholder { text-align: center; color: var(--cat-text-muted, #6b7280); padding: 60px 20px; font-size: 15px; }
.table-wrap { overflow-x: auto; }
.matrix { border-collapse: collapse; font-size: 13px; }
.matrix th, .matrix td { border: 1px solid var(--cat-border, #e5e7eb); padding: 3px 4px; text-align: center; min-width: 68px; }
.col-model { text-align: left; min-width: 170px; font-weight: 500; position: sticky; left: 0; background: var(--cat-surface, #fff); z-index: 1; }
.col-ps-header { background: #eef2ff; font-weight: 600; font-size: 12px; padding: 5px 3px; }
.col-sub { background: #f8fafc; font-weight: 400; font-size: 10px; color: #64748b; min-width: 62px; max-width: 90px; white-space: normal; word-break: break-word; line-height: 1.2; vertical-align: top; padding: 4px 2px; }
.matrix input { width: 100%; border: none; padding: 3px 2px; font-size: 11px; text-align: center; background: transparent; color: var(--cat-text, #1f2937); box-sizing: border-box; outline: none; }
.matrix input:focus { background: #fff; box-shadow: inset 0 0 0 2px #2563eb; border-radius: 2px; }
.cell-has-data { background: #f0fdf4; } .cell-touched { background: #fefce8; } .cell-empty { background: #f9fafb; }
.cell-default { background: #dbeafe; } .cell-missing { background: #fef2f2; }
.matrix tbody tr:hover td { filter: brightness(0.97); }

.tabs { display: flex; gap: 4px; margin-bottom: 16px; }
.tab { padding: 8px 20px; border: 1px solid var(--cat-border, #d1d5db); background: var(--cat-bg, #f3f4f6); border-radius: 6px 6px 0 0; font-size: 14px; cursor: pointer; color: var(--cat-text, #1f2937); }
.tab.active { background: #fff; border-bottom-color: #fff; font-weight: 600; }

.copy-panel { margin-top: 12px; }
.copy-controls { margin-bottom: 12px; display: flex; align-items: center; gap: 10px; }
.palette-summary { font-size: 12px; color: #64748b; }
.copy-matrix { display: flex; flex-direction: column; gap: 20px; }
.copy-section h4 { font-size: 14px; margin: 0 0 8px; display: flex; align-items: center; gap: 10px; }
.copy-ref { width: auto; }
.copy-target-table { width: auto; }
.check-all { font-weight: 400; font-size: 12px; margin-left: 8px; cursor: pointer; }
.target-check { display: flex; align-items: center; gap: 4px; font-size: 12px; cursor: pointer; }
.row-source { opacity: 0.5; }
.row-no-ps { opacity: 0.4; }
.hint { color: #9ca3af; font-size: 13px; padding: 12px 0; }
</style>
