<!-- widget/App.vue — Роутер. Слушает hashchange, рендерит нужный каталог. -->
<template>
  <div class="widget-app">
    <!-- Индекс: список доступных каталогов -->
    <CatalogIndex
      v-if="route.view === 'index'"
      :catalogs="allowedCatalogs"
      @select="catalog => navigate(catalog, 'lines')"
    />

    <!-- Страница серий -->
    <GearboxSection
      v-else-if="route.catalog === 'gearbox' && route.view === 'lines'"
      @select-series="brandId => navigate('gearbox', 'brand', brandId)"
      @select="navigate('gearbox', 'list')"
    />

    <!-- Каталог с фильтрами -->
    <GearboxList
      v-else-if="route.catalog === 'gearbox' && route.view === 'list'"
      @select="id => navigate('gearbox', 'detail', id)"
    />

    <!-- Карточка товара -->
    <GearboxDetail
      v-else-if="route.catalog === 'gearbox' && route.view === 'detail'"
      :id="route.id"
      @close="navigate('gearbox', 'list')"
    />

    <!-- Витрина бренда -->
    <GearboxBrand
      v-else-if="route.catalog === 'gearbox' && route.view === 'brand'"
      :brand-id="route.id"
      @select="id => navigate('gearbox', 'detail', id)"
    />

    <!-- ===== FILTER-REGULATOR ===== -->
    <FrSection
      v-else-if="route.catalog === 'filter_regulator' && route.view === 'lines'"
      @select-series="brandId => navigate('filter_regulator', 'brand', brandId)"
      @select="navigate('filter_regulator', 'list')"
    />
    <FrList
      v-else-if="route.catalog === 'filter_regulator' && route.view === 'list'"
      @select="id => navigate('filter_regulator', 'detail', id)"
    />
    <FrDetail
      v-else-if="route.catalog === 'filter_regulator' && route.view === 'detail'"
      :id="route.id"
      @close="navigate('filter_regulator', 'list')"
    />
    <FrBrand
      v-else-if="route.catalog === 'filter_regulator' && route.view === 'brand'"
      :model-line-id="route.id"
      @select="id => navigate('filter_regulator', 'detail', id)"
    />
    <FrEngineer
      v-else-if="route.catalog === 'filter_regulator' && route.view === 'engineer'"
      @select="id => navigate('filter_regulator', 'detail', id)"
    />

    <!-- 404 -->
    <div v-else class="not-found">
      <p>Страница не найдена</p>
      <button @click="navigate('gearbox', 'lines')">Вернуться в каталог</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { parseHash, navigate } from './router.js'

// Компоненты каталогов — импортируются из их директорий
import CatalogIndex from './CatalogIndex.vue'
import GearboxSection from '@/apps/gearbox-catalog/components/GearboxSection.vue'
import GearboxList from '@/apps/gearbox-catalog/components/GearboxList.vue'
import GearboxDetail from '@/apps/gearbox-catalog/components/GearboxDetail.vue'
import GearboxBrand from '@/apps/gearbox-catalog/components/GearboxBrand.vue'
import FrSection from '@/apps/filter-regulator-catalog/components/GearboxSection.vue'
import FrList from '@/apps/filter-regulator-catalog/components/GearboxList.vue'
import FrDetail from '@/apps/filter-regulator-catalog/components/GearboxDetail.vue'
import FrBrand from '@/apps/filter-regulator-catalog/components/GearboxBrand.vue'
import FrEngineer from '@/apps/filter-regulator-catalog/components/EngineerCatalog.vue'

const props = defineProps({
  /** Список разрешённых каталогов (из конфига виджета) */
  allowedCatalogs: { type: Array, default: () => ['gearbox'] },
})

const route = ref(parseHash())

function onHashChange() {
  route.value = parseHash()
}

onMounted(() => window.addEventListener('hashchange', onHashChange))
onUnmounted(() => window.removeEventListener('hashchange', onHashChange))
</script>

<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--cat-font);background:var(--cat-bg-page);color:var(--cat-text)}
.widget-app{max-width:1440px;margin:0 auto;padding:16px}
.not-found{text-align:center;padding:60px 20px;color:var(--cat-muted-light)}
.not-found button{margin-top:12px;padding:8px 20px;cursor:pointer}
</style>
