<!-- limit-switch-catalog/components/GearboxList.vue -->
<template>
  <div class="list-page">
    <h1 class="page-title">Блоки концевых выключателей</h1>

    <div class="filters-bar">
      <input v-model="searchText" placeholder="Поиск..." class="filter-input" @input="debouncedFetch" />
      <select v-model="activeFilters.model_line_id" class="filter-select" @change="fetchData">
        <option value="">Все серии</option>
        <option v-for="o in filterOptions.model_line_id || []" :key="o.id" :value="o.id">{{ o.name }}</option>
      </select>
      <select v-model="activeFilters.sensor_variety_id" class="filter-select" @change="fetchData">
        <option value="">Тип сенсора</option>
        <option v-for="o in filterOptions.sensor_variety_id || []" :key="o.id" :value="o.id">{{ o.name }}</option>
      </select>
      <select v-model="activeFilters.model_line_brand_id" class="filter-select" @change="fetchData">
        <option value="">Бренд</option>
        <option v-for="o in filterOptions.model_line_brand_id || []" :key="o.id" :value="o.id">{{ o.name }}</option>
      </select>
      <button class="refresh-btn" @click="fetchData">Обновить</button>
    </div>

    <div v-if="loading" class="status">Загрузка...</div>
    <div v-else-if="error" class="status error">{{ error }}</div>
    <div v-else class="cards-grid">
      <div v-for="item in items" :key="item.id" class="card" @click="$emit('select', item.id)">
        <div class="card-image">
          <img v-if="item.images?.[0]?.preview_url" :src="item.images[0].preview_url" :alt="item.name" loading="lazy" />
          <span v-else class="no-image">🔌</span>
        </div>
        <div class="card-body">
          <h3>{{ item.name }}</h3>
          <p class="card-code" v-if="item.code">{{ item.code }}</p>
          <p class="card-brand" v-if="item.model_line?.name">{{ item.model_line.name }}</p>
        </div>
      </div>
      <div v-if="items.length === 0 && !loading" class="status">Ничего не найдено</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import lsbApi from '../api'

const props = defineProps({
  filters: { type: Object, default: () => ({}) },
})
defineEmits(['select'])

const items = ref([])
const filterOptions = ref({})
const activeFilters = reactive({})
const searchText = ref('')
const loading = ref(false)
const error = ref(null)

let debounceTimer = null
function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchData, 200)
}

async function fetchData() {
  loading.value = true; error.value = null
  try {
    const params = {}
    for (const [k, v] of Object.entries(activeFilters)) {
      if (v) params[k] = v
    }
    if (searchText.value) params.search = searchText.value
    const r = await lsbApi.list(params)
    items.value = r.data?.data || []
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка загрузки'
  } finally { loading.value = false }
}

onMounted(async () => {
  try {
    const r = await lsbApi.getFilters()
    filterOptions.value = r.data || {}
  } catch (e) { console.error('Failed to load filters', e) }
  fetchData()
})
</script>

<style scoped>
.list-page { max-width: 1200px; margin: 0 auto; padding: 16px; }
.page-title { font-size: var(--cat-text-2xl, 24px); font-weight: 700; margin: 0 0 16px; color: var(--cat-text, #1f2937); }
.filters-bar { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; align-items: center; }
.filter-input { flex: 1; padding: 6px 10px; border: 1px solid var(--cat-border, #d1d5db); border-radius: var(--cat-radius-md, 6px); font-size: 13px; min-width: 120px; background: var(--cat-surface, #fff); color: var(--cat-text, #1f2937); }
.filter-select { padding: 6px 10px; border: 1px solid var(--cat-border, #d1d5db); border-radius: var(--cat-radius-md, 6px); font-size: 13px; background: var(--cat-surface, #fff); color: var(--cat-text, #1f2937); }
.refresh-btn { padding: 6px 14px; background: var(--cat-primary, #2563eb); color: #fff; border: none; border-radius: var(--cat-radius-md, 6px); cursor: pointer; font-size: 13px; }
.cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: var(--cat-gap-2xl, 16px); }
.card { background: var(--cat-surface, #fff); border: 1px solid var(--cat-border, #e5e7eb); border-radius: var(--cat-radius-lg, 10px); overflow: hidden; cursor: pointer; transition: box-shadow .15s; }
.card:hover { box-shadow: var(--cat-shadow-card, 0 4px 20px rgba(0,0,0,.06)); }
.card-image { aspect-ratio: 4/3; background: var(--cat-bg, #f9fafb); display: flex; align-items: center; justify-content: center; }
.card-image img { width: 100%; height: 100%; object-fit: contain; }
.no-image { font-size: 40px; }
.card-body { padding: 12px; }
.card-body h3 { font-size: var(--cat-text-base, 14px); font-weight: 600; margin: 0 0 4px; color: var(--cat-text, #1f2937); }
.card-code { font-size: 12px; color: var(--cat-muted, #6b7280); font-family: monospace; margin: 0 0 4px; }
.card-brand { font-size: 12px; color: var(--cat-muted-light, #9ca3af); margin: 0; }
.status { text-align: center; padding: 40px; color: var(--cat-muted-light, #9ca3af); }
.status.error { color: var(--cat-price-color, #dc2626); }
</style>
