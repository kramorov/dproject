<!-- cable-gland-catalog/components/QuickSelectCableType.vue -->
<!-- Быстрый подбор кабельных вводов: топ-селектор «Тип кабеля» вместо «Серии». -->
<template>
  <div class="qs-page">
    <PageTitle :title="pageTitle" />

    <div class="chip-group" v-if="primaryOptions.length">
      <div class="chip-label">{{ primaryLabel }}</div>
      <div class="chip-row">
        <button
          v-for="opt in primaryOptions" :key="opt.value"
          class="chip"
          :class="{ active: String(activeFilters[primaryKey]) === String(opt.value) }"
          @click="togglePrimary(opt.value)"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>

    <div v-if="filterGroups.length" class="filter-chips">
      <div v-for="group in filterGroups" :key="group.key" class="chip-group">
        <div class="chip-label">{{ group.label }}</div>
        <div class="chip-row">
          <button
            v-for="opt in group.options" :key="opt.value ?? opt.id"
            class="chip"
            :class="{ active: String(activeFilters[group.key]) === String(opt.value ?? opt.id) }"
            @click="toggleFilter(group.key, opt.value ?? opt.id)"
          >
            {{ opt.label || opt.name }}
            <span class="chip-count" v-if="opt.count != null">({{ opt.count }})</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="product" class="product-area">
      <ProductDetail :product="product" :price="product.price" :breadcrumbs="detailBreadcrumbs" @navigate="$emit('navigate', $event)" />
    </div>
    <div class="empty" v-else-if="loaded">Модель не найдена — измените фильтры</div>
    <Spinner v-else-if="!loaded" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import PageTitle from '@/shared/components/PageTitle.vue'
import ProductDetail from '@/shared/components/ProductDetail.vue'
import Spinner from '@/shared/components/Spinner.vue'

const props = defineProps({
  api: { type: Object, required: true },
  labels: { type: Object, default: () => ({}) },
  filterLabels: { type: Object, default: () => ({}) },
  primaryKey: { type: String, default: 'cable_type_id' },
})
defineEmits(['select', 'navigate'])

const primaryOptions = ref([])
const filterGroups = ref([])
const activeFilters = reactive({})
const product = ref(null)
const loaded = ref(false)
let primaryCaptured = false

const pageTitle = computed(() => props.labels.title || 'Быстрый подбор')
const eqLabel = computed(() => props.labels.breadcrumbName || 'Каталог')
const primaryKey = props.primaryKey
const primaryLabel = computed(() => props.filterLabels[primaryKey] || 'Тип кабеля')

const detailBreadcrumbs = computed(() => [
  { name: 'Каталог', to: '/' },
  { name: eqLabel.value },
  { name: 'Быстрый подбор' },
  { name: product.value?.model_line?.name || '' },
])

onMounted(async () => {
  try {
    await load({})
  } catch (e) { /* ignore */ }
  loaded.value = true
})

async function load(filters) {
  const r = await props.api.getQuickSelectNoSeries(filters)
  const data = r.data

  // Топ-селектор фиксируем один раз: список всех типов кабеля не сжимается.
  if (!primaryCaptured) {
    primaryOptions.value = (data.filters?.[primaryKey] || [])
      .map(o => ({ value: o.value ?? o.id, label: o.label ?? o.name }))
    primaryCaptured = true
  }

  const groups = []
  for (const [key, options] of Object.entries(data.filters || {})) {
    if (key === primaryKey) continue
    if (!options || !options.length) continue
    groups.push({ key, label: props.filterLabels[key] || key, options })
  }
  filterGroups.value = groups

  // Убираем значения фильтров, которые стали недоступны при текущем наборе.
  for (const group of groups) {
    const curVal = activeFilters[group.key]
    if (curVal !== undefined && curVal !== null) {
      const valid = group.options.some(o => String(o.value ?? o.id) === String(curVal))
      if (!valid) delete activeFilters[group.key]
    }
  }

  product.value = data.items?.[0] || null
}

async function togglePrimary(value) {
  if (String(activeFilters[primaryKey]) === String(value)) {
    delete activeFilters[primaryKey]
  } else {
    activeFilters[primaryKey] = value
  }
  await load({ ...activeFilters })
}

async function toggleFilter(key, value) {
  if (String(activeFilters[key]) === String(value)) {
    delete activeFilters[key]
  } else {
    activeFilters[key] = value
  }
  await load({ ...activeFilters })
}
</script>

<style scoped>
.qs-page { max-width: 1200px; margin: 0 auto; padding: var(--cat-gap-xl, 16px); }
.chip-group { margin-bottom: 12px; }
.chip-label { font-weight: 500; font-size: 13px; margin-bottom: 4px; color: var(--cat-muted-dark, #374151); }
.chip-row { display: flex; flex-wrap: wrap; gap: 4px; }
.chip { padding: 4px 12px; font-size: 12px; border: 1px solid var(--cat-border, #d1d5db); border-radius: 16px; background: var(--cat-surface, #fff); cursor: pointer; transition: all .12s; white-space: nowrap; color: var(--cat-text, #1f2937); }
.chip:hover { border-color: var(--cat-primary, #2563eb); color: var(--cat-primary, #2563eb); }
.chip.active { background: var(--cat-primary, #2563eb); color: #fff; border-color: var(--cat-primary, #2563eb); }
.chip-count { font-size: 10px; opacity: .7; margin-left: 2px; }
.filter-chips { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
.product-area { margin-top: 20px; }
.empty { text-align: center; padding: 60px 20px; color: var(--cat-muted-light, #9ca3af); font-size: var(--cat-text-md, 16px); }
</style>
