<template>
  <div class="list-page">
    <!-- Поиск -->
    <div class="search-bar">
      <input
        v-model="search"
        placeholder="Поиск редукторов по названию, коду, описанию..."
        @input="onSearchInput"
      />
    </div>

    <div class="content">
      <!-- Боковая панель фильтров -->
      <aside class="sidebar" v-if="filters.loaded">
        <div class="filter-block">
          <h3>Фильтры</h3>
          <button class="reset-btn" @click="resetFilters" v-if="hasActiveFilters">Сбросить</button>
        </div>

        <div
          v-for="(f, key) in sortedFilters"
          :key="key"
          class="filter-group"
        >
          <label>{{ f.label }}</label>
          <select v-model="activeFilters[key]" @change="applyFilters">
            <option value="">Все</option>
            <option
              v-for="opt in f.options"
              :key="opt.id"
              :value="opt.id"
            >{{ opt.name }}</option>
          </select>
        </div>
      </aside>

      <!-- Сетка карточек -->
      <main class="main">
        <div class="results-info" v-if="total >= 0">
          Найдено: {{ total }}
        </div>

        <div class="grid" v-if="items.length">
          <GearboxCard
            v-for="item in items"
            :key="item.id"
            :item="item"
            :price="prices[item.sku?.code] || null"
            @click="select(item.id)"
          />
        </div>

        <div class="empty" v-else-if="loaded">
          Ничего не найдено
        </div>

        <!-- Пагинация -->
        <div class="pagination" v-if="total > limit">
          <button
            :disabled="offset === 0"
            @click="goPage(offset - limit)"
          >← Назад</button>
          <span>{{ offset + 1 }}–{{ Math.min(offset + limit, total) }} из {{ total }}</span>
          <button
            :disabled="offset + limit >= total"
            @click="goPage(offset + limit)"
          >Вперёд →</button>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import GearboxCard from './GearboxCard.vue'
import gearboxApi from '../api'

const props = defineProps({ filters: Object })
const emit = defineEmits(['select'])

const search = ref('')
const items = ref([])
const prices = reactive({})
const loaded = ref(false)
const total = ref(0)
const limit = ref(24)
const offset = ref(0)

const activeFilters = reactive({})

let searchTimer = null

// Сортировка фильтров по order
const sortedFilters = computed(() => {
  const arr = []
  for (const [key, val] of Object.entries(props.filters.data)) {
    arr.push({ key, ...val })
  }
  arr.sort((a, b) => (a.order || 99) - (b.order || 99))
  return arr
})

const hasActiveFilters = computed(() => {
  return Object.values(activeFilters).some(v => v !== '' && v != null)
})

function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    offset.value = 0
    fetchData()
  }, 300)
}

function applyFilters() {
  offset.value = 0
  fetchData()
}

function resetFilters() {
  for (const k of Object.keys(activeFilters)) {
    activeFilters[k] = ''
  }
  search.value = ''
  offset.value = 0
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

    // Загружаем цены
    const codes = r.data.sku_codes || []
    if (codes.length) {
      try {
        const pr = await gearboxApi.getPrices(codes)
        if (pr.data?.snapshots) {
          for (const [code, entry] of Object.entries(pr.data.snapshots)) {
            prices[code] = entry
          }
        }
      } catch (e) {
        console.error('Failed to load prices', e)
      }
    }
  } catch (e) {
    console.error('Failed to load catalog', e)
    items.value = []
    total.value = 0
  }
  loaded.value = true
}

function select(id) {
  emit('select', id)
}

onMounted(() => {
  if (props.filters.loaded) fetchData()
})

watch(() => props.filters.loaded, (val) => {
  if (val) fetchData()
})
</script>

<style scoped>
.list-page{max-width:1440px;margin:0 auto}
.search-bar{margin-bottom:20px}
.search-bar input{width:100%;padding:12px 16px;font-size:16px;border:1px solid #d1d5db;border-radius:8px;background:#fff;outline:none}
.search-bar input:focus{border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.1)}
.content{display:flex;gap:24px}
.sidebar{width:260px;flex-shrink:0}
.filter-block{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.filter-block h3{font-size:18px;font-weight:600;margin:0}
.reset-btn{padding:4px 12px;font-size:13px;background:#f3f4f6;border:1px solid #d1d5db;border-radius:4px;cursor:pointer}
.reset-btn:hover{background:#e5e7eb}
.filter-group{margin-bottom:16px}
.filter-group label{display:block;font-size:13px;font-weight:500;color:#6b7280;margin-bottom:4px}
.filter-group select{width:100%;padding:8px 10px;font-size:14px;border:1px solid #d1d5db;border-radius:6px;background:#fff}
.main{flex:1;min-width:0}
.results-info{font-size:14px;color:#6b7280;margin-bottom:16px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}
.empty{text-align:center;padding:60px 20px;color:#9ca3af;font-size:16px}
.pagination{display:flex;justify-content:center;align-items:center;gap:16px;margin-top:32px;padding:16px 0}
.pagination button{padding:8px 20px;font-size:14px;background:#fff;border:1px solid #d1d5db;border-radius:6px;cursor:pointer}
.pagination button:disabled{opacity:.4;cursor:default}
.pagination button:not(:disabled):hover{border-color:#2563eb;color:#2563eb}
.pagination span{font-size:14px;color:#6b7280}
@media(max-width:1100px){.grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:768px){.content{flex-direction:column}.sidebar{width:100%}.grid{grid-template-columns:1fr}}
</style>
