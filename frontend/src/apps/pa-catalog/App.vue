<!-- pa-catalog/App.vue — QuickSelect-каталог пневмоприводов -->
<template>
  <div class="app">
    <Breadcrumbs :items="breadcrumbs" @navigate="goToSection" />
    <CatalogActions
      :active="activeTab"
      @section="goToSection"
      @engineer="goToEngineer"
      @quickselect="goToQuickSelect"
      @wizard="goToSection"
      @ai="goToAi"
    />

    <!-- Просмотр по сериям -->
    <div v-if="page === 'section'" class="page-section">
      <PageTitle :title="labels.section.title" :subtitle="labels.section.subtitle" />
      <div class="series-grid" v-if="modelLines.length">
        <div v-for="ml in modelLines" :key="ml.id" class="series-card" @click="selectModelLine(ml)">
          <div class="series-body">
            <h3>Серия {{ ml.name }}</h3>
            <p class="series-desc" v-if="ml.description">{{ ml.description }}</p>
          </div>
        </div>
      </div>
      <Spinner v-else-if="loadingML" />
      <div class="empty" v-else>Нет доступных серий</div>
    </div>

    <!-- Страница серии: модели -->
    <div v-else-if="page === 'brand'" class="page-section">
      <PageTitle :title="'Серия ' + selectedML?.name" :subtitle="selectedML?.description" />
      <div class="series-grid" v-if="items.length">
        <div v-for="item in items" :key="item.id" class="series-card" @click="selectItem(item)">
          <div class="series-body">
            <h3>{{ item.name }}</h3>
            <p class="series-code">{{ item.code }}</p>
          </div>
        </div>
      </div>
      <Spinner v-else-if="loadingItems" />
    </div>

    <!-- Инженерный подбор = PaQuickSelect -->
    <PaQuickSelect
      v-else-if="page === 'engineer'"
      :api="api"
      :labels="{ title: 'Конфигуратор пневмопривода' }"
      @add-to-cart="onAddToCart"
      @navigate="goToSection"
    />

    <!-- Быстрый подбор (selector) -->
    <div v-else-if="page === 'quickselect'" class="page-section">
      <PageTitle title="Быстрый подбор" subtitle="По моменту и давлению" />
      <div class="selector-form">
        <div class="form-row">
          <label>Момент без запаса (Нм)</label>
          <input type="number" v-model.number="selectorForm.torque" min="0" />
        </div>
        <div class="form-row">
          <label>Коэффициент запаса</label>
          <input type="number" v-model.number="selectorForm.safety" min="1" step="0.1" />
        </div>
        <div class="form-row">
          <label>Давление</label>
          <select v-model="selectorForm.pressure_id">
            <option :value="null">— Выберите —</option>
            <option v-for="p in pressures" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
        <div class="form-row">
          <label>Тип привода</label>
          <select v-model="selectorForm.variety">
            <option value="DA">DA</option>
            <option value="SR">SR</option>
          </select>
        </div>
        <button class="btn primary" @click="runSearch" :disabled="searching">Подобрать</button>
      </div>

      <div v-if="searchResults.length" class="results">
        <div v-for="ml in searchResults" :key="ml.model_line_name" class="result-group">
          <h4>{{ ml.model_line_name }}</h4>
          <div v-for="item in ml.model_line_items" :key="item.model_line_item_id" class="result-card" @click="openFromSearch(item)">
            <strong>{{ item.model_line_item_name }}</strong>
            <code>{{ item.model_line_item_code }}</code>
            <span>⭐ {{ item.score?.toFixed(1) }} | Запас: {{ item.spring_margin?.toFixed(0) }} Нм</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Breadcrumbs from '@/shared/components/Breadcrumbs.vue'
import CatalogActions from '@/shared/components/catalog/CatalogActions.vue'
import PageTitle from '@/shared/components/PageTitle.vue'
import Spinner from '@/shared/components/Spinner.vue'
import PaQuickSelect from '@/shared/components/catalog/PaQuickSelect.vue'
import paApi from './api'

const api = paApi

const labels = {
  section: { title:'Пневмоприводы', subtitle:'Выберите серию пневмопривода', breadcrumbName:'Пневмоприводы' },
}

const page = ref('section')
const previousPage = ref('section')
const pageSubtitle = ref('')

const eqLabel = 'Пневмоприводы'
const modeNames = { section:'Просмотр по сериям', brand:'Просмотр по сериям', engineer:'Инженерный подбор', quickselect:'Быстрый подбор' }
const parentModeName = computed(() => modeNames[page.value] || 'Просмотр по сериям')
const breadcrumbs = computed(() => {
  const items = [{ name:'Каталог', to:'/' }, { name:eqLabel }]
  const mode = parentModeName.value
  if (mode) items.push({ name:mode })
  if (pageSubtitle.value) items.push({ name:pageSubtitle.value })
  return items
})

const tabKeys = { section:'section', brand:'section', engineer:'engineer', quickselect:'quickselect' }
const activeTab = computed(() => tabKeys[page.value] || 'section')

// ── Section page ──
const modelLines = ref([])
const loadingML = ref(false)
const selectedML = ref(null)
const items = ref([])
const loadingItems = ref(false)

onMounted(async () => {
  loadingML.value = true
  try {
    const [mlRes, initRes] = await Promise.all([
      api.getModelLines(),
      api.getInitialData ? api.getInitialData() : Promise.resolve({ data: {} }),
    ])
    modelLines.value = mlRes.data || []
    pressures.value = initRes.data?.air_pressure || []
    // Предвыбор давления по умолчанию (6 бар), чтобы запрос подбора был валиден
    if (!selectorForm.value.pressure_id && pressures.value.length) {
      const def = pressures.value.find(p => p.is_default) || pressures.value[0]
      selectorForm.value.pressure_id = def ? def.id : null
    }
  } catch (e) { console.error(e) }
  loadingML.value = false
})

async function selectModelLine(ml) {
  selectedML.value = ml; page.value = 'brand'; loadingItems.value = true
  try { const { data } = await api.getModelLineItems(ml.id); items.value = data || [] } catch (e) { console.error(e) }
  loadingItems.value = false
}

function selectItem(item) {
  // Navigate to engineer tab — PaQuickSelect will load options for this item
  page.value = 'engineer'
}

// ── Quick select ──
const selectorForm = ref({ torque: 500, safety: 1.5, pressure_id: null, variety: 'DA' })
const searchResults = ref([]); const searching = ref(false); const pressures = ref([])

async function runSearch() {
  searching.value = true
  try {
    const { data } = await api.search({
      torque_without_safety: Number(selectorForm.value.torque) || 0,
      safety_factor: Number(selectorForm.value.safety) || 1.5,
      air_pressure_id: selectorForm.value.pressure_id ?? null,
      actuator_variety_code: selectorForm.value.variety || 'DA',
    })
    if (data?.success) {
      searchResults.value = data.search_results || []
    } else {
      console.warn('Поиск не выполнен:', data?.error)
      searchResults.value = []
    }
  } catch (e) { console.error(e); searchResults.value = [] }
  searching.value = false
}

function openFromSearch(item) {
  // Open the selected item in engineer tab
  page.value = 'engineer'
}

// ── Cart ──
async function onAddToCart(payload) {
  try {
    const { data } = await api.createSku(payload)
    alert(`Добавлено в корзину: ${data.code || data.name}`)
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  }
}

// ── Navigation ──
function goToSection() { pageSubtitle.value = ''; previousPage.value = page.value; page.value = 'section' }
function goToEngineer() { previousPage.value = page.value; page.value = 'engineer' }
function goToQuickSelect() { previousPage.value = page.value; page.value = 'quickselect' }
</script>

<style scoped>
.app { max-width: 1200px; margin: 0 auto; padding: 16px; }
.page-section { margin-top: 16px; }
.series-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 16px; }
.series-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; cursor: pointer; transition: box-shadow .15s; }
.series-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,.06); border-color: #2563eb; }
.series-body h3 { font-size: 16px; font-weight: 600; margin: 0 0 4px; }
.series-code { font-size: 13px; color: #6b7280; }
.series-desc { font-size: 13px; color: #9ca3af; margin: 4px 0 0; }
.empty { text-align: center; padding: 60px; color: #9ca3af; }

.selector-form { background: #fafafa; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; margin-top: 16px; }
.form-row { margin-bottom: 12px; }
.form-row label { display: block; font-size: 13px; color: #666; margin-bottom: 4px; }
.form-row select, .form-row input { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 6px; font-size: 14px; }

.btn { padding: 10px 24px; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; }
.btn.primary { background: #2563eb; color: #fff; }
.btn.primary:disabled { opacity: 0.6; cursor: not-allowed; }

.results { margin-top: 16px; }
.result-group { margin-bottom: 16px; }
.result-group h4 { font-size: 15px; color: #374151; margin-bottom: 8px; }
.result-card { background: #f0f4ff; border: 1px solid #c7d2fe; border-radius: 8px; padding: 12px; margin-bottom: 8px; cursor: pointer; display: flex; gap: 16px; align-items: center; font-size: 13px; }
.result-card:hover { border-color: #2563eb; }
</style>
