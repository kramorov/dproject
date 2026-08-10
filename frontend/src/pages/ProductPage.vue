<!-- pages/ProductPage.vue — Страница товара из корзины -->
<template>
  <div v-if="loading" class="pp-loading">Загрузка...</div>
  <div v-else-if="error" class="pp-error">{{ error }}</div>
  <template v-else-if="product">
    <ProductDetail :product="product" :price="null" />
  </template>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/shared/api'
import ProductDetail from '@/shared/components/ProductDetail.vue'

const route = useRoute()
const product = ref(null)
const loading = ref(true)
const error = ref('')

watch(() => route.params.id, async (itemId) => {
  if (!itemId) { error.value = 'Нет ID'; loading.value = false; return }
  loading.value = true
  error.value = ''
  try {
    const res = await api.get(`/cart/items/${itemId}/detail/`)
    product.value = res.data
  } catch (e) {
    error.value = 'Ошибка загрузки товара: ' + (e?.message || e)
  } finally {
    loading.value = false
  }
}, { immediate: true })
</script>

<style scoped>
.pp-loading, .pp-error { text-align: center; padding: 60px 20px; color: var(--cat-muted, #6b7280); }
.pp-error { color: #ef4444; }
</style>
