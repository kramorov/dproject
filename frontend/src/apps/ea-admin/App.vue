<template>
  <div class="ea-admin">
    <div class="toolbar">
      <label class="ml-label">Серия:</label>
      <select v-model="selectedMlId" @change="loadMatrix" class="ml-select">
        <option :value="null">— выберите серию —</option>
        <option v-for="ml in modelLines" :key="ml.id" :value="ml.id">{{ ml.name }}</option>
      </select>
      <span v-if="loading" class="spinner">⏳</span>
      <span v-if="msg" class="msg" :class="msgType">{{ msg }}</span>
      <div class="spacer"></div>
      <button v-if="selectedMlId" class="btn btn-export" @click="doExport">📥 Экспорт</button>
      <label v-if="selectedMlId" class="btn btn-import">
        📤 Импорт
        <input type="file" accept=".xlsx" hidden @change="doImport" />
      </label>
      <button v-if="dirty" class="btn btn-save" @click="save" :disabled="saving">💾 Сохранить</button>
      <button v-if="dirty" class="btn btn-cancel" @click="loadMatrix">↩ Отменить</button>
    </div>

    <div v-if="!selectedMlId" class="placeholder">
      Выберите серию электроприводов для редактирования опций напряжения.
    </div>

    <div v-if="selectedMlId && modelItems.length" class="table-wrap">
      <table class="matrix">
        <thead>
          <tr>
            <th class="col-model" rowspan="2">Модель</th>
            <th v-for="ps in powerSupplies" :key="ps.id" :colspan="FIELDS.length" class="col-ps-header">
              {{ ps.name }}
            </th>
          </tr>
          <tr>
            <template v-for="ps in powerSupplies" :key="'sub-'+ps.id">
              <th v-for="f in FIELDS" :key="f.key" class="col-sub">{{ f.label }}</th>
            </template>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(m, mi) in modelItems" :key="m.id">
            <td class="col-model">{{ m.name }}</td>
            <template v-for="(v, vi) in m.voltages" :key="v.power_supply_id">
              <td v-for="f in FIELDS" :key="f.key" :class="cellClass(mi, vi, f.key)">
                <input
                  type="number"
                  :step="f.step"
                  min="0"
                  :value="displayValue(v[f.key])"
                  @input="onInput(mi, vi, f.key, $event)"
                  @focus="onFocus(mi, vi)"
                  placeholder="0"
                />
              </td>
            </template>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import eaApi from './api'

const FIELDS = [
  { key: 'current_rated',     label: 'I ном, А',  step: '0.01' },
  { key: 'current_starting',  label: 'I пуск, А',  step: '0.01' },
  { key: 'motor_power',       label: 'P, кВт',     step: '0.001' },
  { key: 'time_to_open',      label: 't откр, с',  step: '0.01' },
  { key: 'time_to_close',     label: 't закр, с',  step: '0.01' },
  { key: 'torque_min',        label: 'M мин, Нм',  step: '1' },
  { key: 'torque_max',        label: 'M макс, Нм', step: '1' },
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
// reactive object вместо Set — Vue 3 отслеживает изменения ключей
const touched = reactive({})

onMounted(async () => {
  try {
    modelLines.value = await eaApi.getModelLines()
  } catch (e) {
    console.error('Failed to load model lines', e)
  }
})

async function loadMatrix() {
  if (!selectedMlId.value) {
    modelItems.value = []
    powerSupplies.value = []
    return
  }
  loading.value = true
  dirty.value = false
  clearTouched()
  msg.value = ''
  try {
    const data = await eaApi.getMatrix(selectedMlId.value)
    powerSupplies.value = data.power_supplies || []
    modelItems.value = (data.models || []).map(m => ({
      ...m,
      voltages: m.voltages.map(v => ({ ...v })),
    }))
  } catch (e) {
    msg.value = 'Ошибка загрузки: ' + (e.response?.data?.error || e.message)
    msgType.value = 'err'
  } finally {
    loading.value = false
  }
}

function clearTouched() {
  Object.keys(touched).forEach(k => delete touched[k])
}

function touchedKey(mi, vi) {
  return `${mi}-${vi}`
}

function onFocus(mi, vi) {
  touched[touchedKey(mi, vi)] = true
  dirty.value = true
}

function onInput(mi, vi, field, event) {
  const raw = event.target.value
  let val
  if (raw === '') {
    val = ''
  } else {
    const num = parseFloat(raw)
    val = isNaN(num) ? raw : num  // keep raw if NaN — user will see the error
  }
  modelItems.value[mi].voltages[vi][field] = val
  dirty.value = true
}

function displayValue(val) {
  if (val === '' || val === null || val === undefined) return ''
  if (typeof val === 'string') return ''
  return val
}

function cellClass(mi, vi, field) {
  const v = modelItems.value[mi].voltages[vi]
  const hasData = FIELDS.some(f => v[f.key])
  if (hasData) return 'cell-has-data'
  if (touched[touchedKey(mi, vi)]) return 'cell-touched'
  return 'cell-empty'
}

async function save() {
  saving.value = true
  msg.value = ''

  const rows = []
  for (const m of modelItems.value) {
    for (const v of m.voltages) {
      const row = {
        model_line_item_id: m.id,
        power_supply_id: v.power_supply_id,
      }
      for (const f of FIELDS) {
        const raw = v[f.key]
        row[f.key] = (raw === '' || raw === null || isNaN(raw)) ? 0 : raw
      }
      rows.push(row)
    }
  }

  try {
    const d = await eaApi.saveMatrix({ model_line_id: selectedMlId.value, rows })
    msg.value = `Сохранено: создано ${d.created}, обновлено ${d.updated}, удалено ${d.deleted}`
    msgType.value = 'ok'
    dirty.value = false
    await loadMatrix()
  } catch (e) {
    msg.value = 'Ошибка сохранения: ' + (e.response?.data?.error || e.message)
    msgType.value = 'err'
  } finally {
    saving.value = false
  }
}

async function doExport() {
  try {
    const blob = await eaApi.exportMatrix(selectedMlId.value)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ea_power_supply_${selectedMlId.value}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
    msg.value = 'Экспорт готов'
    msgType.value = 'ok'
  } catch (e) {
    msg.value = 'Ошибка экспорта: ' + (e.response?.data?.error || e.message)
    msgType.value = 'err'
  }
}

async function doImport(event) {
  const file = event.target.files[0]
  if (!file) return
  saving.value = true
  msg.value = ''
  try {
    const d = await eaApi.importMatrix(selectedMlId.value, file)
    msg.value = `Импорт: создано ${d.created}, обновлено ${d.updated}, удалено ${d.deleted}, строк ${d.rows_processed}`
    msgType.value = 'ok'
    await loadMatrix()
  } catch (e) {
    msg.value = 'Ошибка импорта: ' + (e.response?.data?.error || e.message)
    msgType.value = 'err'
  } finally {
    saving.value = false
    event.target.value = ''
  }
}
</script>

<style scoped>
.ea-admin {
  padding: 20px;
  font-family: var(--cat-font, 'Segoe UI', sans-serif);
  color: var(--cat-text, #1f2937);
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.ml-label { font-weight: 600; font-size: 14px; }

.ml-select {
  padding: 6px 10px;
  border: 1px solid var(--cat-border, #d1d5db);
  border-radius: 6px;
  font-size: 14px;
  min-width: 180px;
  background: var(--cat-surface, #fff);
  color: var(--cat-text, #1f2937);
}

.spacer { flex: 1; }
.spinner { font-size: 16px; }

.msg { font-size: 13px; padding: 4px 10px; border-radius: 4px; }
.msg.ok { color: #065f46; background: #d1fae5; }
.msg.err { color: #991b1b; background: #fee2e2; }

.btn {
  padding: 6px 14px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  font-weight: 500;
}
.btn-save { background: #2563eb; color: #fff; }
.btn-save:disabled { opacity: .5; cursor: not-allowed; }
.btn-cancel { background: var(--cat-bg, #f3f4f6); color: var(--cat-text, #1f2937); border: 1px solid var(--cat-border, #d1d5db); }
.btn-export { background: #059669; color: #fff; }
.btn-import { background: #7c3aed; color: #fff; display: inline-flex; align-items: center; }

.placeholder {
  text-align: center;
  color: var(--cat-text-muted, #6b7280);
  padding: 60px 20px;
  font-size: 15px;
}

.table-wrap { overflow-x: auto; }

.matrix {
  border-collapse: collapse;
  width: auto;
  font-size: 13px;
}

.matrix th, .matrix td {
  border: 1px solid var(--cat-border, #e5e7eb);
  padding: 3px 4px;
  text-align: center;
  min-width: 68px;
}

.col-model {
  text-align: left;
  min-width: 170px;
  font-weight: 500;
  position: sticky;
  left: 0;
  background: var(--cat-surface, #fff);
  z-index: 1;
}

.col-ps-header {
  background: #eef2ff;
  font-weight: 600;
  font-size: 12px;
  padding: 5px 3px;
}

.col-sub {
  background: #f8fafc;
  font-weight: 400;
  font-size: 10px;
  color: #64748b;
  min-width: 62px;
  max-width: 72px;
  white-space: nowrap;
}

.matrix input {
  width: 100%;
  border: none;
  padding: 3px 2px;
  font-size: 11px;
  text-align: center;
  background: transparent;
  color: var(--cat-text, #1f2937);
  box-sizing: border-box;
  outline: none;
}

.matrix input:focus {
  background: #fff;
  box-shadow: inset 0 0 0 2px #2563eb;
  border-radius: 2px;
}

.cell-has-data { background: #f0fdf4; }
.cell-touched { background: #fefce8; }
.cell-empty { background: #f9fafb; }

.matrix tbody tr:hover td { filter: brightness(0.97); }
</style>
