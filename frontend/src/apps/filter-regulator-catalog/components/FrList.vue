<!-- filter-regulator-catalog/components/GearboxList.vue -->
<template>
  <div class="list-page">
    <div class="search-bar">
      <input v-model="search" placeholder="Поиск фильтр-регуляторов по названию, коду..." @input="onSearchInput" />
    </div>
    <div class="content">
      <FilterSidebar v-if="filtersLoaded" :filters="filterData" @change="onFilterChange" @reset="resetFilters" />
      <main class="main">
        <div class="results-info" v-if="total >= 0">Найдено: {{ total }}</div>
        <div class="grid" v-if="items.length">
          <ProductCard v-for="item in items" :key="item.id" :item="item" :price="item.price || null" @select="id => emit('select', id)" />
        </div>
        <div class="empty" v-else-if="loaded">Ничего не найдено</div>
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
import { ref, reactive, onMounted, watch } from 'vue'
import FilterSidebar from '@/shared/components/FilterSidebar.vue'
import ProductCard from '@/shared/components/ProductCard.vue'
import frApi from '../api'

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
  try { const r = await frApi.getFilters(); Object.assign(filterData, r.data || {}) } catch (e) { console.error(e) }
  filtersLoaded.value = true
}

function onSearchInput() { clearTimeout(searchTimer); searchTimer = setTimeout(() => { offset.value = 0; fetchData() }, 300) }
function onFilterChange(key, value) { activeFilters[key] = value; offset.value = 0; fetchData() }
function resetFilters() { for (const k of Object.keys(activeFilters)) activeFilters[k] = ''; offset.value = 0; fetchData() }
function goPage(n) { offset.value = Math.max(0, n); fetchData(); window.scrollTo({ top: 0, behavior: 'smooth' }) }

async function fetchData() {
  loaded.value = false
  try {
    const params = { limit: limit.value, offset: offset.value }
    if (search.value) params.search = search.value
    for (const [k, v] of Object.entries(activeFilters)) { if (v !== '' && v != null) params[k] = v }
    const r = await frApi.list(params)
    items.value = r.data.data || []
    total.value = r.data.total || 0
  } catch (e) { console.error(e); items.value = []; total.value = 0 }
  loaded.value = true
}

onMounted(() => { loadFilters(); if (props.filters?.loaded) fetchData() })
watch(() => props.filters?.loaded, v => { if (v) fetchData() })
</script>

<style scoped>
.list-page { max-width: 1440px; margin: 0 auto; }
.search-bar { margin-bottom: 20px; }
.search-bar input { width: 100%; padding: 12px 16px; font-size: 16px; border: 1px solid #d1d5db; border-radius: 8px; background: #fff; outline: none; }
.search-bar input:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,.1); }
.content { display: flex; gap: 24px; }
.main { flex: 1; min-width: 0; }
.results-info { font-size: 14px; color: #6b7280; margin-bottom: 16px; }
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.empty { text-align: center; padding: 60px 20px; color: #9ca3af; font-size: 16px; }
.pagination { display: flex; justify-content: center; align-items: center; gap: 16px; margin-top: 32px; padding: 16px 0; }
.pagination button { padding: 8px 20px; font-size: 14px; background: #fff; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; }
.pagination button:disabled { opacity: .4; cursor: default; }
.pagination button:not(:disabled):hover { border-color: #2563eb; color: #2563eb; }
.pagination span { font-size: 14px; color: #6b7280; }
@media (max-width: 768px) { .content { flex-direction: column; } .grid { grid-template-columns: 1fr; } }
</style>
