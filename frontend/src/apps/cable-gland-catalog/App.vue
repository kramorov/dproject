<!-- cable-gland-catalog/App.vue -->
<template>
  <div class="app">
    <Breadcrumbs :items="breadcrumbs" @navigate="onNavigate" />
    <CatalogActions
      :active="activeTab"
      @section="goToSection"
      @engineer="goToList"
      @quickselect="goToQuickSelect"
      @wizard="goToWizard"
      @ai="goToAi"
    />
    <KeepAlive :key="cacheEpoch"><CatalogSection
      v-if="page === 'section'"
      :api="api" :labels="labels.section"
      @select-series="goToBrand"
      @navigate="goToSection"
    />
    <EngineerSelection
      v-else-if="page === 'list'"
      :api="api" :labels="labels.list"
      @select="id => onSelectItem(id, 'list')"
      @navigate="goToSection"
    />
    <CatalogDetail
      v-else-if="page === 'detail'"
      :api="api" :labels="labels.detail" :id="selectedId"
      :parent-mode="parentModeName"
      @close="closeDetail"
      @navigate="goToSection"
      @title-ready="t => pageSubtitle = t"
    />
    <CatalogModelLine
      v-else-if="page === 'brand'"
      :api="api" :labels="labels.brand"
      id-prop="model_line_id" :id-value="idValue"
      :parent-mode="parentModeName"
      @select="id => onSelectItem(id, 'brand')"
      @navigate="goToSection"
      @title-ready="t => pageSubtitle = t"
    />
    <QuickSelectCableType
      v-else-if="page === 'quickselect'"
      :api="api" :labels="labels.quickselect"
      :filter-labels="labels.quickselect.filterLabels"
      @select="id => onSelectItem(id, 'quickselect')"
      @navigate="goToSection"
    />
    <QuestionGraphWizard v-else-if="page === 'graph'" :graph-code="'cable-gland'" :total-label="t('catalog.common.foundLower')" @select="id => onSelectItem(id, 'graph')" @navigate="goToSection" />
    <WizardSelection
      v-else-if="page === 'wizard'"
      :equipment-type-id="equipmentTypeId"
      :labels="labels.wizard"
      @select="id => onSelectItem(id, 'wizard')"
      @navigate="goToSection"
    />
    <AiSelectionPage :equipment-code="eqCode"
      v-else-if="page === 'ai'"
      :labels="labels.ai"
      :eq-name="t('cg.eqName')"
      @navigate="goToSection"
    />
    </KeepAlive>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import Breadcrumbs from '@/shared/components/Breadcrumbs.vue'
import CatalogActions from '@/shared/components/catalog/CatalogActions.vue'
import CatalogSection from '@/shared/components/catalog/CatalogSection.vue'
import EngineerSelection from '@/shared/components/catalog/EngineerSelection.vue'
import CatalogDetail from '@/shared/components/catalog/CatalogDetail.vue'
import CatalogModelLine from '@/shared/components/catalog/CatalogModelLine.vue'
import QuickSelectCableType from './components/QuickSelectCableType.vue'
import WizardSelection from '@/shared/components/catalog/WizardSelection.vue'
import QuestionGraphWizard from '@/shared/components/catalog/QuestionGraphWizard.vue'
import AiSelectionPage from '@/pages/AiSelectionPage.vue'
import { useCatalogRoute } from '@/shared/composables/useCatalogRoute.js'
import { useI18n, localizedPath } from '@/shared/i18n'
import { useCatalogWizard } from '@/shared/composables/useCatalogWizard'
import cableGlandApi from './api'
const api = cableGlandApi
const equipmentTypeId = 12  // Кабельный ввод

const eqCode = 'cable-gland'
const labels = computed(() => ({
  section: { title: t('cg.section.title'), subtitle: t('cg.section.subtitle'), breadcrumbName: t('cg.breadcrumb') },
  list: { title: t('cg.list.title'), searchPlaceholder: t('catalog.common.search'), resultsLabel: t('catalog.common.found'), emptyLabel: t('catalog.common.nothingFound'), breadcrumbName: t('cg.breadcrumb') },
  detail: { backLabel: t('catalog.common.backToCatalog'), breadcrumbName: t('cg.breadcrumb') },
  brand: { title: t('catalog.section.seriesPrefix'), countLabel: t('catalog.common.items'), emptyLabel: t('catalog.common.noItems'), breadcrumbName: t('cg.breadcrumb') },
  quickselect: { title: t('cg.quickselect.title'), breadcrumbName: t('cg.breadcrumb'),
    filterLabels:{
      thread_id: t('cg.filter.thread'),
      body_material_id: t('cg.filter.body_material'),
      exd_id: t('cg.filter.exd'),
      ip_id: t('cg.filter.ip'),
      cable_type_id: t('cg.filter.cable_type'),
      cable_diameter_min: t('cg.filter.cable_diameter_min'),
      cable_diameter_max: t('cg.filter.cable_diameter_max'),
      work_temp_min: t('cg.filter.temp_min'),
    },
    autoSelectRules:{},
  },
  wizard: { breadcrumbName: t('cg.breadcrumb'), wizardTitle: t('cg.wizard.title') },
  ai: { breadcrumbName: t('cg.breadcrumb'), aiTitle: t('cg.ai.title') },
}))

const cacheEpoch = ref(0)
const graphAvailable = ref(false)

const {
  page, selectedId, idValue, fromPage, router,
  goToSection: navSection, goToEngineer: navEngineer, goToBrand: navBrand,
  goToQuickSelect: navQuickSelect, goToWizard: navWizard, goToGraph: navGraph,
  goToAi: navAi, onSelectItem: navSelectItem, closeDetail: navCloseDetail,
} = useCatalogRoute()

const pageSubtitle = ref('')
const { t, locale } = useI18n()

const modeNames = computed(() => ({
  section: t('catalog.mode.section'),
  list: t('catalog.mode.engineer'),
  brand: t('catalog.mode.section'),
  detail: '',
  quickselect: t('catalog.mode.quickselect'),
  wizard: t('catalog.mode.wizard'),
  graph: t('catalog.mode.wizard'),
  ai: t('catalog.mode.ai'),
}))
const targetByPage = { section:'section', list:'engineer', brand:'section', quickselect:'quickselect', wizard:'wizard', graph:'graph', ai:'ai' }

const parentModeName = computed(() => {
  if (page.value === 'detail') return modeNames.value[fromPage.value] || t('catalog.mode.section')
  if (page.value === 'brand') return t('catalog.mode.section')
  return modeNames.value[page.value] || t('catalog.mode.section')
})
const parentTarget = computed(() => targetByPage[fromPage.value] || 'section')

const eqLabel = computed(() => t('cg.breadcrumb'))
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

const tabKeys = { section:'section', brand:'section', list:'engineer', detail:'', quickselect:'quickselect', wizard:'wizard', graph:'wizard', ai:'ai' }
const activeTab = computed(() => tabKeys[page.value] || 'section')

function goToList() { cacheEpoch.value++; navEngineer() }
function goToBrand(id) { cacheEpoch.value++; navBrand(id) }
function onSelectItem(id, from) { navSelectItem(id, from) }
function goToQuickSelect() { cacheEpoch.value++; navQuickSelect() }
function goToWizard() { cacheEpoch.value++; graphAvailable.value ? navGraph() : navWizard() }
function goToAi() { navAi() }
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
  const map = { section: navSection, engineer: navEngineer, quickselect: navQuickSelect, wizard: navWizard, graph: navGraph, ai: navAi }
  const nav = map[t] || navSection
  nav()
}

watch(page, (p) => {
  if (p !== 'brand' && p !== 'detail') pageSubtitle.value = ''
})

onMounted(async () => {
  try {
    const { type } = await useCatalogWizard('cable-gland')
    graphAvailable.value = type === 'graph'
  } catch { }
})
</script>
<style scoped>
.app { max-width: 1200px; margin: 0 auto; }
</style>
