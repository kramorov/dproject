<!-- shared/components/ProductHeader.vue -->
<!-- Шапка товара: название, код, цена + JsonLd -->
<template>
  <div class="product-header">
    <h1 class="product-title">{{ name || code }}</h1>

    <div class="product-price" v-if="price">
      <span class="price-value">{{ price.price }}</span>
      <span class="price-currency">{{ price.currency }}</span>
    </div>

    <JsonLd v-if="schema" :data="schema" />
  </div>
</template>

<script setup>
import JsonLd from './JsonLd.vue'

defineProps({
  name: { type: String, default: '' },
  code: { type: String, default: '' },
  price: { type: Object, default: null },
  schema: { type: Object, default: null },
})
</script>

<style scoped>
.product-header { }
.product-title { font-size: var(--cat-header-title-size); font-weight: 700; margin: 0 0 4px; color: var(--cat-text); }
.product-code { font-size: var(--cat-header-code-size); color: var(--cat-muted); margin: 0 0 12px; font-family: var(--cat-font-mono); }
.product-price { margin-bottom: 16px; }
.price-value { font-size: var(--cat-header-price-size); font-weight: var(--cat-header-price-weight); color: var(--cat-price-color); }
.price-currency { font-size: var(--cat-text-lg); color: var(--cat-muted); margin-left: 4px; }
</style>