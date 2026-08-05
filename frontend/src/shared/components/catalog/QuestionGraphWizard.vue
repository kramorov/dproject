<template>
  <div class="qg-wizard">
    <!-- Progress -->
    <div v-if="!terminal && node" class="qg-progress">
      {{ pageTitle }} — {{ subPage + 1 }}/{{ totalSubPages }}
    </div>

    <!-- Question -->
    <div v-if="!terminal && node" class="qg-card">
      <h3>{{ pageTitle || node.question }}</h3>
      <p v-if="node.description" class="qg-desc">{{ node.description }}</p>

      <div v-for="pn in currentParamNames" :key="pn" class="qg-options">
        <div class="qg-label">{{ pn }}</div>
        <div v-if="options[pn]">
          <div
            v-for="opt in options[pn]"
            :key="opt.id"
            class="qg-chip"
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
          class="qg-input"
          :placeholder="pn"
          @keyup.enter="advance"
        />
      </div>

      <div class="qg-nav">
        <button v-if="subPage > 0" class="qg-back" @click="goBack">← Назад</button>
        <button class="qg-next" :disabled="!canAdvance" @click="advance">
          {{ isLastSubPage ? 'Далее →' : 'Далее →' }}
        </button>
      </div>
    </div>

    <!-- Results -->
    <div v-if="terminal" class="qg-results">
      <h3>Результаты подбора</h3>
      <p>{{ total }} {{ totalLabel }}</p>
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
import { ref, computed, onMounted } from 'vue'
import api from '@/shared/api'

const props = defineProps({
  graphCode: { type: String, required: true },
  totalLabel: { type: String, default: 'найдено' },
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
  if (!pns.length) return false
  return pns.every(pn => {
    // skip filters with no available options
    const opts = options.value[pn]
    if (opts !== undefined && opts.length === 0) return true
    const v = answers.value[pn]
    return v !== undefined && v !== null && v !== ''
  })
})

onMounted(async () => {
  try {
    const { data } = await api.get(`/core/question-graph/${props.graphCode}/`)
    nodeId.value = data.entry_node_id
    node.value = data.entry_node
    options.value = data.entry_options || {}
    subPage.value = data.sub_page || 0
    totalSubPages.value = data.total_sub_pages || 1
    pageTitle.value = data.page_title || data.entry_node?.question || ''
  } catch (e) {
    error.value = 'Ошибка загрузки: ' + (e.response?.data?.error || e.message)
  }
})

function selectOption(paramName, value) {
  answers.value = { ...answers.value, [paramName]: value }
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
.qg-wizard { max-width: 800px; margin: 0 auto; padding: 1rem; }
.qg-progress { color: #666; margin-bottom: 1rem; font-size: 0.9rem; }
.qg-card { background: #f8f9fa; border-radius: 12px; padding: 2rem; margin-bottom: 1rem; }
.qg-card h3 { margin: 0 0 0.5rem; }
.qg-desc { color: #666; margin-bottom: 1.5rem; }
.qg-options { margin-bottom: 1.5rem; }
.qg-label { font-weight: 600; margin-bottom: 0.5rem; font-size: 0.9rem; color: #555; }
.qg-chip { display: inline-block; padding: 0.5rem 1rem; margin: 0.25rem; border: 2px solid #ddd; border-radius: 8px; cursor: pointer; transition: all 0.15s; user-select: none; }
.qg-chip:hover { border-color: #999; }
.qg-chip.active { border-color: #2563eb; background: #eff6ff; color: #2563eb; }
.qg-input { padding: 0.5rem; border: 2px solid #ddd; border-radius: 8px; width: 200px; font-size: 1rem; }
.qg-input:focus { border-color: #2563eb; outline: none; }
.qg-nav { display: flex; justify-content: space-between; margin-top: 1.5rem; }
.qg-back { padding: 0.75rem 1.5rem; background: #e5e7eb; color: #374151; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; }
.qg-next { padding: 0.75rem 2rem; background: #2563eb; color: #fff; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; }
.qg-next:disabled { background: #ccc; cursor: not-allowed; }
.qg-results h3 { margin: 1rem 0 0.5rem; }
.qg-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.5rem; margin: 1rem 0; }
.qg-item { background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 0.75rem; cursor: pointer; }
.qg-item strong { display: block; }
.qg-pagination { display: flex; gap: 1rem; align-items: center; justify-content: center; margin-top: 1rem; }
.qg-error { background: #fee2e2; border: 1px solid #fca5a5; border-radius: 8px; padding: 1rem; color: #991b1b; margin-top: 1rem; }
</style>
