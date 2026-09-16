<!-- pages/SkuProductPage.vue — карточка модели, открытая из глобального поиска по артикулу. -->
<template>
  <div class="sku-product-page">
    <div class="sp-toolbar">
      <button class="back-btn" @click="$router.back()">← Назад</button>
    </div>
    <div v-if="loading" class="sp-state">Загрузка…</div>
    <div v-else-if="error" class="sp-state sp-error">{{ error }}</div>
    <ProductDetail v-else-if="product" :product="product" :price="product.price" />
  </div>
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

watch(() => route.params.id, async (skuId) => {
  if (!skuId) { error.value = 'Нет идентификатора'; loading.value = false; return }
  loading.value = true
  error.value = ''
  product.value = null
  try {
    const res = await api.get('/admin/sku/model-detail/', { params: { sku_id: skuId } })
    product.value = res.data
  } catch (e) {
    error.value = 'Не удалось загрузить карточку: ' + (e?.displayMessage || e?.message || 'модель не найдена')
  } finally {
    loading.value = false
  }
}, { immediate: true })
</script>

<style scoped>
.sku-product-page { max-width: 1200px; margin: 0 auto; padding: 16px; }
.sp-toolbar { margin-bottom: 12px; }
.back-btn { padding: 8px 16px; font-size: 14px; background: #fff; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; color: #1f2937; }
.back-btn:hover { border-color: #2563eb; color: #2563eb; }
.sp-state { text-align: center; padding: 60px 20px; color: #6b7280; }
.sp-error { color: #ef4444; }
</style>
