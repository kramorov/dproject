<template>
  <div class="qg-wizard">
    <div v-if="!terminal && node">
      <!-- Step indicator -->
      <div class="qg-stepper">
        <span class="qg-step-label">{{ pageTitle }}</span>
        <span class="qg-step-counter" v-if="totalSubPages > 1">{{ subPage + 1 }}/{{ totalSubPages }}</span>
      </div>

      <div class="qg-card">
        <p v-if="node.description" class="qg-desc">{{ node.description }}</p>

        <div v-for="pn in currentParamNames" :key="pn" class="qg-filter-group">
          <h3 class="qg-label">{{ filterLabels[pn] || pn }}</h3>

          <!-- Radio options for select lists -->
          <div v-if="options[pn] && options[pn].length > 0" class="filter-options">
            <label
              v-for="opt in options[pn]"
              :key="opt.id"
              class="filter-option"
              :class="{ selected: answers[pn] === opt.id }"
            >
              <input
                type="radio"
                :name="pn"
                :value="opt.id"
                :checked="answers[pn] === opt.id"
                @change="selectOption(pn, opt.id)"
              />
              <div class="option-content">
                <strong class="option-name">{{ opt.name }}</strong>
                <span class="option-desc" v-if="opt.description && opt.description !== opt.name">{{ opt.description }}</span>
              </div>
            </label>
          </div>

          <!-- Empty options -->
          <div v-else-if="options[pn] && options[pn].length === 0" class="filter-empty">
            Нет доступных вариантов
          </div>

          <!-- Text input for numeric/text params -->
          <input
            v-else
            v-model.number="answers[pn]"
            type="text"
            class="qg-input"
            :placeholder="'Введите ' + (filterLabels[pn] || pn)"
            @keyup.enter="advance"
          />
        </div>

        <div class="qg-nav">
          <button v-if="subPage > 0" class="qg-back" @click="goBack">← Назад</button>
          <span v-else />
          <button class="qg-next" :disabled="!canAdvance" @click="advance">
            {{ isLastSubPage ? 'Показать результаты' : 'Далее →' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Results -->
    <div v-if="terminal" class="qg-results">
      <h3>Результаты подбора</h3>
      <p class="qg-count">{{ total }} {{ totalLabel }}</p>
      <div class="qg-grid">
        <div v-for="item in results" :key="item.id" class="qg-item" @click="$emit('select', item.id)">
          <strong>{{ item.code || item.name }}</strong>
          <span>{{ item.name }}</span>
        </div>
      </div>
      <div class="qg-pagination" v-if="totalPages > 1">
        <button :disabled="page <= 1" @click="loadResults(page - 1)">←</button>
        <span>Стр. {{ page }} из {{ totalPages }}</span>
        <button :disabled="page >= totalPages" @click="loadResults(page + 1)">→</button>
      </div>
    </div>

    <div v-if="error" class="qg-error">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import api from '@/shared/api'

const props = defineProps({
  graphCode: { type: String, required: true },
  totalLabel: { type: String, default: 'найдено' },
  filterLabels: { type: Object, default: () => ({}) },
})

defineEmits(['select', 'navigate'])

const node = ref(null)
const nodeId = ref(null)
const options = ref({})
const answers = ref({})
const filtersApplied = ref({})
const terminal = ref(false)
const subPage = ref(0)
const totalSubPages = ref(1)
const pageTitle = ref('')
const error = ref('')

const history = ref([])
const results = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 24
const totalPages = computed(() => total.value ? Math.ceil(total.value / pageSize) : 0)
const isLastSubPage = computed(() => subPage.value >= totalSubPages.value - 1)

const currentParamNames = computed(() => {
  if (!node.value) return []
  const pages = node.value.pages
  if (pages && subPage.value < pages.length) {
    return pages[subPage.value].param_names || []
  }
  if (node.value.param_name) return [node.value.param_name]
  if (node.value.param_names) return node.value.param_names
  return []
})

const canAdvance = computed(() => {
  const pns = currentParamNames.value
  if (!pns.length) return true  // branch/pass-through node — auto-advance
  return pns.every(pn => {
    const opts = options.value[pn]
    if (opts !== undefined && opts.length === 0) return true
    const v = answers.value[pn]
    return v !== undefined && v !== null && v !== ''
  })
})

onMounted(async () => {
  try {
    const { data } = await api.get(`/core/question-graph/${props.graphCode}/`)
    applyGraphConfig(data)
  } catch (e) {
    error.value = 'Ошибка загрузки: ' + (e.response?.data?.error || e.message)
  }
})

function applyGraphConfig(data) {
  nodeId.value = data.entry_node_id
  node.value = data.entry_node
  options.value = data.entry_options || {}
  subPage.value = data.sub_page || 0
  totalSubPages.value = data.total_sub_pages || 1
  pageTitle.value = data.page_title || data.entry_node?.question || ''
  if (data.entry_node?.default_value) {
    node.value = { ...node.value, default_value: data.entry_node.default_value }
  }
  autoApplyDefaults()
  nextTick(() => autoSelectSingle())
}

function selectOption(paramName, value) {
  answers.value = { ...answers.value, [paramName]: value }
}

function autoSelectSingle() {
  let changed = false
  for (const pn of currentParamNames.value) {
    const optList = options.value[pn]
    if (optList && optList.length === 1 && (answers.value[pn] === undefined || answers.value[pn] === null)) {
      selectOption(pn, optList[0].id)
      changed = true
    }
  }
  return changed
}

function autoApplyDefaults() {
  if (!node.value) return
  const defs = node.value.default_value
  if (!defs || !Object.keys(defs).length) return
  for (const [pn, val] of Object.entries(defs)) {
    if (answers.value[pn] === undefined || answers.value[pn] === null) {
      answers.value = { ...answers.value, [pn]: val }
    }
  }
}

async function advance() {
  if (!nodeId.value) return
  try {
    history.value.push({ nodeId: nodeId.value, answers: { ...answers.value }, subPage: subPage.value })
    const { data } = await api.post(`/core/question-graph/${props.graphCode}/advance/`, {
      node_id: nodeId.value,
      answers: answers.value,
      filters_applied: { ...filtersApplied.value },
      sub_page: subPage.value,
    })
    if (data.terminal) {
      terminal.value = true
      filtersApplied.value = data.filters_applied
      await loadResults(1)
    } else {
      applyGraphConfig(data)
      answers.value = {}
    }
  } catch (e) {
    error.value = 'Ошибка: ' + (e.response?.data?.error || e.message)
  }
}

function goBack() {
  const prev = history.value.pop()
  if (!prev) return
  nodeId.value = prev.nodeId
  answers.value = prev.answers
  subPage.value = prev.subPage
}

async function loadResults(p) {
  page.value = p
  try {
    const { data } = await api.post(`/core/question-graph/${props.graphCode}/results/`, {
      filters: filtersApplied.value,
      page: p,
      page_size: pageSize,
    })
    results.value = data.results
    total.value = data.total
  } catch (e) {
    error.value = 'Ошибка поиска: ' + (e.response?.data?.error || e.message)
  }
}
</script>

<style scoped>
.qg-wizard { max-width: 700px; margin: 0 auto; padding: 2rem 1rem; font-family: system-ui, sans-serif; }
.qg-stepper { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.qg-step-label { font-size: 1.1rem; font-weight: 600; color: #1e293b; }
.qg-step-counter { font-size: 0.85rem; color: #94a3b8; }
.qg-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 2rem; }
.qg-desc { color: #64748b; margin-bottom: 1.5rem; line-height: 1.5; }

/* Filter groups — match WizardSelection */
.qg-filter-group {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px 20px;
  background: #fff;
  margin-bottom: 16px;
}
.qg-label { font-size: 14px; font-weight: 600; color: #1f2937; margin: 0 0 12px; }

/* Radio options — same as WizardSelection */
.filter-options { display: flex; flex-direction: column; gap: 4px; }
.filter-option {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 12px 16px; border-radius: 6px; cursor: pointer;
  transition: background .12s; border: 1px solid transparent;
}
.filter-option:hover { background: #f9fafb; }
.filter-option.selected { background: rgba(37, 99, 235, 0.06); border-color: #2563eb; }
.filter-option input[type="radio"] { margin-top: 4px; accent-color: #2563eb; flex-shrink: 0; }
.option-content { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.option-name { font-size: 14px; font-weight: 500; color: #1f2937; }
.option-desc { font-size: 13px; color: #6b7280; line-height: 1.4; }

.qg-input { width: 100%; padding: 0.75rem; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 1rem; }
.qg-input:focus { border-color: #3b82f6; outline: none; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }
.filter-empty { font-size: 13px; color: #9ca3af; padding: 8px 0; }

.qg-nav { display: flex; justify-content: space-between; margin-top: 2rem; }
.qg-back { padding: 0.75rem 1.5rem; background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 0.95rem; cursor: pointer; }
.qg-back:hover { background: #e2e8f0; }
.qg-next { padding: 0.75rem 2rem; background: #2563eb; color: #fff; border: none; border-radius: 8px; font-size: 0.95rem; font-weight: 500; cursor: pointer; }
.qg-next:disabled { background: #cbd5e1; cursor: not-allowed; }

.qg-results { margin-top: 1rem; }
.qg-results h3 { margin-bottom: 0.5rem; }
.qg-count { color: #64748b; margin-bottom: 1rem; }
.qg-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.5rem; margin: 1rem 0; }
.qg-item { background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 0.75rem; cursor: pointer; }
.qg-item strong { display: block; }
.qg-pagination { display: flex; gap: 1rem; align-items: center; justify-content: center; margin-top: 1rem; }
.qg-error { background: #fee2e2; border: 1px solid #fca5a5; border-radius: 8px; padding: 1rem; color: #991b1b; margin-top: 1rem; }
</style>
