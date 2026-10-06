<!-- pneumatic-fittings-catalog/App.vue -->
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
    <KeepAlive :key="cacheEpoch">
    <CatalogSection v-if="page === 'section'" :api="api" :labels="labels.section" @select-series="goToBrand" @navigate="goToSection" />
    <EngineerSelection v-else-if="page === 'list'" :api="api" :labels="labels.list" :graph-code="graphCode" @select="id => onSelectItem(id, 'list')" @navigate="goToSection" />
    <CatalogDetail v-else-if="page === 'detail'" :api="api" :labels="labels.detail" :id="selectedId" :parent-mode="parentModeName" @close="closeDetail" @navigate="goToSection" @title-ready="t => pageSubtitle = t" />
    <CatalogModelLine v-else-if="page === 'brand'" :api="api" :labels="labels.brand" id-prop="model_line_id" :id-value="idValue" :parent-mode="parentModeName" @select="id => onSelectItem(id, 'brand')" @navigate="goToSection" @title-ready="t => pageSubtitle = t" />
    <QuickSelectNoSeries v-else-if="page === 'quickselect'" :api="api" :labels="labels.quickselect" :filter-labels="labels.quickselect.filterLabels" :auto-select-rules="labels.quickselect.autoSelectRules" @select="id => onSelectItem(id, 'quickselect')" @navigate="goToSection" />
    <QuestionGraphWizard v-else-if="page === 'graph'" :graph-code="'pneumatic_fittings'" :total-label="labels.graph.totalLabel" @select="id => onSelectItem(id, 'graph')" @navigate="goToSection" />
    <WizardSelection
      v-else-if="page === 'wizard'"
      :equipment-type-id="equipmentTypeId"
      :labels="labels.wizard"
      @select="id => onSelectItem(id, 'wizard')"
      @navigate="goToSection"
    />
    <AiSelectionPage :equipment-code="eqCode"
      v-else-if="page === 'ai'"
      :labels="labels.ai || {}"
      eq-name="Пневмофитинги"
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
import QuickSelectNoSeries from '@/shared/components/catalog/QuickSelectNoSeries.vue'
import AiSelectionPage from '@/pages/AiSelectionPage.vue'
import WizardSelection from '@/shared/components/catalog/WizardSelection.vue'
import QuestionGraphWizard from '@/shared/components/catalog/QuestionGraphWizard.vue'
import { useCatalogRoute } from '@/shared/composables/useCatalogRoute.js'
import { useI18n, localizedPath } from '@/shared/i18n'
import { useCatalogWizard } from '@/shared/composables/useCatalogWizard'
import fittingApi from './api'
const api = fittingApi
const equipmentTypeId = 9  // Пневмофитинги

const eqCode = 'fittings'
const graphCode = 'pneumatic_fittings'
const labels = {
  section: { title:'Пневматические фитинги', subtitle:'Выберите серию фитингов', breadcrumbName:'Фитинги' },
  list: { title:'Фитинги — инженерный подбор', searchPlaceholder:'Поиск...', resultsLabel:'Найдено:', emptyLabel:'Ничего не найдено' },
  detail: { backLabel:'Назад к каталогу', breadcrumbName:'Фитинги' },
  brand: { title:'Серия', countLabel:'Товаров:', emptyLabel:'Нет товаров', breadcrumbName:'Фитинги' },
  quickselect: { title:'Быстрый подбор', breadcrumbName:'Фитинги',
    filterLabels:{
      fitting_variety_id:'Тип фитинга', body_material_id:'Материал корпуса',
      pipe_material_id:'Материал трубки', pipe_diameter:'Диаметр трубки',
      thread_id:'Резьба', thread_inner_outer_id:'Резьба (нар/внут)',
    },
    autoSelectRules:{},
  },
  wizard: { breadcrumbName:'Пневмофитинги', wizardTitle:'Мастер подбора Пневмофитинги' },
  graph: { totalLabel:'найдено' },
}
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

const eqLabel = 'Фитинги'
const breadcrumbs = computed(() => {
  const items = [
    { name: t('breadcrumb.catalog'), target: 'catalog-index' },
    { name: eqLabel, target: 'section' },
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
    const { type } = await useCatalogWizard('pneumatic_fittings')
    graphAvailable.value = type === 'graph'
  } catch { }
})
</script>
<style scoped>
.app { max-width: 1200px; margin: 0 auto; }
</style>
