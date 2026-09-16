<!-- cable-gland-catalog/App.vue -->
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
      @close="page = previousPage"
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
    <QuestionGraphWizard v-else-if="page === 'graph'" :graph-code="'cable-gland'" :total-label="'найдено'" @select="id => onSelectItem(id, 'graph')" @navigate="goToSection" />
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
      eq-name="Кабельные вводы"
      @navigate="goToSection"
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
import QuickSelectCableType from './components/QuickSelectCableType.vue'
import WizardSelection from '@/shared/components/catalog/WizardSelection.vue'
import QuestionGraphWizard from '@/shared/components/catalog/QuestionGraphWizard.vue'
import AiSelectionPage from '@/pages/AiSelectionPage.vue'
import { useCatalogRouter } from '@/shared/composables/useCatalogRouter.js'
import { useCatalogWizard } from '@/shared/composables/useCatalogWizard'
import cableGlandApi from './api'
const api = cableGlandApi
const equipmentTypeId = 12  // Кабельный ввод

const eqCode = 'cable-gland'
const labels = {
  section: { title:'Кабельные вводы', subtitle:'Выберите серию кабельного ввода', breadcrumbName:'Кабельные вводы' },
  list: { title:'Кабельные вводы — инженерный подбор', searchPlaceholder:'Поиск...', resultsLabel:'Найдено:', emptyLabel:'Ничего не найдено', breadcrumbName:'Кабельные вводы' },
  detail: { backLabel:'Назад к каталогу', breadcrumbName:'Кабельные вводы' },
  brand: { title:'Серия', countLabel:'Товаров:', emptyLabel:'Нет товаров', breadcrumbName:'Кабельные вводы' },
  quickselect: { title:'Быстрый подбор', breadcrumbName:'Кабельные вводы',
    filterLabels:{
      thread_id:'Резьба',
      body_material_id:'Материал корпуса',
      exd_id:'Взрывозащита',
      ip_id:'IP',
      cable_type_id:'Тип кабеля',
      cable_diameter_min:'Кабель от, мм',
      cable_diameter_max:'Кабель до, мм',
      work_temp_min:'Температура от, °С',
    },
    autoSelectRules:{},
  },
  wizard: { breadcrumbName:'Кабельные вводы', wizardTitle:'Мастер подбора кабельных вводов' },
  ai: { breadcrumbName:'Кабельные вводы', aiTitle:'AI подбор кабельных вводов' },
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

const eqLabel = 'Кабельные вводы'
const breadcrumbs = computed(() => {
  const items = [{ name:'Каталог', to:'/' }, { name:eqLabel }]
  const mode = parentModeName.value
  if (mode) items.push({ name:mode })
  if (pageSubtitle.value) items.push({ name:pageSubtitle.value })
  return items
})

const tabKeys = { section:'section', brand:'section', list:'engineer', detail:'', quickselect:'quickselect', wizard:'wizard', graph:'wizard', ai:'ai' }
const activeTab = computed(() => tabKeys[page.value] || 'section')

function goToList() { cacheEpoch.value++; _goToList() }
function goToBrand(id) { cacheEpoch.value++; _goToBrand(id) }

onMounted(async () => {
  try {
    const { type } = await useCatalogWizard('cable-gland')
    graphAvailable.value = type === 'graph'
  } catch { }
})
function onSelectItem(id, fromPage) { previousPage.value = fromPage; selectedId.value = id; page.value = 'detail' }
function goToQuickSelect() { cacheEpoch.value++; previousPage.value = page.value; page.value = 'quickselect' }
function goToWizard() { cacheEpoch.value++; previousPage.value = page.value; page.value = graphAvailable.value ? 'graph' : 'wizard' }
function goToAi() { previousPage.value = page.value; page.value = 'ai' }
function goToSection() { cacheEpoch.value++; pageSubtitle.value = ''; previousPage.value = page.value; page.value = 'section' }
</script>
<style scoped>
.app { max-width: 1200px; margin: 0 auto; }
</style>
