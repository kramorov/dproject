<template>
  <div class="media-grid">
    <div class="filters">
      <input v-model="search" placeholder="Поиск..." class="filter-input" @input="onFilterChange" />
      <select v-model="selectedCategory" class="filter-select" @change="onFilterChange">
        <option :value="null">Все категории</option>
        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.icon }} {{ c.name }}</option>
      </select>
      <select v-model="selectedEquipmentType" class="filter-select" @change="onFilterChange">
        <option :value="null">Тип оборудования</option>
        <option v-for="e in equipmentTypes" :key="e.id" :value="e.id">{{ e.name }}</option>
      </select>
      <select v-model="selectedBrand" class="filter-select" @change="onFilterChange">
        <option :value="null">Бренд</option>
        <option v-for="b in brands" :key="b.id" :value="b.id">{{ b.name }}</option>
      </select>
      <input v-model="keyword" placeholder="Ключевое слово..." class="filter-input filter-sm" @input="onFilterChange" />
      <button class="refresh-btn" @click="fetchData" :disabled="loading">Обновить</button>
    </div>

    <div v-if="loading" class="status-msg">Загрузка...</div>
    <div v-else-if="error" class="status-msg error">{{ error }}</div>
    <div v-else class="cards">
      <div
        v-for="item in items" :key="item.id"
        class="card" :class="{ inactive: !item.is_active }"
        @click="$emit('select', item)"
      >
        <div class="card-preview">
          <img
            v-if="item.has_file && isImage(item.mime_type)"
            :src="previewUrl(item.id)" :alt="item.title" class="card-img"
          />
          <div v-else-if="item.has_file" class="card-placeholder">{{ iconFor(item.mime_type) }}</div>
          <div v-else class="card-placeholder no-file">∅</div>
        </div>
        <div class="card-body">
          <div class="card-title">{{ item.title || '—' }}</div>
          <div class="card-meta">
            <span v-if="item.category">{{ item.category.icon }} {{ item.category.name }}</span>
            <span v-if="item.brand">{{ item.brand.name }}</span>
          </div>
        </div>
      </div>
      <div v-if="items.length === 0 && !loading" class="status-msg">Ничего не найдено</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import mediaApi from '../api'

const items = ref([])
const categories = ref([])
const equipmentTypes = ref([])
const brands = ref([])
const search = ref('')
const keyword = ref('')
const selectedCategory = ref(null)
const selectedEquipmentType = ref(null)
const selectedBrand = ref(null)
const loading = ref(false)
const error = ref(null)

defineEmits(['select'])
defineExpose({ fetchData })

function previewUrl(id) { return mediaApi.previewUrl(id) }
function isImage(mime) { return mime && mime.startsWith('image/') }
function iconFor(mime) {
  if (!mime) return '📁'
  if (mime.startsWith('image/')) return '🖼️'
  if (mime.includes('pdf')) return '📄'
  if (mime.includes('word') || mime.includes('document')) return '📝'
  if (mime.includes('sheet') || mime.includes('excel')) return '📊'
  if (mime.startsWith('video/')) return '🎬'
  return '📁'
}

let debounceTimer = null
function onFilterChange() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchData, 200)
}

async function fetchData() {
  loading.value = true; error.value = null
  try {
    const params = {}
    if (selectedCategory.value) params.category_id = selectedCategory.value
    if (selectedEquipmentType.value) params.equipment_type_id = selectedEquipmentType.value
    if (selectedBrand.value) params.brand_id = selectedBrand.value
    if (search.value) params.search = search.value
    if (keyword.value) params.keyword = keyword.value

    const { data } = await mediaApi.list(params)
    items.value = Array.isArray(data.data) ? data.data : []

    // Загружаем справочники при первом вызове
    if (!categories.value.length) {
      const [catRes, etRes, brandRes] = await Promise.all([
        mediaApi.list({ model: 'media_library.MediaCategory' }),
        mediaApi.list({ model: 'core.EquipmentType' }),
        mediaApi.list({ model: 'producers.Brands' }),
      ])
      categories.value = Array.isArray(catRes.data.data) ? catRes.data.data : []
      equipmentTypes.value = Array.isArray(etRes.data.data) ? etRes.data.data : []
      brands.value = Array.isArray(brandRes.data.data) ? brandRes.data.data : []
    }
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка загрузки'
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.media-grid { width: 100%; }
.filters {
  display: flex; gap: 8px; margin-bottom: 16px; align-items: center; flex-wrap: wrap;
}
.filter-input {
  flex: 1; padding: 6px 10px; border: 1px solid #d1d5db;
  border-radius: 6px; font-size: 13px; min-width: 120px;
}
.filter-input.filter-sm { flex: 0.7; min-width: 100px; }
.filter-select {
  padding: 6px 10px; border: 1px solid #d1d5db;
  border-radius: 6px; font-size: 13px; min-width: 140px;
}
.refresh-btn {
  padding: 6px 14px; background: #2563eb; color: #fff;
  border: none; border-radius: 6px; cursor: pointer; font-size: 13px; white-space: nowrap;
}
.cards {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px;
}
.card {
  border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;
  cursor: pointer; transition: box-shadow 0.15s; background: #fff;
}
.card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.card.inactive { opacity: 0.5; }
.card-preview {
  height: 120px; background: #f9fafb;
  display: flex; align-items: center; justify-content: center;
}
.card-img { width: 100%; height: 100%; object-fit: cover; }
.card-placeholder { font-size: 32px; }
.card-placeholder.no-file { color: #d1d5db; font-size: 40px; font-weight: 300; }
.card-body { padding: 8px 10px; }
.card-title {
  font-size: 13px; font-weight: 500; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis;
}
.card-meta { font-size: 11px; color: #6b7280; margin-top: 4px; display: flex; gap: 8px; }
.status-msg { grid-column: 1 / -1; text-align: center; padding: 40px; color: #6b7280; }
.status-msg.error { color: #dc2626; }
</style>
