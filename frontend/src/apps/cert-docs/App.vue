<template>
  <div class="cert-app">
    <header class="app-header">
      <h1>📜 Сертификаты</h1>
      <div class="ha">
        <button class="btn-pri" @click="openCreate">{{ showForm ? '← Список' : '+ Создать' }}</button>
      </div>
    </header>

    <CertEdit v-if="showForm && editMode==='create'" :show="showForm" :opts="opts"
      @saved="onSaved" @cancel="showForm=false" @view-media="onViewMedia" />

    <CertGrid v-else ref="gridRef" :opts="opts"
      @select="onSelect" @view-media="onViewMedia" />

    <CertEdit v-if="showForm && editMode==='edit'" :show="showForm" :item="selectedItem" :opts="opts"
      @saved="onSaved" @deleted="onDeleted" @cancel="showForm=false" @view-media="onViewMedia"
      @copied="onCopied" />

    <MediaViewer :show="viewerShow" :items="viewerItems" :index="0"
      @close="viewerShow=false" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import CertGrid from './components/CertGrid.vue'
import CertEdit from './components/CertEdit.vue'
import MediaViewer from '@/shared/components/MediaViewer.vue'
import certApi from './api'

const showForm = ref(false), editMode = ref('create'), selectedItem = ref(null), gridRef = ref(null)
const viewerShow = ref(false), viewerItems = ref([])
const opts = ref({ varieties: [], brands: [], equipmentTypes: [] })

onMounted(async () => {
  try {
    const { data } = await certApi.filterOptions()
    opts.value.varieties = data.cert_variety_id || []
    opts.value.brands = data.brand_id || []
    opts.value.equipmentTypes = data.equipment_type_id || []
  } catch (e) {
    console.error('Filter options failed', e)
  }
})

function openCreate() { showForm.value=!showForm.value; editMode.value='create'; selectedItem.value=null }
function onSelect(item) { selectedItem.value=item; editMode.value='edit'; showForm.value=true }
function onSaved() { showForm.value=false; selectedItem.value=null; gridRef.value?.fetchData() }
function onDeleted() { showForm.value=false; selectedItem.value=null; gridRef.value?.fetchData() }
function onCopied(newItem) {
  showForm.value = false
  gridRef.value?.fetchData()
  setTimeout(() => { selectedItem.value = newItem; editMode.value = 'edit'; showForm.value = true }, 300)
}
function onViewMedia(id) {
  if (!id) return
  viewerItems.value = [{ id, mime_type: 'application/pdf', has_file: true, title: 'Сертификат' }]
  viewerShow.value = true
}
</script>

<style scoped>
.cert-app { max-width:1300px; margin:0 auto; padding:20px; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }
.app-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
.app-header h1 { margin:0; font-size:24px; }
.btn-pri { padding:8px 20px; background:#2563eb; color:#fff; border:none; border-radius:6px; font-size:14px; cursor:pointer; }
</style>
