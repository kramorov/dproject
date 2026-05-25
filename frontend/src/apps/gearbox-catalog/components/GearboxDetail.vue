<!-- gearbox-catalog/components/GearboxDetail.vue -->
<!-- Страница карточки редуктора — использует ProductDetail -->
<template>
  <div class="gearbox-detail-page">
    <button class="back-btn" @click="$emit('close')">← Назад к каталогу</button>
    <ProductDetail
      v-if="product"
      :product="product"
      :price="price"
      :breadcrumbs="breadcrumbs"
    />
    <div class="loading" v-else-if="loading">Загрузка...</div>
    <div class="error" v-else>Товар не найден</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import ProductDetail from '@/shared/components/ProductDetail.vue'
import gearboxApi from '../api'

const props = defineProps({ id: [Number, String] })
defineEmits(['close'])

const product = ref(null)
const price = ref(null)
const loading = ref(true)

const breadcrumbs = computed(() => [
  { name: 'Каталог', url: '#' },
  { name: 'Редукторы', url: '#' },
  { name: product.value?.name || product.value?.code || '...' },
])

async function fetchDetail() {
  if (!props.id) return
  loading.value = true
  try {
    const r = await gearboxApi.getDetail(props.id)
    product.value = r.data || null
    price.value = r.data?.price || null
  } catch (e) {
    console.error('Failed to load gearbox detail', e)
    product.value = null
  }
  loading.value = false
}

onMounted(fetchDetail)
watch(() => props.id, fetchDetail)
</script>

<style scoped>
.gearbox-detail-page { max-width: 1200px; margin: 0 auto; padding: 16px; }
.back-btn {
  padding: 8px 16px;
  font-size: var(--cat-text-base);
  background: var(--cat-surface);
  border: 1px solid var(--cat-border);
  border-radius: var(--cat-radius-md);
  cursor: pointer;
  margin-bottom: 16px;
}
.back-btn:hover { border-color: var(--cat-primary); color: var(--cat-primary); }
.loading, .error { text-align: center; padding: 60px 20px; color: var(--cat-muted-light); font-size: var(--cat-text-lg); }
</style>