<!-- gearbox-catalog/App.vue -->
<template>
  <div class="app">
    <CatalogActions
      :active="activeTab"
      @section="goToSection"
      @engineer="goToList"
      @quickselect="goToQuickSelect"
      @wizard="goToSection"
      @ai="goToSection"
    />
    <CatalogSection v-if="page === 'section'" :api="api" :labels="labels.section" @select-series="goToBrand" @navigate="goToSection" />
    <EngineerSelection v-else-if="page === 'list'" :api="api" :labels="labels.list" @select="onSelectItem" @navigate="goToSection" />
    <CatalogDetail v-else-if="page === 'detail'" :api="api" :labels="labels.detail" :id="selectedId" @close="page = 'list'" @navigate="goToSection" />
    <CatalogModelLine v-else-if="page === 'brand'" :api="api" :labels="labels.brand" id-prop="model_line_id" :id-value="idValue" @select="onSelectItem" @navigate="goToSection" />
    <QuickSelect v-else-if="page === 'quickselect'" :api="api" :labels="labels.quickselect" :filter-labels="labels.quickselect.filterLabels" :auto-select-rules="labels.quickselect.autoSelectRules" @select="onSelectItem" @navigate="goToSection" />
  </div>
</template>
<script setup>
import { computed } from 'vue'
import CatalogActions from '@/shared/components/catalog/CatalogActions.vue'
import CatalogSection from '@/shared/components/catalog/CatalogSection.vue'
import EngineerSelection from '@/shared/components/catalog/EngineerSelection.vue'
import CatalogDetail from '@/shared/components/catalog/CatalogDetail.vue'
import CatalogModelLine from '@/shared/components/catalog/CatalogModelLine.vue'
import QuickSelect from '@/shared/components/catalog/QuickSelect.vue'
import { useCatalogRouter } from '@/shared/composables/useCatalogRouter.js'
import gearboxApi from './api'
const api = gearboxApi
const labels = {
  section: { title:'Редукторы', subtitle:'Выберите серию редуктора', breadcrumbName:'Редукторы' },
  list: { title:'Редукторы — инженерный подбор', searchPlaceholder:'Поиск...', resultsLabel:'Найдено:', emptyLabel:'Ничего не найдено' },
  detail: { backLabel:'Назад к каталогу', breadcrumbName:'Редукторы' },
  brand: { title:'Серия', countLabel:'Товаров:', emptyLabel:'Нет товаров', breadcrumbName:'Редукторы' },
  quickselect: { title:'Быстрый подбор', breadcrumbName:'Редукторы',
    filterLabels:{
      body_material_id:'Материал корпуса', min_work_torque:'Рабочий момент не менее, Нм',
      mounting_plate_top_id:'Монтажная площадка',
    },
    autoSelectRules:{},
  },
}
const { page, selectedId, idValue, goToList, goToBrand, onSelectItem } = useCatalogRouter(api, { idProp:'model_line_id' })
const tabKeys = { section: 'section', brand: 'section', list: 'engineer', quickselect: 'quickselect' }
const activeTab = computed(() => tabKeys[page.value] || 'section')
function goToQuickSelect() { page.value = 'quickselect' }
function goToSection() { page.value = 'section' }
</script>
