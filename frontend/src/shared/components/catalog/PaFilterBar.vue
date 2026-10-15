<!-- shared/components/catalog/PaFilterBar.vue -->
<!-- Переиспользуемая панель фильтров подбора ПП по моменту.
     Используется на /selector/pa (PaSelectionPage) и в инженерном подборе
     /catalog/pa-actuators?mode=engineer (PaEngineerSelector). Стили — общие,
     scoped внутри этого компонента (не дублируются в страницах). -->
<template>
  <div class="eng-filter-bar">
    <div class="eng-filter-bar__header">
      <span class="eng-filter-bar__title">{{ t('catalog.engineer.filters') }}</span>
      <button class="eng-filter-bar__reset" @click="onReset">{{ t('catalog.engineer.reset') }}</button>
    </div>

    <!-- Параметры арматуры (необязательны) -->
    <div class="eng-filter-bar__chips">
      <div class="eng-filter-bar__chip">
        <label class="eng-filter-bar__chip-label">{{ label('valve_type') }}</label>
        <select class="eng-filter-bar__chip-select" v-model="form.valve_type_id">
          <option value="">{{ t('catalog.engineer.notSpecified') }}</option>
          <option v-for="v in refs.valve_types" :key="v.id" :value="v.id">{{ v.name }}</option>
        </select>
      </div>
      <div class="eng-filter-bar__chip">
        <label class="eng-filter-bar__chip-label">{{ label('dn') }}</label>
        <select class="eng-filter-bar__chip-select" v-model="form.dn_id">
          <option value="">{{ t('catalog.engineer.notSpecified') }}</option>
          <option v-for="v in refs.dn_varieties" :key="v.id" :value="v.id">{{ v.name }}</option>
        </select>
      </div>
      <div class="eng-filter-bar__chip">
        <label class="eng-filter-bar__chip-label">{{ label('pn') }}</label>
        <select class="eng-filter-bar__chip-select" v-model="form.pn_id">
          <option value="">{{ t('catalog.engineer.notSpecified') }}</option>
          <option v-for="v in refs.pn_varieties" :key="v.id" :value="v.id">{{ v.name }}</option>
        </select>
      </div>
      <div class="eng-filter-bar__chip">
        <label class="eng-filter-bar__chip-label">{{ label('mounting_plate') }}</label>
        <select class="eng-filter-bar__chip-select" v-model="form.mounting_plate_id">
          <option value="">{{ t('catalog.engineer.notSpecified') }}</option>
          <option v-for="v in refs.mounting_plates" :key="v.id" :value="v.id">{{ v.name }}</option>
        </select>
      </div>
      <div class="eng-filter-bar__chip">
        <label class="eng-filter-bar__chip-label">{{ label('stem_shape') }}</label>
        <select class="eng-filter-bar__chip-select" v-model="form.stem_shape_id" @change="onStemShapeChange">
          <option value="">{{ t('catalog.engineer.notSpecified') }}</option>
          <option v-for="v in refs.stem_shapes" :key="v.id" :value="v.id">{{ v.name }}</option>
        </select>
      </div>
      <div class="eng-filter-bar__chip">
        <label class="eng-filter-bar__chip-label">{{ label('stem') }}</label>
        <select class="eng-filter-bar__chip-select" v-model="form.stem_id">
          <option value="">{{ t('catalog.engineer.notSpecified') }}</option>
          <option v-for="v in filteredStems" :key="v.id" :value="v.id">{{ v.name }}</option>
        </select>
      </div>
    </div>

    <!-- Расчёт момента -->
    <div class="eng-filter-bar__chips">
      <div class="eng-filter-bar__chip">
        <label class="eng-filter-bar__chip-label">{{ label('torque_without_safety') }}</label>
        <input type="number" min="0" step="1" class="eng-filter-bar__chip-input" v-model.number="form.torque_without_safety" />
      </div>
      <div class="eng-filter-bar__chip">
        <label class="eng-filter-bar__chip-label">{{ label('safety_factor') }}</label>
        <input type="number" min="1.0" step="0.1" class="eng-filter-bar__chip-input" v-model.number="form.safety_factor" />
      </div>
      <div class="eng-filter-bar__chip">
        <label class="eng-filter-bar__chip-label">{{ label('torque_with_safety') }}</label>
        <span class="eng-filter-bar__chip-single">{{ torqueWithSafety }}</span>
      </div>
    </div>

    <!-- Требования к приводу -->
    <div class="eng-filter-bar__chips">
      <div class="eng-filter-bar__chip">
        <label class="eng-filter-bar__chip-label">{{ label('model_line') }}</label>
        <select class="eng-filter-bar__chip-select" v-model="form.model_line_id">
          <option value="">{{ t('catalog.engineer.notSpecified') }}</option>
          <option v-for="v in filteredModelLines" :key="v.id" :value="v.id">{{ v.name }}</option>
        </select>
      </div>
      <div class="eng-filter-bar__chip">
        <label class="eng-filter-bar__chip-label">{{ label('actuator_variety') }}</label>
        <select class="eng-filter-bar__chip-select" v-model="form.actuator_variety_id">
          <option value="">{{ t('catalog.engineer.notSpecified') }}</option>
          <option v-for="v in actuatorVarieties" :key="v.id" :value="v.id">{{ v.name }}</option>
        </select>
      </div>
      <div class="eng-filter-bar__chip">
        <label class="eng-filter-bar__chip-label">{{ t('pa.filter.construction') }}</label>
        <select class="eng-filter-bar__chip-select" v-model="form.construction_variety_id">
          <option value="">{{ t('catalog.engineer.notSpecified') }}</option>
          <option v-for="v in refs.construction_varieties" :key="v.id" :value="v.id">{{ v.name }}</option>
        </select>
      </div>
      <div class="eng-filter-bar__chip">
        <label class="eng-filter-bar__chip-label">{{ label('safety_position') }}</label>
        <select class="eng-filter-bar__chip-select" v-model="form.safety_position_id">
          <option value="">{{ t('catalog.engineer.notSpecified') }}</option>
          <option v-for="v in safetyPositions" :key="v.id" :value="v.id">{{ v.name }}</option>
        </select>
      </div>
      <div class="eng-filter-bar__chip">
        <label class="eng-filter-bar__chip-label">{{ label('air_pressure') }}</label>
        <select class="eng-filter-bar__chip-select" v-model="form.air_pressure_id">
          <option value="">{{ t('catalog.engineer.notSpecified') }}</option>
          <option v-for="v in refs.air_pressure" :key="v.id" :value="v.id" :disabled="v.code === 'spring'">{{ v.name }}</option>
        </select>
      </div>
    </div>

    <!-- Доп. опции -->
    <div class="eng-filter-bar__chips">
      <div class="eng-filter-bar__chip">
        <label class="eng-filter-bar__chip-label">{{ label('ip') }}</label>
        <select class="eng-filter-bar__chip-select" v-model="form.ip_id">
          <option value="">{{ t('catalog.engineer.notSpecified') }}</option>
          <option v-for="v in options.ip_options" :key="v.id" :value="v.id">{{ v.name }}</option>
        </select>
      </div>
      <div class="eng-filter-bar__chip">
        <label class="eng-filter-bar__chip-label">{{ label('body_material') }}</label>
        <select class="eng-filter-bar__chip-select" v-model="form.body_material_id">
          <option value="">{{ t('catalog.engineer.notSpecified') }}</option>
          <option v-for="v in options.body_material_options" :key="v.id" :value="v.id">{{ v.name }}</option>
        </select>
      </div>
      <div class="eng-filter-bar__chip">
        <label class="eng-filter-bar__chip-label">{{ label('coating') }}</label>
        <select class="eng-filter-bar__chip-select" v-model="form.coating_id">
          <option value="">{{ t('catalog.engineer.notSpecified') }}</option>
          <option v-for="v in options.coating_options" :key="v.id" :value="v.id">{{ v.name }}</option>
        </select>
      </div>
      <div class="eng-filter-bar__chip">
        <label class="eng-filter-bar__chip-label">{{ label('manual_override') }}</label>
        <select class="eng-filter-bar__chip-select" v-model="form.manual_override_id">
          <option value="">{{ t('catalog.engineer.notSpecified') }}</option>
          <option v-for="v in options.manual_override_options" :key="v.id" :value="v.id">{{ v.name }}</option>
        </select>
      </div>
    </div>

    <!-- Exd-каскад + климат (как в инженерном подборе) -->
    <div class="eng-filter-bar__special">
      <ExdFilter @update:modelValue="onExdChange" @update:exactId="onExdExact" />
      <ClimateFilter @update:temps="onClimateChange" />
    </div>

    <div class="eng-filter-bar__actions">
      <button class="btn-primary" @click="onSearch" :disabled="searching">
        {{ searching ? t('catalog.common.search') : t('pa.engineer.search') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import api from '@/shared/api'
import ExdFilter from '@/shared/components/ExdFilter.vue'
import ClimateFilter from '@/shared/components/ClimateFilter.vue'
import { useI18n } from '@/shared/i18n'

const { t } = useI18n()

defineProps({
  searching: { type: Boolean, default: false },
})

const emit = defineEmits(['search', 'search-error', 'reset'])

// Форма — v-model от страницы (страница владеет состоянием и читает его
// для запроса/карточек/восстановления).
const form = defineModel({ type: Object, required: true })

const labels = ref({})
const refs = ref({
  valve_types: [], dn_varieties: [], pn_varieties: [],
  mounting_plates: [], stem_shapes: [], stem_sizes: [],
  air_pressure: [], model_lines: [], construction_varieties: [],
})
const options = ref({
  actuator_varieties: [], safety_positions: [],
  ip_options: [], exd_options: [], coating_options: [], body_material_options: [], manual_override_options: [],
})

let initialized = false
// Подавление каскадных сбросов watcher'ов при восстановлении из sessionStorage.
let restoring = false

const torqueWithSafety = computed(() =>
  (form.value.torque_without_safety * form.value.safety_factor).toFixed(1)
)
const filteredStems = computed(() => {
  if (!form.value.stem_shape_id) return refs.value.stem_sizes
  return refs.value.stem_sizes.filter(s => s.stem_shape_id === form.value.stem_shape_id)
})
const filteredModelLines = computed(() => {
  if (!form.value.construction_variety_id) return refs.value.model_lines
  return refs.value.model_lines.filter(
    ml => ml.pneumatic_actuator_construction_variety_id === form.value.construction_variety_id
  )
})
const actuatorVarieties = computed(() => options.value.actuator_varieties || [])
const safetyPositions = computed(() => options.value.safety_positions || [])

watch(() => form.value.construction_variety_id, () => {
  if (restoring) return
  form.value.model_line_id = ''
})
watch(() => form.value.model_line_id, () => {
  if (restoring) return
  form.value.actuator_variety_id = ''
  form.value.safety_position_id = ''
  form.value.coating_id = ''
  form.value.body_material_id = ''
  options.value.safety_positions = []
  loadActuatorOptions()
})
watch(() => form.value.actuator_variety_id, () => {
  if (restoring) return
  form.value.safety_position_id = ''
  options.value.safety_positions = []
  loadActuatorOptions()
})

function label(key) {
  return labels.value[key] || key
}

async function loadInitialData() {
  try {
    const { data } = await api.get('/pneumatic_actuators/engineer/initial-data/')
    labels.value = data.labels || {}
    refs.value = { ...refs.value, ...data }
  } catch (e) {
    emit('search-error', t('pa.engineer.errorGeneric') + ': ' + (e.displayMessage || e.message))
  }
}

async function loadActuatorOptions() {
  try {
    const params = {}
    if (form.value.model_line_id) params.model_line_id = form.value.model_line_id
    if (form.value.actuator_variety_id) params.actuator_variety_id = form.value.actuator_variety_id
    const { data } = await api.get('/pneumatic_actuators/engineer/options/', { params })
    options.value = data
    // DA имеет единственное положение безопасности («Оставаться в текущем положении») — автовыбор.
    if (data.safety_positions && data.safety_positions.length === 1) {
      form.value.safety_position_id = data.safety_positions[0].id
    }
  } catch (e) {
    console.error('loadActuatorOptions failed:', e.displayMessage || e.message)
  }
}

async function init() {
  if (initialized) return
  initialized = true
  await loadInitialData()
  await loadActuatorOptions()
}

async function restore(savedForm) {
  restoring = true
  Object.assign(form.value, savedForm)
  // Watcher'ы (pre-flush) выполнятся до post-flush nextTick — сбросы подавлены.
  await nextTick()
  restoring = false
  await loadActuatorOptions()
}

function getBodyMaterialOptions() {
  return options.value.body_material_options || []
}

function onStemShapeChange() { form.value.stem_id = '' }

function onExdChange(ids) {
  if (!ids || !ids.length) form.value.exd_id = ''
  else if (ids[0] === '_none_' || ids[0] === '_empty_') form.value.exd_id = ids[0]
  else form.value.exd_id = ids.join(',')
}

function onExdExact(id) { form.value.exd_id_exact = id != null ? id : '' }

function onClimateChange(temps) {
  form.value.temp_min = null
  form.value.temp_max = null
  if (!temps) return
  if (temps.min_temp != null) form.value.temp_min = temps.min_temp
  if (temps.max_temp != null) form.value.temp_max = temps.max_temp
}

function onSearch() {
  if (!form.value.torque_without_safety || form.value.torque_without_safety <= 0) {
    emit('search-error', t('pa.engineer.errorTorque')); return
  }
  if (!form.value.air_pressure_id) {
    emit('search-error', t('pa.engineer.errorPressure')); return
  }
  if (!form.value.actuator_variety_id) {
    emit('search-error', t('pa.engineer.errorVariety')); return
  }
  if (!form.value.safety_position_id) {
    emit('search-error', t('pa.engineer.errorSafety')); return
  }

  const varietyObj = actuatorVarieties.value.find(v => v.id === form.value.actuator_variety_id)
  const actuator_variety_code = varietyObj?.code || 'DA'

  emit('search', {
    ...form.value,
    actuator_variety_code,
    torque_with_safety: parseFloat(torqueWithSafety.value),
  })
}

function onReset() {
  emit('reset')
}

defineExpose({ init, restore, getBodyMaterialOptions, loadActuatorOptions })
</script>

<style scoped>
.eng-filter-bar {
  background: var(--cat-surface, #fff);
  border: 1px solid var(--cat-border, #e5e7eb);
  border-radius: var(--cat-radius-lg, 10px);
  padding: 12px 16px;
  margin-bottom: 20px;
}
.eng-filter-bar__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.eng-filter-bar__title { font-size: var(--cat-text-sm, 13px); font-weight: 600; color: var(--cat-muted, #6b7280); text-transform: uppercase; letter-spacing: .5px; }
.eng-filter-bar__reset { padding: 4px 12px; font-size: var(--cat-text-xs, 12px); background: var(--cat-bg, #f3f4f6); border: 1px solid var(--cat-border, #d1d5db); border-radius: var(--cat-radius-sm, 4px); cursor: pointer; color: var(--cat-muted, #6b7280); }
.eng-filter-bar__reset:hover { background: var(--cat-border, #e5e7eb); }
.eng-filter-bar__chips { display: flex; flex-wrap: wrap; gap: 8px; align-items: flex-end; margin-bottom: 8px; }
.eng-filter-bar__chip { display: flex; flex-direction: column; gap: 2px; }
.eng-filter-bar__chip-label { font-size: var(--cat-text-xs, 11px); color: var(--cat-muted, #9ca3af); padding-left: 2px; }
.eng-filter-bar__chip-select, .eng-filter-bar__chip-input { padding: 6px 10px; font-size: var(--cat-text-sm, 13px); color: var(--cat-text, #1f2937); border: 1px solid var(--cat-border, #d1d5db); border-radius: var(--cat-radius-md, 6px); background: var(--cat-surface, #fff); min-width: 120px; outline: none; }
.eng-filter-bar__chip-select:focus, .eng-filter-bar__chip-input:focus { border-color: var(--cat-primary, #2563eb); box-shadow: 0 0 0 2px rgba(37, 99, 235, .1); }
.eng-filter-bar__chip-single { padding: 6px 10px; font-size: var(--cat-text-sm, 13px); color: var(--cat-text, #1f2937); background: var(--cat-bg, #f9fafb); border: 1px solid var(--cat-border, #d1d5db); border-radius: var(--cat-radius-md, 6px); min-width: 120px; display: inline-block; }
.eng-filter-bar__special { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 4px; }
.eng-filter-bar__actions { display: flex; gap: 12px; margin-top: 12px; }
.btn-primary { padding: 10px 28px; background: var(--cat-primary, #2563eb); color: #fff; border: none; border-radius: 6px; font-size: 1rem; cursor: pointer; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
@media (max-width: 900px) {
  .eng-filter-bar__special { grid-template-columns: 1fr; }
}
</style>
