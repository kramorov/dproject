<!-- filter-regulator-catalog/App.vue -->
<!-- Standalone SPA для разработки. Повторяет структуру gearbox App.vue. -->
<template>
  <div class="app">
    <GearboxSection
      v-if="page === 'section'"
      @select-series="goToBrand"
      @select="goToList"
      @engineer="page = 'engineer'"
    />

    <GearboxList
      v-else-if="page === 'list'"
      :filters="filters"
      @select="onSelectItem"
    />

    <GearboxDetail
      v-else-if="page === 'detail'"
      :id="selectedId"
      @close="page = 'list'"
    />

    <GearboxBrand
      v-else-if="page === 'brand'"
      :model-line-id="modelLineId"
      @select="onSelectItem"
    />

    <EngineerCatalog
      v-else-if="page === 'engineer'"
      @select="onSelectItem"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import GearboxSection from './components/GearboxSection.vue'
import GearboxList from './components/GearboxList.vue'
import GearboxDetail from './components/GearboxDetail.vue'
import GearboxBrand from './components/FrBrand.vue'
import EngineerCatalog from './components/EngineerCatalog.vue'
import frApi from './api'

const page = ref('section')
const showEngineer = ref(false)
const selectedId = ref(null)
const modelLineId = ref(null)
const filters = reactive({ loaded: false, data: {} })

function goToList() { page.value = 'list' }
function goToBrand(id) { modelLineId.value = id; page.value = 'brand' }

function onSelectItem(id) {
  selectedId.value = id
  page.value = 'detail'
}

onMounted(async () => {
  if (window.location.hash === '#engineer') page.value = 'engineer'
  try {
    const r = await frApi.getFilters()
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
