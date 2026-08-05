<template>
  <div class="question-graph-demo">
    <h2>{{ graphName || 'Граф вопросов-ответов' }}</h2>

    <!-- Progress -->
    <div v-if="node" class="progress">
      {{ pageTitle }} — {{ subPage + 1 }}/{{ totalSubPages }}
    </div>

    <!-- Current question -->
    <div v-if="!terminal && node" class="question-card">
      <h3>{{ pageTitle || node.question }}</h3>
      <p v-if="node.description" class="desc">{{ node.description }}</p>

      <div v-for="pn in currentParamNames" :key="pn" class="options">
        <div class="option-label">{{ pn }}</div>
        <div v-if="options[pn]">
          <div
            v-for="opt in options[pn]"
            :key="opt.id"
            class="option-chip"
            :class="{ active: answers[pn] === opt.id }"
            @click="selectOption(pn, opt.id)"
          >
            {{ opt.name }}
          </div>
        </div>
        <input
          v-else
          v-model.number="answers[pn]"
          type="text"
          class="text-input"
          :placeholder="pn"
          @keyup.enter="advance"
        />
      </div>

      <div class="nav-row">
        <button v-if="subPage > 0" class="back-btn" @click="goBack">← Назад</button>
        <button class="advance-btn" :disabled="!canAdvance" @click="advance">
          {{ isLastSubPage ? 'Далее →' : 'Далее →' }}
        </button>
      </div>
    </div>

    <!-- Results -->
    <div v-if="terminal" class="results-section">
      <h3>Результаты подбора</h3>
      <p>{{ total }} найдено</p>
      <div class="results-grid">
        <div v-for="item in results" :key="item.id" class="result-card">
          <strong>{{ item.code || item.name }}</strong>
          <span>{{ item.name }}</span>
        </div>
      </div>
      <div class="pagination" v-if="totalPages > 1">
        <button :disabled="page <= 1" @click="loadResults(page - 1)">←</button>
        <span>Стр. {{ page }} из {{ totalPages }}</span>
        <button :disabled="page >= totalPages" @click="loadResults(page + 1)">→</button>
      </div>
    </div>

    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/shared/api'

const GRAPH_CODE = 'pneumatic_fittings'

const graphName = ref('')
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

// History for back-navigation within sub-pages
const history = ref([])

// Results
const results = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 24
const totalPages = computed(() => total.value ? Math.ceil(total.value / pageSize) : 0)

const isLastSubPage = computed(() => subPage.value >= totalSubPages.value - 1)

const currentParamNames = computed(() => {
  if (!node.value) return []
  if (node.value.param_name) return [node.value.param_name]
  if (node.value.param_names) return node.value.param_names
  return []
})

const canAdvance = computed(() => {
  const pns = currentParamNames.value
  if (!pns.length) return false
  return pns.every(pn => answers.value[pn] !== undefined && answers.value[pn] !== null && answers.value[pn] !== '')
})

onMounted(async () => {
  try {
    const { data } = await api.get(`/api/core/question-graph/${GRAPH_CODE}/`)
    graphName.value = data.graph_name
    nodeId.value = data.entry_node_id
    node.value = data.entry_node
    options.value = data.entry_options || {}
    subPage.value = data.sub_page || 0
    totalSubPages.value = data.total_sub_pages || 1
    pageTitle.value = data.page_title || data.entry_node?.question || ''
  } catch (e) {
    error.value = 'Ошибка загрузки графа: ' + (e.response?.data?.error || e.message)
  }
})

function selectOption(paramName, value) {
  answers.value = { ...answers.value, [paramName]: value }
}

async function advance() {
  if (!nodeId.value) return

  try {
    history.value.push({
      nodeId: nodeId.value,
      answers: { ...answers.value },
      subPage: subPage.value,
    })

    const { data } = await api.post(`/api/core/question-graph/${GRAPH_CODE}/advance/`, {
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
      nodeId.value = data.node_id
      node.value = data.node
      options.value = data.options || {}
      filtersApplied.value = data.filters_applied
      subPage.value = data.sub_page || 0
      totalSubPages.value = data.total_sub_pages || 1
      pageTitle.value = data.page_title || data.node?.question || ''
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
    const { data } = await api.post(`/api/core/question-graph/${GRAPH_CODE}/results/`, {
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
.question-graph-demo { max-width: 800px; margin: 2rem auto; padding: 0 1rem; font-family: system-ui, sans-serif; }
.progress { color: #666; margin-bottom: 1rem; font-size: 0.9rem; }
.question-card { background: #f8f9fa; border-radius: 12px; padding: 2rem; margin-bottom: 1rem; }
.question-card h3 { margin: 0 0 0.5rem; }
.desc { color: #666; margin-bottom: 1.5rem; }
.options { margin-bottom: 1.5rem; }
.option-label { font-weight: 600; margin-bottom: 0.5rem; font-size: 0.9rem; color: #555; }
.option-chip { display: inline-block; padding: 0.5rem 1rem; margin: 0.25rem; border: 2px solid #ddd; border-radius: 8px; cursor: pointer; transition: all 0.15s; user-select: none; }
.option-chip:hover { border-color: #999; }
.option-chip.active { border-color: #2563eb; background: #eff6ff; color: #2563eb; }
.text-input { padding: 0.5rem; border: 2px solid #ddd; border-radius: 8px; width: 200px; font-size: 1rem; }
.text-input:focus { border-color: #2563eb; outline: none; }
.nav-row { display: flex; justify-content: space-between; margin-top: 1.5rem; }
.back-btn { padding: 0.75rem 1.5rem; background: #e5e7eb; color: #374151; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; }
.advance-btn { padding: 0.75rem 2rem; background: #2563eb; color: #fff; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; }
.advance-btn:disabled { background: #ccc; cursor: not-allowed; }
.results-section { margin-top: 1rem; }
.results-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.5rem; margin: 1rem 0; }
.result-card { background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 0.75rem; }
.result-card strong { display: block; }
.pagination { display: flex; gap: 1rem; align-items: center; justify-content: center; margin-top: 1rem; }
.error { background: #fee2e2; border: 1px solid #fca5a5; border-radius: 8px; padding: 1rem; color: #991b1b; }
</style>
