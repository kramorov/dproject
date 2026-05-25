<template>
  <div class="app">
    <!-- Страница серий -->
    <GearboxSection
      v-if="page === 'section'"
      @select-series="goToBrand"
      @select="goToList"
    />

    <!-- Страница подбора (каталог с фильтрами) -->
    <GearboxList
      v-else-if="page === 'list'"
      :filters="filters"
      @select="onSelectItem"
    />

    <!-- Страница карточки товара -->
    <GearboxDetail
      v-else-if="page === 'detail'"
      :id="selectedId"
      @close="page = 'list'"
    />

    <!-- Страница бренда -->
    <GearboxBrand
      v-else-if="page === 'brand'"
      :brand-id="brandId"
      @select="onSelectItem"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import GearboxSection from './components/GearboxSection.vue'
import GearboxList from './components/GearboxList.vue'
import GearboxDetail from './components/GearboxDetail.vue'
import GearboxBrand from './components/GearboxBrand.vue'
import gearboxApi from './api'

const page = ref('section')
const selectedId = ref(null)
const brandId = ref(null)
const filters = reactive({ loaded: false, data: {} })

function goToList() { page.value = 'list' }
function goToBrand(id) { brandId.value = id; page.value = 'brand' }

function onSelectItem(id) {
  selectedId.value = id
  page.value = 'detail'
}

// Предзагрузка фильтров
onMounted(async () => {
  try {
    const r = await gearboxApi.getFilters()
    filters.data = r.data || {}
    filters.loaded = true
  } catch (e) {
    console.error('Failed to load filters', e)
    filters.loaded = true
  }
})
</script>

<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--cat-font);background:var(--cat-bg-page);color:var(--cat-text)}
.app{max-width:1440px;margin:0 auto;padding:16px}
</style>