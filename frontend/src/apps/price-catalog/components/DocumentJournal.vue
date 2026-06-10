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
      @open-card="id => $emit('open', id)"
      @create-new="showCreate = true"
      @batch-register="batchRegister"
      @batch-unregister="batchUnregister"
      @batch-delete="batchMarkDeleted"
      @sort-by="sortBy"
      @filter-change="onFilterChange"
    />

    <div v-if="showCreate" class="create-card">
      <h4>Новый документ</h4>
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
        <input v-model="createForm.date" type="date" class="fi" />
        <button class="btn-create" @click="doCreate">Создать</button>
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

function todayStr() { return new Date().toISOString().slice(0, 10) }

const journalApi = {
  list: (params) => priceApi.listDocuments(params),
  create: (data) => priceApi.createDocument(data),
  register: (id) => priceApi.applyDocument(id),
  unregister: (id) => priceApi.unapplyDocument(id),
  markDeleted: (id) => priceApi.deleteDocument(id),
}

const journal = useDocumentJournal(journalApi, { limit: 25 })

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

const showCreate = ref(false)
const createForm = reactive({ name: '', priceVariety: null, currency: null, date: todayStr() })
const createErr = ref('')

function onFilterChange(key, val) {
  filters[key] = val
  applyFilters()
}

async function doCreate() {
  if (!createForm.name) { createErr.value = 'Название обязательно'; return }
  createErr.value = null
  try {
    await journal.createDocument({
      name: createForm.name,
      default_price_variety_id: createForm.priceVariety || undefined,
      default_currency_id: createForm.currency || undefined,
      document_date: createForm.date || undefined,
    })
    Object.assign(createForm, { name: '', priceVariety: null, currency: null, date: todayStr() })
    showCreate.value = false
  } catch (e) { createErr.value = e?.displayMessage || 'Ошибка создания' }
}

onMounted(fetchList)
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
