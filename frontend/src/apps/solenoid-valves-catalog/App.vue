<!-- solenoid-valves-catalog/App.vue -->
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
    <QuickSelect v-else-if="page === 'quickselect'" :api="api" :labels="labels.quickselect" :filter-labels="labels.quickselect.filterLabels" :auto-select-rules="labels.quickselect.autoSelectRules" @select="id => onSelectItem(id, 'quickselect')" @navigate="goToSection" />
    <QuestionGraphWizard v-else-if="page === 'graph'" :graph-code="'directional-valve'" :total-label="'найдено'" @select="id => onSelectItem(id, 'graph')" @navigate="goToSection" />
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
      eq-name="Соленоидные клапаны"
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
import QuickSelect from '@/shared/components/catalog/QuickSelect.vue'
import AiSelectionPage from '@/pages/AiSelectionPage.vue'
import WizardSelection from '@/shared/components/catalog/WizardSelection.vue'
import { useCatalogRouter } from '@/shared/composables/useCatalogRouter.js'
import { useCatalogWizard } from '@/shared/composables/useCatalogWizard'
import QuestionGraphWizard from '@/shared/components/catalog/QuestionGraphWizard.vue'
import svApi from './api'
const api = svApi
const equipmentTypeId = 7  // Соленоидные клапаны

const eqCode = 'directional-valve'
const labels = {
  section: { title:'Распределительные клапаны', subtitle:'Выберите серию клапана', breadcrumbName:'Клапаны' },
  list: { title:'Клапаны — инженерный подбор', searchPlaceholder:'Поиск...', resultsLabel:'Найдено:', emptyLabel:'Ничего не найдено' },
  detail: { backLabel:'Назад к каталогу', breadcrumbName:'Клапаны' },
  brand: { title:'Серия', countLabel:'Товаров:', emptyLabel:'Нет товаров', breadcrumbName:'Клапаны' },
  quickselect: { title:'Быстрый подбор', breadcrumbName:'Клапаны',
    filterLabels:{
      function_id:'Схема', actuation_id:'Управление', power_supply_id:'Напряжение соленоида',
      body_material_id:'Материал корпуса', pneumatic_connection_id:'Пневматическое присоединение',
      pneumatic_connection_thread_id:'Резьба присоединения', work_temp_min:'Температура мин., °С',
      ip_id:'IP', exd_id:'Взрывозащита',
    },
    autoSelectRules:{},
  },
  wizard: { breadcrumbName:'Соленоидные клапаны', wizardTitle:'Мастер подбора Соленоидные клапаны' },
}
const cacheEpoch = ref(0)
const graphAvailable = ref(false)
const { page, selectedId, idValue, goToList: _goToList, goToBrand: _goToBrand } = useCatalogRouter(api, { idProp:'model_line_id' })
const previousPage = ref('section')
const pageSubtitle = ref('')

const modeNames = { section:'Просмотр по сериям', list:'Инженерный подбор', brand:'Просмотр по сериям', detail:'', quickselect:'Быстрый подбор', wizard:'Мастер подбора', ai:'AI подбор' }
const parentModeName = computed(() => {
  if (page.value === 'detail') return modeNames[previousPage.value] || 'Просмотр по сериям'
  if (page.value === 'brand') return 'Просмотр по сериям'
  return modeNames[page.value] || 'Просмотр по сериям'
})

const eqLabel = 'Клапаны'
const breadcrumbs = computed(() => {
  const items = [{ name:'Каталог', to:'/' }, { name:eqLabel }]
  const mode = parentModeName.value
  if (mode) items.push({ name:mode })
  if (pageSubtitle.value) items.push({ name:pageSubtitle.value })
  return items
})

const tabKeys = { section: 'section', brand: 'section', list: 'engineer', detail:'', quickselect: 'quickselect', wizard: 'wizard' }
function goToList() { cacheEpoch.value++; _goToList() }
function goToBrand(id) { cacheEpoch.value++; _goToBrand(id) }

onMounted(async () => {
  try {
    const { type } = await useCatalogWizard('directional-valve')
    graphAvailable.value = type === 'graph'
  } catch { }
})
const activeTab = computed(() => tabKeys[page.value] || 'section')

function onSelectItem(id, fromPage) { previousPage.value = fromPage; selectedId.value = id; page.value = 'detail' }
function goToQuickSelect() { cacheEpoch.value++; previousPage.value = page.value; page.value = 'quickselect' }
function goToAi() { previousPage.value = page.value; page.value = 'ai' }
function goToWizard() { cacheEpoch.value++; previousPage.value = page.value; page.value = graphAvailable.value ? 'graph' : 'wizard' }
function goToSection() { cacheEpoch.value++; pageSubtitle.value = ''; previousPage.value = page.value; page.value = 'section' }
</script>
<style scoped>
.app { max-width: 1200px; margin: 0 auto; }
</style>
