<!-- filter-regulator-catalog/components/EngineerCatalog.vue -->
<!-- Инженерный каталог: подбор по параметрам с карточкой товара -->
<template>
  <div class="engineer-page">
    <Breadcrumbs :items="breadcrumbs" />
    <h1 class="page-title">Инженерный каталог</h1>

    <!-- Серия -->
    <div class="chip-group" v-if="modelLines.length">
      <div class="chip-label">Серия</div>
      <div class="chip-row">
        <button
          v-for="ml in modelLines" :key="ml.id"
          class="chip" :class="{ active: selectedML === ml.id }"
          @click="selectSeries(ml.id)"
        >{{ ml.name }}</button>
      </div>
    </div>

    <!-- Фильтры -->
    <div v-if="masterFilterGroups.length" class="filter-chips">
      <div v-for="group in masterFilterGroups" :key="group.key" class="chip-group">
        <div class="chip-label">{{ group.label }}</div>
        <div class="chip-row">
          <button
            v-for="opt in group.options" :key="opt.value || opt.id"
            class="chip"
            :class="{ active: String(activeFilters[group.key]) === String(opt.value ?? opt.id) }"
            @click="toggleFilter(group.key, opt.value ?? opt.id)"
          >
            {{ opt.label || opt.name }}
          </button>
        </div>
      </div>
    </div>

    <!-- Карточка -->
    <div v-if="product" class="product-area">
      <ProductDetail :product="product" :price="product.price" :breadcrumbs="detailBreadcrumbs" />
    </div>
    <div class="empty" v-else-if="selectedML && loaded">
      Модель не найдена — измените фильтры
    </div>
    <div class="loading" v-else-if="selectedML && !loaded">Загрузка...</div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import Breadcrumbs from '@/shared/components/Breadcrumbs.vue'
import ProductDetail from '@/shared/components/ProductDetail.vue'
import frApi from '../api'

const modelLines = ref([])
const selectedML = ref(null)
const masterFilterGroups = ref([])
const activeFilters = reactive({})
const product = ref(null)
const loaded = ref(false)

const breadcrumbs = computed(() => [
  { name: 'Каталог' }, { name: 'Фильтр-регуляторы' }, { name: 'Инженерный каталог' },
])
const detailBreadcrumbs = computed(() => [
  { name: 'Каталог' }, { name: 'Фильтр-регуляторы' },
  { name: 'Инженерный каталог' }, { name: product.value?.model_line?.name || '' },
])

const FILTER_LABELS = {
  filtration_rating_min: 'Тонкость фильтрации, мкм',
  body_material_id: 'Материал корпуса',
  flow_rate_min: 'Расход, л/мин',
  thread_id: 'Резьба портов',
}

onMounted(async () => {
  try {
    const r = await frApi.list({ limit: 1000 })
    const items = r.data?.data || []
    const mlMap = {}
    for (const item of items) {
      const ml = item.model_line
      if (ml && !mlMap[ml.id]) mlMap[ml.id] = ml
    }
    modelLines.value = Object.values(mlMap).sort((a, b) => a.name.localeCompare(b.name))
    if (modelLines.value.length) {
      selectedML.value = modelLines.value[0].id
      await initSeries()
    }
  } catch (e) { console.error('Failed to load', e) }
})

function selectSeries(id) {
  if (selectedML.value === id) return
  selectedML.value = id
  for (const k of Object.keys(activeFilters)) delete activeFilters[k]
  product.value = null
  masterFilterGroups.value = []
  initSeries()
}

async function initSeries() {
  if (!selectedML.value) return
  loaded.value = false
  try {
    const r = await frApi.getEngineer(selectedML.value, {})
    const data = r.data
    const groups = []
    for (const [key, options] of Object.entries(data.filters || {})) {
      if (!options || !options.length) continue
      groups.push({ key, label: FILTER_LABELS[key] || key, options })
    }
    masterFilterGroups.value = groups

    // Авто-дефолты
    for (const group of groups) {
      const opts = group.options
      if (!opts.length) continue
      if (group.key === 'filtration_rating_min') {
        const sorted = [...opts].sort((a, b) => (b.value || 0) - (a.value || 0))
        activeFilters[group.key] = sorted[0].value
      } else if (group.key === 'flow_rate_min') {
        const sorted = [...opts].sort((a, b) => (a.value || 0) - (b.value || 0))
        activeFilters[group.key] = sorted[0].value
      }
    }

    await fetchProduct()
  } catch (e) { console.error('Init series error', e) }
  loaded.value = true
}

async function fetchProduct() {
  if (!selectedML.value) return
  try {
    const r = await frApi.getEngineer(selectedML.value, activeFilters)
    product.value = r.data?.items?.[0] || null
  } catch (e) { console.error('Fetch product error', e) }
}

async function toggleFilter(key, value) {
  // Переключаем фильтр
  if (String(activeFilters[key]) === String(value)) {
    delete activeFilters[key]
  } else {
    activeFilters[key] = value
  }

  // Проверяем совместимость остальных фильтров с новым набором
  for (const group of masterFilterGroups.value) {
    if (group.key === key) continue  // только что изменённый пропускаем

    // Запрашиваем доступные значения для этого фильтра при текущих остальных
    const otherFilters = { ...activeFilters }
    delete otherFilters[group.key]
    const r = await frApi.getEngineer(selectedML.value, otherFilters)
    const opts = r.data?.filters?.[group.key] || []

    if (!opts.length) {
      // Вообще нет доступных значений — сбрасываем
      delete activeFilters[group.key]
      continue
    }

    // Проверяем, валидно ли текущее значение
    const curVal = activeFilters[group.key]
    if (curVal !== undefined && curVal !== null) {
      const valid = opts.some(o => String(o.value ?? o.id) === String(curVal))
      if (!valid) {
        // Текущее значение недоступно — берём первое попавшееся
        activeFilters[group.key] = opts[0].value ?? opts[0].id
      }
    }
  }

  await fetchProduct()
}
</script>

<style scoped>
.engineer-page { max-width: 1200px; margin: 0 auto; padding: 16px; }
.page-title { font-size: 28px; font-weight: 700; margin: 8px 0 16px; }
.chip-group { margin-bottom: 12px; }
.chip-label { font-weight: 500; font-size: 13px; margin-bottom: 4px; color: #374151; }
.chip-row { display: flex; flex-wrap: wrap; gap: 4px; }
.chip {
  padding: 4px 12px; font-size: 12px; border: 1px solid #d1d5db;
  border-radius: 16px; background: #fff; cursor: pointer;
  transition: all .12s; white-space: nowrap;
}
.chip:hover { border-color: #2563eb; color: #2563eb; }
.chip.active { background: #2563eb; color: #fff; border-color: #2563eb; }
.filter-chips { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
.product-area { margin-top: 20px; }
.empty, .loading { text-align: center; padding: 60px 20px; color: #9ca3af; font-size: 16px; }
</style>
