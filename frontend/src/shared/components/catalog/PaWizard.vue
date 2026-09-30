<!-- PaWizard.vue — пошаговый мастер подбора пневмопривода.
     Переиспользует движок /selector/pa: справочники (initial-data + options)
     и подбор (selector/search). Результат — серия → типоразмер, клик ведёт
     в конфигуратор (как PaSelectionPage.openProduct). -->
<template>
  <div class="pa-wizard">
    <PageTitle :title="title" :subtitle="subtitle" />

    <div v-if="loading" class="state"><Spinner text="Загрузка…" /></div>

    <template v-else-if="!showResults">
      <!-- индикатор шагов -->
      <div class="steps-bar">
        <span
          v-for="(s, i) in steps" :key="s.key"
          class="step-dot"
          :class="{ active: i === stepIndex, done: i < stepIndex }"
          @click="stepIndex = i"
        >{{ i + 1 }}. {{ s.title }}</span>
      </div>

      <div class="step-card">
        <h3 class="step-title">{{ currentStep.title }}</h3>

        <!-- 1. Конструкция -->
        <div v-if="currentStep.key === 'construction'" class="chips">
          <button
            v-for="c in refs.construction_varieties" :key="c.id"
            class="chip" :class="{ active: form.construction_variety_id === c.id }"
            @click="form.construction_variety_id = c.id"
          >{{ c.name }}</button>
        </div>

        <!-- 1a. Момент -->
        <div v-else-if="currentStep.key === 'torque'" class="field">
          <input v-model.number="form.torque_with_safety" type="number" min="0" step="1"
                 class="num" placeholder="Момент с запасом, Нм" @keyup.enter="next" />
        </div>

        <!-- 2. DA/SR -->
        <div v-else-if="currentStep.key === 'variety'" class="chips">
          <button
            v-for="v in actuatorVarieties" :key="v.id"
            class="chip" :class="{ active: form.actuator_variety_id === v.id }"
            @click="selectVariety(v)"
          >{{ v.name }}</button>
        </div>

        <!-- 3. Положение безопасности (SR) -->
        <div v-else-if="currentStep.key === 'safety'" class="chips">
          <button
            v-for="s in safetyPositions" :key="s.id"
            class="chip" :class="{ active: form.safety_position_id === s.id }"
            @click="form.safety_position_id = s.id"
          >{{ s.name }}</button>
        </div>

        <!-- 4. Давление -->
        <div v-else-if="currentStep.key === 'pressure'" class="chips">
          <button
            v-for="p in pressureOptions" :key="p.id"
            class="chip" :class="{ active: form.air_pressure_id === p.id }"
            @click="form.air_pressure_id = p.id"
          >{{ p.name }}</button>
        </div>

        <!-- 5. Exd / общепром -->
        <div v-else-if="currentStep.key === 'exd'" class="chips">
          <button class="chip" :class="{ active: form.exd_id === null }" @click="form.exd_id = null">Общепром</button>
          <button
            v-for="e in exdOptions" :key="e.id"
            class="chip" :class="{ active: form.exd_id === e.id }"
            @click="form.exd_id = e.id"
          >{{ e.name }}</button>
        </div>

        <!-- 6. Температура -->
        <div v-else-if="currentStep.key === 'temperature'" class="chips">
          <button
            v-for="t in temperatureOptions" :key="t.id"
            class="chip" :class="{ active: form.temp_min === t.id }"
            @click="form.temp_min = t.id"
          >{{ t.name }} и ниже</button>
        </div>

        <!-- 7. Материал корпуса -->
        <div v-else-if="currentStep.key === 'material'" class="chips">
          <button
            v-for="m in materialOptions" :key="m.id"
            class="chip" :class="{ active: form.body_material_id === m.id }"
            @click="form.body_material_id = m.id"
          >{{ m.name }}</button>
        </div>

        <div class="actions">
          <button class="btn-sec" :disabled="stepIndex === 0" @click="prev">← Назад</button>
          <button v-if="stepIndex < steps.length - 1" class="btn-pri" :disabled="!canNext" @click="next">Далее →</button>
          <button v-else class="btn-pri" :disabled="searching" @click="search">{{ searching ? 'Поиск…' : 'Показать результаты' }}</button>
        </div>
      </div>
    </template>

    <!-- Результаты -->
    <section v-else class="results">
      <div class="results-head">
        <h2>Результаты подбора</h2>
        <button class="btn-sec" @click="showResults = false">← К шагам</button>
      </div>
      <div v-if="error" class="err">{{ error }}</div>
      <SelectionResultGrid
        :items="cards"
        :total="cards.length"
        :loading="searching"
        empty-text="Ничего не найдено. Измените критерии."
        @select="onSelectCard"
      />
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageTitle from '@/shared/components/PageTitle.vue'
import Spinner from '@/shared/components/Spinner.vue'
import SelectionResultGrid from '@/shared/components/catalog/SelectionResultGrid.vue'
import { paResultsToCards, buildPaConfigQuery } from '@/shared/utils/paResults'

const props = defineProps({
  api: { type: Object, required: true },
  title: { type: String, default: 'Мастер подбора пневмопривода' },
  subtitle: { type: String, default: 'Ответьте на вопросы — подберём привод по моменту' },
})
const emit = defineEmits(['navigate'])
const router = useRouter()

const loading = ref(true)
const refs = reactive({ construction_varieties: [], air_pressure: [] })
const opts = reactive({ actuator_varieties: [], safety_positions: [], exd_options: [], body_material_options: [], temperature_options: [] })

const form = reactive({
  construction_variety_id: null,
  torque_with_safety: null,
  actuator_variety_id: null,
  actuator_variety_code: null,
  safety_position_id: null,
  air_pressure_id: null,
  exd_id: null,           // null = общепром
  temp_min: null,
  body_material_id: null,
})

const stepIndex = ref(0)
const showResults = ref(false)
const results = ref([])
const searching = ref(false)
const error = ref('')
const cards = computed(() => paResultsToCards(results.value))

const steps = computed(() => {
  const s = [
    { key: 'construction', title: 'Конструкция' },
    { key: 'torque', title: 'Требуемый момент с запасом' },
    { key: 'variety', title: 'Вид привода' },
  ]
  if (form.actuator_variety_code === 'SR') s.push({ key: 'safety', title: 'Положение безопасности' })
  s.push(
    { key: 'pressure', title: 'Давление в пневмосистеме' },
    { key: 'exd', title: 'Взрывозащита' },
    { key: 'temperature', title: 'Температура окружающей среды' },
    { key: 'material', title: 'Материал корпуса' },
  )
  return s
})
const currentStep = computed(() => steps.value[stepIndex.value] || steps.value[0])

const actuatorVarieties = computed(() => opts.actuator_varieties)
const safetyPositions = computed(() => opts.safety_positions)
const exdOptions = computed(() => opts.exd_options)
const materialOptions = computed(() => opts.body_material_options)
const temperatureOptions = computed(() => opts.temperature_options)
const pressureOptions = computed(() =>
  (refs.air_pressure || []).filter(p => [3, 4, 5, 6, 7].includes(p.pressure_bar))
)

function stepAnswered(key) {
  switch (key) {
    case 'construction': return !!form.construction_variety_id
    case 'torque': return form.torque_with_safety != null && form.torque_with_safety > 0
    case 'variety': return !!form.actuator_variety_id
    case 'safety': return !!form.safety_position_id
    case 'pressure': return !!form.air_pressure_id
    case 'exd': return true
    case 'temperature': return form.temp_min != null
    case 'material': return !!form.body_material_id
    default: return true
  }
}
const canNext = computed(() => stepAnswered(currentStep.value.key))

function selectVariety(v) {
  form.actuator_variety_id = v.id
  form.actuator_variety_code = v.code || null
  form.safety_position_id = null
}

function next() {
  if (stepIndex.value < steps.value.length - 1) stepIndex.value++
  else search()
}
function prev() { if (stepIndex.value > 0) stepIndex.value-- }

async function search() {
  searching.value = true
  error.value = ''
  results.value = []
  try {
    const payload = {
      construction_variety_id: form.construction_variety_id,
      torque_with_safety: form.torque_with_safety,
      actuator_variety_id: form.actuator_variety_id,
      actuator_variety_code: form.actuator_variety_code,
      safety_position_id: form.safety_position_id || undefined,
      air_pressure_id: form.air_pressure_id,
      exd_id: form.exd_id || undefined,
      temp_min: form.temp_min ?? undefined,
      body_material_id: form.body_material_id || undefined,
    }
    const { data } = await props.api.search(payload)
    if (data.success === false) { error.value = data.error || 'Ошибка подбора'; return }
    results.value = data.search_results || []
    showResults.value = true
  } catch (e) {
    error.value = e?.displayMessage || e?.response?.data?.error || 'Ошибка подбора'
  } finally {
    searching.value = false
  }
}

function openProduct(item, ml, options = {}) {
  if (!item?.model_line_item_id) return
  router.push({ path: '/catalog/pa-actuators', query: buildPaConfigQuery(ml, item, options) })
}

function collectOptions() {
  const o = {}
  if (form.safety_position_id) o.safety_position = form.safety_position_id
  if (form.exd_id) o.exd = form.exd_id
  const mat = materialOptions.value.find(m => m.id === form.body_material_id)
  if (mat) o.body_material = mat.name
  return o
}

function onSelectCard(id) {
  const c = cards.value.find(x => x.id === id)
  if (c) openProduct(c._item, c._ml, collectOptions())
}

onMounted(async () => {
  try {
    const [initR, optR] = await Promise.all([
      props.api.getInitialData(),
      props.api.getActuatorOptions(),
    ])
    refs.construction_varieties = initR.data?.construction_varieties || []
    refs.air_pressure = initR.data?.air_pressure || []
    opts.actuator_varieties = optR.data?.actuator_varieties || []
    opts.safety_positions = optR.data?.safety_positions || []
    opts.exd_options = optR.data?.exd_options || []
    opts.body_material_options = optR.data?.body_material_options || []
    opts.temperature_options = optR.data?.temperature_options || []

    // Дефолты: шестерня-рейка, DA, алюминий
    const rp = refs.construction_varieties.find(c => c.code === 'RACK-PINION' || c.code === 'RP')
      || refs.construction_varieties[0]
    if (rp) form.construction_variety_id = rp.id
    const da = opts.actuator_varieties.find(v => v.code === 'DA')
    if (da) selectVariety(da)
    const alu = opts.body_material_options.find(m => m.name === 'Алюминий')
      || opts.body_material_options[0]
    if (alu) form.body_material_id = alu.id
  } catch (e) {
    console.error('[PaWizard] load failed:', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.pa-wizard { max-width: 1100px; margin: 0 auto; padding: 16px; font-family: var(--cat-font, system-ui, sans-serif); font-size: var(--cat-text-sm, 13px); }
.state { text-align: center; padding: 60px 20px; color: var(--cat-muted, #6b7280); }
.steps-bar { display: flex; flex-wrap: wrap; gap: 6px; margin: 12px 0; }
.step-dot { padding: 3px 10px; border: 1px solid var(--cat-border, #e5e7eb); border-radius: 999px; color: var(--cat-muted, #6b7280); cursor: pointer; }
.step-dot.active { background: var(--cat-primary, #2563eb); color: #fff; border-color: var(--cat-primary, #2563eb); }
.step-dot.done { color: var(--cat-primary, #2563eb); border-color: var(--cat-primary, #2563eb); }
.step-card { background: var(--cat-surface, #fff); border: 1px solid var(--cat-border, #e5e7eb); border-radius: 12px; padding: 20px; margin: 12px 0; }
.step-title { margin: 0 0 14px; font-size: 15px; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chip { padding: 7px 14px; border: 1px solid var(--cat-border, #e5e7eb); border-radius: 999px; background: #fff; color: var(--cat-text, #1f2937); cursor: pointer; }
.chip:hover { border-color: var(--cat-primary, #2563eb); color: var(--cat-primary, #2563eb); }
.chip.active { background: var(--cat-primary, #2563eb); color: #fff; border-color: var(--cat-primary, #2563eb); }
.field { display: flex; }
.num { padding: 8px 12px; border: 1px solid var(--cat-border, #e5e7eb); border-radius: 6px; font-size: 14px; max-width: 240px; }
.actions { display: flex; gap: 10px; margin-top: 18px; }
.btn-pri { padding: 8px 20px; border: none; border-radius: 6px; background: var(--cat-primary, #2563eb); color: #fff; cursor: pointer; }
.btn-pri:disabled { opacity: 0.5; cursor: default; }
.btn-sec { padding: 8px 16px; border: 1px solid var(--cat-border, #e5e7eb); border-radius: 6px; background: #fff; cursor: pointer; }
.btn-sec:disabled { opacity: 0.5; cursor: default; }
.results-head { display: flex; justify-content: space-between; align-items: center; }
.result-group { margin: 16px 0; }
.result-card { border: 1px solid var(--cat-border, #e5e7eb); border-radius: 8px; padding: 12px; margin: 8px 0; cursor: pointer; }
.result-card:hover { border-color: var(--cat-primary, #2563eb); }
.meta { color: var(--cat-muted, #6b7280); font-size: 12px; margin-top: 4px; }
.err { color: #c00; margin: 10px 0; }
.empty { text-align: center; padding: 40px; color: var(--cat-muted, #6b7280); }
</style>
