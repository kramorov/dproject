<!-- apps/limit-switch-admin/components/AdminTable.vue — переиспользуемая таблица -->
<template>
  <div class="admin-table">
    <div class="at-toolbar">
      <input v-model="searchText" class="at-search" :placeholder="searchPlaceholder || 'Поиск...'"
        @input="debouncedSearch" />
      <button class="at-btn" @click="$emit('create')">+ {{ createLabel || 'Создать' }}</button>
    </div>

    <Spinner v-if="loading" />
    <div v-else-if="error" class="at-error">{{ error }}</div>

    <table v-else class="at-tbl">
      <thead>
        <tr>
          <th v-for="col in columns" :key="col.key" :style="col.width ? { width: col.width } : {}">
            {{ col.label }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="!items.length">
          <td :colspan="columns.length" class="at-empty">Ничего не найдено</td>
        </tr>
        <tr v-for="item in items" :key="item.id" class="at-row" :class="{ ina: item.is_active === false }"
          @click="$emit('select', item)">
          <td v-for="col in columns" :key="col.key">
            <slot :name="'cell-' + col.key" :item="item" :value="getNested(item, col.key)">
              <span :class="col.class">{{ getNested(item, col.key) }}</span>
            </slot>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="at-pager" v-if="total > pageSize">
      <button :disabled="offset <= 0" @click="goPage(offset - pageSize)">← Назад</button>
      <span>{{ offset + 1 }}–{{ Math.min(offset + pageSize, total) }} из {{ total }}</span>
      <button :disabled="offset + pageSize >= total" @click="goPage(offset + pageSize)">Вперёд →</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import Spinner from '@/shared/components/Spinner.vue'

const props = defineProps({
  columns: { type: Array, required: true },       // [{key, label, width?, class?}]
  fetchFn: { type: Function, required: true },     // (params) => Promise<{data, total}>
  searchPlaceholder: { type: String, default: 'Поиск...' },
  createLabel: { type: String, default: 'Создать' },
  pageSize: { type: Number, default: 25 },
})

const emit = defineEmits(['select', 'create'])

const items = ref([])
const loading = ref(false)
const error = ref(null)
const searchText = ref('')
const offset = ref(0)
const total = ref(0)

function getNested(obj, path) {
  return path.split('.').reduce((o, k) => (o && o[k] !== undefined ? o[k] : ''), obj)
}

let searchTimer = null
function debouncedSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { offset.value = 0; fetchData() }, 250)
}

async function fetchData() {
  loading.value = true; error.value = null
  try {
    const params = { limit: props.pageSize, offset: offset.value }
    if (searchText.value) params.search = searchText.value
    const res = await props.fetchFn(params)
    const data = res.data
    items.value = Array.isArray(data?.data) ? data.data : (Array.isArray(data) ? data : [])
    total.value = data?.total || data?.count || items.value.length
  } catch (e) {
    error.value = e.displayMessage || e.message || 'Ошибка загрузки'
  } finally { loading.value = false }
}

function goPage(newOffset) {
  offset.value = Math.max(0, newOffset)
  fetchData()
}

onMounted(fetchData)

defineExpose({ fetchData, items })
</script>

<style scoped>
.admin-table { width: 100%; }
.at-toolbar { display: flex; gap: 8px; margin-bottom: 12px; }
.at-search { flex: 1; padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; min-width: 180px; }
.at-btn { padding: 6px 16px; background: #2563eb; color: #fff; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; white-space: nowrap; }
.at-btn:hover { background: #1d4ed8; }
.at-tbl { width: 100%; border-collapse: collapse; font-size: 13px; }
.at-tbl th { text-align: left; padding: 8px 10px; background: #f9fafb; border-bottom: 2px solid #e5e7eb; color: #6b7280; font-weight: 500; white-space: nowrap; }
.at-tbl td { padding: 8px 10px; border-bottom: 1px solid #f3f4f6; }
.at-row { cursor: pointer; transition: background .1s; }
.at-row:hover { background: #f0f9ff; }
.at-row.ina { opacity: .5; }
.at-empty { text-align: center; padding: 40px; color: #6b7280; }
.at-error { text-align: center; padding: 40px; color: #dc2626; }
.at-pager { display: flex; align-items: center; justify-content: center; gap: 12px; margin-top: 12px; font-size: 13px; color: #6b7280; }
.at-pager button { padding: 4px 12px; border: 1px solid #d1d5db; border-radius: 4px; background: #fff; cursor: pointer; font-size: 13px; }
.at-pager button:disabled { opacity: .4; cursor: default; }
.at-pager button:not(:disabled):hover { background: #f3f4f6; }
</style>
