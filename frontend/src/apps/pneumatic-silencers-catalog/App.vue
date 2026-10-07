<!-- pneumatic-silencers-catalog/App.vue -->
<template>
  <div class="app">
    <Breadcrumbs :items="breadcrumbs" @navigate="onNavigate" />
    <CatalogActions
      :active="activeTab"
      :tabs="tabs"
      @section="goToSection"
      @engineer="goToList"
      @quickselect="goToQuickSelect"
    />
    <KeepAlive :key="cacheEpoch">
    <CatalogSection v-if="page === 'section'" :api="api" :labels="labels.section" @select-series="goToBrand" @navigate="goToSection" />
    <EngineerSelection v-else-if="page === 'list'" :api="api" :labels="labels.list" @select="id => onSelectItem(id, 'list')" @navigate="goToSection" />
    <CatalogDetail v-else-if="page === 'detail'" :api="api" :labels="labels.detail" :id="selectedId" :parent-mode="parentModeName" @close="closeDetail" @navigate="goToSection" @title-ready="t => pageSubtitle = t" />
    <CatalogModelLine v-else-if="page === 'brand'" :api="api" :labels="labels.brand" id-prop="model_line_id" :id-value="idValue" :parent-mode="parentModeName" @select="id => onSelectItem(id, 'brand')" @navigate="goToSection" @title-ready="t => pageSubtitle = t" />
    <QuickSelectNoSeries v-else-if="page === 'quickselect'" :api="api" :labels="labels.quickselect" :filter-labels="labels.quickselect.filterLabels" :auto-select-rules="labels.quickselect.autoSelectRules" @select="id => onSelectItem(id, 'quickselect')" @navigate="goToSection" />
    </KeepAlive>
  </div>
</template>
<script setup>
import { ref, computed, watch } from 'vue'
import Breadcrumbs from '@/shared/components/Breadcrumbs.vue'
import CatalogActions from '@/shared/components/catalog/CatalogActions.vue'
import CatalogSection from '@/shared/components/catalog/CatalogSection.vue'
import EngineerSelection from '@/shared/components/catalog/EngineerSelection.vue'
import CatalogDetail from '@/shared/components/catalog/CatalogDetail.vue'
import CatalogModelLine from '@/shared/components/catalog/CatalogModelLine.vue'
import QuickSelectNoSeries from '@/shared/components/catalog/QuickSelectNoSeries.vue'
import { useCatalogRoute } from '@/shared/composables/useCatalogRoute.js'
import { useI18n, localizedPath } from '@/shared/i18n'
import silencerApi from './api'

const api = silencerApi

const tabs = [
  { key: 'section',     label: 'catalog.mode.section', event: 'section' },
  { key: 'engineer',    label: 'catalog.mode.engineer',  event: 'engineer' },
  { key: 'quickselect', label: 'catalog.mode.quickselect', event: 'quickselect' },
]

const labels = computed(() => ({
  section: { title: t('ps.section.title'), subtitle: t('ps.section.subtitle'), breadcrumbName: t('ps.breadcrumb') },
  list: { title: t('ps.list.title'), searchPlaceholder: t('catalog.common.search'), resultsLabel: t('catalog.common.found'), emptyLabel: t('catalog.common.nothingFound') },
  detail: { backLabel: t('catalog.common.backToCatalog'), breadcrumbName: t('ps.breadcrumb') },
  brand: { title: t('catalog.section.seriesPrefix'), countLabel: t('catalog.common.items'), emptyLabel: t('catalog.common.noItems'), breadcrumbName: t('ps.breadcrumb') },
  quickselect: { title: t('ps.quickselect.title'), breadcrumbName: t('ps.breadcrumb'),
    filterLabels:{
      thread_id: t('ps.filter.thread'), thread_inner_outer_id: t('ps.filter.thread_inner_outer'),
      body_material_id: t('ps.filter.body_material'),
    },
    autoSelectRules:{},
  },
}))

const cacheEpoch = ref(0)

const {
  page, selectedId, idValue, fromPage, router,
  goToSection: navSection, goToEngineer: navEngineer, goToBrand: navBrand,
  goToQuickSelect: navQuickSelect, onSelectItem: navSelectItem, closeDetail: navCloseDetail,
} = useCatalogRoute()

const pageSubtitle = ref('')
const { t, locale } = useI18n()

const modeNames = computed(() => ({
  section: t('catalog.mode.section'),
  list: t('catalog.mode.engineer'),
  brand: t('catalog.mode.section'),
  detail: '',
  quickselect: t('catalog.mode.quickselect'),
}))
const targetByPage = { section:'section', list:'engineer', brand:'section', quickselect:'quickselect' }

const parentModeName = computed(() => {
  if (page.value === 'detail') return modeNames.value[fromPage.value] || t('catalog.mode.section')
  if (page.value === 'brand') return t('catalog.mode.section')
  return modeNames.value[page.value] || t('catalog.mode.section')
})
const parentTarget = computed(() => targetByPage[fromPage.value] || 'section')

const eqLabel = computed(() => t('ps.breadcrumb'))
const breadcrumbs = computed(() => {
  const items = [
    { name: t('breadcrumb.catalog'), target: 'catalog-index' },
    { name: eqLabel.value, target: 'section' },
  ]
  if (page.value === 'brand' || page.value === 'detail') {
    items.push({ name: parentModeName.value, target: parentTarget.value })
  }
  if (pageSubtitle.value) {
    items.push({ name: pageSubtitle.value })
  } else {
    const current = modeNames.value[page.value]
    if (current && page.value !== 'section') items.push({ name: current })
  }
  return items
})

const tabKeys = { section:'section', brand:'section', list:'engineer', detail:'', quickselect:'quickselect' }
const activeTab = computed(() => tabKeys[page.value] || 'section')

function goToList() { cacheEpoch.value++; navEngineer() }
function goToBrand(id) { cacheEpoch.value++; navBrand(id) }
function onSelectItem(id, from) { navSelectItem(id, from) }
function goToQuickSelect() { cacheEpoch.value++; navQuickSelect() }
function goToSection() { cacheEpoch.value++; pageSubtitle.value = ''; navSection() }
function closeDetail() { navCloseDetail() }

function onNavigate(item) {
  const t = item?.target
  if (!t) return
  if (t === 'catalog-index') {
    if (router) { router.push(localizedPath('/catalogs/equipment', locale.value)) } else { navSection() }
    return
  }
  cacheEpoch.value++
  pageSubtitle.value = ''
  const map = { section: navSection, engineer: navEngineer, quickselect: navQuickSelect }
  const nav = map[t] || navSection
  nav()
}

watch(page, (p) => {
  if (p !== 'brand' && p !== 'detail') pageSubtitle.value = ''
})
</script>
<style scoped>
.app { max-width: 1200px; margin: 0 auto; }
</style>
