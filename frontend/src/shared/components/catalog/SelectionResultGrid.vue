<!-- shared/components/catalog/SelectionResultGrid.vue — Сетка результатов подбора -->
<template>
  <div class="srg">
    <span class="debug-tag" v-if="debug">SelectionResultGrid</span>
    <!-- Счётчик -->
    <div class="srg-info">
      <span class="srg-spinner" v-if="loading" />
      <span v-else>{{ resultsLabel }} {{ total }}</span>
    </div>

    <!-- Основной список -->
    <section v-if="items.length" class="srg-section">
      <h3 class="srg-title" v-if="splitMode && mainTitle">{{ mainTitle }} ({{ items.length }})</h3>
      <div class="srg-grid">
        <EngineerProductCard
          v-for="item in items"
          :key="item.id"
          :item="item"
          :price="item.price || null"
          @select="id => $emit('select', id)"
        />
      </div>
    </section>

    <!-- Совместимые (опционально) -->
    <section v-if="compatibleItems && compatibleItems.length" class="srg-section">
      <h3 class="srg-title">{{ compatibleTitle || '🔗 Выполняют условия' }} ({{ compatibleItems.length }})</h3>
      <div class="srg-grid">
        <EngineerProductCard
          v-for="item in compatibleItems"
          :key="'c-' + item.id"
          :item="item"
          :price="item.price || null"
          @select="id => $emit('select', id)"
        />
      </div>
    </section>

    <!-- Пусто -->
    <div class="srg-empty" v-else-if="!loading && !items.length">{{ emptyText }}</div>

    <!-- Пагинация: страничная -->
    <div class="srg-pagination" v-if="mode === 'page' && totalPages > 1">
      <button :disabled="page <= 1" @click="$emit('page-change', page - 1)">← Назад</button>
      <span>Стр. {{ page }} из {{ totalPages }}</span>
      <button :disabled="page >= totalPages" @click="$emit('page-change', page + 1)">Вперёд →</button>
    </div>

    <!-- Пагинация: offset-based -->
    <div class="srg-pagination" v-if="mode === 'offset' && total > limit">
      <button :disabled="offset === 0" @click="$emit('offset-change', offset - limit)">← Назад</button>
      <span>{{ offset + 1 }}–{{ Math.min(offset + limit, total) }} из {{ total }}</span>
      <button :disabled="offset + limit >= total" @click="$emit('offset-change', offset + limit)">Вперёд →</button>
    </div>
  </div>
</template>

<script setup>
import { debug } from '@/shared/config'
import EngineerProductCard from '@/shared/components/catalog/EngineerProductCard.vue'

defineProps({
  items: { type: Array, default: () => [] },
  compatibleItems: { type: Array, default: null },
  total: { type: Number, default: 0 },
  loading: { type: Boolean, default: false },
  emptyText: { type: String, default: 'Ничего не найдено' },
  resultsLabel: { type: String, default: 'Найдено:' },
  // Page mode (default)
  mode: { type: String, default: 'page' },
  page: { type: Number, default: 1 },
  totalPages: { type: Number, default: 0 },
  // Offset mode
  offset: { type: Number, default: 0 },
  limit: { type: Number, default: 24 },
  // Split mode
  splitMode: { type: Boolean, default: false },
  mainTitle: { type: String, default: '' },
  compatibleTitle: { type: String, default: '' },
})

defineEmits(['select', 'page-change', 'offset-change'])
</script>

<style scoped>
.srg { max-width: 100%; }

.srg-info {
  font-size: var(--cat-text-base, 14px);
  color: var(--cat-muted, #6b7280);
  margin-bottom: 16px;
}

.srg-section { margin-bottom: 32px; }

.srg-title {
  font-size: var(--cat-text-md, 16px);
  font-weight: 600;
  color: var(--cat-text, #1f2937);
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--cat-border, #e5e7eb);
}

.srg-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.srg-empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--cat-muted-light, #9ca3af);
  font-size: var(--cat-text-lg, 16px);
}

.srg-pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 32px;
  padding: 16px 0;
}

.srg-pagination button {
  padding: 8px 20px;
  font-size: var(--cat-text-base, 14px);
  background: var(--cat-surface, #fff);
  border: 1px solid var(--cat-border, #d1d5db);
  border-radius: var(--cat-radius-md, 6px);
  cursor: pointer;
  color: var(--cat-text, #1f2937);
}

.srg-pagination button:disabled { opacity: .4; cursor: default; }

.srg-pagination button:not(:disabled):hover {
  border-color: var(--cat-primary, #2563eb);
  color: var(--cat-primary, #2563eb);
}

.srg-pagination span {
  font-size: var(--cat-text-base, 14px);
  color: var(--cat-muted, #6b7280);
}

.srg-spinner {
  display: inline-block;
  width: 18px; height: 18px;
  border: 2px solid var(--cat-border, #e5e7eb);
  border-top-color: var(--cat-primary, #2563eb);
  border-radius: 50%;
  animation: srg-spin 0.6s linear infinite;
}
@keyframes srg-spin { to { transform: rotate(360deg); } }
</style>
