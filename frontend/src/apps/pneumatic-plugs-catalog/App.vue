<!-- pneumatic-plugs-catalog/App.vue -->
<template>
  <div class="app">
    <Breadcrumbs :items="breadcrumbs" @navigate="goToSection" />
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
    <CatalogDetail v-else-if="page === 'detail'" :api="api" :labels="labels.detail" :id="selectedId" :parent-mode="parentModeName" @close="page = previousPage" @navigate="goToSection" @title-ready="t => pageSubtitle = t" />
    <CatalogModelLine v-else-if="page === 'brand'" :api="api" :labels="labels.brand" id-prop="model_line_id" :id-value="idValue" :parent-mode="parentModeName" @select="id => onSelectItem(id, 'brand')" @navigate="goToSection" @title-ready="t => pageSubtitle = t" />
    <QuickSelectNoSeries v-else-if="page === 'quickselect'" :api="api" :labels="labels.quickselect" :filter-labels="labels.quickselect.filterLabels" :auto-select-rules="labels.quickselect.autoSelectRules" @select="id => onSelectItem(id, 'quickselect')" @navigate="goToSection" />
    </KeepAlive>
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
import QuickSelectNoSeries from '@/shared/components/catalog/QuickSelectNoSeries.vue'
import { useCatalogRouter } from '@/shared/composables/useCatalogRouter.js'
import plugApi from './api'

const api = plugApi

const tabs = [
  { key: 'section',     label: 'Просмотр по сериям', event: 'section' },
  { key: 'engineer',    label: 'Инженерный подбор',  event: 'engineer' },
  { key: 'quickselect', label: 'Быстрый подбор',     event: 'quickselect' },
]

const labels = {
  section: { title:'Заглушки пневматические', subtitle:'Выберите серию заглушек', breadcrumbName:'Заглушки' },
  list: { title:'Заглушки — инженерный подбор', searchPlaceholder:'Поиск...', resultsLabel:'Найдено:', emptyLabel:'Ничего не найдено' },
  detail: { backLabel:'Назад к каталогу', breadcrumbName:'Заглушки' },
  brand: { title:'Серия', countLabel:'Товаров:', emptyLabel:'Нет товаров', breadcrumbName:'Заглушки' },
  quickselect: { title:'Быстрый подбор', breadcrumbName:'Заглушки',
    filterLabels:{
      thread_id:'Резьба', thread_inner_outer_id:'Резьба (нар/внут)',
      body_material_id:'Материал корпуса',
    },
    autoSelectRules:{},
  },
}

const cacheEpoch = ref(0)
const { page, selectedId, idValue, goToList: _goToList, goToBrand: _goToBrand } = useCatalogRouter(api, { idProp:'model_line_id' })
const previousPage = ref('section')
const pageSubtitle = ref('')

const modeNames = { section:'Просмотр по сериям', list:'Инженерный подбор', brand:'Просмотр по сериям', detail:'', quickselect:'Быстрый подбор' }
const parentModeName = computed(() => {
  if (page.value === 'detail') return modeNames[previousPage.value] || 'Просмотр по сериям'
  if (page.value === 'brand') return 'Просмотр по сериям'
  return modeNames[page.value] || 'Просмотр по сериям'
})

const eqLabel = 'Заглушки'
const breadcrumbs = computed(() => {
  const items = [{ name:'Каталог', to:'/' }, { name:eqLabel }]
  const mode = parentModeName.value
  if (mode) items.push({ name:mode })
  if (pageSubtitle.value) items.push({ name:pageSubtitle.value })
  return items
})

const tabKeys = { section: 'section', brand: 'section', list: 'engineer', detail:'', quickselect: 'quickselect' }
const activeTab = computed(() => tabKeys[page.value] || 'section')
function goToList() { cacheEpoch.value++; _goToList() }
function goToBrand(id) { cacheEpoch.value++; _goToBrand(id) }

function onSelectItem(id, fromPage) { previousPage.value = fromPage; selectedId.value = id; page.value = 'detail' }
function goToQuickSelect() { cacheEpoch.value++; previousPage.value = page.value; page.value = 'quickselect' }
function goToSection() { cacheEpoch.value++; pageSubtitle.value = ''; previousPage.value = page.value; page.value = 'section' }
</script>
<style scoped>
.app { max-width: 1200px; margin: 0 auto; }
</style>
