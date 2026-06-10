<template>
  <div>
    <SharedDocumentJournal
      :items="items"
      :total="total"
      :loading="loading"
      :limit="limit"
      :offset="offset"
      :filters="filters"
      :hasFilters="hasFilters"
      :selectedIds="selectedIds"
      :selectedCount="selectedCount"
      :allSelected="allSelected"
      :STATUS_LABELS="STATUS_LABELS"
      :STATUS_ICONS="STATUS_ICONS"
      :sortField="sortField"
      :sortDir="sortDir"
      :onSearchInput="onSearchInput"
      :onApplyFilters="applyFilters"
      :onResetFilters="resetFilters"
      :onGoPage="goPage"
      :onToggleSelect="toggleSelect"
      :onToggleAll="toggleAll"
      @open-card="id => $emit('open', { id })"
      @create-new="showCreate = true"
      @batch-register="batchRegister"
      @batch-unregister="batchUnregister"
      @batch-delete="batchMarkDeleted"
      @sort-by="sortBy"
      @filter-change="onFilterChange"
    />

    <!-- Создание -->
    <div v-if="showCreate" class="create-card">
      <h4>Новый документ конфигуратора ЭП</h4>
      <div class="create-row">
        <input v-model="createForm.name" placeholder="Название" class="fi" />
        <select v-model="createForm.priceVariety" class="fi">
          <option :value="null">Тип цены</option>
          <option v-for="v in opts.varieties" :key="v.id" :value="v.id">{{ v.name }}</option>
        </select>
        <select v-model="createForm.currency" class="fi">
          <option :value="null">Валюта</option>
          <option v-for="c in opts.currencies" :key="c.id" :value="c.id">{{ c.code }}</option>
        </select>
        <select v-model="createForm.mlId" @change="onSeriesChange" class="fi">
          <option :value="null">— серия —</option>
          <option v-for="ml in modelLines" :key="ml.id" :value="ml.id">{{ ml.name }} ({{ ml.code }})</option>
        </select>
        <select v-model="createForm.psId" class="fi" :disabled="!createForm.mlId">
          <option :value="null">— напряжение —</option>
          <option v-for="ps in powerSupplies" :key="ps.id" :value="ps.id">{{ ps.name }} ({{ ps.encoding }})</option>
        </select>
        <button class="btn-create" @click="doCreate" :disabled="!createForm.name || !createForm.psId">Создать и заполнить</button>
        <button class="btn-cancel" @click="showCreate = false">Отмена</button>
      </div>
      <div v-if="createErr" class="er">{{ createErr }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, inject, onMounted } from 'vue'
import SharedDocumentJournal from '@/shared/components/documents/DocumentJournal.vue'
import { useDocumentJournal } from '@/shared/composables/useDocumentJournal'
import priceApi from '../api'

const emit = defineEmits(['open'])
const opts = inject('opts')

// API adapter — transform EA responses to composable format
const journalApi = {
  list: async (params) => {
    const r = await priceApi.getEaConfigDocs()
    const data = (r.data || []).map(d => ({
      ...d,
      code: d.model_line?.name || '—',
      items_count: d.rows_count,
    }))
    return { data: { data, total: data.length } }
  },
  create: async (data) => {
    // Handled manually in doCreate — emits open instead of refresh
    return { data: {} }
  },
  register: (id) => priceApi.postEaConfigDoc(id),
  unregister: (id) => priceApi.unpostEaConfigDoc(id),
  markDeleted: (id) => priceApi.deleteEaConfigDoc(id),
}

const journal = useDocumentJournal(journalApi, { limit: 50 })

const {
  items, total, loading, limit, offset,
  filters, hasFilters,
  selectedIds, selectedCount, allSelected,
  sortField, sortDir,
  fetchList, goPage, onSearchInput, applyFilters, resetFilters, sortBy,
  toggleSelect, toggleAll,
  batchRegister, batchUnregister, batchMarkDeleted,
  STATUS_LABELS, STATUS_ICONS,
} = journal

// Create form with cascading selectors
const showCreate = ref(false)
const createForm = reactive({ name: '', priceVariety: null, currency: null, mlId: null, psId: null })
const createErr = ref(null)
const modelLines = ref([])
const powerSupplies = ref([])

function onFilterChange(key, val) {
  filters[key] = val
  applyFilters()
}

async function doCreate() {
  if (!createForm.name) { createErr.value = 'Название обязательно'; return }
  createErr.value = null
  try {
    const r = await priceApi.createEaConfigDoc({
      name: createForm.name,
      price_variety_id: createForm.priceVariety || undefined,
      currency_id: createForm.currency || undefined,
      model_line_id: createForm.mlId,
      power_supply_id: createForm.psId,
    })
    createForm.name = ''; createForm.priceVariety = null; createForm.currency = null
    showCreate.value = false
    emit('open', { id: r.data.id })
  } catch (e) { createErr.value = e?.displayMessage || 'Ошибка создания' }
}

async function loadModelLines() {
  try {
    const r = await fetch('/api/electric_actuators/constructor/model_lines/')
    modelLines.value = await r.json()
  } catch (e) { console.error(e) }
}

async function onSeriesChange() {
  powerSupplies.value = []
  createForm.psId = null
  if (!createForm.mlId) return
  try {
    const r = await fetch(`/api/electric_actuators/constructor/power-supplies/?model_line_id=${createForm.mlId}`)
    powerSupplies.value = await r.json()
  } catch (e) { console.error(e) }
}

onMounted(() => { fetchList(); loadModelLines() })
</script>

<style scoped>
.create-card {
  margin-top: var(--cat-gap-md);
  padding: var(--cat-gap-sm) var(--cat-gap-md);
  border: 1px solid var(--cat-border);
  border-radius: var(--cat-radius-md);
  background: var(--cat-surface);
  font-family: var(--cat-font);
  font-size: var(--cat-text-sm);
}
.create-card h4 { margin: 0 0 var(--cat-gap-sm); font-size: var(--cat-text-base); }
.create-row { display: flex; gap: var(--cat-gap-sm); align-items: center; flex-wrap: wrap; }
.fi {
  padding: 2px 6px;
  border: 1px solid var(--cat-input-border, var(--cat-border));
  border-radius: var(--cat-radius-sm);
  font-size: var(--cat-text-sm);
  font-family: var(--cat-font);
  background: var(--cat-input-bg, #fff);
  height: 26px;
  box-sizing: border-box;
}
.btn-create {
  padding: 2px 12px;
  border: none;
  border-radius: var(--cat-radius-sm);
  background: var(--cat-primary);
  color: #fff;
  cursor: pointer;
  font-size: var(--cat-text-sm);
  font-family: var(--cat-font);
  height: 26px;
}
.btn-create:disabled { opacity: 0.5; cursor: default; }
.btn-cancel {
  padding: 2px 12px;
  border: 1px solid var(--cat-border);
  border-radius: var(--cat-radius-sm);
  background: var(--cat-surface);
  color: var(--cat-text);
  cursor: pointer;
  font-size: var(--cat-text-sm);
  font-family: var(--cat-font);
  height: 26px;
}
.er { color: var(--cat-status-deleted); font-size: var(--cat-text-xs); margin-top: var(--cat-gap-xs); }
</style>
