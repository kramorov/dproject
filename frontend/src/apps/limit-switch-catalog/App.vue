<!-- limit-switch-catalog/App.vue -->
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
import lsbApi from './api'
const api = lsbApi
const labels = {
  section: { title:'Блоки концевых выключателей', subtitle:'Выберите серию', icon:'🔌', countLabel:'моделей', breadcrumbs:[{name:'Каталог'},{name:'Блоки концевых выключателей'}], extraButtons:[{key:'quickselect',label:'⚡ Быстрый подбор',event:'quickselect'},{key:'showAll',label:'Показать все',event:'select'}] },
  list: { title:'Блоки концевых выключателей', searchPlaceholder:'Поиск...', resultsLabel:'Найдено:', emptyLabel:'Ничего не найдено' },
  detail: { backLabel:'Назад к каталогу', breadcrumbName:'Блоки концевых выключателей' },
  brand: { title:'Серия', countLabel:'Товаров:', emptyLabel:'Нет товаров', breadcrumbName:'Блоки концевых выключателей' },
  quickselect: { title:'Быстрый подбор', breadcrumbName:'Блоки концевых выключателей', filterLabels:{ sensor_variety_id:'Тип сенсора', points:'Кол-во датчиков', body_material_id:'Материал корпуса', signal_type_id:'Тип сигнала' }, autoSelectRules:{} },
}
const { page, selectedId, idValue, goToList, goToBrand, onSelectItem } = useCatalogRouter(api, { idProp:'model_line_id' })
function goToQuickSelect() { page.value = 'quickselect' }
function goToSection() { page.value = 'section' }
</script>
<style scoped> .app{max-width:1200px;margin:0 auto;padding:16px} </style>