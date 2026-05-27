<!-- widget/App.vue -->
<template>
  <div class="widget-app">
    <CatalogIndex v-if="route.view === 'index'" :catalogs="allowedCatalogs" @select="catalog => navigate(catalog, 'lines')" />

    <!-- GEARBOX -->
    <CatalogSection v-else-if="route.catalog === 'gearbox' && route.view === 'lines'" :api="gearboxApi" :labels="labels.gearbox.section" :extra-buttons="labels.gearbox.section.extraButtons" @select-series="brandId => navigate('gearbox', 'brand', brandId)" @select="navigate('gearbox', 'list')" @quickselect="navigate('gearbox', 'quickselect')" />
    <CatalogList v-else-if="route.catalog === 'gearbox' && route.view === 'list'" :api="gearboxApi" :labels="labels.gearbox.list" @select="id => navigate('gearbox', 'detail', id)" />
    <CatalogDetail v-else-if="route.catalog === 'gearbox' && route.view === 'detail'" :api="gearboxApi" :labels="labels.gearbox.detail" :id="route.id" @close="navigate('gearbox', 'list')" />
    <CatalogBrand v-else-if="route.catalog === 'gearbox' && route.view === 'brand'" :api="gearboxApi" :labels="labels.gearbox.brand" id-prop="brand_id" :id-value="route.id" @select="id => navigate('gearbox', 'detail', id)" />
    <QuickSelect v-else-if="route.catalog === 'gearbox' && route.view === 'quickselect'" :api="gearboxApi" :labels="labels.gearbox.quickselect" :filter-labels="labels.gearbox.quickselect.filterLabels" :auto-select-rules="labels.gearbox.quickselect.autoSelectRules" @select="id => navigate('gearbox', 'detail', id)" />

    <!-- FILTER-REGULATOR -->
    <CatalogSection v-else-if="route.catalog === 'filter_regulator' && route.view === 'lines'" :api="frApi" :labels="labels.filter_regulator.section" :extra-buttons="labels.filter_regulator.section.extraButtons" @select-series="brandId => navigate('filter_regulator', 'brand', brandId)" @select="navigate('filter_regulator', 'list')" @quickselect="navigate('filter_regulator', 'quickselect')" />
    <CatalogList v-else-if="route.catalog === 'filter_regulator' && route.view === 'list'" :api="frApi" :labels="labels.filter_regulator.list" @select="id => navigate('filter_regulator', 'detail', id)" />
    <CatalogDetail v-else-if="route.catalog === 'filter_regulator' && route.view === 'detail'" :api="frApi" :labels="labels.filter_regulator.detail" :id="route.id" @close="navigate('filter_regulator', 'list')" />
    <CatalogBrand v-else-if="route.catalog === 'filter_regulator' && route.view === 'brand'" :api="frApi" :labels="labels.filter_regulator.brand" id-prop="model_line_id" :id-value="route.id" @select="id => navigate('filter_regulator', 'detail', id)" />
    <QuickSelect v-else-if="route.catalog === 'filter_regulator' && route.view === 'quickselect'" :api="frApi" :labels="labels.filter_regulator.quickselect" :filter-labels="labels.filter_regulator.quickselect.filterLabels" :auto-select-rules="labels.filter_regulator.quickselect.autoSelectRules" @select="id => navigate('filter_regulator', 'detail', id)" />

    <!-- LIMIT-SWITCH -->
    <CatalogSection v-else-if="route.catalog === 'limit_switch' && route.view === 'lines'" :api="lsbApi" :labels="labels.limit_switch.section" :extra-buttons="labels.limit_switch.section.extraButtons" @select-series="brandId => navigate('limit_switch', 'brand', brandId)" @select="navigate('limit_switch', 'list')" @quickselect="navigate('limit_switch', 'quickselect')" />
    <CatalogList v-else-if="route.catalog === 'limit_switch' && route.view === 'list'" :api="lsbApi" :labels="labels.limit_switch.list" @select="id => navigate('limit_switch', 'detail', id)" />
    <CatalogDetail v-else-if="route.catalog === 'limit_switch' && route.view === 'detail'" :api="lsbApi" :labels="labels.limit_switch.detail" :id="route.id" @close="navigate('limit_switch', 'list')" />
    <CatalogBrand v-else-if="route.catalog === 'limit_switch' && route.view === 'brand'" :api="lsbApi" :labels="labels.limit_switch.brand" id-prop="model_line_id" :id-value="route.id" @select="id => navigate('limit_switch', 'detail', id)" />
    <QuickSelect v-else-if="route.catalog === 'limit_switch' && route.view === 'quickselect'" :api="lsbApi" :labels="labels.limit_switch.quickselect" :filter-labels="labels.limit_switch.quickselect.filterLabels" :auto-select-rules="labels.limit_switch.quickselect.autoSelectRules" @select="id => navigate('limit_switch', 'detail', id)" />

    <div v-else class="not-found"><p>Страница не найдена</p><button @click="navigate('gearbox', 'lines')">Вернуться в каталог</button></div>
  </div>
</template>
<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { parseHash, navigate } from './router.js'
import CatalogIndex from './CatalogIndex.vue'
import CatalogSection from '@/shared/components/catalog/CatalogSection.vue'
import CatalogList from '@/shared/components/catalog/CatalogList.vue'
import CatalogDetail from '@/shared/components/catalog/CatalogDetail.vue'
import CatalogBrand from '@/shared/components/catalog/CatalogBrand.vue'
import QuickSelect from '@/shared/components/catalog/QuickSelect.vue'
import gearboxApi from '@/apps/gearbox-catalog/api'
import frApi from '@/apps/filter-regulator-catalog/api'
import lsbApi from '@/apps/limit-switch-catalog/api'
const props = defineProps({ allowedCatalogs: { type: Array, default: () => ['gearbox'] } })
const route = ref(parseHash())
function onHashChange() { route.value = parseHash() }
onMounted(() => window.addEventListener('hashchange', onHashChange))
onUnmounted(() => window.removeEventListener('hashchange', onHashChange))
const labels = {
  gearbox: {
    section: { title:'Редукторы', subtitle:'Выберите серию', icon:'⚙️', countLabel:'моделей', breadcrumbs:[{name:'Каталог'},{name:'Редукторы'}], extraButtons:[{key:'quickselect',label:'⚡ Быстрый подбор',event:'quickselect'},{key:'showAll',label:'Показать все',event:'select'}] },
    list: { searchPlaceholder:'Поиск редукторов...', resultsLabel:'Найдено:', emptyLabel:'Ничего не найдено' },
    detail: { backLabel:'Назад к каталогу', breadcrumbName:'Редукторы' },
    brand: { countLabel:'Редукторов:', emptyLabel:'Нет товаров', breadcrumbName:'Редукторы' },
    quickselect: { title:'Быстрый подбор', breadcrumbName:'Редукторы', filterLabels:{ body_material_id:'Материал корпуса', min_work_torque:'Рабочий момент, Нм', mounting_plate_top_id:'Монтажная площадка' }, autoSelectRules:{} },
  },
  filter_regulator: {
    section: { title:'Фильтр-регуляторы', subtitle:'Выберите серию', icon:'🔧', countLabel:'моделей', breadcrumbs:[{name:'Каталог'},{name:'Фильтр-регуляторы'}], extraButtons:[{key:'quickselect',label:'⚡ Быстрый подбор',event:'quickselect'},{key:'showAll',label:'Показать все',event:'select'}] },
    list: { searchPlaceholder:'Поиск фильтр-регуляторов...', resultsLabel:'Найдено:', emptyLabel:'Ничего не найдено' },
    detail: { backLabel:'Назад к каталогу', breadcrumbName:'Фильтр-регуляторы' },
    brand: { countLabel:'Фильтр-регуляторов:', emptyLabel:'Нет товаров', breadcrumbName:'Фильтр-регуляторы' },
    quickselect: { title:'Быстрый подбор', breadcrumbName:'Фильтр-регуляторы', filterLabels:{ filtration_rating_min:'Тонкость фильтрации, мкм', body_material_id:'Материал корпуса', flow_rate_min:'Расход, л/мин', thread_id:'Резьба портов' }, autoSelectRules:{ filtration_rating_min:'max', flow_rate_min:'min' } },
  },
  limit_switch: {
    section: { title:'Блоки концевых выключателей', subtitle:'Выберите серию', icon:'🔌', countLabel:'моделей', breadcrumbs:[{name:'Каталог'},{name:'Блоки концевых выключателей'}], extraButtons:[{key:'quickselect',label:'⚡ Быстрый подбор',event:'quickselect'},{key:'showAll',label:'Показать все',event:'select'}] },
    list: { title:'Блоки концевых выключателей', searchPlaceholder:'Поиск...', resultsLabel:'Найдено:', emptyLabel:'Ничего не найдено' },
    detail: { backLabel:'Назад к каталогу', breadcrumbName:'Блоки концевых выключателей' },
    brand: { title:'Серия', countLabel:'Товаров:', emptyLabel:'Нет товаров', breadcrumbName:'Блоки концевых выключателей' },
    quickselect: { title:'Быстрый подбор', breadcrumbName:'Блоки концевых выключателей', filterLabels:{ sensor_variety_id:'Тип сенсора', points:'Кол-во датчиков', body_material_id:'Материал корпуса', signal_type_id:'Тип сигнала' }, autoSelectRules:{} },
  },
}
</script>
<style> *{box-sizing:border-box;margin:0;padding:0} body{font-family:var(--cat-font);background:var(--cat-bg-page);color:var(--cat-text)} .widget-app{max-width:1440px;margin:0 auto;padding:16px} .not-found{text-align:center;padding:60px 20px;color:var(--cat-muted-light)} .not-found button{margin-top:12px;padding:8px 20px;cursor:pointer} </style>
