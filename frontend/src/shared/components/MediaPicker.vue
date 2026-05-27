<!-- shared/components/MediaPicker.vue — переиспользуемый выбор из медиабиблиотеки -->
<template>
  <div v-if="show" class="mp-overlay" @click.self="$emit('close')">
    <div class="mp-modal">
      <div class="mp-header">
        <h3>{{ title }}</h3>
        <button class="mp-close" @click="$emit('close')">&times;</button>
      </div>

      <!-- Фильтры -->
      <div class="mp-filters">
        <input v-model="search" placeholder="Поиск..." class="mp-search" @input="debouncedFetch" />
        <select v-model="selCategory" class="mp-sel" @change="onFilterChange">
          <option :value="null">Все категории</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.icon }} {{ c.name }}</option>
        </select>
        <select v-model="selEquipmentType" class="mp-sel" @change="onFilterChange">
          <option :value="null">Тип оборудования</option>
          <option v-for="e in equipmentTypes" :key="e.id" :value="e.id">{{ e.name }}</option>
        </select>
      </div>

      <!-- Сетка -->
      <Spinner v-if="loading" />
      <div v-else-if="error" class="mp-error">{{ error }}</div>
      <div v-else class="mp-grid">
        <div v-for="item in items" :key="item.id" class="mp-card"
          :class="{ sel: selectedIds.includes(item.id) }"
          @click="toggle(item.id)">
          <div class="mp-card-check">
            <span v-if="selectedIds.includes(item.id)">☑</span>
            <span v-else>☐</span>
          </div>
          <div class="mp-card-preview">
            <img v-if="isImage(item)" :src="previewUrl(item.id)" :alt="item.name" class="mp-img" />
            <span v-else class="mp-icon">{{ iconFor(item.mime_type) }}</span>
          </div>
          <div class="mp-card-body">
            <div class="mp-card-title">{{ item.name || '—' }}</div>
            <div class="mp-card-meta">
              {{ item.category?.name || '' }}
              {{ item.equipment_type?.name ? '· ' + item.equipment_type.name : '' }}
            </div>
          </div>
        </div>
        <div v-if="!items.length" class="mp-empty">Ничего не найдено</div>
      </div>

      <!-- Пагинация -->
      <div class="mp-pager" v-if="total > limit">
        <button :disabled="offset <= 0" @click="goPage(-1)">←</button>
        <span>{{ offset + 1 }}–{{ Math.min(offset + limit, total) }} из {{ total }}</span>
        <button :disabled="offset + limit >= total" @click="goPage(1)">→</button>
      </div>

      <!-- Действия -->
      <div class="mp-actions">
        <span class="mp-count">Выбрано: {{ selectedIds.length }}</span>
        <button class="mp-btn-cancel" @click="$emit('close')">Отмена</button>
        <button class="mp-btn-ok" :disabled="!selectedIds.length" @click="confirm">
          Добавить выбранное ({{ selectedIds.length }})
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '@/shared/api'
import Spinner from '@/shared/components/Spinner.vue'

const props = defineProps({
  show: Boolean,
  title: { type: String, default: 'Выбрать из медиабиблиотеки' },
  categoryCode: { type: String, default: null },     // предфильтр: 'IMAGE', 'TECH_DOC'
  equipmentTypeId: { type: [Number, String], default: null },
  preselected: { type: Array, default: () => [] },
})
const emit = defineEmits(['close', 'selected'])

const items = ref([])
const categories = ref([])
const equipmentTypes = ref([])
const search = ref('')
const selCategory = ref(null)
const selEquipmentType = ref(props.equipmentTypeId || null)
const selectedIds = ref([...props.preselected])
const loading = ref(false)
const error = ref(null)
const limit = ref(20)
const offset = ref(0)
const total = ref(0)

function previewUrl(id) { return `/api/media/${id}/view/` }
function isImage(item) { return item.mime_type?.startsWith('image/') }
function iconFor(mime) {
  if (!mime) return '📁'
  if (mime.startsWith('image/')) return '🖼️'
  if (mime.includes('pdf')) return '📄'
  return '📁'
}

function toggle(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

function confirm() {
  const selected = items.value.filter(it => selectedIds.value.includes(it.id))
  emit('selected', selected.map(s => ({ id: s.id, name: s.name, url: s.media_file || '' })))
  emit('close')
}

watch(() => props.show, (v) => {
  if (v) {
    selectedIds.value = [...props.preselected]
    offset.value = 0
    fetchData()
    if (!categories.value.length) loadFilters()
  }
})

let timer = null
function debouncedFetch() { clearTimeout(timer); timer = setTimeout(() => { offset.value = 0; fetchData() }, 250) }
function onFilterChange() { offset.value = 0; fetchData() }

async function loadFilters() {
  try {
    const { data } = await api.get('/admin/media/filters/', { params: { scope: 'all' } })
    categories.value = data.category_id || []
    equipmentTypes.value = data.equipment_type_id || []
    // Предвыбор категории по коду
    if (props.categoryCode && !selCategory.value) {
      const match = categories.value.find(c => c.code === props.categoryCode)
      if (match) selCategory.value = match.id
    }
  } catch {}
}

async function fetchData() {
  loading.value = true; error.value = null
  try {
    const params = { model: 'media_library.MediaLibraryItem', fmt: 'compact', limit: limit.value, offset: offset.value }
    if (search.value) params.search = search.value
    if (selCategory.value) params.category_id = selCategory.value
    if (selEquipmentType.value) params.equipment_type_id = selEquipmentType.value
    const { data } = await api.get('/core/', { params })
    items.value = Array.isArray(data.data) ? data.data : []
    total.value = data.total || items.value.length
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка загрузки'
  } finally { loading.value = false }
}

function goPage(dir) {
  offset.value = Math.max(0, offset.value + dir * limit.value)
  fetchData()
}
</script>

<style scoped>
.mp-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.4); display: flex; align-items: center; justify-content: center; z-index: 1100; }
.mp-modal { background: #fff; border-radius: 10px; width: 90%; max-width: 900px; max-height: 85vh; display: flex; flex-direction: column; box-shadow: 0 8px 32px rgba(0,0,0,.15); }
.mp-header { display: flex; justify-content: space-between; align-items: center; padding: 14px 20px; border-bottom: 1px solid #e5e7eb; }
.mp-header h3 { margin: 0; font-size: 16px; }
.mp-close { background: none; border: none; font-size: 22px; cursor: pointer; color: #6b7280; }
.mp-filters { display: flex; gap: 8px; padding: 10px 20px; border-bottom: 1px solid #f3f4f6; }
.mp-search { flex: 1; padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; }
.mp-sel { padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; min-width: 150px; }
.mp-grid { flex: 1; overflow-y: auto; padding: 12px 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; align-content: start; }
.mp-card { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border: 1px solid #e5e7eb; border-radius: 8px; cursor: pointer; transition: all .1s; }
.mp-card:hover { background: #f9fafb; }
.mp-card.sel { border-color: #2563eb; background: #eff6ff; }
.mp-card-check { width: 20px; font-size: 16px; text-align: center; flex-shrink: 0; }
.mp-card-preview { width: 50px; height: 50px; flex-shrink: 0; background: #f3f4f6; border-radius: 4px; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.mp-img { width: 100%; height: 100%; object-fit: cover; }
.mp-icon { font-size: 22px; }
.mp-card-body { flex: 1; min-width: 0; }
.mp-card-title { font-size: 13px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.mp-card-meta { font-size: 11px; color: #6b7280; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.mp-empty { grid-column: 1 / -1; text-align: center; padding: 40px; color: #6b7280; }
.mp-error { text-align: center; padding: 40px; color: #dc2626; }
.mp-pager { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 10px; border-top: 1px solid #f3f4f6; font-size: 13px; color: #6b7280; }
.mp-pager button { padding: 4px 12px; border: 1px solid #d1d5db; border-radius: 4px; background: #fff; cursor: pointer; font-size: 13px; }
.mp-pager button:disabled { opacity: .4; cursor: default; }
.mp-actions { display: flex; align-items: center; gap: 10px; padding: 12px 20px; border-top: 1px solid #e5e7eb; }
.mp-count { flex: 1; font-size: 13px; color: #6b7280; }
.mp-btn-cancel { padding: 6px 16px; border: 1px solid #d1d5db; border-radius: 6px; background: #fff; cursor: pointer; font-size: 13px; }
.mp-btn-ok { padding: 6px 20px; background: #2563eb; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; }
.mp-btn-ok:disabled { opacity: .5; cursor: default; }
.mp-btn-ok:hover:not(:disabled) { background: #1d4ed8; }
</style>
