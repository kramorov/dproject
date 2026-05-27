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
        v-for="(item, index) in items" :key="item.id"
        class="card" :class="{ inactive: !item.is_active }"
        @click="$emit('select', item)"
      >
        <div class="card-preview" @click.stop="$emit('preview', item, index)">
          <img
            v-if="isPreviewable(item)"
            :src="previewUrl(item.id)" :alt="item.title" class="card-img"
          />
          <div v-else-if="item.has_file" class="card-placeholder">{{ iconFor(item.mime_type) }}</div>
          <div v-else class="card-placeholder no-file">∅</div>
        </div>
        <div class="card-body">
          <div class="card-row card-row-meta">
            <span class="card-cell" :title="(item.category?.icon||'') + ' ' + (item.category?.name||'—')">
              {{ item.category?.icon || '' }} {{ item.category?.name || '—' }}
            </span>
            <span class="card-cell" :title="item.brand?.name || ''">
              {{ item.brand?.name || '—' }}
            </span>
            <span class="card-cell" :title="item.equipment_type?.name || ''">
              {{ item.equipment_type?.name || '—' }}
            </span>
          </div>
          <div class="card-row card-row-title">{{ item.title || '—' }}</div>
        </div>
      </div>
      <div v-if="items.length === 0 && !loading" class="status-msg">Ничего не найдено</div>
      <div class="pagination" v-if="total > limit">
        <select v-model="limit" @change="offset=0;fetchData()" class="limit-select">
          <option :value="10">10</option>
          <option :value="20">20</option>
          <option :value="50">50</option>
        </select>
        <button :disabled="offset === 0" @click="prevPage">← Назад</button>
        <span>{{ offset + 1 }}–{{ Math.min(offset + limit, total) }} из {{ total }}</span>
        <button :disabled="offset + limit >= total" @click="nextPage">Вперёд →</button>
      </div>
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
const limit = ref(20)
const offset = ref(0)
const total = ref(0)

defineEmits(['select', 'preview'])
function getItems() { return items.value }
defineExpose({ fetchData, getItems })

function previewUrl(id) { return mediaApi.previewUrl(id) }
function isImage(mime) { return mime && mime.startsWith('image/') }
function isPreviewable(item) {
  return item.has_file && (isImage(item.mime_type) || item.mime_type === 'application/pdf')
}
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
  debounceTimer = setTimeout(() => { offset.value = 0; fetchData() }, 200)
}

function nextPage() { offset.value += limit.value; fetchData(); window.scrollTo(0,0) }
function prevPage() { offset.value = Math.max(0, offset.value - limit.value); fetchData(); window.scrollTo(0,0) }

async function fetchData() {
  loading.value = true; error.value = null
  try {
    const params = { limit: limit.value, offset: offset.value }
    if (!params.limit) delete params.limit
    if (!params.offset) delete params.offset
    if (selectedCategory.value) params.category_id = selectedCategory.value
    if (selectedEquipmentType.value) params.equipment_type_id = selectedEquipmentType.value
    if (selectedBrand.value) params.brand_id = selectedBrand.value
    if (search.value) params.search = search.value
    if (keyword.value) params.keyword = keyword.value

    const { data } = await mediaApi.list(params)
    items.value = Array.isArray(data.data) ? data.data : []
    total.value = data.total || items.value.length

    // Загружаем опции фильтров при первом вызове
    if (!categories.value.length) {
      try {
        const { data } = await mediaApi.filterOptions()
        categories.value = data.category_id || []
        equipmentTypes.value = data.equipment_type_id || []
        brands.value = data.brand_id || []
      } catch { /* fallback — фильтры будут пустые */ }
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
  display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
}
.card {
  display: flex; flex-direction: row; align-items: stretch;
  border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;
  cursor: pointer; transition: box-shadow 0.15s; background: #fff;
}
.card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.card.inactive { opacity: 0.5; }
.card-preview {
  width: 100px; min-width: 100px; height: 75px; flex-shrink: 0;
  background: #f9fafb;
  display: flex; align-items: center; justify-content: center;
}
.card-img { width: 100%; height: 100%; object-fit: contain; }
.card-placeholder { font-size: 28px; }
.card-placeholder.no-file { color: #d1d5db; font-size: 36px; font-weight: 300; }
.card-body {
  flex: 1; padding: 8px 12px;
  display: flex; flex-direction: column; justify-content: center;
  min-width: 0;
}
.card-row-meta {
  display: flex; gap: 0; margin-bottom: 4px;
}
.card-cell {
  flex: 1; min-width: 0; padding: 0 6px;
  font-size: 11px; color: #6b7280; line-height: 1.3;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.card-cell:first-child { padding-left: 0; }
.card-cell:last-child  { padding-right: 0; }
.card-row-title {
  font-size: 13px; font-weight: 500; line-height: 1.3;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; max-height: 2.6em;
}
.status-msg { grid-column: 1 / -1; text-align: center; padding: 40px; color: #6b7280; }
.status-msg.error { color: #dc2626; }
.pagination { display:flex; justify-content:center; align-items:center; gap:12px; margin-top:20px; padding:16px 0 }
.pagination button { padding:8px 20px; font-size:14px; background:#fff; border:1px solid #d1d5db; border-radius:6px; cursor:pointer }
.pagination button:disabled { opacity:.4; cursor:default }
.pagination button:not(:disabled):hover { border-color:#2563eb; color:#2563eb }
.pagination .limit-select { padding:7px 8px; font-size:14px; border:1px solid #d1d5db; border-radius:6px; background:#fff }
.pagination span { font-size:14px; color:#6b7280 }
</style>