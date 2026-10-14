<!-- PaSelectionPage.vue — Подбор пневмопривода по моменту (/selector/pa).
     Дизайн фильтров — как в инженерном подборе (EngineerFilterBar: чипы +
     Exd-каскад + климат). Отличие от инженерного: поиск идёт по сериям/корпусам
     (/selector/search/) с переходом в конфигуратор по клику на карточку.
     Локализация: подписи селекторов и опции — с бэка (Accept-Language),
     UI-хром — через t(). Параметры арматуры (тип, DN, PN, …) — необязательны. -->
<template>
  <div class="pa-selector">
    <PageTitle :title="title" />
    <div class="eng-filter-bar">
      <div class="eng-filter-bar__header">
        <span class="eng-filter-bar__title">{{ t('catalog.engineer.filters') }}</span>
        <button class="eng-filter-bar__reset" @click="reset">{{ t('catalog.engineer.reset') }}</button>
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
            <option v-for="v in actuatorOptions.ip_options" :key="v.id" :value="v.id">{{ v.name }}</option>
          </select>
        </div>
        <div class="eng-filter-bar__chip">
          <label class="eng-filter-bar__chip-label">{{ label('body_material') }}</label>
          <select class="eng-filter-bar__chip-select" v-model="form.body_material_id">
            <option value="">{{ t('catalog.engineer.notSpecified') }}</option>
            <option v-for="v in actuatorOptions.body_material_options" :key="v.id" :value="v.id">{{ v.name }}</option>
          </select>
        </div>
        <div class="eng-filter-bar__chip">
          <label class="eng-filter-bar__chip-label">{{ label('coating') }}</label>
          <select class="eng-filter-bar__chip-select" v-model="form.coating_id">
            <option value="">{{ t('catalog.engineer.notSpecified') }}</option>
            <option v-for="v in actuatorOptions.coating_options" :key="v.id" :value="v.id">{{ v.name }}</option>
          </select>
        </div>
        <div class="eng-filter-bar__chip">
          <label class="eng-filter-bar__chip-label">{{ label('manual_override') }}</label>
          <select class="eng-filter-bar__chip-select" v-model="form.manual_override_id">
            <option value="">{{ t('catalog.engineer.notSpecified') }}</option>
            <option v-for="v in actuatorOptions.manual_override_options" :key="v.id" :value="v.id">{{ v.name }}</option>
          </select>
        </div>
      </div>

      <!-- Exd-каскад + климат (как в инженерном подборе) -->
      <div class="eng-filter-bar__special">
        <ExdFilter @update:modelValue="onExdChange" @update:exactId="onExdExact" />
        <ClimateFilter @update:temps="onClimateChange" />
      </div>

      <div class="pa-selector__actions">
        <button class="btn-primary" @click="search" :disabled="searching">
          {{ searching ? t('catalog.common.search') : t('pa.engineer.search') }}
        </button>
      </div>
    </div>

    <div v-if="error" class="error-msg">❌ {{ error }}</div>

    <SelectionResultGrid
      :items="cards"
      :total="cards.length"
      :loading="searching"
      :results-label="t('catalog.common.found')"
      :empty-text="t('catalog.common.nothingFound')"
      @select="onSelectCard"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/shared/api'
import PageTitle from '@/shared/components/PageTitle.vue'
import ExdFilter from '@/shared/components/ExdFilter.vue'
import ClimateFilter from '@/shared/components/ClimateFilter.vue'
import SelectionResultGrid from '@/shared/components/catalog/SelectionResultGrid.vue'
import { paResultsToCards, buildPaConfigQuery } from '@/shared/utils/paResults'
import { useI18n } from '@/shared/i18n'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const labels = ref({})
const refs = ref({
  valve_types: [], dn_varieties: [], pn_varieties: [],
  mounting_plates: [], stem_shapes: [], stem_sizes: [],
  air_pressure: [], model_lines: [], construction_varieties: [],
})
const actuatorOptions = ref({
  actuator_varieties: [], safety_positions: [],
  ip_options: [], exd_options: [], coating_options: [], body_material_options: [], manual_override_options: [],
})

function emptyForm() {
  return {
    valve_type_id: '', dn_id: '', pn_id: '',
    mounting_plate_id: '', stem_shape_id: '', stem_id: '',
    torque_without_safety: null, safety_factor: 1.5,
    model_line_id: '', model_line_item_id: null,
    construction_variety_id: '',
    actuator_variety_id: '', safety_position_id: '',
    air_pressure_id: '', ip_id: '', exd_id: '', exd_id_exact: '',
    coating_id: '', body_material_id: '', manual_override_id: '',
    temp_min: null, temp_max: null,
  }
}
const form = reactive(emptyForm())
const results = ref([])
const error = ref('')
const searching = ref(false)

// Подавление каскадных сбросов watcher'ов при восстановлении из sessionStorage
// (возврат из конфигуратора по кнопке «← К фильтрам подбора»).
let restoring = false

const title = computed(() => t('pa.selector.title'))
const torqueWithSafety = computed(() =>
  (form.torque_without_safety * form.safety_factor).toFixed(1)
)
const filteredStems = computed(() => {
  if (!form.stem_shape_id) return refs.value.stem_sizes
  return refs.value.stem_sizes.filter(s => s.stem_shape_id === form.stem_shape_id)
})
const filteredModelLines = computed(() => {
  if (!form.construction_variety_id) return refs.value.model_lines
  return refs.value.model_lines.filter(
    ml => ml.pneumatic_actuator_construction_variety_id === form.construction_variety_id
  )
})
const actuatorVarieties = computed(() => actuatorOptions.value.actuator_varieties || [])
const safetyPositions = computed(() => actuatorOptions.value.safety_positions || [])
const cards = computed(() => paResultsToCards(results.value, {
  series: t('pa.engineer.card.series'),
  body: t('pa.engineer.card.body'),
  type: t('pa.engineer.card.type'),
  margin: t('pa.engineer.card.margin'),
  nm: t('pa.engineer.card.nm'),
}))

watch(() => form.construction_variety_id, () => {
  if (restoring) return
  form.model_line_id = ''
})
watch(() => form.model_line_id, () => {
  if (restoring) return
  form.actuator_variety_id = ''
  form.safety_position_id = ''
  form.coating_id = ''
  form.body_material_id = ''
  actuatorOptions.value.safety_positions = []
  loadActuatorOptions()
})
watch(() => form.actuator_variety_id, () => {
  if (restoring) return
  form.safety_position_id = ''
  actuatorOptions.value.safety_positions = []
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
    error.value = t('pa.engineer.errorGeneric') + ': ' + (e.displayMessage || e.message)
  }
}

async function loadActuatorOptions() {
  try {
    const params = {}
    if (form.model_line_id) params.model_line_id = form.model_line_id
    if (form.actuator_variety_id) params.actuator_variety_id = form.actuator_variety_id
    const { data } = await api.get('/pneumatic_actuators/engineer/options/', { params })
    actuatorOptions.value = data
    // DA имеет единственное положение безопасности («Оставаться в текущем положении») — автовыбор.
    if (data.safety_positions && data.safety_positions.length === 1) {
      form.safety_position_id = data.safety_positions[0].id
    }
  } catch (e) {
    console.error('loadActuatorOptions failed:', e.displayMessage || e.message)
  }
}

function onStemShapeChange() { form.stem_id = '' }

function onExdChange(ids) {
  if (!ids || !ids.length) form.exd_id = ''
  else if (ids[0] === '_none_' || ids[0] === '_empty_') form.exd_id = ids[0]
  else form.exd_id = ids.join(',')
}

function onExdExact(id) { form.exd_id_exact = id != null ? id : '' }

function onClimateChange(temps) {
  form.temp_min = null
  form.temp_max = null
  if (!temps) return
  if (temps.min_temp != null) form.temp_min = temps.min_temp
  if (temps.max_temp != null) form.temp_max = temps.max_temp
}

async function search() {
  searching.value = true
  error.value = ''
  results.value = []

  // Параметры арматуры (тип, DN, PN, …) — необязательны: их можно не заполнять.
  if (!form.torque_without_safety || form.torque_without_safety <= 0) {
    error.value = t('pa.engineer.errorTorque'); searching.value = false; return
  }
  if (!form.air_pressure_id) {
    error.value = t('pa.engineer.errorPressure'); searching.value = false; return
  }
  if (!form.actuator_variety_id) {
    error.value = t('pa.engineer.errorVariety'); searching.value = false; return
  }
  if (!form.safety_position_id) {
    error.value = t('pa.engineer.errorSafety'); searching.value = false; return
  }

  const varietyObj = actuatorVarieties.value.find(v => v.id === form.actuator_variety_id)
  const actuator_variety_code = varietyObj?.code || 'DA'

  try {
    const payload = {
      ...form,
      actuator_variety_code,
      torque_with_safety: parseFloat(torqueWithSafety.value),
    }
    const { data } = await api.post('/pneumatic_actuators/selector/search/', payload)
    results.value = data.search_results || []
    if (!results.value.length) error.value = t('catalog.common.nothingFound')
  } catch (e) {
    error.value = e.response?.data?.error || e.displayMessage || t('pa.engineer.errorGeneric')
  } finally {
    searching.value = false
  }
}

function openProduct(item, ml, options = {}) {
  if (!item?.model_line_item_id) return
  router.push({ path: '/catalog/pa-actuators', query: buildPaConfigQuery(ml, item, options) })
}

function collectOptions(card) {
  const o = {}
  if (form.safety_position_id) o.safety_position = form.safety_position_id
  if (form.ip_id) o.ip = form.ip_id
  // Exd: в конфигуратор идёт точный вид (или одиночный id старого формата).
  if (form.exd_id_exact) o.exd = form.exd_id_exact
  else if (/^\d+$/.test(String(form.exd_id))) o.exd = form.exd_id
  if (form.manual_override_id) o.manual_override = form.manual_override_id
  // Материал корпуса — по имени (конфигуратор хранит имя), как в мастере.
  const mat = (actuatorOptions.value.body_material_options || []).find(m => m.id === form.body_material_id)
  if (mat) o.body_material = mat.name
  // Покрытие — id конкретного исполнения корпуса (аннотируется бэком в результат).
  const bdId = card?._ml?.body_design_option_id
  if (bdId) o.body_coating = bdId
  // Температура: диапазон из фильтров — конфигуратор выберет подходящий чипс.
  if (form.temp_min != null) o.temp_min = form.temp_min
  if (form.temp_max != null) o.temp_max = form.temp_max
  // Маркер происхождения — по нему конфигуратор показывает кнопку возврата.
  o.origin = 'pa-selector'
  return o
}

function onSelectCard(id) {
  const c = cards.value.find(x => x.id === id)
  if (!c) return
  // Сохраняем состояние фильтров/результатов для кнопки возврата из конфигуратора.
  try {
    sessionStorage.setItem('pa-selector-state', JSON.stringify({
      form: { ...form },
      results: results.value,
    }))
  } catch (e) { /* переполнение хранилища — не критично */ }
  openProduct(c._item, c._ml, collectOptions(c))
}

function reset() {
  Object.assign(form, emptyForm())
  results.value = []
  error.value = ''
  try { sessionStorage.removeItem('pa-selector-state') } catch (e) { /* ignore */ }
}

onMounted(async () => {
  await loadInitialData()
  await loadActuatorOptions()
  // Возврат из конфигуратора (?restore=1): восстанавливаем фильтры и результаты,
  // чтобы не перенастраивать подбор для просмотра другой модели.
  if (route.query.restore === '1') {
    try {
      const raw = sessionStorage.getItem('pa-selector-state')
      if (raw) {
        const s = JSON.parse(raw)
        if (s.form) {
          restoring = true
          Object.assign(form, s.form)
          results.value = s.results || []
          // Watcher'ы (pre-flush) выполнятся до post-flush nextTick — сбросы подавлены.
          await nextTick()
          restoring = false
          await loadActuatorOptions()
        }
      }
    } catch (e) { /* повреждённое состояние — игнорируем */ }
    router.replace({ path: route.path, query: {} })
  }
})
</script>

<style scoped>
.pa-selector { max-width: 1200px; margin: 0 auto; padding: var(--cat-gap-xl, 16px); }
.eng-filter-bar {
  background: var(--cat-surface, #fff);
  border: 1px solid var(--cat-border, #e5e7eb);
  border-radius: var(--cat-radius-lg, 10px);
  padding: 12px 16px;
  margin-bottom: 20px;
}
.eng-filter-bar__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.eng-filter-bar__title { font-size: 13px; font-weight: 600; color: var(--cat-muted, #6b7280); text-transform: uppercase; letter-spacing: .5px; }
.eng-filter-bar__reset { padding: 4px 12px; font-size: 12px; background: var(--cat-bg, #f3f4f6); border: 1px solid var(--cat-border, #d1d5db); border-radius: 4px; cursor: pointer; color: var(--cat-muted, #6b7280); }
.eng-filter-bar__chips { display: flex; flex-wrap: wrap; gap: 8px; align-items: flex-end; margin-bottom: 8px; }
.eng-filter-bar__chip { display: flex; flex-direction: column; gap: 2px; }
.eng-filter-bar__chip-label { font-size: 11px; color: var(--cat-muted, #9ca3af); padding-left: 2px; }
.eng-filter-bar__chip-select, .eng-filter-bar__chip-input { padding: 6px 10px; font-size: 13px; color: var(--cat-text, #1f2937); border: 1px solid var(--cat-border, #d1d5db); border-radius: 6px; background: var(--cat-surface, #fff); min-width: 120px; outline: none; }
.eng-filter-bar__chip-single { padding: 6px 10px; font-size: 13px; color: var(--cat-text, #1f2937); background: var(--cat-bg, #f9fafb); border: 1px solid var(--cat-border, #d1d5db); border-radius: 6px; min-width: 120px; display: inline-block; }
.eng-filter-bar__special { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 4px; }
.pa-selector__actions { display: flex; gap: 12px; margin-top: 12px; }
.btn-primary { padding: 10px 28px; background: var(--cat-primary, #2563eb); color: #fff; border: none; border-radius: 6px; font-size: 1rem; cursor: pointer; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.error-msg { background: #fee; color: #c00; padding: 10px 16px; border-radius: 6px; margin: 12px 0; }
@media (max-width: 900px) {
  .eng-filter-bar__special { grid-template-columns: 1fr; }
}
</style>
