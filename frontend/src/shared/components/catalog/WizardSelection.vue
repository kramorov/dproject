<!-- shared/components/catalog/WizardSelection.vue — Мастер подбора -->
<template>
  <div class="wizard-selection">
    <span class="debug-tag" v-if="debug">WizardSelection</span>

    <!-- Загрузка -->
    <div v-if="loadingConfig" class="wizard-loading">Загрузка мастера подбора...</div>

    <!-- Ошибка -->
    <div v-else-if="error" class="wizard-error">
      <h2>Мастер подбора недоступен</h2>
      <p>{{ error }}</p>
    </div>

    <!-- Состояние: Шаги -->
    <template v-else-if="!showResults">
      <PageTitle :title="wizardTitle" />

      <!-- Навигация по шагам (хлебные крошки) -->
      <nav class="wizard-steps-nav">
        <button
          v-for="(s, i) in steps"
          :key="s.step_number"
          class="wizard-step-chip"
          :class="{ active: currentStep === i, completed: i < currentStep }"
          :disabled="i > currentStep && !canProceed"
          @click="goToStep(i)"
        >
          <span class="step-num">{{ s.step_number }}</span>
          <span class="step-label">{{ s.title }}</span>
        </button>
      </nav>

      <!-- Текущий шаг -->
      <div class="wizard-step" v-if="currentStepData">
        <div class="step-header">
          <h2 class="step-title">{{ currentStepData.title }}</h2>
          <p class="step-desc" v-if="currentStepData.description">{{ currentStepData.description }}</p>
        </div>

        <!-- Фильтры шага -->
        <div class="step-filters">
          <div
            v-for="filter in currentStepData.filters"
            :key="filter.param_name"
            class="wizard-filter-group"
          >
            <h3 class="filter-label">{{ filter.label }}</h3>

            <div v-if="loadingFilter === filter.param_name" class="filter-loading">
              Загрузка вариантов...
            </div>

            <!-- ClimateFilter -->
            <ClimateFilter
              v-else-if="filter.param_name === 'climate'"
              @update:temps="onClimateChange"
            />

            <!-- ExdFilter -->
            <ExdFilter
              v-else-if="filter.param_name === 'exd_id'"
              @update:model-value="onExdChange"
            />

            <!-- Стандартные radio-группы -->
            <div v-else class="filter-options">
              <label
                v-for="opt in filterOptions[filter.param_name] || []"
                :key="opt.id || opt.value"
                class="filter-option"
                :class="{ selected: isOptionSelected(filter.param_name, opt) }"
              >
                <input
                  type="radio"
                  :name="filter.param_name"
                  :value="opt.id || opt.value"
                  :checked="isOptionSelected(filter.param_name, opt)"
                  @change="selectOption(filter.param_name, opt)"
                />
                <div class="option-content">
                  <strong class="option-name">{{ opt.name }}</strong>
                  <span class="option-desc" v-if="opt.description && opt.description !== opt.name">{{ opt.description }}</span>
                </div>
              </label>
              <div v-if="!filterOptions[filter.param_name]?.length" class="filter-empty">
                Нет доступных вариантов
              </div>
            </div>
          </div>
        </div>

        <!-- Кнопки навигации -->
        <div class="wizard-actions">
          <button class="wizard-btn wizard-btn-back" :disabled="currentStep === 0" @click="prevStep">
            ← Назад
          </button>
          <button
            v-if="isLastStep"
            class="wizard-btn wizard-btn-submit"
            :disabled="submitting"
            @click="submitWizard"
          >
            {{ submitting ? 'Подбираем...' : 'Подобрать' }}
          </button>
          <button v-else class="wizard-btn wizard-btn-next" :disabled="!canProceed" @click="nextStep">
            Дальше →
          </button>
        </div>
      </div>
    </template>

    <!-- Состояние: Результаты -->
    <template v-else>
      <div class="wizard-results-header">
        <button class="wizard-btn wizard-btn-back" @click="backToSteps">← К шагам</button>
        <PageTitle :title="`Результаты подбора`" />
      </div>

      <SelectionResultGrid
        :items="results"
        :total="total"
        :loading="loadingResults"
        :results-label="totalLabel"
        :empty-text="'Ничего не найдено. Попробуйте изменить критерии.'"
        mode="page"
        :page="currentPage"
        :total-pages="totalPages"
        @select="id => $emit('select', id)"
        @page-change="goResultsPage"
      />
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { debug } from '@/shared/config'
import api from '@/shared/api'
import PageTitle from '@/shared/components/PageTitle.vue'
import SelectionResultGrid from '@/shared/components/catalog/SelectionResultGrid.vue'
import ClimateFilter from '@/shared/components/ClimateFilter.vue'
import ExdFilter from '@/shared/components/ExdFilter.vue'

const props = defineProps({
  equipmentTypeId: { type: Number, required: true },
  labels: { type: Object, default: () => ({}) },
  pageSize: { type: Number, default: 24 },
})

defineEmits(['select', 'navigate'])

// ── Состояние ──
const loadingConfig = ref(true)
const error = ref('')
const steps = ref([])
const wizardName = ref('')
const currentStep = ref(0)
const selectedValues = ref({})   // { param_name: value }
const filterOptions = ref({})    // { param_name: [{id, name, description}, ...] }
const loadingFilter = ref(null)
const showResults = ref(false)
const results = ref([])
const total = ref(0)
const currentPage = ref(1)
const totalPages = ref(0)
const loadingResults = ref(false)
const submitting = ref(false)

// ── Вычисляемые ──
const wizardTitle = computed(() => props.labels.wizardTitle || wizardName.value || 'Мастер подбора')
const totalLabel = computed(() => props.labels.countLabel || 'найдено')
const currentStepData = computed(() => steps.value[currentStep.value] || null)
const isLastStep = computed(() => currentStep.value >= steps.value.length - 1)
const canProceed = computed(() => {
  const step = currentStepData.value
  if (!step || !step.filters) return false
  if (step.filters.length === 0) return true
  return step.filters.every(filter => {
    // skip filters with no available options (e.g. pipe_diameter for silencers)
    const opts = filterOptions.value[filter.param_name]
    if (opts !== undefined && opts.length === 0) return true
    // exd_id always filled -- defaults to Общепромышленное
    if (filter.param_name === 'exd_id') return true
    // climate requires both temps
    if (filter.param_name === 'climate') {
      return selectedValues.value['work_temp_min'] != null
        && selectedValues.value['work_temp_max'] != null
    }
    const val = selectedValues.value[filter.param_name]
    return val !== undefined && val !== null && val !== ''
  })
})

// ── Загрузка конфигурации ──
onMounted(async () => {
  try {
    const { data } = await api.get(`/core/wizard/${props.equipmentTypeId}/`)
    wizardName.value = data.wizard_name || ''
    steps.value = data.steps || []
    if (steps.value.length > 0) {
      await loadStepFilters(0)
    }
  } catch (e) {
    error.value = e.response?.data?.error || 'Не удалось загрузить мастер подбора'
    console.error('[WizardSelection] Config load error:', e)
  } finally {
    loadingConfig.value = false
  }
})

// ── Загрузка опций фильтров для шага ──
async function loadStepFilters(stepIndex) {
  const step = steps.value[stepIndex]
  if (!step || !step.filters) return

  for (const filter of step.filters) {
    if (filterOptions.value[filter.param_name] != null) continue  // уже загружено

    // ClimateFilter и ExdFilter загружают данные самостоятельно
    if (filter.param_name === 'climate' || filter.param_name === 'exd_id') {
      filterOptions.value[filter.param_name] = []
      continue
    }

    loadingFilter.value = filter.param_name
    try {
      const { data } = await api.post(`/core/wizard/${props.equipmentTypeId}/filter-options/`, {
        param_name: filter.param_name,
        filters_applied: selectedValues.value,
      })
      filterOptions.value[filter.param_name] = data.options || []

      // Авто-выбор значения по умолчанию
      if (filter.default_value !== null && filter.default_value !== undefined) {
        const dv = filter.default_value
        const match = (data.options || []).find(o => String(o.id || o.value) === String(dv))
        if (match) {
          selectedValues.value[filter.param_name] = match.id || match.value
        }
      } else if ((data.options || []).length === 1) {
        selectedValues.value[filter.param_name] = data.options[0].id || data.options[0].value
      }
    } catch (e) {
      console.error(`[WizardSelection] Failed to load options for ${filter.param_name}:`, e)
      filterOptions.value[filter.param_name] = []
    } finally {
      loadingFilter.value = null
    }
  }
}

// ── Climate/Exd handlers ──
function onClimateChange(temps) {
  if (temps) {
    selectedValues.value['work_temp_min'] = temps.min_temp
    selectedValues.value['work_temp_max'] = temps.max_temp
  } else {
    delete selectedValues.value['work_temp_min']
    delete selectedValues.value['work_temp_max']
  }
}

function onExdChange(ids) {
  selectedValues.value['exd_id'] = ids
}

// ── Выбор опции ──
function isOptionSelected(paramName, opt) {
  const val = selectedValues.value[paramName]
  if (val === undefined || val === null) return false
  return String(val) === String(opt.id ?? opt.value)
}

function selectOption(paramName, opt) {
  selectedValues.value[paramName] = opt.id ?? opt.value
}

// ── Навигация по шагам ──
async function goToStep(index) {
  currentStep.value = index
  await loadStepFilters(index)
}

async function nextStep() {
  if (currentStep.value < steps.value.length - 1) {
    currentStep.value++
    await loadStepFilters(currentStep.value)
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

// ── Подбор ──
async function fetchResults(page) {
  loadingResults.value = true
  currentPage.value = page
  try {
    const { data } = await api.post(`/core/wizard/${props.equipmentTypeId}/results/`, {
      filters_applied: selectedValues.value,
      page,
      page_size: props.pageSize,
    })
    results.value = data.items || []
    total.value = data.total || 0
    totalPages.value = data.total_pages || 0
  } catch (e) {
    console.error('[WizardSelection] Results error:', e)
    results.value = []
    total.value = 0
  } finally {
    loadingResults.value = false
  }
}

async function submitWizard() {
  submitting.value = true
  showResults.value = true
  await fetchResults(1)
  submitting.value = false
}

async function goResultsPage(p) {
  await fetchResults(p)
}

function backToSteps() {
  showResults.value = false
}
</script>

<style scoped>
.wizard-selection {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--cat-gap-xl, 20px);
}

.wizard-loading, .wizard-error, .wizard-empty {
  text-align: center;
  padding: 80px 20px;
  color: var(--cat-muted, #6b7280);
  font-size: var(--cat-text-lg, 16px);
}
.wizard-error h2 {
  font-size: var(--cat-text-2xl, 24px);
  color: var(--cat-text, #1f2937);
  margin: 0 0 12px;
}

/* Навигация по шагам */
.wizard-steps-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--cat-border, #e5e7eb);
}
.wizard-step-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 20px;
  border: 1px solid var(--cat-border, #d1d5db);
  background: var(--cat-surface, #fff);
  cursor: pointer;
  font-size: var(--cat-text-sm, 13px);
  color: var(--cat-muted, #6b7280);
  transition: all .15s;
  white-space: nowrap;
}
.wizard-step-chip:hover {
  border-color: var(--cat-primary, #2563eb);
  color: var(--cat-primary, #2563eb);
}
.wizard-step-chip.active {
  background: var(--cat-primary, #2563eb);
  color: #fff;
  border-color: var(--cat-primary, #2563eb);
}
.wizard-step-chip.completed {
  border-color: var(--cat-success, #10b981);
  color: var(--cat-success, #10b981);
}
.step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: currentColor;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
}
.wizard-step-chip.active .step-num { background: rgba(255,255,255,.3); }
.wizard-step-chip.completed .step-num { background: var(--cat-success, #10b981); }

/* Шаг */
.wizard-step {
  animation: fadeIn .2s ease;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

.step-header {
  margin-bottom: 24px;
}
.step-title {
  font-size: var(--cat-text-xl, 20px);
  font-weight: 600;
  color: var(--cat-text, #1f2937);
  margin: 0 0 8px;
}
.step-desc {
  font-size: var(--cat-text-base, 14px);
  color: var(--cat-muted, #6b7280);
  max-width: 640px;
  line-height: 1.5;
}

/* Фильтры */
.step-filters {
  display: flex;
  flex-direction: column;
  gap: 28px;
  margin-bottom: 32px;
}
.wizard-filter-group {
  border: 1px solid var(--cat-border, #e5e7eb);
  border-radius: var(--cat-radius-lg, 8px);
  padding: 16px 20px;
  background: var(--cat-surface, #fff);
}
.filter-label {
  font-size: var(--cat-text-base, 14px);
  font-weight: 600;
  color: var(--cat-text, #1f2937);
  margin: 0 0 12px;
}
.filter-loading {
  font-size: var(--cat-text-sm, 13px);
  color: var(--cat-muted, #9ca3af);
  padding: 8px 0;
}
.filter-options {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.filter-option {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  border-radius: var(--cat-radius-md, 6px);
  cursor: pointer;
  transition: background .12s;
  border: 1px solid transparent;
}
.filter-option:hover {
  background: var(--cat-bg, #f9fafb);
}
.filter-option.selected {
  background: rgba(37, 99, 235, 0.06);
  border-color: var(--cat-primary, #2563eb);
}
.filter-option input[type="radio"] {
  margin-top: 4px;
  accent-color: var(--cat-primary, #2563eb);
  flex-shrink: 0;
}
.option-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.option-name {
  font-size: var(--cat-text-base, 14px);
  font-weight: 500;
  color: var(--cat-text, #1f2937);
}
.option-desc {
  font-size: var(--cat-text-sm, 13px);
  color: var(--cat-muted, #6b7280);
  line-height: 1.4;
}
.filter-empty {
  font-size: var(--cat-text-sm, 13px);
  color: var(--cat-muted-light, #9ca3af);
  padding: 8px 0;
}

/* Кнопки */
.wizard-actions {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--cat-border, #e5e7eb);
}
.wizard-btn {
  padding: 10px 24px;
  border-radius: var(--cat-radius-md, 6px);
  font-size: var(--cat-text-base, 14px);
  font-weight: 500;
  cursor: pointer;
  border: 1px solid var(--cat-border, #d1d5db);
  background: var(--cat-surface, #fff);
  color: var(--cat-text, #1f2937);
  transition: all .15s;
}
.wizard-btn:hover:not(:disabled) {
  border-color: var(--cat-primary, #2563eb);
  color: var(--cat-primary, #2563eb);
}
.wizard-btn:disabled {
  opacity: .4;
  cursor: default;
}
.wizard-btn-next, .wizard-btn-submit {
  background: var(--cat-primary, #2563eb);
  color: #fff;
  border-color: var(--cat-primary, #2563eb);
}
.wizard-btn-next:hover:not(:disabled), .wizard-btn-submit:hover:not(:disabled) {
  background: var(--cat-primary-dark, #1d4ed8);
  border-color: var(--cat-primary-dark, #1d4ed8);
}
.wizard-btn-submit {
  min-width: 140px;
}

/* Результаты */
.wizard-results-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
</style>
