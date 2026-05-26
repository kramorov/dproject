<!-- limit-switch-catalog/components/LsbDetail.vue -->
<template>
  <div class="detail-page">
    <button class="back-btn" @click="$emit('close')">← Назад к каталогу</button>
    <ProductDetail
      v-if="product"
      :product="product"
      :price="null"
      :breadcrumbs="breadcrumbs"
    />
    <div class="loading" v-else-if="loading">Загрузка...</div>
    <div class="error" v-else>Товар не найден</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import ProductDetail from '@/shared/components/ProductDetail.vue'
import lsbApi from '../api'

const props = defineProps({ id: [Number, String] })
defineEmits(['close'])

const product = ref(null)
const loading = ref(true)

const breadcrumbs = computed(() => [
  { name: 'Каталог' },
  { name: 'Блоки концевых выключателей' },
  { name: product.value?.code || product.value?.name || '...' },
])

async function fetchDetail() {
  if (!props.id) return
  loading.value = true
  try {
    const r = await lsbApi.getDetail(props.id)
    const data = r.data || {}
    product.value = {
      ...data,
      image_alt: data.name || data.code || '',
    }
  } catch (e) { product.value = null }
  loading.value = false
}

onMounted(fetchDetail)
watch(() => props.id, fetchDetail)
</script>

<style scoped>
.detail-page { max-width: 1200px; margin: 0 auto; padding: 16px; }
.back-btn {
  padding: 8px 16px; font-size: 14px;
  background: var(--cat-surface, #fff);
  border: 1px solid var(--cat-border, #d1d5db);
  border-radius: var(--cat-radius-md, 6px);
  cursor: pointer; margin-bottom: 16px;
  color: var(--cat-text, #1f2937);
}
.back-btn:hover { border-color: var(--cat-primary, #2563eb); color: var(--cat-primary, #2563eb); }
.loading, .error { text-align: center; padding: 60px 20px; color: var(--cat-muted, #9ca3af); font-size: 16px; }
</style>
