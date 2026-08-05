<!-- pneumatic-fittings-catalog/App.vue -->
<template>
  <div class="app">
    <Breadcrumbs :items="breadcrumbs" @navigate="goToSection" />
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
    <EngineerSelection v-else-if="page === 'list'" :api="api" :labels="labels.list" @select="id => onSelectItem(id, 'list')" @navigate="goToSection" />
    <CatalogDetail v-else-if="page === 'detail'" :api="api" :labels="labels.detail" :id="selectedId" :parent-mode="parentModeName" @close="page = previousPage" @navigate="goToSection" @title-ready="t => pageSubtitle = t" />
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
    <AiPlaceholder
      v-else-if="page === 'ai'"
      :labels="labels.ai || {}"
      eq-name="Пневмофитинги"
    />
    </KeepAlive>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import Breadcrumbs from '@/shared/components/Breadcrumbs.vue'
import CatalogActions from '@/shared/components/catalog/CatalogActions.vue'
import CatalogSection from '@/shared/components/catalog/CatalogSection.vue'
import EngineerSelection from '@/shared/components/catalog/EngineerSelection.vue'
import CatalogDetail from '@/shared/components/catalog/CatalogDetail.vue'
import CatalogModelLine from '@/shared/components/catalog/CatalogModelLine.vue'
import QuickSelectNoSeries from '@/shared/components/catalog/QuickSelectNoSeries.vue'
import AiPlaceholder from '@/shared/components/catalog/AiPlaceholder.vue'
import WizardSelection from '@/shared/components/catalog/WizardSelection.vue'
import QuestionGraphWizard from '@/shared/components/catalog/QuestionGraphWizard.vue'
import { useCatalogRouter } from '@/shared/composables/useCatalogRouter.js'
import fittingApi from './api'
import globalApi from '@/shared/api'
const api = fittingApi
const equipmentTypeId = 9  // Пневмофитинги

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
const { page, selectedId, idValue, goToList: _goToList, goToBrand: _goToBrand } = useCatalogRouter(api, { idProp:'model_line_id' })
const previousPage = ref('section')
const pageSubtitle = ref('')

const modeNames = { section:'Просмотр по сериям', list:'Инженерный подбор', brand:'Просмотр по сериям', detail:'', quickselect:'Быстрый подбор', wizard:'Мастер подбора', graph:'Мастер подбора', ai:'AI подбор' }
const parentModeName = computed(() => {
  if (page.value === 'detail') return modeNames[previousPage.value] || 'Просмотр по сериям'
  if (page.value === 'brand') return 'Просмотр по сериям'
  return modeNames[page.value] || 'Просмотр по сериям'
})

const eqLabel = 'Фитинги'
const breadcrumbs = computed(() => {
  const items = [{ name:'Каталог', to:'/' }, { name:eqLabel }]
  const mode = parentModeName.value
  if (mode) items.push({ name:mode })
  if (pageSubtitle.value) items.push({ name:pageSubtitle.value })
  return items
})

const tabKeys = { section: 'section', brand: 'section', list: 'engineer', detail:'', quickselect: 'quickselect', wizard: 'wizard', graph: 'wizard' }
const activeTab = computed(() => tabKeys[page.value] || 'section')
function goToList() { cacheEpoch.value++; _goToList() }
function goToBrand(id) { cacheEpoch.value++; _goToBrand(id) }

onMounted(async () => {
  try { await globalApi.get('/core/question-graph/pneumatic_fittings/'); graphAvailable.value = true } catch { }
})

function onSelectItem(id, fromPage) { previousPage.value = fromPage; selectedId.value = id; page.value = 'detail' }
function goToQuickSelect() { cacheEpoch.value++; previousPage.value = page.value; page.value = 'quickselect' }
function goToAi() { previousPage.value = page.value; page.value = 'ai' }
function goToWizard() { cacheEpoch.value++; previousPage.value = page.value; page.value = graphAvailable.value ? 'graph' : 'wizard' }
function goToSection() { cacheEpoch.value++; pageSubtitle.value = ''; previousPage.value = page.value; page.value = 'section' }
</script>
<style scoped>
.app { max-width: 1200px; margin: 0 auto; }
</style>
