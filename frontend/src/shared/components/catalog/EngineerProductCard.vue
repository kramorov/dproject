<!-- shared/components/catalog/EngineerProductCard.vue -->
<!-- Карточка для EngineerSelection. Единый шаблон: изображение + блок информации
     о модели (PaModelInfoBlock) + «Блок купить» (PaBuyBlock). Без чипсов опций. -->
<template>
  <div class="eng-card" @click="emit('select', item.id)">
    <div class="eng-card__image">
      <ProgressiveImage
        v-if="imagePreview || imageFull"
        :preview="imagePreview"
        :full="imageFull"
        :alt="item.code"
      />
      <span v-else class="eng-card__no-img">🈚</span>
    </div>

    <PaModelInfoBlock :item="item" class="eng-card__info" />
    <PaBuyBlock :sku-id="item.sku_id" :price="price" class="eng-card__buy" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ProgressiveImage from '@/shared/components/ProgressiveImage.vue'
import PaModelInfoBlock from '@/shared/components/catalog/PaModelInfoBlock.vue'
import PaBuyBlock from '@/shared/components/catalog/PaBuyBlock.vue'

const props = defineProps({
  item: { type: Object, required: true },
  price: { type: Object, default: null },
})

const emit = defineEmits(['select'])

const imgs = computed(() => props.item.images || [])
const imagePreview = computed(() => imgs.value[0]?.preview_url || imgs.value[0]?.url || null)
const imageFull = computed(() => {
  const first = imgs.value[0]
  if (!first) return null
  return first.url !== first.preview_url ? (first.url || null) : null
})
</script>

<style scoped>
.eng-card {
  display: flex;
  align-items: stretch;
  gap: 16px;
  background: var(--cat-surface, #fff);
  border: 1px solid var(--cat-border, #e5e7eb);
  border-radius: var(--cat-radius-lg, 12px);
  padding: 16px;
  cursor: pointer;
  transition: box-shadow .15s, border-color .15s;
}
.eng-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,.06);
  border-color: var(--cat-primary, #2563eb);
}

.eng-card__image {
  flex: 0 0 96px;
  height: 96px;
  border-radius: var(--cat-radius-md, 8px);
  background: var(--cat-bg, #f9fafb);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.eng-card__image :deep(img) {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.eng-card__no-img {
  font-size: 28px;
  color: var(--cat-border, #d1d5db);
}

.eng-card__info {
  flex: 1;
  min-width: 0;
}
.eng-card__buy {
  flex: 0 0 auto;
  align-self: stretch;
}

@media (max-width: 640px) {
  .eng-card { gap: 12px; padding: 12px; }
  .eng-card__image { flex: 0 0 72px; height: 72px; }
}
</style>
