<!-- filter-regulator-catalog/components/GearboxDetail.vue -->
<template>
  <div class="detail-page">
    <button class="back-btn" @click="$emit('close')">← Назад к каталогу</button>
    <ProductDetail v-if="product" :product="product" :price="product.price" :breadcrumbs="breadcrumbs" />
    <div class="loading" v-else-if="loading">Загрузка...</div>
    <div class="error" v-else>Товар не найден</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import ProductDetail from '@/shared/components/ProductDetail.vue'
import frApi from '../api'

const props = defineProps({ id: [Number, String] })
defineEmits(['close'])

const product = ref(null)
const loading = ref(true)

const breadcrumbs = computed(() => [
  { name: 'Каталог' }, { name: 'Фильтр-регуляторы' }, { name: product.value?.name || product.value?.code || '...' },
])

async function fetchDetail() {
  if (!props.id) return
  loading.value = true
  try { const r = await frApi.getDetail(props.id); product.value = r.data || null } catch (e) { product.value = null }
  loading.value = false
}

onMounted(fetchDetail)
watch(() => props.id, fetchDetail)
</script>

<style scoped>
.detail-page { max-width: 1200px; margin: 0 auto; padding: 16px; }
.back-btn { padding: 8px 16px; font-size: 14px; background: #fff; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; margin-bottom: 16px; }
.back-btn:hover { border-color: #2563eb; color: #2563eb; }
.loading, .error { text-align: center; padding: 60px 20px; color: #9ca3af; font-size: 16px; }
</style>
