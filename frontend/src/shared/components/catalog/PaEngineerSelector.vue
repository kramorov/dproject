<!-- shared/components/catalog/PaEngineerSelector.vue -->
<!-- Инженерный подбор пневмопривода: два режима —
     «Обычный» (момент одним числом, PaFilterBar) и
     «Точечный 4/6 точек» (кривая требования по коэффициентам арматуры). -->
<template>
  <div class="pa-engineer">
    <PageTitle :title="title" />

    <div class="pa-engineer__mode">
      <button
        type="button"
        class="mode-btn"
        :class="{ active: mode === 'standard' }"
        @click="switchMode('standard')"
      >{{ t('pa.engineerPointwise.modeStandard') }}</button>
      <button
        type="button"
        class="mode-btn"
        :class="{ active: mode === 'pointwise' }"
        @click="switchMode('pointwise')"
      >{{ t('pa.engineerPointwise.modePointwise') }}</button>
      <button
        type="button"
        class="mode-btn"
        :class="{ active: mode === 'pointwise4' }"
        @click="switchMode('pointwise4')"
      >{{ t('pa.engineerPointwise.modePointwise4') }}</button>
    </div>

    <!-- Режим 1: обычный подбор -->
    <template v-if="mode === 'standard'">
      <PaFilterBar
        ref="filterBar"
        v-model="form"
        :searching="searching"
        @search="onSearch"
        @search-error="onSearchError"
        @reset="onReset"
      />

      <div v-if="error" class="error-msg">❌ {{ error }}</div>

      <div class="pa-engineer__results">
        <div class="pa-engineer__info">
          <span class="srg-spinner" v-if="searching" />
          <span v-else>{{ t('catalog.common.found') }} {{ cards.length }}</span>
        </div>

        <section v-if="exactCards.length" class="pa-engineer__section">
          <h3 v-if="compatibleCards.length" class="pa-engineer__section-title">{{ t('catalog.engineer.exactMatch') }} ({{ exactCards.length }})</h3>
          <div class="pa-engineer__grid">
            <PaEngineerGroupCard
              v-for="g in exactCards"
              :key="g.model_line_item_id || ('b' + g.body_id)"
              :group="g"
              @select="onSelectCard"
            />
          </div>
        </section>

        <section v-if="compatibleCards.length" class="pa-engineer__section">
          <h3 class="pa-engineer__section-title">{{ t('catalog.engineer.meetsConditions') }} ({{ compatibleCards.length }})</h3>
          <div class="pa-engineer__grid">
            <PaEngineerGroupCard
              v-for="g in compatibleCards"
              :key="'c-' + (g.model_line_item_id || ('b' + g.body_id))"
              :group="g"
              @select="onSelectCard"
            />
          </div>
        </section>

        <div v-if="!searching && !cards.length" class="pa-engineer__empty">{{ t('catalog.common.nothingFound') }}</div>
      </div>
    </template>

    <!-- Режим 2: точечный подбор (6 точек) / 3: точечный линейный (4 точки) -->
    <template v-else>
      <div class="pw-form">
        <div class="pw-row" v-if="mode === 'pointwise'">
          <label class="pw-field">
            <span>{{ t('pa.engineerPointwise.characteristics') }}</span>
            <select v-model="pwForm.characteristics_id">
              <option value="">{{ '—' }}</option>
              <option v-for="c in pointwise.characteristics" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </label>
          <label class="pw-field">
            <span>{{ t('pa.engineerPointwise.valveType') }}</span>
            <select v-model="pwForm.valve_type_id">
              <option value="">{{ '—' }}</option>
              <option v-for="v in pointwise.valve_types" :key="v.id" :value="v.id">{{ v.name }}</option>
            </select>
          </label>
          <label class="pw-field">
            <span>{{ t('pa.engineerPointwise.support') }}</span>
            <select v-model="pwForm.support_id">
              <option value="">{{ '—' }}</option>
              <option v-for="s in pointwise.supports" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
          </label>
          <label class="pw-field">
            <span>{{ t('pa.engineerPointwise.seal') }}</span>
            <select v-model="pwForm.seal_type_id">
              <option value="">{{ '—' }}</option>
              <option v-for="s in pointwise.seals" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
          </label>
        </div>

        <div class="pw-row" v-else>
          <label class="pw-field">
            <span>{{ t('pa.engineerPointwise.openStart') }}</span>
            <input type="number" min="0" v-model.number="pwPoints.bto" />
          </label>
          <label class="pw-field">
            <span>{{ t('pa.engineerPointwise.openEnd') }}</span>
            <input type="number" min="0" v-model.number="pwPoints.eto" />
          </label>
          <label class="pw-field">
            <span>{{ t('pa.engineerPointwise.closeStart') }}</span>
            <input type="number" min="0" v-model.number="pwPoints.etc" />
          </label>
          <label class="pw-field">
            <span>{{ t('pa.engineerPointwise.closeEnd') }}</span>
            <input type="number" min="0" v-model.number="pwPoints.btc" />
          </label>
          <label class="pw-field">
            <span>{{ t('pa.engineerPointwise.stroke') }}</span>
            <input type="number" min="0" v-model.number="pwForm.stroke_mm" />
          </label>
          <label class="pw-field">
            <span>{{ t('pa.engineerPointwise.strokeFactor') }}</span>
            <input type="number" min="1" step="0.05" v-model.number="pwForm.stroke_safety_factor" />
          </label>
        </div>

        <div class="pw-row">
          <template v-if="mode === 'pointwise'">
            <label class="pw-field">
              <span>{{ t('pa.engineerPointwise.baseTorque') }}</span>
              <input type="number" min="0" step="1" v-model.number="pwForm.base_torque" />
            </label>
            <label class="pw-field">
              <span>{{ t('pa.engineerPointwise.safetyFactor') }}</span>
              <input type="number" min="1" step="0.1" v-model.number="pwForm.safety_factor" />
            </label>
          </template>
          <label class="pw-field">
            <span>{{ t('pa.engineerPointwise.airPressure') }}</span>
            <select v-model="pwForm.air_pressure_id">
              <option v-for="p in pointwise.air_pressure" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </label>
          <label class="pw-field">
            <span>{{ t('pa.engineerPointwise.actuatorVariety') }}</span>
            <select v-model="pwForm.actuator_variety_code">
              <option v-for="v in pointwise.actuator_varieties" :key="v.id" :value="v.code">{{ v.name }}</option>
            </select>
          </label>
          <label class="pw-field">
            <span>{{ t('pa.engineerPointwise.safetyPosition') }}</span>
            <select v-model="pwForm.safety_position_code">
              <option v-for="s in pointwise.safety_positions" :key="s.code" :value="s.code">{{ s.name }}</option>
            </select>
          </label>
          <label class="pw-field">
            <span>{{ t('pa.engineerPointwise.modelLine') }}</span>
            <select v-model="pwForm.model_line_id">
              <option value="">{{ '—' }}</option>
              <option v-for="ml in pwModelLines" :key="ml.id" :value="ml.id">{{ ml.name }}</option>
            </select>
          </label>
        </div>

        <div class="pw-row">
          <label class="pw-field">
            <span>{{ t('pa.engineerPointwise.exd') }}</span>
            <select v-model="pwForm.exd_id">
              <option value="">{{ '—' }}</option>
              <option value="_none_">{{ t('pa.engineerPointwise.exdNone') }}</option>
              <option v-for="e in pointwise.exd_options" :key="e.id" :value="e.id">{{ e.name || e.code }}</option>
            </select>
          </label>
          <label class="pw-field">
            <span>{{ t('pa.engineerPointwise.tempRange') }}</span>
            <span class="pw-inline">
              <input type="number" v-model.number="pwForm.temp_min" placeholder="min °C" />
              <input type="number" v-model.number="pwForm.temp_max" placeholder="max °C" />
            </span>
          </label>
          <label class="pw-field">
            <span>{{ t('pa.engineerPointwise.coating') }}</span>
            <select v-model="pwForm.coating_id">
              <option value="">{{ '—' }}</option>
              <option v-for="c in pointwise.coating_options" :key="c.id" :value="c.id">{{ c.name || c.code }}</option>
            </select>
          </label>
          <label class="pw-field">
            <span>{{ t('pa.engineerPointwise.bodyMaterial') }}</span>
            <select v-model="pwForm.body_material_id">
              <option value="">{{ '—' }}</option>
              <option v-for="m in pointwise.body_material_options" :key="m.id" :value="m.id">{{ m.name || m.code }}</option>
            </select>
          </label>
          <label class="pw-field">
            <span>{{ t('pa.engineerPointwise.shaftMaterial') }}</span>
            <select v-model="pwForm.shaft_material_id">
              <option value="">{{ '—' }}</option>
              <option v-for="m in pointwise.shaft_material_options" :key="m.id" :value="m.id">{{ m.name || m.code }}</option>
            </select>
          </label>
        </div>

        <button type="button" class="pw-run" :disabled="pwSearching" @click="onPointwiseSearch">
          {{ pwSearching ? '…' : t('pa.engineerPointwise.run') }}
        </button>
      </div>

      <div v-if="pwError" class="error-msg">❌ {{ pwError }}</div>

      <div v-if="pwResult.required_curve" class="pw-curve">
        <h4>{{ t('pa.engineerPointwise.requiredCurve') }} <span v-if="pwUnit">({{ pwUnit }})</span></h4>
        <div class="pw-curve__values">
          <span v-for="(v, code) in pwResult.required_curve" :key="code" class="pw-curve__item">
            {{ code.toUpperCase() }}: {{ Math.round(v * 10) / 10 }}
          </span>
        </div>
      </div>

      <div v-if="pwResult.search_results" class="pw-results">
        <h4>{{ t('pa.engineerPointwise.results') }}</h4>
        <div v-for="g in pwResult.search_results" :key="g.model_line_id" class="pw-group">
          <div class="pw-group__title">
            {{ g.model_line_name || g.model_line_code }}
            <span class="pw-badge" :class="{ exact: g.is_exact }">
              {{ g.is_exact ? t('catalog.engineer.exactMatch') : t('catalog.engineer.meetsConditions') }}
            </span>
          </div>
          <div
            v-for="item in g.model_line_items"
            :key="item.model_line_item_id"
            class="pw-item"
          >
            <span class="pw-item__name">{{ item.model_line_item_code }}</span>
            <span v-if="item.spring_qty_code && item.spring_qty_code !== 'DA'" class="pw-item__spring">
              {{ item.spring_qty_code }}
            </span>
            <span class="pw-item__margin">
              {{ t('pa.engineerPointwise.margin') }}: {{ Math.round(item.margin * 10) / 10 }} {{ pwUnit }}
            </span>
            <span v-if="item.stroke_max" class="pw-item__critical">
              {{ t('pa.engineerPointwise.strokeMax') }}: {{ item.stroke_max }} {{ t('pa.engineerPointwise.mm') }}
            </span>
            <span class="pw-item__critical">
              {{ t('pa.engineerPointwise.critical') }}: {{ item.critical_position }}
            </span>
            <span v-if="item.cards && item.cards.length" class="pw-item__cards">
              <button
                v-for="card in item.cards.slice(0, 3)"
                :key="card.id"
                type="button"
                class="pw-card-link"
                @click="onSelectCard(card.sku_id)"
              >{{ card.code }}</button>
            </span>
          </div>
        </div>
        <div v-if="!pwResult.search_results.length" class="pa-engineer__empty">{{ t('catalog.common.nothingFound') }}</div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/shared/api'
import PageTitle from '@/shared/components/PageTitle.vue'
import PaFilterBar from '@/shared/components/catalog/PaFilterBar.vue'
import PaEngineerGroupCard from '@/shared/components/catalog/PaEngineerGroupCard.vue'
import { useI18n, localizedPath } from '@/shared/i18n'

const { t, locale } = useI18n()
const router = useRouter()

const filterBar = ref(null)

function emptyForm() {
  return {
    valve_type_id: '', dn_id: '', pn_id: '',
    mounting_plate_id: '', stem_shape_id: '', stem_id: '',
    torque_without_safety: null, safety_factor: 1.5,
    model_line_id: '', model_line_item_id: null,
    construction_variety_id: '',
    actuator_variety_id: '', safety_position_id: '',
    air_pressure_id: '', ip_id: '', exd_id: '', exd_id_exact: '',
    coating_id: '', body_material_id: '', shaft_material_id: '', shaft_material_specified_id: '', manual_override_id: '',
    temp_min: null, temp_max: null,
  }
}
const form = reactive(emptyForm())
const results = ref([])
const error = ref('')
const searching = ref(false)

const mode = ref('standard')
const pointwise = reactive({
  characteristics: [], valve_types: [], supports: [], seals: [],
  air_pressure: [], actuator_varieties: [], safety_positions: [], model_lines: [],
  exd_options: [], coating_options: [], body_material_options: [], shaft_material_options: [],
})
const pwForm = reactive({
  characteristics_id: '', valve_type_id: '', support_id: '', seal_type_id: '',
  base_torque: null, safety_factor: 1.5,
  air_pressure_id: '', actuator_variety_code: 'DA', safety_position_code: 'nc',
  model_line_id: '',
  exd_id: '', temp_min: null, temp_max: null,
  coating_id: '', body_material_id: '', shaft_material_id: '',
  stroke_mm: null, stroke_safety_factor: 1.0,
})
const pwPoints = reactive({ bto: null, eto: null, etc: null, btc: null })
const pwUnit = ref('Нм')
const pwResult = reactive({ required_curve: null, search_results: null })
const pwError = ref('')
const pwSearching = ref(false)

// В линейном режиме — только серии LN, в шеститочечном — только ротационные.
const pwModelLines = computed(() => {
  if (mode.value === 'pointwise4') {
    return pointwise.model_lines.filter(ml => ml.construction_variety_code === 'LN')
  }
  if (mode.value === 'pointwise') {
    return pointwise.model_lines.filter(ml => ml.construction_variety_code !== 'LN')
  }
  return pointwise.model_lines
})

const title = computed(() => t('pa.engineer.title'))
const cards = computed(() => results.value)
const exactCards = computed(() => cards.value.filter(c => c.is_exact))
const compatibleCards = computed(() => cards.value.filter(c => !c.is_exact))

async function onSearch(payload) {
  searching.value = true
  error.value = ''
  results.value = []

  try {
    const { data } = await api.post('/pneumatic_actuators/engineer/search/', payload)
    results.value = data.search_results || []
    if (!results.value.length) error.value = t('catalog.common.nothingFound')
  } catch (e) {
    error.value = e.response?.data?.error || e.displayMessage || t('pa.engineer.errorGeneric')
  } finally {
    searching.value = false
  }
}

function onSearchError(msg) {
  error.value = msg
  results.value = []
  searching.value = false
}

function onSelectCard(skuId) {
  if (skuId) router.push(localizedPath(`/sku/${skuId}`, locale.value))
}

function onReset() {
  Object.assign(form, emptyForm())
  results.value = []
  error.value = ''
}

function switchMode(m) {
  mode.value = m
  error.value = ''
  pwError.value = ''
}

async function onPointwiseSearch() {
  pwSearching.value = true
  pwError.value = ''
  pwResult.required_curve = null
  pwResult.search_results = null
  try {
    const payload = mode.value === 'pointwise4'
      ? { ...pwForm, mode: 'four', required_points: { ...pwPoints } }
      : { ...pwForm, mode: 'six' }
    const { data } = await api.post('/pneumatic_actuators/engineer/pointwise-search/', payload)
    pwResult.required_curve = data.required_curve || null
    pwResult.search_results = data.search_results || []
    pwUnit.value = data.unit || 'Нм'
    if (!pwResult.search_results.length) pwError.value = t('catalog.common.nothingFound')
  } catch (e) {
    pwError.value = e.response?.data?.error || e.displayMessage || t('pa.engineer.errorGeneric')
  } finally {
    pwSearching.value = false
  }
}

onMounted(async () => {
  await filterBar.value?.init()
  try {
    const { data } = await api.get('/pneumatic_actuators/engineer/pointwise-initial-data/')
    Object.assign(pointwise, {
      characteristics: data.characteristics || [],
      valve_types: data.valve_types || [],
      supports: data.supports || [],
      seals: data.seals || [],
      air_pressure: data.air_pressure || [],
      actuator_varieties: data.actuator_varieties || [],
      safety_positions: data.safety_positions || [],
      model_lines: data.model_lines || [],
    })
    if (!pwForm.air_pressure_id && pointwise.air_pressure.length) {
      // 6 бар по умолчанию, иначе первое
      pwForm.air_pressure_id = pointwise.air_pressure.find(p => p.code === '6')?.id
        || pointwise.air_pressure[0].id
    }
  } catch (e) {
    pwError.value = e.response?.data?.error || t('pa.engineer.errorGeneric')
  }
  try {
    const { data: optData } = await api.get('/pneumatic_actuators/engineer/options/')
    pointwise.exd_options = optData.exd_options || []
    pointwise.coating_options = optData.coating_options || []
    pointwise.body_material_options = optData.body_material_options || []
    pointwise.shaft_material_options = optData.shaft_material_options || []
  } catch (e) {
    // опции не критичны — форма работает и без них
  }
})
</script>

<style scoped>
.pa-engineer { max-width: 1200px; margin: 0 auto; padding: var(--cat-gap-xl, 16px); }
.error-msg { background: #fee; color: #c00; padding: 10px 16px; border-radius: 6px; margin: 12px 0; }
.pa-engineer__info { font-size: var(--cat-text-base, 14px); color: var(--cat-muted, #6b7280); margin-bottom: 16px; }
.pa-engineer__section { margin-bottom: 32px; }
.pa-engineer__section-title { font-size: var(--cat-text-md, 16px); font-weight: 600; color: var(--cat-text, #1f2937); margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid var(--cat-border, #e5e7eb); }
.pa-engineer__grid { display: flex; flex-direction: column; gap: 12px; }
.pa-engineer__empty { text-align: center; padding: 60px 20px; color: var(--cat-muted-light, #9ca3af); font-size: var(--cat-text-lg, 16px); }
.srg-spinner { display: inline-block; width: 18px; height: 18px; border: 2px solid var(--cat-border, #e5e7eb); border-top-color: var(--cat-primary, #2563eb); border-radius: 50%; animation: srg-spin .6s linear infinite; }
@keyframes srg-spin { to { transform: rotate(360deg); } }

.pa-engineer__mode { display: flex; gap: 8px; margin-bottom: 16px; }
.mode-btn { padding: 8px 16px; border: 1px solid var(--cat-border, #e5e7eb); border-radius: 6px; background: var(--cat-bg, #fff); color: var(--cat-text, #1f2937); cursor: pointer; font-size: var(--cat-text-base, 14px); }
.mode-btn.active { background: var(--cat-primary, #2563eb); border-color: var(--cat-primary, #2563eb); color: #fff; }

.pw-form { display: flex; flex-direction: column; gap: 12px; background: var(--cat-bg, #fff); border: 1px solid var(--cat-border, #e5e7eb); border-radius: 8px; padding: 16px; }
.pw-row { display: flex; flex-wrap: wrap; gap: 12px; }
.pw-field { display: flex; flex-direction: column; gap: 4px; min-width: 160px; flex: 1 1 180px; font-size: var(--cat-text-sm, 13px); color: var(--cat-muted, #6b7280); }
.pw-field select, .pw-field input { padding: 6px 8px; border: 1px solid var(--cat-border, #e5e7eb); border-radius: 6px; font-size: var(--cat-text-base, 14px); }
.pw-run { align-self: flex-start; padding: 8px 24px; background: var(--cat-primary, #2563eb); color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: var(--cat-text-base, 14px); }
.pw-run:disabled { opacity: .6; cursor: default; }
.pw-curve, .pw-results { margin-top: 20px; }
.pw-curve h4, .pw-results h4 { font-size: var(--cat-text-md, 16px); font-weight: 600; margin-bottom: 10px; }
.pw-curve__values { display: flex; flex-wrap: wrap; gap: 8px; }
.pw-curve__item { background: var(--cat-bg-muted, #f3f4f6); border-radius: 6px; padding: 4px 10px; font-size: var(--cat-text-sm, 13px); }
.pw-group { margin-bottom: 16px; }
.pw-group__title { font-weight: 600; margin-bottom: 6px; }
.pw-item { display: flex; gap: 16px; padding: 8px 12px; border: 1px solid var(--cat-border, #e5e7eb); border-radius: 6px; margin-bottom: 6px; align-items: center; flex-wrap: wrap; }
.pw-item__name { font-weight: 500; }
.pw-item__spring { color: var(--cat-primary, #2563eb); }
.pw-item__margin { color: var(--cat-success, #16a34a); }
.pw-item__critical { color: var(--cat-muted, #6b7280); font-size: var(--cat-text-sm, 13px); }
.pw-badge { margin-left: 8px; padding: 2px 8px; border-radius: 10px; font-size: var(--cat-text-sm, 13px); font-weight: 400; background: #fef3c7; color: #92400e; }
.pw-badge.exact { background: #d1fae5; color: #065f46; }
.pw-inline { display: flex; gap: 6px; }
.pw-inline input { flex: 1; min-width: 70px; }
.pw-item__cards { display: flex; gap: 6px; flex-wrap: wrap; }
.pw-card-link { border: 1px solid var(--cat-border, #e5e7eb); background: var(--cat-bg, #fff); border-radius: 4px; padding: 2px 8px; font-size: var(--cat-text-sm, 13px); cursor: pointer; }
.pw-card-link:hover { border-color: var(--cat-primary, #2563eb); color: var(--cat-primary, #2563eb); }
</style>
