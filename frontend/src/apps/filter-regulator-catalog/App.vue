<!-- filter-regulator-catalog/App.vue -->
<template>
  <div class="app">
    <CatalogSection v-if="page === 'section'" :api="api" :labels="labels.section" @select-series="goToBrand" @select="goToList" @quickselect="goToQuickSelect" @navigate="goToSection" />
    <EngineerSelection v-else-if="page === 'list'" :api="api" :labels="labels.list" @select="onSelectItem" @navigate="goToSection" />
    <CatalogDetail v-else-if="page === 'detail'" :api="api" :labels="labels.detail" :id="selectedId" @close="page = 'list'" @navigate="goToSection" />
    <CatalogModelLine v-else-if="page === 'brand'" :api="api" :labels="labels.brand" id-prop="model_line_id" :id-value="idValue" @select="onSelectItem" @navigate="goToSection" />
    <QuickSelect v-else-if="page === 'quickselect'" :api="api" :labels="labels.quickselect" :filter-labels="labels.quickselect.filterLabels" :auto-select-rules="labels.quickselect.autoSelectRules" @select="onSelectItem" @navigate="goToSection" />
  </div>
</template>
<script setup>
import CatalogSection from '@/shared/components/catalog/CatalogSection.vue'
import EngineerSelection from '@/shared/components/catalog/EngineerSelection.vue'
import CatalogDetail from '@/shared/components/catalog/CatalogDetail.vue'
import CatalogModelLine from '@/shared/components/catalog/CatalogModelLine.vue'
import QuickSelect from '@/shared/components/catalog/QuickSelect.vue'
import { useCatalogRouter } from '@/shared/composables/useCatalogRouter.js'
import frApi from './api'
const api = frApi
const labels = {
  section: { title:'Фильтр-регуляторы', subtitle:'Выберите серию фильтр-регулятора', breadcrumbs:[{name:'Каталог'},{name:'Фильтр-регуляторы'}] },
  list: { title:'Фильтр-регуляторы — инженерный подбор', searchPlaceholder:'Поиск...', resultsLabel:'Найдено:', emptyLabel:'Ничего не найдено' },
  detail: { backLabel:'Назад к каталогу', breadcrumbName:'Фильтр-регуляторы' },
  brand: { title:'Серия', countLabel:'Товаров:', emptyLabel:'Нет товаров', breadcrumbName:'Фильтр-регуляторы' },
  quickselect: { title:'Быстрый подбор', breadcrumbName:'Фильтр-регуляторы',
    filterLabels:{
      filtration_rating_min:'Тонкость фильтрации, мкм', body_material_id:'Материал корпуса',
      flow_rate_min:'Расход не менее, л/мин', thread_id:'Резьба портов',
    },
    autoSelectRules:{},
  },
}
const { page, selectedId, idValue, goToList, goToBrand, onSelectItem } = useCatalogRouter(api, { idProp:'model_line_id' })
function goToQuickSelect() { page.value = 'quickselect' }
function goToSection() { page.value = 'section' }
</script>
