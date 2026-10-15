<!-- positioners-catalog/App.vue — каталог позиционеров (по образцу БКВ) -->
<template>
  <div class="app">
    <Breadcrumbs :items="breadcrumbs" @navigate="onNavigate" />
    <CatalogActions
      :active="activeTab"
      :tabs="tabs"
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
    <QuickSelect
      v-else-if="page === 'quickselect'"
      :api="api" :labels="labels.quickselect"
      :filter-labels="labels.quickselect.filterLabels"
      :auto-select-rules="labels.quickselect.autoSelectRules"
      @select="id => onSelectItem(id, 'quickselect')"
      @navigate="goToSection"
    />
    <QuestionGraphWizard v-else-if="page === 'graph'" :graph-code="'posi'" :total-label="t('catalog.common.foundLower')" @select="id => onSelectItem(id, 'graph')" @navigate="goToSection" />
    <WizardSelection
      v-else-if="page === 'wizard' && wizardAvailable"
      :equipment-type-id="equipmentTypeId"
      :labels="labels.wizard"
      @select="id => onSelectItem(id, 'wizard')"
      @navigate="goToSection"
    />
    <AiSelectionPage :equipment-code="eqCode"
      v-else-if="page === 'ai' && aiAvailable"
      :labels="labels.ai"
      :eq-name="t('posi.eqName')"
      @navigate="goToSection"
    />
    <CatalogSection
      v-else
      :api="api" :labels="labels.section"
      @select-series="goToBrand"
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
import QuickSelect from '@/shared/components/catalog/QuickSelect.vue'
import WizardSelection from '@/shared/components/catalog/WizardSelection.vue'
import AiSelectionPage from '@/pages/AiSelectionPage.vue'
import { useCatalogRoute } from '@/shared/composables/useCatalogRoute.js'
import globalApi from '@/shared/api'
import { useI18n, localizedPath } from '@/shared/i18n'
import { useCatalogWizard } from '@/shared/composables/useCatalogWizard'
import QuestionGraphWizard from '@/shared/components/catalog/QuestionGraphWizard.vue'
import posiApi from './api'
const api = posiApi
const equipmentTypeId = 4  // Позиционер для ПП

const eqCode = 'pa-posi'
const labels = computed(() => ({
  section: { title: t('posi.section.title'), subtitle: t('posi.section.subtitle'), breadcrumbName: t('posi.breadcrumb') },
  list: { title: t('posi.list.title'), searchPlaceholder: t('catalog.common.search'), resultsLabel: t('catalog.common.found'), emptyLabel: t('catalog.common.nothingFound'), breadcrumbName: t('posi.breadcrumb') },
  detail: { backLabel: t('catalog.common.backToCatalog'), breadcrumbName: t('posi.breadcrumb') },
  brand: { title: t('catalog.section.seriesPrefix'), countLabel: t('catalog.common.items'), emptyLabel: t('catalog.common.noItems'), breadcrumbName: t('posi.breadcrumb') },
  quickselect: { title: t('posi.quickselect.title'), breadcrumbName: t('posi.breadcrumb'),
    filterLabels: { body_connection_id: t('posi.filter.body_connection'), lever_id: t('posi.filter.lever'), signal_profile_id: t('posi.filter.signal_profile'), exd_id: t('posi.filter.exd') },
    autoSelectRules: {},
  },
  wizard: { breadcrumbName: t('posi.breadcrumb'), wizardTitle: t('posi.wizard.title') },
  ai: { breadcrumbName: t('posi.breadcrumb'), aiTitle: t('posi.ai.title') },
}))

const cacheEpoch = ref(0)
const graphAvailable = ref(false)
const wizardAvailable = ref(false)
const aiAvailable = ref(false)

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

const eqLabel = computed(() => t('posi.breadcrumb'))
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

// Сброс подзаголовка при уходе с brand/detail (в т.ч. по браузерной «назад»)
watch(page, (p) => {
  if (p !== 'brand' && p !== 'detail') pageSubtitle.value = ''
})

onMounted(async () => {
  // Мастер подбора: есть только если для EquipmentType сконфигурирован wizard/graph.
  try {
    const res = await useCatalogWizard('pa-posi')
    graphAvailable.value = res.type === 'graph'
    wizardAvailable.value = res.type === 'graph'
      ? !!(res.config && res.config.entry_node_id)
      : !!(res.config && res.config.wizard_id)
  } catch { }
  // AI-подбор: есть только если заполнены filter_endpoint/семантика EquipmentType.
  try {
    const { data } = await globalApi.get('/core/ai-schema/pa-posi/')
    aiAvailable.value = !!data.ai_configured
  } catch { }
})

// Вкладки режимов: мастер/AI показываем только при наличии конфигурации.
const tabs = computed(() => {
  const list = [
    { key: 'section', label: 'catalog.mode.section', event: 'section' },
    { key: 'engineer', label: 'catalog.mode.engineer', event: 'engineer' },
    { key: 'quickselect', label: 'catalog.mode.quickselect', event: 'quickselect' },
  ]
  if (wizardAvailable.value) list.push({ key: 'wizard', label: 'catalog.mode.wizard', event: 'wizard' })
  if (aiAvailable.value) list.push({ key: 'ai', label: 'catalog.mode.ai', event: 'ai' })
  return list
})
</script>
<style scoped>
.app { max-width: 1200px; margin: 0 auto; }
</style>
