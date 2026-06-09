<template>
  <div class="doc-journal">
    <!-- Фильтры -->
    <div class="journal-filters">
      <div class="filter-row">
        <input
          type="text"
          :value="filters.search"
          @input="e => onSearchInput && onSearchInput(e.target.value)"
          placeholder="Поиск по названию / коду..."
          class="filter-input filter-search"
        />
        <select :value="filters.status" @change="e => $emit('filter-change', 'status', e.target.value)" class="filter-select">
          <option value="">Все статусы</option>
          <option value="draft">Черновик</option>
          <option value="on_approval">На согласовании</option>
          <option value="posted">Проведён</option>
          <option value="deleted">Удалён</option>
        </select>
        <input type="date" :value="filters.date_from" @change="e => $emit('filter-change', 'date_from', e.target.value)" class="filter-date" title="Дата от" />
        <span class="filter-sep">—</span>
        <input type="date" :value="filters.date_to" @change="e => $emit('filter-change', 'date_to', e.target.value)" class="filter-date" title="Дата до" />
        <AppButton v-if="hasFilters" variant="ghost" @click="onResetFilters && onResetFilters()">Сбросить</AppButton>
      </div>
    </div>

    <!-- Batch-действия -->
    <div v-if="selectedCount" class="batch-bar">
      <span class="batch-info">Выбрано: {{ selectedCount }}</span>
      <AppButton variant="primary" @click="$emit('batch-register')">Провести</AppButton>
      <AppButton variant="cancel" @click="$emit('batch-unregister')">Отменить проведение</AppButton>
      <AppButton variant="danger" @click="$emit('batch-delete')">Пометить на удаление</AppButton>
    </div>

    <!-- Список -->
    <div class="journal-table-wrap">
      <table class="journal-table" v-if="!loading && items.length">
        <thead>
          <tr>
            <th class="col-cb"><input type="checkbox" :checked="allSelected" @change="onToggleAll && onToggleAll()" /></th>
            <th class="col-code sortable" @click="$emit('sort-by', 'code')">Код {{ sortIndicator('code') }}</th>
            <th class="col-name sortable" @click="$emit('sort-by', 'name')">Название {{ sortIndicator('name') }}</th>
            <th class="col-date sortable" @click="$emit('sort-by', 'document_date')">Дата {{ sortIndicator('document_date') }}</th>
            <th class="col-status">Статус</th>
            <th class="col-count">Позиций</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in items"
            :key="item.id"
            :class="{ 'row-deleted': item.is_deleted }"
            @click="$emit('open-card', item.id)"
          >
            <td class="col-cb" @click.stop>
              <input
                type="checkbox"
                :checked="selectedIds.has(item.id)"
                @change="onToggleSelect && onToggleSelect(item.id)"
                :disabled="item.is_deleted"
              />
            </td>
            <td class="col-code">{{ item.code || '—' }}</td>
            <td class="col-name">{{ item.name }}</td>
            <td class="col-date">{{ formatDate(item.document_date) }}</td>
            <td class="col-status">
              <span :class="statusClass(item.status)">{{ STATUS_ICONS[item.status] }} {{ STATUS_LABELS[item.status] }}</span>
            </td>
            <td class="col-count">{{ item.items_count ?? '—' }}</td>
          </tr>
        </tbody>
      </table>

      <!-- Пусто -->
      <div v-else-if="!loading && !items.length" class="journal-empty">
        Документов не найдено
      </div>

      <!-- Загрузка -->
      <Spinner v-if="loading" text="Загрузка..." />
    </div>

    <!-- Пагинация -->
    <div v-if="total > limit" class="journal-pagination">
      <button
        v-for="p in pages"
        :key="p"
        :class="{ active: currentPage === p }"
        @click="onGoPage && onGoPage(p)"
        class="btn-page"
      >{{ p }}</button>
    </div>

    <!-- Кнопка создать -->
    <div class="journal-create-bar">
      <AppButton variant="primary" @click="$emit('create-new')">+ Новый документ</AppButton>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AppButton from '@/shared/components/AppButton.vue'
import Spinner from '@/shared/components/Spinner.vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  total: { type: Number, default: 0 },
  loading: { type: Boolean, default: false },
  limit: { type: Number, default: 25 },
  offset: { type: Number, default: 0 },
  filters: { type: Object, required: true },
  hasFilters: { type: Boolean, default: false },
  selectedIds: { type: Set, default: () => new Set() },
  selectedCount: { type: Number, default: 0 },
  allSelected: { type: Boolean, default: false },
  STATUS_LABELS: { type: Object, default: () => ({}) },
  STATUS_ICONS: { type: Object, default: () => ({}) },
  sortField: { type: String, default: 'document_date' },
  sortDir: { type: String, default: 'desc' },
  // Функции-обработчики (передаются родителем из composable)
  onSearchInput: { type: Function, default: null },
  onApplyFilters: { type: Function, default: null },
  onResetFilters: { type: Function, default: null },
  onGoPage: { type: Function, default: null },
  onToggleSelect: { type: Function, default: null },
  onToggleAll: { type: Function, default: null },
})

defineEmits([
  'open-card', 'create-new',
  'batch-register', 'batch-unregister', 'batch-delete',
  'sort-by',
  'filter-change',
])

// Функции-обработчики передаются родителем через props

const currentPage = computed(() => Math.floor(props.offset / props.limit) + 1)
const pages = computed(() => {
  const total = Math.ceil(props.total / props.limit)
  const arr = []
  for (let i = 1; i <= total; i++) arr.push(i)
  return arr
})

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU')
}

function statusClass(s) {
  return 'status-' + (s || 'draft')
}

function sortIndicator(field) {
  if (props.sortField !== field) return ''
  return props.sortDir === 'asc' ? '▲' : '▼'
}
</script>

<style scoped>
.doc-journal {
  display: flex;
  flex-direction: column;
  gap: var(--cat-gap-md);
}
.journal-filters {
  background: var(--cat-surface);
  border: 1px solid var(--cat-border);
  border-radius: var(--cat-radius-md);
  padding: var(--cat-gap-sm) var(--cat-gap-md);
}
.filter-row {
  display: flex;
  gap: var(--cat-gap-sm);
  align-items: center;
  flex-wrap: wrap;
}
.filter-input, .filter-select, .filter-date {
  padding: 2px 6px;
  border: 1px solid var(--cat-input-border, var(--cat-border));
  border-radius: var(--cat-radius-sm);
  font-size: var(--cat-text-sm);
  background: var(--cat-input-bg, #fff);
  font-family: var(--cat-font);
  height: var(--cat-filter-select-height, 26px);
  box-sizing: border-box;
}
.filter-input:focus-visible, .filter-select:focus-visible, .filter-date:focus-visible {
  border-color: var(--cat-input-focus-border, var(--cat-primary));
  box-shadow: 0 0 0 1px var(--cat-input-focus-border, var(--cat-primary));
  outline: none;
}
.filter-search { min-width: 240px; }
.filter-date { width: 150px; }
.filter-sep { color: var(--cat-muted); }

.batch-bar {
  display: flex;
  gap: var(--cat-gap-sm);
  align-items: center;
  background: var(--cat-primary-light);
  border-radius: var(--cat-radius-md);
  padding: var(--cat-gap-sm) var(--cat-gap-md);
}
.batch-info { font-weight: 600; font-size: var(--cat-text-sm); margin-right: var(--cat-gap-sm); font-family: var(--cat-font); }

.journal-table-wrap { overflow-x: auto; }
.journal-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--cat-text-sm);
  font-family: var(--cat-font);
}
.journal-table th {
  text-align: left;
  padding: 3px 6px;
  border-bottom: 2px solid var(--cat-header-border, var(--cat-border));
  background: var(--cat-header-bg, var(--cat-bg));
  color: var(--cat-text-soft);
  font-weight: 600;
  white-space: nowrap;
  font-size: var(--cat-text-xs);
}
.journal-table td {
  padding: 2px 6px;
  border-bottom: 1px solid var(--cat-border-light);
  cursor: pointer;
  font-size: var(--cat-text-sm);
}
.journal-table tbody tr:nth-child(even) td { background: var(--cat-row-stripe, #fafaf7); }
.journal-table tbody tr:hover td { background: var(--cat-row-hover, #fdfcf9); }
.row-deleted td { opacity: 0.5; text-decoration: line-through; color: var(--cat-status-deleted); }

.col-cb { width: 36px; }
.col-code { width: 120px; font-family: var(--cat-font-mono); }
.col-name { min-width: 200px; }
.col-date { width: 110px; white-space: nowrap; }
.col-status { width: 160px; white-space: nowrap; }
.col-count { width: 70px; text-align: center; }
.sortable { cursor: pointer; user-select: none; }
.sortable:hover { color: var(--cat-primary); }

.status-draft { color: var(--cat-status-draft); }
.status-on_approval { color: var(--cat-status-approval); }
.status-posted { color: var(--cat-status-posted); font-weight: 600; }
.status-deleted { color: var(--cat-status-deleted); }

.journal-empty, .journal-loading {
  text-align: center;
  padding: var(--cat-gap-3xl);
  color: var(--cat-muted);
}

.journal-pagination {
  display: flex;
  gap: var(--cat-gap-xs);
  justify-content: center;
  flex-wrap: wrap;
}
.btn-page {
  padding: 1px 8px;
  border: 1px solid var(--cat-border);
  border-radius: var(--cat-radius-sm);
  background: var(--cat-pagination-btn-bg);
  cursor: pointer;
  font-size: var(--cat-text-xs);
  font-family: var(--cat-font);
}
.btn-page.active {
  background: var(--cat-primary);
  color: #fff;
  border-color: var(--cat-primary);
}

.journal-create-bar { margin-top: var(--cat-gap-sm); }
</style>