<!-- filter-regulator-catalog/App.vue -->
<template>
  <div class="app">
    <CatalogSection v-if="page === 'section'" :api="api" :labels="labels.section" :extra-buttons="labels.section.extraButtons" @select-series="goToBrand" @select="goToList" @quickselect="goToQuickSelect" />
    <CatalogList v-else-if="page === 'list'" :api="api" :labels="labels.list" @select="onSelectItem" @navigate="goToSection" />
    <CatalogDetail v-else-if="page === 'detail'" :api="api" :labels="labels.detail" :id="selectedId" @close="page = 'list'" @navigate="goToSection" />
    <CatalogBrand v-else-if="page === 'brand'" :api="api" :labels="labels.brand" id-prop="model_line_id" :id-value="idValue" @select="onSelectItem" @navigate="goToSection" />
    <QuickSelect v-else-if="page === 'quickselect'" :api="api" :labels="labels.quickselect" :filter-labels="labels.quickselect.filterLabels" :auto-select-rules="labels.quickselect.autoSelectRules" @select="onSelectItem" @navigate="goToSection" />
  </div>
</template>
<script setup>
import CatalogSection from '@/shared/components/catalog/CatalogSection.vue'
import CatalogList from '@/shared/components/catalog/CatalogList.vue'
import CatalogDetail from '@/shared/components/catalog/CatalogDetail.vue'
import CatalogBrand from '@/shared/components/catalog/CatalogBrand.vue'
import QuickSelect from '@/shared/components/catalog/QuickSelect.vue'
import { useCatalogRouter } from '@/shared/composables/useCatalogRouter.js'
import frApi from './api'
const api = frApi
const labels = {
  section: { title:'Фильтр-регуляторы', subtitle:'Выберите серию', icon:'🔧', countLabel:'моделей', breadcrumbs:[{name:'Каталог'},{name:'Фильтр-регуляторы'}], extraButtons:[{key:'quickselect',label:'⚡ Быстрый подбор',event:'quickselect'},{key:'showAll',label:'Показать все',event:'select'}] },
  list: { searchPlaceholder:'Поиск фильтр-регуляторов...', resultsLabel:'Найдено:', emptyLabel:'Ничего не найдено' },
  detail: { backLabel:'Назад к каталогу', breadcrumbName:'Фильтр-регуляторы' },
  brand: { countLabel:'Фильтр-регуляторов:', emptyLabel:'Нет товаров', breadcrumbName:'Фильтр-регуляторы' },
  quickselect: { title:'Быстрый подбор', breadcrumbName:'Фильтр-регуляторы', filterLabels:{ filtration_rating_min:'Тонкость фильтрации, мкм', body_material_id:'Материал корпуса', flow_rate_min:'Расход, л/мин', thread_id:'Резьба портов' }, autoSelectRules:{ filtration_rating_min:'max', flow_rate_min:'min' } },
}
const { page, selectedId, idValue, goToList, goToBrand, onSelectItem } = useCatalogRouter(api, { idProp:'model_line_id' })
function goToQuickSelect() { page.value = 'quickselect' }
function goToSection() { page.value = 'section' }
</script>
<style scoped> .app{max-width:1440px;margin:0 auto;padding:16px} </style>