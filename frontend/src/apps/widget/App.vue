<!-- widget/App.vue -->
<template>
  <div class="widget-app">
    <CatalogIndex v-if="route.view === 'index'" :catalogs="allowedCatalogs" @select="catalog => navigate(catalog, 'lines')" />

    <!-- GEARBOX -->
    <CatalogSection v-else-if="route.catalog === 'gearbox' && route.view === 'lines'" :api="gearboxApi" :labels="labels.gearbox.section" @select-series="brandId => navigate('gearbox', 'brand', brandId)" @select="() => navigate('gearbox', 'list')" @quickselect="() => navigate('gearbox', 'quickselect')" @navigate="() => navigate('gearbox', 'lines')" />
    <CatalogModelLine v-else-if="route.catalog === 'gearbox' && route.view === 'brand'" :api="gearboxApi" :labels="labels.gearbox.brand" id-prop="brand_id" :id-value="route.id" @select="id => navigate('gearbox', 'detail', id)" />
    <EngineerSelection v-else-if="route.catalog === 'gearbox' && route.view === 'list'" :api="gearboxApi" :labels="labels.gearbox.list" @select="id => navigate('gearbox', 'detail', id)" @navigate="() => navigate('gearbox', 'lines')" />
    <CatalogDetail v-else-if="route.catalog === 'gearbox' && route.view === 'detail'" :api="gearboxApi" :labels="labels.gearbox.detail" :id="route.id" @close="() => navigate('gearbox', 'list')" @navigate="() => navigate('gearbox', 'lines')" />
    <QuickSelect v-else-if="route.catalog === 'gearbox' && route.view === 'quickselect'" :api="gearboxApi" :labels="labels.gearbox.quickselect" :filter-labels="labels.gearbox.quickselect.filterLabels" :auto-select-rules="labels.gearbox.quickselect.autoSelectRules" @select="id => navigate('gearbox', 'detail', id)" @navigate="() => navigate('gearbox', 'lines')" />

    <!-- FILTER-REGULATOR -->
    <CatalogSection v-else-if="route.catalog === 'filter_regulator' && route.view === 'lines'" :api="frApi" :labels="labels.filter_regulator.section" @select-series="id => navigate('filter_regulator', 'brand', id)" @select="() => navigate('filter_regulator', 'list')" @quickselect="() => navigate('filter_regulator', 'quickselect')" @navigate="() => navigate('filter_regulator', 'lines')" />
    <CatalogModelLine v-else-if="route.catalog === 'filter_regulator' && route.view === 'brand'" :api="frApi" :labels="labels.filter_regulator.brand" id-prop="model_line_id" :id-value="route.id" @select="id => navigate('filter_regulator', 'detail', id)" />
    <EngineerSelection v-else-if="route.catalog === 'filter_regulator' && route.view === 'list'" :api="frApi" :labels="labels.filter_regulator.list" @select="id => navigate('filter_regulator', 'detail', id)" @navigate="() => navigate('filter_regulator', 'lines')" />
    <CatalogDetail v-else-if="route.catalog === 'filter_regulator' && route.view === 'detail'" :api="frApi" :labels="labels.filter_regulator.detail" :id="route.id" @close="() => navigate('filter_regulator', 'list')" @navigate="() => navigate('filter_regulator', 'lines')" />
    <QuickSelect v-else-if="route.catalog === 'filter_regulator' && route.view === 'quickselect'" :api="frApi" :labels="labels.filter_regulator.quickselect" :filter-labels="labels.filter_regulator.quickselect.filterLabels" :auto-select-rules="labels.filter_regulator.quickselect.autoSelectRules" @select="id => navigate('filter_regulator', 'detail', id)" @navigate="() => navigate('filter_regulator', 'lines')" />

    <!-- LIMIT-SWITCH -->
    <CatalogSection v-else-if="route.catalog === 'limit_switch' && route.view === 'lines'" :api="lsbApi" :labels="labels.limit_switch.section" @select-series="id => navigate('limit_switch', 'brand', id)" @select="() => navigate('limit_switch', 'list')" @quickselect="() => navigate('limit_switch', 'quickselect')" @navigate="() => navigate('limit_switch', 'lines')" />
    <CatalogModelLine v-else-if="route.catalog === 'limit_switch' && route.view === 'brand'" :api="lsbApi" :labels="labels.limit_switch.brand" id-prop="model_line_id" :id-value="route.id" @select="id => navigate('limit_switch', 'detail', id)" />
    <EngineerSelection v-else-if="route.catalog === 'limit_switch' && route.view === 'list'" :api="lsbApi" :labels="labels.limit_switch.list" @select="id => navigate('limit_switch', 'detail', id)" @navigate="() => navigate('limit_switch', 'lines')" />
    <CatalogDetail v-else-if="route.catalog === 'limit_switch' && route.view === 'detail'" :api="lsbApi" :labels="labels.limit_switch.detail" :id="route.id" @close="() => navigate('limit_switch', 'list')" @navigate="() => navigate('limit_switch', 'lines')" />
    <QuickSelect v-else-if="route.catalog === 'limit_switch' && route.view === 'quickselect'" :api="lsbApi" :labels="labels.limit_switch.quickselect" :filter-labels="labels.limit_switch.quickselect.filterLabels" :auto-select-rules="labels.limit_switch.quickselect.autoSelectRules" @select="id => navigate('limit_switch', 'detail', id)" @navigate="() => navigate('limit_switch', 'lines')" />

    <!-- SOLENOID VALVES -->
    <CatalogSection v-else-if="route.catalog === 'solenoid_valves' && route.view === 'lines'" :api="svApi" :labels="labels.solenoid_valves.section" @select-series="id => navigate('solenoid_valves', 'brand', id)" @select="() => navigate('solenoid_valves', 'list')" @quickselect="() => navigate('solenoid_valves', 'quickselect')" @navigate="() => navigate('solenoid_valves', 'lines')" />
    <CatalogModelLine v-else-if="route.catalog === 'solenoid_valves' && route.view === 'brand'" :api="svApi" :labels="labels.solenoid_valves.brand" id-prop="model_line_id" :id-value="route.id" @select="id => navigate('solenoid_valves', 'detail', id)" />
    <EngineerSelection v-else-if="route.catalog === 'solenoid_valves' && route.view === 'list'" :api="svApi" :labels="labels.solenoid_valves.list" @select="id => navigate('solenoid_valves', 'detail', id)" @navigate="() => navigate('solenoid_valves', 'lines')" />
    <CatalogDetail v-else-if="route.catalog === 'solenoid_valves' && route.view === 'detail'" :api="svApi" :labels="labels.solenoid_valves.detail" :id="route.id" @close="() => navigate('solenoid_valves', 'list')" @navigate="() => navigate('solenoid_valves', 'lines')" />
    <QuickSelect v-else-if="route.catalog === 'solenoid_valves' && route.view === 'quickselect'" :api="svApi" :labels="labels.solenoid_valves.quickselect" :filter-labels="labels.solenoid_valves.quickselect.filterLabels" :auto-select-rules="labels.solenoid_valves.quickselect.autoSelectRules" @select="id => navigate('solenoid_valves', 'detail', id)" @navigate="() => navigate('solenoid_valves', 'lines')" />

    <div v-else class="not-found"><p>Страница не найдена</p><button @click="navigate('gearbox', 'lines')">Вернуться в каталог</button></div>
  </div>
</template>
<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { parseHash, navigate } from './router.js'
import CatalogIndex from './CatalogIndex.vue'
import CatalogSection from '@/shared/components/catalog/CatalogSection.vue'
import CatalogModelLine from '@/shared/components/catalog/CatalogModelLine.vue'
import EngineerSelection from '@/shared/components/catalog/EngineerSelection.vue'
import CatalogDetail from '@/shared/components/catalog/CatalogDetail.vue'
import QuickSelect from '@/shared/components/catalog/QuickSelect.vue'
import gearboxApi from '@/apps/gearbox-catalog/api'
import frApi from '@/apps/filter-regulator-catalog/api'
import lsbApi from '@/apps/limit-switch-catalog/api'
import svApi from '@/apps/solenoid-valves-catalog/api'
const props = defineProps({ allowedCatalogs: { type: Array, default: () => ['gearbox'] } })
const route = ref(parseHash())
function onHashChange() { route.value = parseHash() }
onMounted(() => window.addEventListener('hashchange', onHashChange))
onUnmounted(() => window.removeEventListener('hashchange', onHashChange))
const labels = {
  gearbox: {
    section: { title:'Редукторы', subtitle:'Выберите серию редуктора', breadcrumbs:[{name:'Каталог'}] },
    brand: { title:'Серия', countLabel:'Товаров:', emptyLabel:'Нет товаров' },
    list: { title:'Редукторы — инженерный подбор', searchPlaceholder:'Поиск...', resultsLabel:'Найдено:', emptyLabel:'Ничего не найдено' },
    detail: { backLabel:'Назад к каталогу' },
    quickselect: { title:'Быстрый подбор', filterLabels:{}, autoSelectRules:{} },
  },
  filter_regulator: {
    section: { title:'Фильтр-регуляторы', subtitle:'Выберите серию фильтр-регулятора', breadcrumbs:[{name:'Каталог'}] },
    brand: { title:'Серия', countLabel:'Товаров:', emptyLabel:'Нет товаров' },
    list: { title:'Фильтр-регуляторы — инженерный подбор', searchPlaceholder:'Поиск...', resultsLabel:'Найдено:', emptyLabel:'Ничего не найдено' },
    detail: { backLabel:'Назад к каталогу' },
    quickselect: { title:'Быстрый подбор', filterLabels:{}, autoSelectRules:{} },
  },
  limit_switch: {
    section: { title:'Блоки концевых выключателей', subtitle:'Выберите серию БКВ', breadcrumbs:[{name:'Каталог'}] },
    brand: { title:'Серия', countLabel:'Товаров:', emptyLabel:'Нет товаров' },
    list: { title:'БКВ — инженерный подбор', searchPlaceholder:'Поиск...', resultsLabel:'Найдено:', emptyLabel:'Ничего не найдено' },
    detail: { backLabel:'Назад к каталогу' },
    quickselect: { title:'Быстрый подбор', filterLabels:{}, autoSelectRules:{} },
  },
  solenoid_valves: {
    section: { title:'Распределительные клапаны', subtitle:'Выберите серию клапана', breadcrumbs:[{name:'Каталог'}] },
    brand: { title:'Серия', countLabel:'Товаров:', emptyLabel:'Нет товаров' },
    list: { title:'Клапаны — инженерный подбор', searchPlaceholder:'Поиск...', resultsLabel:'Найдено:', emptyLabel:'Ничего не найдено' },
    detail: { backLabel:'Назад к каталогу' },
    quickselect: { title:'Быстрый подбор', filterLabels:{}, autoSelectRules:{} },
  },
}
</script>
<style scoped>.widget-app{max-width:1200px;margin:0 auto;padding:16px}.not-found{text-align:center;padding:60px 20px}.not-found button{margin-top:16px;padding:8px 20px;background:#2563eb;color:#fff;border:none;border-radius:6px;cursor:pointer}</style>
