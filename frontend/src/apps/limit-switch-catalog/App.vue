<!-- limit-switch-catalog/App.vue -->
<template>
  <div class="app">
    <LsbSection
      v-if="page === 'section'"
      @select-series="goToBrand"
      @select="goToList"
    />

    <LsbList
      v-else-if="page === 'list'"
      :filters="filters"
      @select="onSelectItem"
    />

    <LsbDetail
      v-else-if="page === 'detail'"
      :id="selectedId"
      @close="page = 'list'"
    />

    <LsbBrand
      v-else-if="page === 'brand'"
      :model-line-id="modelLineId"
      @select="onSelectItem"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import LsbSection from './components/LsbSection.vue'
import LsbList from './components/LsbList.vue'
import LsbDetail from './components/LsbDetail.vue'
import LsbBrand from './components/LsbBrand.vue'
import lsbApi from './api'

const page = ref('section')
const selectedId = ref(null)
const modelLineId = ref(null)
const filters = reactive({})

onMounted(async () => {
  try {
    const r = await lsbApi.getFilters()
    if (r.data) Object.assign(filters, r.data)
  } catch (e) { console.error('Failed to load filters', e) }
})

function goToList(f = {}) {
  Object.assign(filters, f)
  page.value = 'list'
}

function goToBrand(id) {
  modelLineId.value = id
  page.value = 'brand'
}

function onSelectItem(id) {
  selectedId.value = id
  page.value = 'detail'
}
</script>

<style>
.app { max-width: 1200px; margin: 0 auto; padding: 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
</style>
