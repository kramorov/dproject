<!-- shared/components/ProductCard.vue -->
<template>
  <div class="product-card" @click="emit('select', item.id)">
    <div class="card-image">
      <ProgressiveImage
        v-if="imagePreview || imageFull"
        :preview="imagePreview"
        :full="imageFull"
        :alt="item.image_alt || item.code"
      />
      <span v-else class="no-image">🈚</span>
    </div>
    <div class="card-body">
      <h3 class="card-title">{{ item.title || item.name || item.code }}</h3>
      <p class="card-code" v-if="item.code">{{ item.code }}</p>
      <div class="card-price" v-if="price && price.price != null && price.price !== '0' && price.price !== '0.00'">
        <span class="price-val">{{ price.price }}</span>
        <span class="price-cur">{{ price.symbol || price.currency }}</span>
      </div>
      <div class="card-price card-price-request" v-else>Цена по запросу</div>
      <div class="card-actions-row" v-if="skuId != null">
        <AddToCartButton :skuId="skuId" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ProgressiveImage from '@/shared/components/ProgressiveImage.vue'
import AddToCartButton from '@/shared/components/AddToCartButton.vue'

const props = defineProps({
  item: { type: Object, required: true },
  price: { type: Object, default: null },
  skuId: { type: Number, default: null },
})

const emit = defineEmits(['select'])

const imgs = computed(() => props.item.images || [])
const imagePreview = computed(() => imgs.value[0]?.preview_url || imgs.value[0]?.url || null)
const imageFull = computed(() => {
  const first = imgs.value[0]
  if (!first) return null
  // full только если отличается от preview
  return first.url !== first.preview_url ? (first.url || null) : null
})
</script>

<style scoped>
.product-card {
  background: var(--cat-card-bg);
  border: 1px solid var(--cat-border);
  border-radius: var(--cat-radius-lg);
  overflow: hidden;
  cursor: pointer;
  transition: box-shadow .2s, transform .2s, border-color .2s;
}
.product-card:hover { box-shadow: var(--cat-shadow-card-hover); border-color: var(--cat-primary); transform: translateY(-2px); }
.card-image { aspect-ratio: var(--cat-card-image-ratio); background: var(--cat-bg); display: flex; align-items: center; justify-content: center; overflow: hidden; }
.card-image :deep(img) { width: 100%; height: 100%; object-fit: contain; }
.no-image { font-size: 32px; color: var(--cat-border); }
.card-body { padding: var(--cat-card-padding); }
.card-title { font-size: var(--cat-card-title-size); font-weight: var(--cat-card-title-weight); margin: 0 0 4px; color: var(--cat-text); line-height: 1.3; display: -webkit-box; -webkit-line-clamp: var(--cat-card-title-lines); -webkit-box-orient: vertical; overflow: hidden; }
.card-code { font-size: var(--cat-text-xs); color: var(--cat-muted); font-family: var(--cat-font-mono); margin: 0 0 8px; }
.price-val { font-size: var(--cat-price-size); font-weight: var(--cat-price-weight); color: var(--cat-price-color); }
.price-cur { font-size: var(--cat-text-xs); color: var(--cat-muted); margin-left: 2px; }
.card-price-request { font-size: var(--cat-text-sm, 13px); color: var(--cat-muted, #6b7280); font-style: italic; }
</style>
