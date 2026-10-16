<!-- shared/components/catalog/FrEngineerSelector.vue -->
<!-- Инженерный подбор ФР: фильтры (как у EngineerSelection) + сетка с чипсами
     по корпусу (PaEngineerGroupCard), только для фильтр-регуляторов. -->
<template>
  <div class="engineer-selection">
    <span class="debug-tag" v-if="debug">FrEngineerSelector</span>
    <PageTitle :title="labels.title" />
    <div class="search-bar" v-if="withSearch"><input v-model="search" :placeholder="labels.searchPlaceholder || t('catalog.common.search')" @input="onSearchInput" /></div>
    <EngineerFilterBar
      v-if="filtersLoaded"
      :filters="filterData"
      :show-compatible="showCompatible"
      :show-compatible-toggle="showCompatibleAvailable"
      :graph-code="graphCode"
      @change="onFilterChange"
      @reset="resetFilters"
      @toggle-compatible="toggleCompatible"
    />
    <main class="main">
      <div class="fr-grid">
        <PaEngineerGroupCard
          v-for="g in groups"
          :key="g.body_id"
          :group="g"
          @select="onSelectCard"
        />
      </div>
      <div class="empty" v-if="!loading && !groups.length">{{ labels.emptyLabel || t('catalog.common.nothingFound') }}</div>
      <div class="pagination" v-if="total > limit">
        <button :disabled="offset === 0" @click="goPage(offset - limit)">{{ t('catalog.engineer.prev') }}</button>
        <span>{{ t('catalog.engineer.rangeOf', { from: offset + 1, to: Math.min(offset + limit, total), total }) }}</span>
        <button :disabled="offset + limit >= total" @click="goPage(offset + limit)">{{ t('catalog.engineer.next') }}</button>
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { debug } from '@/shared/config'
import PageTitle from '@/shared/components/PageTitle.vue'
import EngineerFilterBar from '@/shared/components/catalog/EngineerFilterBar.vue'
import PaEngineerGroupCard from '@/shared/components/catalog/PaEngineerGroupCard.vue'
import { useCatalog } from '@/shared/composables/useCatalog.js'
import { useI18n } from '@/shared/i18n'

const { t } = useI18n()

const props = defineProps({
  api: { type: Object, required: true },
  labels: { type: Object, default: () => ({}) },
  withSearch: { type: Boolean, default: true },
  fixedParams: { type: [Object, Function], default: null },
  presetFilters: { type: Object, default: null },
  graphCode: { type: String, default: '' },
})

const emit = defineEmits(['select', 'navigate'])

const {
  groups, total, loading, limit, offset,
  filterData, filtersLoaded, showCompatibleAvailable, showCompatible, search, activeFilters,
  loadFilters, fetchData, onFilterChange, toggleCompatible, resetFilters, onSearchInput, goPage,
} = useCatalog(props.api, {
  mode: 'engineer',
  withSearch: props.withSearch,
  fixedParams: props.fixedParams,
})

function onSelectCard(skuId) {
  // PaEngineerGroupCard эмитит sku_id; для FR нужна деталка по id карточки.
  const item = groups.value.flatMap(g => g.items).find(it => it.sku_id === skuId)
  emit('select', item ? item.id : skuId)
}

onMounted(async () => {
  await loadFilters()
  if (props.presetFilters) {
    for (const [k, v] of Object.entries(props.presetFilters)) { activeFilters[k] = v }
  }
  fetchData()
})
</script>

<style scoped>
.engineer-selection { max-width: 1200px; margin: 0 auto; padding: var(--cat-gap-xl, 16px); }
.search-bar { margin-bottom: 20px; }
.search-bar input { width: 100%; padding: 12px 16px; font-size: var(--cat-text-lg, 16px); border: 1px solid var(--cat-border, #d1d5db); border-radius: var(--cat-radius-lg, 8px); background: var(--cat-surface, #fff); outline: none; color: var(--cat-text, #1f2937); }
.search-bar input:focus { border-color: var(--cat-primary, #2563eb); box-shadow: 0 0 0 3px rgba(37, 99, 235, .1); }
.main { max-width: 100%; }
.fr-grid { display: flex; flex-direction: column; gap: 12px; }
.empty { text-align: center; padding: 60px 20px; color: var(--cat-muted-light, #9ca3af); font-size: var(--cat-text-lg, 16px); }
.pagination { display: flex; justify-content: center; align-items: center; gap: 16px; margin-top: 32px; padding: 16px 0; }
.pagination button { padding: 8px 20px; font-size: var(--cat-text-base, 14px); background: var(--cat-surface, #fff); border: 1px solid var(--cat-border, #d1d5db); border-radius: var(--cat-radius-md, 6px); cursor: pointer; color: var(--cat-text, #1f2937); }
.pagination button:disabled { opacity: .4; cursor: default; }
.pagination button:not(:disabled):hover { border-color: var(--cat-primary, #2563eb); color: var(--cat-primary, #2563eb); }
.pagination span { font-size: var(--cat-text-base, 14px); color: var(--cat-muted, #6b7280); }
</style>
