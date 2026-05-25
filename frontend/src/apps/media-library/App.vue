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
    <MediaGrid v-else ref="gridRef" @select="onSelectItem" @preview="onPreviewItem" />

    <MediaViewer
      :show="viewerVisible"
      :items="viewerItems"
      :index="viewerIndex"
      @close="viewerVisible = false"
      @update:index="viewerIndex = $event"
    />

    <MediaEdit
      :show="editModalVisible"
      :item="selectedItem"
      :categories="categories"
      :brands="brands"
      :equipment-types="equipmentTypes"
      @close="editModalVisible = false"
      @updated="onUpdated"
      @deleted="onDeleted"
      @preview="onPreviewFromEdit"
      @copied="onCopied"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import MediaGrid from './components/MediaGrid.vue'
import MediaUpload from './components/MediaUpload.vue'
import MediaEdit from './components/MediaEdit.vue'
import MediaViewer from '@/shared/components/MediaViewer.vue'
import mediaApi from './api'

const showUpload = ref(false)
const editModalVisible = ref(false)
const selectedItem = ref(null)
const gridRef = ref(null)
const viewerVisible = ref(false)
const viewerItems = ref([])
const viewerIndex = ref(0)
const categories = ref([])
const brands = ref([])
const equipmentTypes = ref([])

mediaApi.filterOptions('all').then(({ data }) => {
  categories.value = data.category_id || []
  brands.value = data.brand_id || []
  equipmentTypes.value = data.equipment_type_id || []
})

function onUploaded() { showUpload.value = false; gridRef.value?.fetchData() }
function onSelectItem(item) { selectedItem.value = item; editModalVisible.value = true }
function onPreviewItem(item, index) {
  if (!item.has_file) return
  viewerItems.value = [item]
  viewerIndex.value = index
  viewerVisible.value = true
}
function onPreviewFromEdit(item) {
  if (!item.has_file) return
  viewerItems.value = [item]
  viewerIndex.value = 0
  viewerVisible.value = true
}
function onUpdated() { editModalVisible.value = false; gridRef.value?.fetchData() }
function onDeleted() { editModalVisible.value = false; gridRef.value?.fetchData() }
function onCopied(newItem) {
  editModalVisible.value = false
  gridRef.value?.fetchData()
  // Открываем карточку копии после обновления списка
  setTimeout(() => {
    selectedItem.value = newItem
    editModalVisible.value = true
  }, 300)
}
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