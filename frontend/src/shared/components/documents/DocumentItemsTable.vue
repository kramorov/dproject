<template>
  <div class="items-table-wrap">
    <table class="items-table" v-if="items.length">
      <thead>
        <tr>
          <th class="it-num">№</th>
          <!-- Слот для заголовков колонок -->
          <slot name="headers" />
          <th class="it-actions">Действия</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, index) in items" :key="item.id || index" :class="{ 'it-draft': item._isNew }">
          <td class="it-num">{{ index + 1 }}</td>
          <!-- Слот для ячеек -->
          <slot name="cells" :item="item" :index="index" />
          <td class="it-actions">
            <button @click="$emit('move-up', index)" :disabled="index === 0" title="Выше" class="it-btn">▲</button>
            <button @click="$emit('move-down', index)" :disabled="index === items.length - 1" title="Ниже" class="it-btn">▼</button>
            <button @click="$emit('remove', item.id, index)" title="Удалить" class="it-btn it-btn-del">✕</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-else class="items-empty">Нет позиций</div>

    <div v-if="error" class="items-error">{{ error }}</div>

    <AppButton v-if="canAdd" variant="ghost" @click="$emit('add')">+ Добавить строку</AppButton>
  </div>
</template>

<script setup>
import AppButton from '@/shared/components/AppButton.vue'

defineProps({
  items: { type: Array, default: () => [] },
  canAdd: { type: Boolean, default: true },
  error: { type: String, default: '' },
})

defineEmits(['add', 'remove', 'move-up', 'move-down'])
</script>

<style scoped>
.items-table-wrap { margin-top: var(--cat-gap-sm); }
.items-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--cat-text-sm);
  font-family: var(--cat-font);
}
.items-table th {
  text-align: left;
  padding: 2px 6px;
  border-bottom: 2px solid var(--cat-header-border, var(--cat-border));
  background: var(--cat-header-bg, var(--cat-bg));
  color: var(--cat-text-soft);
  font-weight: 600;
  font-size: var(--cat-text-xs);
}
.items-table td {
  padding: 2px 6px;
  border-bottom: 1px solid var(--cat-border-light);
  vertical-align: middle;
  font-size: var(--cat-text-sm);
}
.items-table tbody tr:nth-child(even) td { background: var(--cat-row-stripe, #fafaf7); }
.items-table tbody tr:hover td { background: var(--cat-row-hover, #fdfcf9); }
.it-draft td { background: var(--cat-primary-light, #e8f0f8); }

.it-num { width: 40px; text-align: center; color: var(--cat-muted); font-size: var(--cat-text-xs); }
.it-actions { width: 90px; text-align: center; white-space: nowrap; }

.it-btn {
  padding: 0 4px;
  border: 1px solid var(--cat-border);
  border-radius: var(--cat-radius-sm);
  background: var(--cat-surface);
  cursor: pointer;
  font-size: var(--cat-text-xs);
}
.it-btn:hover { background: var(--cat-bg-hover); }
.it-btn:disabled { opacity: 0.3; cursor: default; }
.it-btn-del { color: var(--cat-status-deleted); border-color: var(--cat-badge-deleted-bg); }
.it-btn-del:hover { background: var(--cat-badge-deleted-bg); }

.items-empty { text-align: center; padding: var(--cat-gap-xl); color: var(--cat-muted); font-size: var(--cat-text-sm); }
.items-error { background: var(--cat-badge-deleted-bg); color: var(--cat-status-deleted); padding: var(--cat-gap-sm) var(--cat-gap-md); border-radius: var(--cat-radius-sm); font-size: var(--cat-text-xs); margin-top: var(--cat-gap-sm); }
</style>