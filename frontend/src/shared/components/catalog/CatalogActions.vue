<!-- shared/components/catalog/CatalogActions.vue — табы-переключатели режимов подбора -->
<template>
  <div class="catalog-actions">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      class="ca-tab"
      :class="{ active: active === tab.key }"
      @click="tab.event && $emit(tab.event)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>
<script setup>
defineProps({
  active: { type: String, default: 'section' },
})
defineEmits(['section', 'engineer', 'quickselect', 'wizard', 'ai'])

const tabs = [
  { key: 'section',    label: 'Просмотр по сериям', event: 'section' },
  { key: 'engineer',   label: 'Инженерный подбор',  event: 'engineer' },
  { key: 'quickselect',label: 'Быстрый подбор',     event: 'quickselect' },
  { key: 'wizard',     label: 'Мастер подбора',     event: 'wizard' },
  { key: 'ai',         label: 'AI подбор',          event: 'ai' },
]
</script>
<style scoped>
.catalog-actions {
  display: flex;
  gap: 0;
  border-bottom: var(--cat-tab-border-width, 2px) solid var(--cat-border, #e5e7eb);
  margin-bottom: var(--cat-gap-2xl, 24px);
}
.ca-tab {
  padding: var(--cat-tab-padding, 12px 24px);
  font-size: var(--cat-tab-font-size, var(--cat-text-base, 14px));
  font-weight: 500;
  background: none;
  border: none;
  border-bottom: var(--cat-tab-border-width, 2px) solid transparent;
  margin-bottom: calc(-1 * var(--cat-tab-border-width, 2px));
  cursor: pointer;
  color: var(--cat-muted, #6b7280);
  transition: color .15s, border-color .15s;
  white-space: nowrap;
}
.ca-tab:hover {
  color: var(--cat-text, #1f2937);
}
.ca-tab.active {
  color: var(--cat-primary, #2563eb);
  border-bottom-color: var(--cat-primary, #2563eb);
}
</style>
