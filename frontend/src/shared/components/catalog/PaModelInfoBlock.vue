<!-- shared/components/catalog/PaModelInfoBlock.vue -->
<!-- Блок информации о модели (переиспользуемый): слева код (крупно), справа
     название (меньше, без жирного, 2–3 строки); ниже — таблица основных
     параметров «Название — Значение» (list_params, настраивается в EquipmentType). -->
<template>
  <div class="pa-model-info">
    <div class="pa-model-info__header">
      <div class="pa-model-info__code">{{ item.code }}</div>
      <div class="pa-model-info__name">{{ item.name || item.list_title || item.title }}</div>
    </div>

    <div v-if="params.length" class="pa-model-info__params">
      <div v-for="p in params" :key="p.label" class="pa-model-info__param">
        <span class="pa-model-info__param-label">{{ p.label }}</span>
        <span class="pa-model-info__param-value">{{ p.value }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  item: { type: Object, required: true },
})

const params = computed(() => {
  const lp = props.item.list_params
  if (!Array.isArray(lp)) return []
  return lp.filter(p => p && p.value != null && p.value !== '')
})
</script>

<style scoped>
.pa-model-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ── Таблица из двух секций: код | название ── */
.pa-model-info__header {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px;
  align-items: stretch;
}
.pa-model-info__code {
  font-size: var(--cat-text-lg, 16px);
  font-weight: 600;
  color: var(--cat-text, #1f2937);
  white-space: nowrap;
  display: flex;
  align-items: center;
}
.pa-model-info__name {
  font-size: var(--cat-text-sm, 13px);
  font-weight: 400;
  line-height: 1.4;
  color: var(--cat-text, #1f2937);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── Таблица параметров: 3 элемента в строке ── */
.pa-model-info__params {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px 16px;
}
.pa-model-info__param {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 4px;
  align-items: baseline;
  min-width: 0;
}
.pa-model-info__param-label {
  color: var(--cat-muted, #6b7280);
  font-size: var(--cat-text-xs, 12px);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.pa-model-info__param-value {
  color: var(--cat-text, #1f2937);
  font-weight: 500;
  font-size: var(--cat-text-sm, 13px);
}
</style>
