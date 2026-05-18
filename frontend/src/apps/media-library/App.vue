<template>
  <div class="media-app">
    <header class="app-header">
      <h1>🖼️ Медиабиблиотека</h1>
      <button class="btn-primary" @click="showUpload = !showUpload">
        {{ showUpload ? '← К списку' : '+ Загрузить' }}
      </button>
    </header>

    <MediaUpload
      v-if="showUpload"
      :categories="categories"
      :brands="brands"
      :equipment-types="equipmentTypes"
      @uploaded="onUploaded"
    />
    <MediaGrid v-else ref="gridRef" @select="onSelectItem" />

    <MediaEdit
      :show="editModalVisible"
      :item="selectedItem"
      :categories="categories"
      :brands="brands"
      :equipment-types="equipmentTypes"
      @close="editModalVisible = false"
      @updated="onUpdated"
      @deleted="onDeleted"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import MediaGrid from './components/MediaGrid.vue'
import MediaUpload from './components/MediaUpload.vue'
import MediaEdit from './components/MediaEdit.vue'
import mediaApi from './api'

const showUpload = ref(false)
const editModalVisible = ref(false)
const selectedItem = ref(null)
const gridRef = ref(null)
const categories = ref([])
const brands = ref([])
const equipmentTypes = ref([])

Promise.all([
  mediaApi.list({ model: 'media_library.MediaCategory' }),
  mediaApi.list({ model: 'producers.Brands' }),
  mediaApi.list({ model: 'core.EquipmentType' }),
]).then(([catRes, brandRes, etRes]) => {
  categories.value = Array.isArray(catRes.data.data) ? catRes.data.data : []
  brands.value = Array.isArray(brandRes.data.data) ? brandRes.data.data : []
  equipmentTypes.value = Array.isArray(etRes.data.data) ? etRes.data.data : []
})

function onUploaded() { showUpload.value = false; gridRef.value?.fetchData() }
function onSelectItem(item) { selectedItem.value = item; editModalVisible.value = true }
function onUpdated() { editModalVisible.value = false; gridRef.value?.fetchData() }
function onDeleted() { editModalVisible.value = false; gridRef.value?.fetchData() }
</script>

<style scoped>
.media-app {
  max-width: 1200px; margin: 0 auto; padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
.app-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.app-header h1 { margin: 0; font-size: 24px; }
.btn-primary {
  padding: 8px 24px; background: #2563eb; color: #fff;
  border: none; border-radius: 6px; font-size: 14px; cursor: pointer;
}
</style>
