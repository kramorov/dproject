<!-- filter-regulator-catalog/components/GearboxBrand.vue -->
<template>
  <div class="brand-page">
    <Breadcrumbs :items="breadcrumbs" />
    <div class="brand-header">
      <h1 class="page-title">{{ brandName || 'Бренд' }}</h1>
      <p class="page-count" v-if="total">Фильтр-регуляторов: {{ total }}</p>
    </div>
    <div class="content" v-if="loaded">
      <FilterSidebar v-if="filtersLoaded" :filters="filterData" @change="onFilterChange" @reset="resetFilters" />
      <main class="main">
        <div class="grid" v-if="items.length">
          <ProductCard v-for="item in items" :key="item.id" :item="item" :price="item.price || null" @select="id => emit('select', id)" />
        </div>
        <div class="empty" v-else>Нет товаров</div>
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
import { ref, reactive, computed, onMounted } from 'vue'
import Breadcrumbs from '@/shared/components/Breadcrumbs.vue'
import FilterSidebar from '@/shared/components/FilterSidebar.vue'
import ProductCard from '@/shared/components/ProductCard.vue'
import frApi from '../api'

const props = defineProps({ brandId: [Number, String], modelLineId: [Number, String] })
const emit = defineEmits(['select'])

const items = ref([])
const loaded = ref(false)
const total = ref(0)
const limit = ref(24)
const offset = ref(0)
const filterData = reactive({})
const filtersLoaded = ref(false)
const activeFilters = reactive({})
const brandName = ref('')

const breadcrumbs = computed(() => [{ name: 'Каталог' }, { name: 'Фильтр-регуляторы' }, { name: brandName.value || 'Бренд' }])

async function loadFilters() { try { const r = await frApi.getFilters(); Object.assign(filterData, r.data || {}) } catch (e) {}; filtersLoaded.value = true }
function onFilterChange(key, value) { activeFilters[key] = value; offset.value = 0; fetchData() }
function resetFilters() { for (const k of Object.keys(activeFilters)) activeFilters[k] = ''; offset.value = 0; fetchData() }
function goPage(n) { offset.value = Math.max(0, n); fetchData(); window.scrollTo({ top: 0, behavior: 'smooth' }) }

async function fetchData() {
  loaded.value = false
  try {
    const params = { limit: limit.value, offset: offset.value }
    if (props.modelLineId) params.model_line_id = props.modelLineId
    if (props.brandId) params.brand_id = props.brandId
    for (const [k, v] of Object.entries(activeFilters)) if (v !== '' && v != null) params[k] = v
    const r = await frApi.list(params)
    items.value = r.data.data || []
    total.value = r.data.total || 0
    if (items.value.length && !brandName.value) brandName.value = items.value[0]?.model_line?.brand?.name || ''
  } catch (e) { console.error(e) }
  loaded.value = true
}

onMounted(async () => { await loadFilters(); fetchData() })
</script>

<style scoped>
.brand-page { max-width: 1200px; margin: 0 auto; padding: 16px; }
.brand-header { margin-bottom: 20px; }
.page-title { font-size: 28px; font-weight: 700; margin: 8px 0 4px; }
.page-count { font-size: 15px; color: #6b7280; margin: 0; }
.content { display: flex; gap: 24px; }
.main { flex: 1; min-width: 0; }
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.empty { text-align: center; padding: 60px 20px; color: #9ca3af; font-size: 16px; }
.pagination { display: flex; justify-content: center; align-items: center; gap: 16px; margin-top: 32px; padding: 16px 0; }
.pagination button { padding: 8px 20px; font-size: 14px; background: #fff; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; }
.pagination button:disabled { opacity: .4; cursor: default; }
.pagination button:not(:disabled):hover { border-color: #2563eb; color: #2563eb; }
.pagination span { font-size: 14px; color: #6b7280; }
@media (max-width: 768px) { .content { flex-direction: column; } .grid { grid-template-columns: 1fr; } }
</style>
