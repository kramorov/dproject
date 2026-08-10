<!-- shared/components/ProductDetailPopup.vue — Popup с карточкой товара -->
<template>
  <Transition name="pdp">
    <div v-if="open" class="pdp-overlay">
      <div class="pdp-modal">
        <button class="pdp-close" @click="emit('close')">Закрыть</button>
        <div v-if="loading" class="pdp-loading">Загрузка...</div>
        <div v-else-if="error" class="pdp-error">{{ error }}</div>
        <template v-else-if="product">
          <ProductDetail :product="product" :price="null" />
        </template>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, watch } from 'vue'
import api from '@/shared/api'
import ProductDetail from './ProductDetail.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  itemId: { type: String, default: null },
})
const emit = defineEmits(['close'])

const product = ref(null)
const loading = ref(false)
const error = ref('')

watch(() => props.open, async (val) => {
  if (!val || !props.itemId) return
  loading.value = true; error.value = ''
  try {
    const res = await api.get(`/cart/items/${props.itemId}/detail/`)
    product.value = res.data
  } catch (e) {
    error.value = 'Ошибка загрузки'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.pdp-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.4); z-index: 1100; display: flex; align-items: center; justify-content: center; }
.pdp-modal { background: #fff; border-radius: 12px; width: 900px; max-width: 95vw; max-height: 90vh; overflow-y: auto; position: relative; padding: 16px 24px 24px; }
.pdp-close { position: sticky; top: 8px; float: right; z-index: 1; background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 6px; padding: 6px 16px; cursor: pointer; font-size: 14px; color: #374151; }
.pdp-close:hover { background: #e5e7eb; }
.pdp-loading, .pdp-error { text-align: center; padding: 40px 0; color: var(--cat-muted, #6b7280); }
.pdp-error { color: #ef4444; }

/* ProductDetail inside popup — fit the modal */
.pdp-modal :deep(.product-detail) { max-width: 100%; padding: 0; }
.pdp-modal :deep(.detail-layout) { gap: 24px; }
.pdp-modal :deep(.detail-gallery) { width: 320px; flex-shrink: 0; }
.pdp-modal :deep(.detail-info) { flex: 1; min-width: 0; }
@media (max-width: 700px) {
  .pdp-modal :deep(.detail-layout) { flex-direction: column; }
  .pdp-modal :deep(.detail-gallery) { width: 100%; }
}
.pdp-enter-active, .pdp-leave-active { transition: opacity .2s; }
.pdp-enter-from, .pdp-leave-to { opacity: 0; }
</style>
