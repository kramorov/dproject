<!-- shared/components/BasePicker.vue — универсальный подбор сущностей (M2M) -->
<template>
  <div v-if="show" class="bp-overlay" @click.self="$emit('close')">
    <div class="bp-modal">
      <div class="bp-header">
        <h3>{{ title }}</h3>
        <button class="bp-close" @click="$emit('close')">&times;</button>
      </div>

      <!-- Фильтры -->
      <div class="bp-filters" v-if="filterDefs.length">
        <template v-for="f in filterDefs" :key="f.key">
          <input v-if="f.type === 'text'"
            v-model="activeFilters[f.key]"
            :placeholder="f.label || 'Поиск...'"
            class="bp-search" @input="debouncedFetch" />
          <select v-else-if="f.type === 'select'"
            v-model="activeFilters[f.key]"
            class="bp-sel" @change="onFilterChange">
            <option :value="null">{{ f.label || 'Все' }}</option>
            <option v-for="o in f.options" :key="o.id" :value="o.id">{{ o.icon || '' }} {{ o.name || o.code }}</option>
          </select>
        </template>
      </div>

      <!-- Таблица -->
      <Spinner v-if="loading" />
      <div v-else-if="error" class="bp-error">{{ error }}</div>
      <div v-else class="bp-table-wrap">
        <table class="bp-tbl">
          <thead>
            <tr>
              <th class="bp-th-chk">☐</th>
              <th v-for="col in columns" :key="col.key" :style="col.width ? {width: col.width} : {}">{{ col.label }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id" class="bp-row"
              :class="{ sel: selectedIds.includes(item.id) }"
              @click="toggle(item.id)">
              <td class="bp-td-chk">
                <span v-if="selectedIds.includes(item.id)">☑</span>
                <span v-else>☐</span>
              </td>
              <td v-for="col in columns" :key="col.key">
                <slot :name="'cell-' + col.key" :item="item" :value="getNested(item, col.key)">
                  {{ getNested(item, col.key) }}
                </slot>
              </td>
            </tr>
            <tr v-if="!items.length"><td :colspan="columns.length + 1" class="bp-empty">Ничего не найдено</td></tr>
          </tbody>
        </table>
      </div>

      <!-- Пагинация -->
      <div class="bp-pager" v-if="total > pageSize">
        <button :disabled="offset <= 0" @click="goPage(-1)">←</button>
        <span>{{ offset + 1 }}–{{ Math.min(offset + pageSize, total) }} из {{ total }}</span>
        <button :disabled="offset + pageSize >= total" @click="goPage(1)">→</button>
      </div>

      <!-- Подвал: перенос -->
      <div class="bp-footer">
        <span class="bp-count">Выбрано: {{ selectedIds.length }}</span>
        <button class="bp-cancel" @click="$emit('close')">Отмена</button>
        <button class="bp-ok" :disabled="!selectedIds.length" @click="confirm">
          Перенести ({{ selectedIds.length }})
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import Spinner from '@/shared/components/Spinner.vue'

const props = defineProps({
  show: Boolean,
  title: { type: String, default: 'Выбрать' },
  fetchFn: { type: Function, required: true },            // (params) => Promise<{data, total}>
  filterDefs: { type: Array, default: () => [] },          // [{key, type:'text'|'select', label, options?}]
  defaultFilters: { type: Object, default: () => ({}) },   // начальные значения фильтров
  columns: { type: Array, default: () => [{key:'code',label:'Код'},{key:'name',label:'Название'}] },
  preselected: { type: Array, default: () => [] },
  pageSize: { type: Number, default: 25 },
})

const emit = defineEmits(['close', 'selected'])

const items = ref([])
const loading = ref(false)
const error = ref(null)
const offset = ref(0)
const total = ref(0)
const selectedIds = ref([])

const activeFilters = reactive({ ...props.defaultFilters })

// При открытии сбрасываем
watch(() => props.show, (v) => {
  if (v) {
    selectedIds.value = [...props.preselected]
    Object.assign(activeFilters, props.defaultFilters)
    // Сбрасываем лишние ключи
    for (const k of Object.keys(activeFilters)) {
      if (!(k in props.defaultFilters) && !props.filterDefs.find(f => f.key === k)) {
        delete activeFilters[k]
      }
    }
    offset.value = 0
    fetchData()
  }
})

function getNested(obj, path) {
  return path.split('.').reduce((o, k) => (o && o[k] !== undefined ? o[k] : ''), obj)
}

function toggle(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

function confirm() {
  const selected = items.value.filter(it => selectedIds.value.includes(it.id))
  emit('selected', selected.map(s => ({ id: s.id, code: s.code, name: s.name, ...s })))
  emit('close')
}

let timer = null
function debouncedFetch() { clearTimeout(timer); timer = setTimeout(() => { offset.value = 0; fetchData() }, 250) }
function onFilterChange() { offset.value = 0; fetchData() }

async function fetchData() {
  loading.value = true; error.value = null
  try {
    const params = { ...activeFilters, limit: props.pageSize, offset: offset.value }
    const res = await props.fetchFn(params)
    const data = res.data
    items.value = Array.isArray(data?.data) ? data.data : (Array.isArray(data) ? data : [])
    total.value = data?.total || data?.count || items.value.length
  } catch (e) {
    error.value = e.displayMessage || e.message || 'Ошибка загрузки'
  } finally { loading.value = false }
}

function goPage(dir) {
  offset.value = Math.max(0, offset.value + dir * props.pageSize)
  fetchData()
}
</script>

<style scoped>
.bp-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.4); display: flex; align-items: center; justify-content: center; z-index: 1100; }
.bp-modal { background: #fff; border-radius: 10px; width: 90%; max-width: 900px; max-height: 85vh; display: flex; flex-direction: column; box-shadow: 0 8px 32px rgba(0,0,0,.15); }
.bp-header { display: flex; justify-content: space-between; align-items: center; padding: 14px 20px; border-bottom: 1px solid #e5e7eb; }
.bp-header h3 { margin: 0; font-size: 16px; }
.bp-close { background: none; border: none; font-size: 22px; cursor: pointer; color: #6b7280; }
.bp-filters { display: flex; gap: 8px; padding: 10px 20px; border-bottom: 1px solid #f3f4f6; flex-wrap: wrap; }
.bp-search { flex: 1; min-width: 140px; padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; }
.bp-sel { padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; min-width: 150px; }
.bp-table-wrap { flex: 1; overflow-y: auto; padding: 0 20px; }
.bp-tbl { width: 100%; border-collapse: collapse; font-size: 13px; }
.bp-tbl th { text-align: left; padding: 8px 8px; background: #f9fafb; border-bottom: 2px solid #e5e7eb; color: #6b7280; font-weight: 500; position: sticky; top: 0; }
.bp-th-chk { width: 36px; text-align: center; }
.bp-td-chk { width: 36px; text-align: center; font-size: 14px; }
.bp-row { cursor: pointer; transition: background .1s; }
.bp-row:hover { background: #f9fafb; }
.bp-row.sel { background: #eff6ff; }
.bp-tbl td { padding: 6px 8px; border-bottom: 1px solid #f3f4f6; }
.bp-empty { text-align: center; padding: 40px; color: #6b7280; }
.bp-error { text-align: center; padding: 40px; color: #dc2626; }
.bp-pager { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 10px; border-top: 1px solid #f3f4f6; font-size: 13px; color: #6b7280; }
.bp-pager button { padding: 4px 12px; border: 1px solid #d1d5db; border-radius: 4px; background: #fff; cursor: pointer; font-size: 13px; }
.bp-pager button:disabled { opacity: .4; cursor: default; }
.bp-footer { display: flex; align-items: center; gap: 10px; padding: 12px 20px; border-top: 1px solid #e5e7eb; }
.bp-count { flex: 1; font-size: 13px; color: #6b7280; }
.bp-cancel { padding: 6px 16px; border: 1px solid #d1d5db; border-radius: 6px; background: #fff; cursor: pointer; font-size: 13px; }
.bp-ok { padding: 6px 20px; background: #2563eb; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; }
.bp-ok:disabled { opacity: .5; cursor: default; }
.bp-ok:hover:not(:disabled) { background: #1d4ed8; }
</style>
