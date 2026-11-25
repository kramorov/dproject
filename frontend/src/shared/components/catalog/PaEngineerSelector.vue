<!-- shared/components/catalog/PaEngineerSelector.vue -->
<!-- Инженерный подбор пневмопривода: два режима —
     «Обычный» (момент одним числом, PaFilterBar) и
     «Точечный 4/6 точек» (кривая требования по коэффициентам арматуры). -->
<template>
  <div class="pa-engineer">
    <PageTitle :title="title" />

    <div class="pa-engineer__mode">
      <label class="mode-select">
        <span class="mode-select__label">{{ t('pa.engineerPointwise.modeLabel') }}</span>
        <select v-model="mode" class="mode-select__control">
          <option value="standard">{{ t('pa.engineerPointwise.modeStandard') }}</option>
          <option value="pointwise">{{ t('pa.engineerPointwise.modePointwise') }}</option>
          <option value="pointwise4">{{ t('pa.engineerPointwise.modePointwise4') }}</option>
        </select>
      </label>
      <button type="button" class="mode-help" :aria-label="t('pa.engineerPointwise.help')" @click="helpOpen = true">?</button>
    </div>

    <!-- Общие фильтры — всегда, независимо от режима подбора.
         Строка «модель арматуры» (Тип → Производитель → Серия + таблица коэффициентов)
         теперь внутри PaFilterBar (showValveModel). -->
    <PaFilterBar
      ref="filterBar"
      v-model="form"
      :searching="searching"
      :hide-actions="mode !== 'standard'"
      :show-valve-model="true"
      :valve-producers="pointwise.valve_producers"
      :valve-series="pointwise.valve_series"
      :characteristics="pointwise.characteristics"
      @search="onSearch"
      @search-error="onSearchError"
      @reset="onReset"
    />

    <div v-if="error" class="error-msg">❌ {{ error }}</div>

    <!-- Результаты обычного подбора -->
    <template v-if="mode === 'standard'">
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

    <!-- Доп. поля точечного подбора (6 точек — таблица коэффициентов; 4 точки — ручная кривая) -->
    <template v-else>
      <div class="pw-extra">
        <!-- Таблица коэффициентов вынесена в PaFilterBar (первая строка фильтров). -->
        <div v-if="mode === 'pointwise4'" class="pw-row">
          <label class="pw-field"><span>{{ t('pa.engineerPointwise.openStart') }}</span><input type="number" min="0" v-model.number="pwPoints.bto" /></label>
          <label class="pw-field"><span>{{ t('pa.engineerPointwise.openEnd') }}</span><input type="number" min="0" v-model.number="pwPoints.eto" /></label>
          <label class="pw-field"><span>{{ t('pa.engineerPointwise.closeStart') }}</span><input type="number" min="0" v-model.number="pwPoints.etc" /></label>
          <label class="pw-field"><span>{{ t('pa.engineerPointwise.closeEnd') }}</span><input type="number" min="0" v-model.number="pwPoints.btc" /></label>
          <label class="pw-field"><span>{{ t('pa.engineerPointwise.stroke') }}</span><input type="number" min="0" v-model.number="pwForm.stroke_mm" /></label>
          <label class="pw-field"><span>{{ t('pa.engineerPointwise.strokeFactor') }}</span><input type="number" min="1" step="0.05" v-model.number="pwForm.stroke_safety_factor" /></label>
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

    <div v-if="helpOpen" class="pw-help-backdrop" @click.self="helpOpen = false">
      <div class="pw-help-modal" role="dialog" aria-modal="true">
        <button type="button" class="pw-help-close" @click="helpOpen = false">×</button>
        <h4 class="pw-help-title">{{ helpContent.title }}</h4>
        <div class="pw-help-body">{{ helpContent.body }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
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
    valve_type_id: '', valve_producer_id: '', valve_series_id: '', characteristics_id: '',
    dn_id: '', pn_id: '',
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
  characteristics: [],
  valve_types: [],
  valve_producers: [], valve_series: [],
  air_pressure: [], actuator_varieties: [], safety_positions: [], model_lines: [],
  exd_options: [], coating_options: [], body_material_options: [], shaft_material_options: [],
})
const pwForm = reactive({
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
const helpOpen = ref(false)

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

// Пояснение к выбранному режиму подбора (для кнопки «?»).
const helpContent = computed(() => ({
  title: t(`pa.engineerPointwise.helpTitle.${mode.value}`),
  body: t(`pa.engineerPointwise.helpBody.${mode.value}`),
}))

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
}

// PaFilterBar (режим «Обычный подбор») размонтируется при переключении на
// точечный режим и монтируется заново при возврате. При ремоунте его внутренние
// подписи (labels) и справочники (refs/options) пусты — поэтому переинициализируем.
watch(mode, (m) => {
  error.value = ''
  pwError.value = ''
  if (m === 'standard') filterBar.value?.init()
}, { flush: 'post' })

async function onPointwiseSearch() {
  pwSearching.value = true
  pwError.value = ''
  pwResult.required_curve = null
  pwResult.search_results = null
  try {
    // Общие фильтры берём из PaFilterBar; маппим id → code для DA/SR и НЗ/НО.
    const varietyCode = pointwise.actuator_varieties.find(v => v.id === form.actuator_variety_id)?.code || 'DA'
    const safetyCode = pointwise.safety_positions.find(s => s.id === form.safety_position_id)?.code || 'nc'
    const payload = {
      air_pressure_id: form.air_pressure_id,
      model_line_id: form.model_line_id,
      exd_id: form.exd_id,
      exd_id_exact: form.exd_id_exact,
      temp_min: form.temp_min, temp_max: form.temp_max,
      coating_id: form.coating_id,
      body_material_id: form.body_material_id,
      shaft_material_id: form.shaft_material_id,
      shaft_material_specified_id: form.shaft_material_specified_id,
      actuator_variety_code: varietyCode,
      safety_position_code: safetyCode,
      base_torque: form.torque_without_safety,
      safety_factor: form.safety_factor,
      characteristics_id: form.characteristics_id,
      valve_type_id: form.valve_type_id,
      valve_producer_id: form.valve_producer_id,
      valve_series_id: form.valve_series_id,
      stroke_mm: pwForm.stroke_mm,
      stroke_safety_factor: pwForm.stroke_safety_factor,
      mode: mode.value === 'pointwise4' ? 'four' : 'six',
      // Кривая требований передаётся только в 4-точечном (линейном) режиме;
      // в 6-точечном кривую считает бэкенд по таблице коэффициентов.
      required_points: mode.value === 'pointwise4' ? { ...pwPoints } : null,
    }
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
      valve_producers: data.valve_producers || [],
      valve_series: data.valve_series || [],
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

.pa-engineer__mode { display: flex; align-items: flex-end; gap: 10px; margin-bottom: 16px; }
.mode-select { display: flex; flex-direction: column; gap: 4px; }
.mode-select__label { font-size: var(--cat-text-xs, 12px); color: var(--cat-muted, #6b7280); }
.mode-select__control { padding: 8px 12px; border: 1px solid var(--cat-border, #e5e7eb); border-radius: 6px; background: var(--cat-surface, #fff); color: var(--cat-text, #1f2937); font-size: var(--cat-text-base, 14px); min-width: 260px; }
.mode-help { width: 30px; height: 30px; border-radius: 50%; border: 1px solid var(--cat-border, #d1d5db); background: var(--cat-surface, #fff); color: var(--cat-text, #374151); font-weight: 600; font-size: 16px; cursor: pointer; line-height: 1; }
.mode-help:hover { border-color: var(--cat-primary, #2563eb); color: var(--cat-primary, #2563eb); }

.pw-help-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,.35); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 16px; }
.pw-help-modal { position: relative; max-width: 560px; width: 100%; background: var(--cat-surface, #fff); border-radius: 12px; padding: 20px 24px; box-shadow: 0 12px 40px rgba(0,0,0,.18); }
.pw-help-close { position: absolute; top: 10px; right: 12px; border: none; background: transparent; font-size: 24px; line-height: 1; cursor: pointer; color: var(--cat-muted, #6b7280); }
.pw-help-close:hover { color: var(--cat-text, #1f2937); }
.pw-help-title { margin: 0 0 10px; font-size: var(--cat-text-lg, 16px); font-weight: 600; color: var(--cat-text, #1f2937); }
.pw-help-body { font-size: var(--cat-text-base, 14px); line-height: 1.5; color: var(--cat-text, #374151); white-space: pre-line; }

.pw-extra { display: flex; flex-direction: column; gap: 12px; background: var(--cat-bg, #fff); border: 1px solid var(--cat-border, #e5e7eb); border-radius: 8px; padding: 16px; margin-bottom: 16px; }
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
