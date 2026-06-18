<template>
  <div class="ea-model-admin">
    <!-- Верхняя панель: выбор серии -->
    <div class="toolbar">
      <label class="ml-label">Серия:</label>
      <select v-model="selectedMlId" @change="onSeriesChange" class="ml-select">
        <option :value="null">— выберите серию —</option>
        <option v-for="ml in modelLines" :key="ml.id" :value="ml.id">{{ ml.name }}</option>
      </select>
      <span v-if="loading" class="spinner">⏳</span>
      <span v-if="msg" class="msg" :class="msgType">{{ msg }}</span>
      <div class="spacer"></div>
      <button v-if="selectedItem && dirty" class="btn btn-save" @click="save" :disabled="saving">💾 Сохранить</button>
      <button v-if="selectedItem && dirty" class="btn btn-cancel" @click="loadItem(selectedItem.id)">↩ Отменить</button>
    </div>

    <div v-if="!selectedMlId" class="placeholder">Выберите серию электроприводов.</div>

    <div v-else class="layout">
      <!-- Левая панель: список моделей -->
      <div class="left-panel">
        <div class="panel-header">Модели в серии</div>
        <div v-if="!items.length && !loading" class="empty-list">Нет моделей</div>
        <div class="item-list">
          <div
            v-for="item in items"
            :key="item.id"
            :class="['item-row', { active: selectedItem?.id === item.id }]"
            @click="loadItem(item.id)"
          >
            <div class="item-name">{{ item.name }}</div>
            <div class="item-code">{{ item.code || '—' }}</div>
          </div>
        </div>
      </div>

      <!-- Правая панель: редактор -->
      <div class="right-panel" v-if="selectedItem">
        <div class="panel-header">{{ selectedItem.name }}</div>

        <!-- Базовые поля -->
        <div class="section">
          <h3>Основные параметры</h3>
          <div class="form-grid">
            <div class="form-field">
              <label>Название</label>
              <input v-model="edit.name" class="field-input" />
            </div>
            <div class="form-field">
              <label>Код</label>
              <input v-model="edit.code" class="field-input" />
            </div>
            <div class="form-field">
              <label>Описание</label>
              <textarea v-model="edit.description" class="field-input" rows="2"></textarea>
            </div>
            <div class="form-field">
              <label>Сортировка</label>
              <input v-model.number="edit.sorting_order" type="number" class="field-input" />
            </div>
            <div class="form-field">
              <label>Время открытия, с</label>
              <input v-model.number="edit.time_to_open" type="number" step="0.1" class="field-input" />
            </div>
            <div class="form-field">
              <label>Время закрытия, с</label>
              <input v-model.number="edit.time_to_close" type="number" step="0.1" class="field-input" />
            </div>
            <div class="form-field">
              <label>Скорость, об/мин</label>
              <input v-model.number="edit.rotation_speed" type="number" class="field-input" />
            </div>
            <div class="form-field">
              <label>Мин. момент, Нм</label>
              <input v-model.number="edit.torque_min" type="number" class="field-input" />
            </div>
            <div class="form-field">
              <label>Макс. момент, Нм</label>
              <input v-model.number="edit.torque_max" type="number" class="field-input" />
            </div>
            <div class="form-field">
              <label>Раб. момент, Нм</label>
              <input v-model.number="edit.torque_work" type="number" class="field-input" />
            </div>
          </div>
        </div>

        <!-- Опции напряжения (карточки) -->
        <div class="section">
          <h3>Опции напряжения</h3>
          <div v-if="!edit.power_supply_options?.length" class="empty-list">Нет напряжений для этой модели</div>
          <div v-for="(pso, psi) in edit.power_supply_options" :key="pso.id || psi" class="voltage-card">
            <div class="voltage-card-header">
              <strong>{{ pso.power_supply?.name || '—' }}</strong>
              <span class="voltage-encoding">{{ pso.power_supply?.encoding || '' }}</span>
            </div>
            <div class="form-grid">
              <div class="form-field">
                <label>Ток ном, А</label>
                <input v-model.number="pso.motor_current_rated" type="number" step="0.01" class="field-input" />
              </div>
              <div class="form-field">
                <label>Ток пуск, А</label>
                <input v-model.number="pso.motor_current_starting" type="number" step="0.01" class="field-input" />
              </div>
              <div class="form-field">
                <label>Мощность, кВт</label>
                <input v-model.number="pso.motor_power" type="number" step="0.001" class="field-input" />
              </div>
              <div class="form-field">
                <label>Время откр., с</label>
                <input v-model.number="pso.time_to_open" type="number" step="0.1" class="field-input" />
              </div>
              <div class="form-field">
                <label>Время закр., с</label>
                <input v-model.number="pso.time_to_close" type="number" step="0.1" class="field-input" />
              </div>
              <div class="form-field">
                <label>Мин. усилие, Нм</label>
                <input v-model.number="pso.torque_min" type="number" class="field-input" />
              </div>
              <div class="form-field">
                <label>Макс. усилие, Нм</label>
                <input v-model.number="pso.torque_max" type="number" class="field-input" />
              </div>
            </div>

            <!-- Блоки управления для этого напряжения -->
            <div class="cu-section">
              <div class="cu-header">Блоки управления</div>
              <div v-for="(cu, cui) in pso.control_unit_options" :key="cu.id || cui" class="cu-card">
                <div class="cu-card-row">
                  <span class="cu-name">{{ cu.control_unit?.name || '—' }}</span>
                  <label class="cu-default-label">
                    <input type="checkbox" v-model="cu.is_default" /> По умолчанию
                  </label>
                </div>
                <div class="cu-card-row">
                  <label>Схема (ControlUnitWiring):</label>
                  <select v-model="cu._wiring_id" class="field-select" @change="onWiringChange(cu)">
                    <option :value="null">— не выбрана —</option>
                    <option v-for="w in filteredWirings(cu)" :key="w.id" :value="w.id">{{ w.code }} — {{ w.name }}</option>
                  </select>
                </div>
                <div v-if="cu.control_unit_wiring" class="wiring-preview">
                  <div class="wiring-info">
                    <span class="wiring-code">{{ cu.control_unit_wiring.code }}</span>
                    <span class="wiring-name">{{ cu.control_unit_wiring.name }}</span>
                    <span v-if="cu.control_unit_wiring.signal_profile" class="wiring-profile">
                      🔹 {{ cu.control_unit_wiring.signal_profile.name }}
                    </span>
                  </div>
                  <img
                    v-if="cu.control_unit_wiring.wiring_diagram?.preview_url"
                    :src="cu.control_unit_wiring.wiring_diagram.preview_url"
                    class="wiring-img"
                    @error="e => e.target.style.display='none'"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import eaApi from './api.js'

const modelLines = ref([])
const items = ref([])
const wirings = ref([])
const selectedMlId = ref(null)
const selectedItem = ref(null)
const edit = reactive({ power_supply_options: [] })
const loading = ref(false)
const saving = ref(false)
const msg = ref('')
const msgType = ref('ok')

/** Сравнивает edit и selectedItem, исключая служебные поля _wiring_id */
const dirty = computed(() => {
  if (!selectedItem.value) return false
  const clean = (obj) => {
    if (!obj || typeof obj !== 'object') return obj
    if (Array.isArray(obj)) return obj.map(clean)
    const out = {}
    for (const [k, v] of Object.entries(obj)) {
      if (k.startsWith('_')) continue
      out[k] = clean(v)
    }
    return out
  }
  const a = clean(edit)
  const b = clean(selectedItem.value)
  return JSON.stringify(a) !== JSON.stringify(b)
})

async function fetchModelLines() {
  try {
    modelLines.value = await eaApi.getModelLines()
  } catch (e) { msg.value = 'Ошибка загрузки серий'; msgType.value = 'err' }
}

async function onSeriesChange() {
  items.value = []
  selectedItem.value = null
  Object.assign(edit, { power_supply_options: [] })
  if (!selectedMlId.value) return
  loading.value = true
  try {
    items.value = await eaApi.getItems(selectedMlId.value)
    msg.value = ''
  } catch (e) { msg.value = 'Ошибка загрузки моделей'; msgType.value = 'err' }
  finally { loading.value = false }
}

async function loadItem(id) {
  loading.value = true
  try {
    const data = await eaApi.getItem(id)
    selectedItem.value = JSON.parse(JSON.stringify(data))
    // подготовить edit
    Object.assign(edit, JSON.parse(JSON.stringify(data)))
    // инициализировать _wiring_id для каждого CU
    for (const pso of edit.power_supply_options || []) {
      for (const cu of pso.control_unit_options || []) {
        cu._wiring_id = cu.control_unit_wiring?.id || null
      }
    }
    msg.value = ''
  } catch (e) { msg.value = 'Ошибка загрузки модели'; msgType.value = 'err' }
  finally { loading.value = false }
}

async function save() {
  saving.value = true; msg.value = ''
  const payload = {
    name: edit.name,
    code: edit.code,
    description: edit.description,
    sorting_order: edit.sorting_order,
    time_to_open: edit.time_to_open,
    time_to_close: edit.time_to_close,
    rotation_speed: edit.rotation_speed,
    torque_min: edit.torque_min,
    torque_max: edit.torque_max,
    torque_work: edit.torque_work,
    power_supply_options: (edit.power_supply_options || []).map(pso => ({
      id: pso.id,
      motor_current_rated: pso.motor_current_rated,
      motor_current_starting: pso.motor_current_starting,
      motor_power: pso.motor_power,
      time_to_open: pso.time_to_open,
      time_to_close: pso.time_to_close,
      torque_min: pso.torque_min,
      torque_max: pso.torque_max,
      control_unit_options: (pso.control_unit_options || []).map(cu => ({
        id: cu.id,
        control_unit_wiring_id: cu._wiring_id || null,
        is_default: cu.is_default,
        sorting_order: cu.sorting_order,
      })),
    })),
  }
  try {
    await eaApi.saveItem(selectedItem.value.id, payload)
    msg.value = 'Сохранено'; msgType.value = 'ok'
    await loadItem(selectedItem.value.id)
  } catch (e) { msg.value = 'Ошибка: ' + (e.response?.data?.error || e.message); msgType.value = 'err' }
  finally { saving.value = false }
}

function onWiringChange(cu) {
  if (!cu._wiring_id) {
    cu.control_unit_wiring = null
    return
  }
  const w = wirings.value.find(x => x.id === cu._wiring_id)
  if (w) {
    cu.control_unit_wiring = w
    // если signal_profile у wiring отличается от БУ, можно синхронизировать
  }
}

function filteredWirings(cu) {
  if (!cu.control_unit?.id) return wirings.value
  return wirings.value.filter(w => w.control_unit?.id === cu.control_unit.id)
}

async function fetchWirings() {
  try {
    wirings.value = await eaApi.getWirings()
  } catch (e) { /* не критично */ }
}

fetchModelLines()
fetchWirings()
</script>

<style scoped>
.ea-model-admin {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 14px;
  color: #1a1a2e;
  background: #f0f2f5;
  min-height: 100vh;
}
.toolbar {
  display: flex; align-items: center; gap: 12px; padding: 12px 20px;
  background: #fff; border-bottom: 1px solid #e0e0e0; position: sticky; top: 0; z-index: 10;
}
.ml-label { font-weight: 600; }
.ml-select { padding: 6px 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 14px; min-width: 280px; }
.spacer { flex: 1; }
.spinner { font-size: 20px; }
.msg { font-size: 13px; padding: 4px 10px; border-radius: 4px; }
.msg.ok { background: #e6ffe6; color: #2e7d32; }
.msg.err { background: #ffe6e6; color: #c62828; }
.btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; }
.btn-save { background: #1976d2; color: #fff; }
.btn-save:disabled { opacity: 0.5; cursor: default; }
.btn-cancel { background: #eee; color: #333; }
.placeholder { text-align: center; padding: 60px 20px; color: #999; font-size: 16px; }

.layout { display: flex; height: calc(100vh - 56px); }
.left-panel {
  width: 320px; min-width: 280px; background: #fff; border-right: 1px solid #e0e0e0;
  overflow-y: auto;
}
.right-panel { flex: 1; overflow-y: auto; padding: 16px 24px; }
.panel-header {
  padding: 12px 16px; font-weight: 700; font-size: 15px; background: #fafafa;
  border-bottom: 1px solid #e0e0e0; position: sticky; top: 0; z-index: 2;
}
.item-list { }
.item-row {
  padding: 10px 16px; border-bottom: 1px solid #f0f0f0; cursor: pointer; transition: background 0.15s;
}
.item-row:hover { background: #f5f7fa; }
.item-row.active { background: #e3f2fd; border-left: 3px solid #1976d2; }
.item-name { font-weight: 600; }
.item-code { font-size: 12px; color: #888; }
.empty-list { text-align: center; padding: 20px; color: #aaa; }

.section { margin-bottom: 24px; }
.section h3 { font-size: 15px; margin: 0 0 12px 0; padding-bottom: 4px; border-bottom: 2px solid #1976d2; }

.form-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; }
.form-field { display: flex; flex-direction: column; }
.form-field label { font-size: 12px; color: #666; margin-bottom: 3px; font-weight: 500; }
.field-input, .field-select {
  padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px;
}
.field-input:focus, .field-select:focus { border-color: #1976d2; outline: none; box-shadow: 0 0 0 2px rgba(25,118,210,0.15); }

.voltage-card {
  background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 14px; margin-bottom: 14px;
}
.voltage-card-header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 10px; font-size: 15px;
}
.voltage-encoding { font-size: 12px; background: #eee; padding: 2px 8px; border-radius: 4px; color: #555; }

.cu-section { margin-top: 12px; }
.cu-header { font-weight: 600; font-size: 13px; color: #555; margin-bottom: 8px; }
.cu-card {
  background: #f8f9fb; border: 1px solid #e8e8e8; border-radius: 6px;
  padding: 10px; margin-bottom: 8px;
}
.cu-card-row { display: flex; align-items: center; gap: 12px; margin-bottom: 6px; font-size: 13px; }
.cu-name { font-weight: 600; min-width: 80px; }
.cu-default-label { font-size: 12px; color: #666; display: flex; align-items: center; gap: 4px; }

.wiring-preview { display: flex; align-items: center; gap: 12px; margin-top: 6px; }
.wiring-info { display: flex; flex-direction: column; gap: 2px; font-size: 12px; }
.wiring-code { font-weight: 600; color: #1976d2; }
.wiring-name { color: #555; }
.wiring-profile { color: #888; }
.wiring-img { max-height: 60px; max-width: 120px; border-radius: 4px; border: 1px solid #ddd; }
</style>