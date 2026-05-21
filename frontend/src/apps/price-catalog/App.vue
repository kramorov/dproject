<template>
  <div class="app">
    <h1>💰 Цены</h1>
    <div class="tabs">
      <button :class="{act:tab==='catalog'}" @click="tab='catalog'">Каталог цен</button>
      <button :class="{act:tab==='docs'}" @click="tab='docs'">Документы</button>
    </div>

    <PriceCatalog v-if="tab==='catalog'" />

    <div v-if="tab==='docs'">
      <DocumentJournal
        v-if="!selectedDocId"
        @open="selectedDocId = $event"
      />
      <DocumentCard
        v-else
        :doc-id="selectedDocId"
        @close="selectedDocId = null; docVersion++"
        @changed="docVersion++"
        :key="selectedDocId + '-' + docVersion"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, provide, onMounted } from 'vue'
import PriceCatalog from './components/PriceCatalog.vue'
import DocumentJournal from './components/DocumentJournal.vue'
import DocumentCard from './components/DocumentCard.vue'
import priceApi from './api'

const tab = ref('catalog')
const selectedDocId = ref(null)
const docVersion = ref(0)

const opts = reactive({ varieties: [], currencies: [] })
const contentTypes = ref([])

provide('opts', opts)
provide('contentTypes', contentTypes)

onMounted(async () => {
  try {
    const r = await priceApi.filterOptions()
    opts.varieties = r.data.varieties || []
    opts.currencies = r.data.currencies || []
    contentTypes.value = r.data.equipment_types || []
  } catch {}
})
</script>

<style scoped>
.app{max-width:1300px;margin:0 auto;padding:20px;font-family:-apple-system,BlinkMacSystemFont,sans-serif}
h1{margin:0 0 12px;font-size:24px}
.tabs{display:flex;gap:4px;margin-bottom:16px}
.tabs button{padding:6px 16px;border:1px solid #d1d5db;border-radius:4px;background:#fff;cursor:pointer;font-size:14px}
.tabs button.act{background:#2563eb;color:#fff;border-color:#2563eb}
</style>
