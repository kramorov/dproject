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
      {{ t(tab.label) }}
    </button>
  </div>
</template>
<script setup>
import { computed } from 'vue'
import { useI18n } from '@/shared/i18n'
const { t } = useI18n()

const props = defineProps({
  active: { type: String, default: 'section' },
  // Опциональный набор вкладок: [{key, label, event}]. По умолчанию — все 5.
  tabs: { type: Array, default: null },
})
defineEmits(['section', 'engineer', 'quickselect', 'wizard', 'ai'])

const allTabs = [
  { key: 'section',    label: 'catalog.mode.section', event: 'section' },
  { key: 'engineer',   label: 'catalog.mode.engineer',  event: 'engineer' },
  { key: 'quickselect',label: 'catalog.mode.quickselect', event: 'quickselect' },
  { key: 'wizard',     label: 'catalog.mode.wizard',     event: 'wizard' },
  { key: 'ai',         label: 'catalog.mode.ai',          event: 'ai' },
]

const tabs = computed(() => (props.tabs && props.tabs.length ? props.tabs : allTabs))
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
