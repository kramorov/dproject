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
      @ai="goToSection"
    />
    <CatalogSection v-if="page === 'section'" :api="api" :labels="labels.section" @select-series="goToBrand" @navigate="goToSection" />
    <EngineerSelection v-else-if="page === 'list'" :api="api" :labels="labels.list" @select="id => onSelectItem(id, 'list')" @navigate="goToSection" />
    <CatalogDetail v-else-if="page === 'detail'" :api="api" :labels="labels.detail" :id="selectedId" :parent-mode="parentModeName" @close="page = previousPage" @navigate="goToSection" @title-ready="t => pageSubtitle = t" />
    <CatalogModelLine v-else-if="page === 'brand'" :api="api" :labels="labels.brand" id-prop="model_line_id" :id-value="idValue" :parent-mode="parentModeName" @select="id => onSelectItem(id, 'brand')" @navigate="goToSection" @title-ready="t => pageSubtitle = t" />
    <QuickSelect v-else-if="page === 'quickselect'" :api="api" :labels="labels.quickselect" :filter-labels="labels.quickselect.filterLabels" :auto-select-rules="labels.quickselect.autoSelectRules" @select="id => onSelectItem(id, 'quickselect')" @navigate="goToSection" />
    <WizardSelection
      v-else-if="page === 'wizard'"
      :equipment-type-id="equipmentTypeId"
      :labels="labels.wizard"
      @select="id => onSelectItem(id, 'wizard')"
      @navigate="goToSection"
    />
  </div>
</template>
<script setup>
import { ref, computed } from 'vue'
import Breadcrumbs from '@/shared/components/Breadcrumbs.vue'
import CatalogActions from '@/shared/components/catalog/CatalogActions.vue'
import CatalogSection from '@/shared/components/catalog/CatalogSection.vue'
import EngineerSelection from '@/shared/components/catalog/EngineerSelection.vue'
import CatalogDetail from '@/shared/components/catalog/CatalogDetail.vue'
import CatalogModelLine from '@/shared/components/catalog/CatalogModelLine.vue'
import QuickSelect from '@/shared/components/catalog/QuickSelect.vue'
import WizardSelection from '@/shared/components/catalog/WizardSelection.vue'
import { useCatalogRouter } from '@/shared/composables/useCatalogRouter.js'
import fittingApi from './api'
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
}
const { page, selectedId, idValue, goToList, goToBrand } = useCatalogRouter(api, { idProp:'model_line_id' })
const previousPage = ref('section')
const pageSubtitle = ref('')

const modeNames = { section:'Просмотр по сериям', list:'Инженерный подбор', brand:'Просмотр по сериям', detail:'', quickselect:'Быстрый подбор', wizard:'Мастер подбора', ai:'AI подбор' }
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

const tabKeys = { section: 'section', brand: 'section', list: 'engineer', detail:'', quickselect: 'quickselect', wizard: 'wizard' }
const activeTab = computed(() => tabKeys[page.value] || 'section')

function onSelectItem(id, fromPage) { previousPage.value = fromPage; selectedId.value = id; page.value = 'detail' }
function goToQuickSelect() { previousPage.value = page.value; page.value = 'quickselect' }
function goToWizard() { previousPage.value = page.value; page.value = 'wizard' }
function goToSection() { pageSubtitle.value = ''; previousPage.value = page.value; page.value = 'section' }
</script>
<style scoped>
.app { max-width: 1200px; margin: 0 auto; }
</style>
