<!-- shared/components/catalog/CatalogActions.vue — кнопки над сеткой серий -->
<template>
  <div class="catalog-actions">
    <button class="ca-btn ca-btn--engineer" @click="$emit('engineer')">
      <span class="ca-icon">🔍</span>
      Инженерный подбор
    </button>
    <button class="ca-btn ca-btn--quickselect" @click="$emit('quickselect')">
      <span class="ca-icon">⚡</span>
      Быстрый подбор
    </button>
  </div>
</template>
<script setup>
defineEmits(['engineer', 'quickselect'])
</script>
<style scoped>
.catalog-actions { display: flex; gap: 12px; margin-bottom: 24px }
.ca-btn { display: flex; align-items: center; gap: 8px; padding: 10px 24px; font-size: 15px; font-weight: 500; border-radius: 8px; border: 1px solid var(--cat-border, #d1d5db); cursor: pointer; transition: all .15s }
.ca-btn--engineer { background: var(--cat-surface, #fff); color: var(--cat-text, #1f2937) }
.ca-btn--engineer:hover { border-color: var(--cat-primary, #2563eb); color: var(--cat-primary, #2563eb) }
.ca-btn--quickselect { background: var(--cat-primary, #2563eb); color: #fff; border-color: var(--cat-primary, #2563eb) }
.ca-btn--quickselect:hover { background: var(--cat-primary-hover, #1d4ed8) }
.ca-icon { font-size: 18px }
</style>
