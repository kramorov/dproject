<template>
  <div class="app">
    <h1>📦 Номенклатура (SKU)</h1>
    <div class="tabs">
      <button :class="{act:tab==='list'}" @click="tab='list'">Список</button>
      <button :class="{act:tab==='batch'}" @click="tab='batch'">Групповая обработка</button>
    </div>
    <SkuList v-if="tab==='list'" ref="skuListRef" @edit="openForm" />
    <BatchProcessing v-if="tab==='batch'" />
    <SkuForm v-if="formSku!==null" :sku="formSku" @close="formSku=null" @saved="onSaved" />
  </div>
</template>

<script setup>
import { ref, reactive, provide, onMounted } from 'vue'
import SkuList from './components/SkuList.vue'
import SkuForm from './components/SkuForm.vue'
import BatchProcessing from './components/BatchProcessing.vue'

const tab = ref('list')
const formSku = ref(null)
const skuListRef = ref(null)

const opts = reactive({ brands: [], equipmentTypes: [] })
provide('opts', opts)

onMounted(async () => {
  await loadFilters()
})

async function loadFilters() {
  try {
    const r = await fetch('/api/admin/prices/filters/').then(r => r.json())
    opts.brands = r.brands || []
    opts.equipmentTypes = r.equipment_types || []
  } catch (e) {
    console.error('SKU filter load error:', e)
  }
}

function openForm(sku) { formSku.value = sku }
function onSaved() {
  formSku.value = null
  skuListRef.value?.load()
}
</script>

<style scoped>
.app{max-width:1400px;margin:0 auto;padding:20px;font-family:-apple-system,BlinkMacSystemFont,sans-serif}
h1{margin:0 0 12px;font-size:24px}
.tabs{display:flex;gap:4px;margin-bottom:16px}
.tabs button{padding:6px 16px;border:1px solid #d1d5db;border-radius:4px;background:#fff;cursor:pointer;font-size:14px}
.tabs button.act{background:#2563eb;color:#fff;border-color:#2563eb}
</style>
