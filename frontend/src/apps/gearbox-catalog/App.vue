<template>
  <div class="app">
    <GearboxList
      v-if="!selectedId"
      :filters="filters"
      @select="selectedId = $event"
    />
    <GearboxDetail
      v-else
      :id="selectedId"
      @close="selectedId = null"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import GearboxList from './components/GearboxList.vue'
import GearboxDetail from './components/GearboxDetail.vue'
import gearboxApi from './api'

const selectedId = ref(null)
const filters = reactive({ loaded: false, data: {} })

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
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f5f5;color:#1a1a1a}
.app{max-width:1440px;margin:0 auto;padding:16px}
</style>
