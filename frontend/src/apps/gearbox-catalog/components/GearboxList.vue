<!-- gearbox-catalog/components/GearboxList.vue -->
<!-- Страница подбора редукторов — использует FilterSidebar + ProductCard -->
<template>
  <div class="list-page">
    <!-- Поиск -->
    <div class="search-bar">
      <input
        v-model="search"
        placeholder="Поиск редукторов по названию, коду..."
        @input="onSearchInput"
      />
    </div>

    <div class="content">
      <!-- Боковая панель фильтров -->
      <FilterSidebar
        v-if="filtersLoaded"
        :filters="filterData"
        @change="onFilterChange"
        @reset="resetFilters"
      />

      <!-- Сетка карточек -->
      <main class="main">
        <div class="results-info" v-if="total >= 0">
          Найдено: {{ total }}
        </div>

        <div class="grid" v-if="items.length">
          <ProductCard
            v-for="item in items"
            :key="item.id"
            :item="item"
            :price="item.price || null"
            @select="id => emit('select', id)"
          />
        </div>

        <div class="empty" v-else-if="loaded">
          Ничего не найдено
        </div>

        <!-- Пагинация -->
        <div class="pagination" v-if="total > limit">
          <button :disabled="offset === 0" @click="goPage(offset - limit)">← Назад</button>
          <span>{{ offset + 1 }}–{{ Math.min(offset + limit, total) }} из {{ total }}</span>
          <button :disabled="offset + limit >= total" @click="goPage(offset + limit)">Вперёд →</button>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import FilterSidebar from '@/shared/components/FilterSidebar.vue'
import ProductCard from '@/shared/components/ProductCard.vue'
import gearboxApi from '../api'

const props = defineProps({ filters: Object })
const emit = defineEmits(['select'])

const search = ref('')
const items = ref([])
const loaded = ref(false)
const total = ref(0)
const limit = ref(24)
const offset = ref(0)
const filterData = reactive({})
const filtersLoaded = ref(false)
const activeFilters = reactive({})

let searchTimer = null

async function loadFilters() {
  try {
    const r = await gearboxApi.getFilters()
    Object.assign(filterData, r.data || {})
  } catch (e) {
    console.error('Failed to load filters', e)
  }
  filtersLoaded.value = true
}

function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    offset.value = 0
    fetchData()
  }, 300)
}

function onFilterChange(key, value) {
  activeFilters[key] = value
  offset.value = 0
  fetchData()
}

function resetFilters() {
  for (const k of Object.keys(activeFilters)) {
    activeFilters[k] = ''
  }
  Object.assign(filterData, {})
  search.value = ''
  offset.value = 0
  loadFilters()
  fetchData()
}

function goPage(newOffset) {
  offset.value = Math.max(0, newOffset)
  fetchData()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function fetchData() {
  loaded.value = false
  try {
    const params = { limit: limit.value, offset: offset.value }
    if (search.value) params.search = search.value
    for (const [k, v] of Object.entries(activeFilters)) {
      if (v !== '' && v != null) params[k] = v
    }

    const r = await gearboxApi.list(params)
    items.value = r.data.data || []
    total.value = r.data.total || 0
  } catch (e) {
    console.error('Failed to load catalog', e)
    items.value = []
    total.value = 0
  }
  loaded.value = true
}

onMounted(async () => {
  await loadFilters()
  fetchData()
})
</script>

<style scoped>
.list-page { max-width: 1440px; margin: 0 auto; }
.search-bar { margin-bottom: 20px; }
.search-bar input { width: 100%; padding: 12px 16px; font-size: var(--cat-text-lg); border: 1px solid var(--cat-border); border-radius: var(--cat-radius-lg); background: var(--cat-surface); outline: none; }
.search-bar input:focus { border-color: var(--cat-primary); box-shadow: 0 0 0 3px rgba(37,99,235,.1); }
.content { display: flex; gap: 24px; }
.main { flex: 1; min-width: 0; }
.results-info { font-size: var(--cat-text-base); color: var(--cat-muted); margin-bottom: 16px; }
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.empty { text-align: center; padding: 60px 20px; color: var(--cat-muted-light); font-size: var(--cat-text-lg); }
.pagination { display: flex; justify-content: center; align-items: center; gap: 16px; margin-top: 32px; padding: 16px 0; }
.pagination button { padding: 8px 20px; font-size: var(--cat-text-base); background: var(--cat-pagination-btn-bg); border: 1px solid var(--cat-border); border-radius: var(--cat-radius-md); cursor: pointer; }
.pagination button:disabled { opacity: .4; cursor: default; }
.pagination button:not(:disabled):hover { border-color: var(--cat-primary); color: var(--cat-primary); }
.pagination span { font-size: var(--cat-text-base); color: var(--cat-muted); }
@media (max-width: 1100px) { .grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 768px) { .content { flex-direction: column; } .grid { grid-template-columns: 1fr; } }
</style>