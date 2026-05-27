<!-- gearbox-catalog/App.vue -->
<template>
  <div class="app">
    <CatalogSection v-if="page === 'section'" :api="api" :labels="labels.section" :extra-buttons="labels.section.extraButtons" @select-series="goToBrand" @select="goToList" @quickselect="goToQuickSelect" />
    <CatalogList v-else-if="page === 'list'" :api="api" :labels="labels.list" @select="onSelectItem" />
    <CatalogDetail v-else-if="page === 'detail'" :api="api" :labels="labels.detail" :id="selectedId" @close="page = 'list'" />
    <CatalogBrand v-else-if="page === 'brand'" :api="api" :labels="labels.brand" id-prop="brand_id" :id-value="idValue" @select="onSelectItem" />
    <QuickSelect v-else-if="page === 'quickselect'" :api="api" :labels="labels.quickselect" :filter-labels="labels.quickselect.filterLabels" :auto-select-rules="labels.quickselect.autoSelectRules" @select="onSelectItem" />
  </div>
</template>
<script setup>
import CatalogSection from '@/shared/components/catalog/CatalogSection.vue'
import CatalogList from '@/shared/components/catalog/CatalogList.vue'
import CatalogDetail from '@/shared/components/catalog/CatalogDetail.vue'
import CatalogBrand from '@/shared/components/catalog/CatalogBrand.vue'
import QuickSelect from '@/shared/components/catalog/QuickSelect.vue'
import { useCatalogRouter } from '@/shared/composables/useCatalogRouter.js'
import gearboxApi from './api'
const api = gearboxApi
const labels = {
  section: { title:'Редукторы', subtitle:'Выберите серию редуктора', icon:'⚙️', countLabel:'моделей', breadcrumbs:[{name:'Каталог'},{name:'Редукторы'}], extraButtons:[{key:'quickselect',label:'⚡ Быстрый подбор',event:'quickselect'},{key:'showAll',label:'Показать все',event:'select'}] },
  list: { searchPlaceholder:'Поиск редукторов...', resultsLabel:'Найдено:', emptyLabel:'Ничего не найдено' },
  detail: { backLabel:'Назад к каталогу', breadcrumbName:'Редукторы' },
  brand: { countLabel:'Редукторов:', emptyLabel:'Нет товаров', breadcrumbName:'Редукторы' },
  quickselect: { title:'Быстрый подбор', breadcrumbName:'Редукторы', filterLabels:{ body_material_id:'Материал корпуса', min_work_torque:'Рабочий момент, Нм', mounting_plate_top_id:'Монтажная площадка' }, autoSelectRules:{} },
}
const { page, selectedId, idValue, goToList, goToBrand, onSelectItem } = useCatalogRouter(api, { idProp:'brand_id' })
function goToQuickSelect() { page.value = 'quickselect' }
</script>
<style> *{box-sizing:border-box;margin:0;padding:0} body{font-family:var(--cat-font);background:var(--cat-bg-page);color:var(--cat-text)} .app{max-width:1440px;margin:0 auto;padding:16px} </style>
