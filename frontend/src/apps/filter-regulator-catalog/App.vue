<!-- filter-regulator-catalog/App.vue -->
<!-- Standalone SPA для разработки. Повторяет структуру Fr App.vue. -->
<template>
  <div class="app">
    <FrSection
      v-if="page === 'section'"
      @select-series="goToBrand"
      @select="goToList"
      @engineer="page = 'engineer'"
    />

    <FrList
      v-else-if="page === 'list'"
      :filters="filters"
      @select="onSelectItem"
    />

    <FrDetail
      v-else-if="page === 'detail'"
      :id="selectedId"
      @close="page = 'list'"
    />

    <FrBrand
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
import FrSection from './components/FrSection.vue'
import FrList from './components/FrList.vue'
import FrDetail from './components/FrDetail.vue'
import FrBrand from './components/FrBrand.vue'
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
