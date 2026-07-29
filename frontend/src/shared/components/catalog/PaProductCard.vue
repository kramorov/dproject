<!-- shared/components/catalog/PaProductCard.vue -->
<!-- Карточка пневмопривода: ProductDetail + кнопки -->
<template>
  <div class="pa-product-card">
    <ProductDetail v-if="preview" :product="preview" :price="null" :breadcrumbs="[]" />
    <div class="pa-actions" v-if="preview">
      <button class="btn primary" @click="$emit('addToCart')">🛒 Добавить в корзину</button>
      <button class="btn secondary" @click="showSpec = true" v-if="preview.tech_description">Просмотр спецификации</button>
    </div>

    <Teleport to="body">
      <div class="modal-overlay" v-if="showSpec" @click.self="showSpec = false">
        <div class="modal-content">
          <div class="modal-header">
            <h3>Спецификация</h3>
            <button class="btn-icon close" @click="showSpec = false">&times;</button>
          </div>
          <div class="modal-body" v-html="preview?.tech_description"></div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ProductDetail from '@/shared/components/ProductDetail.vue'

defineProps({
  preview: { type: Object, default: null },
})
defineEmits(['addToCart'])

const showSpec = ref(false)
</script>

<style scoped>
.pa-product-card { max-width: 1200px; }
.pa-actions { margin-top: 24px; padding: 0 16px 32px; display: flex; gap: 12px; }
.btn { padding: 10px 24px; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; }
.btn.primary { background: #2563eb; color: #fff; }
.btn.primary:hover { background: #1d4ed8; }
.btn.secondary { background: #f3f4f6; color: #374151; border: 1px solid #d1d5db; }
.btn.secondary:hover { background: #e5e7eb; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: #fff; border-radius: 10px; max-width: 780px; width: 92%; max-height: 85vh; display: flex; flex-direction: column; box-shadow: 0 8px 40px rgba(0,0,0,.2); }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #eee; }
.modal-header h3 { margin: 0; font-size: 16px; }
.modal-header .close { font-size: 22px; border: none; background: none; cursor: pointer; color: #888; }
.modal-body { padding: 20px; overflow-y: auto; font-size: 13px; line-height: 1.6; flex: 1; }
</style>
