<!-- shared/components/ProductGallery.vue -->
<template>
  <div class="product-gallery" v-if="images.length">
    <div class="main-image" v-if="currentImage">
      <img :src="currentImage.url" :alt="alt" loading="lazy" />
    </div>
    <div class="thumbnails" v-if="images.length > 1">
      <button v-for="(img, i) in images" :key="img.id" class="thumb" :class="{ active: i === activeIndex }" @click="activeIndex = i">
        <img :src="img.preview_url || img.url" :alt="img.title || alt" loading="lazy" />
      </button>
    </div>
  </div>
  <div class="product-gallery empty" v-else>
    <div class="main-image placeholder">Нет изображений</div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
const props = defineProps({ images: { type: Array, default: () => [] }, alt: { type: String, default: '' } })
const activeIndex = ref(0)
watch(() => props.images, () => { activeIndex.value = 0 })
const currentImage = computed(() => props.images[activeIndex.value] || null)
</script>

<style scoped>
.product-gallery { margin-bottom: 24px; }
.main-image { border-radius: var(--cat-radius-md); overflow: hidden; background: var(--cat-gallery-bg); aspect-ratio: var(--cat-gallery-ratio); display: flex; align-items: center; justify-content: center; }
.main-image img { max-width: 100%; max-height: 100%; object-fit: contain; }
.main-image.placeholder { color: var(--cat-muted-light); font-size: var(--cat-text-base); }
.thumbnails { display: flex; gap: var(--cat-thumb-gap); margin-top: 12px; }
.thumb { width: var(--cat-thumb-size); height: var(--cat-thumb-size); border: 2px solid var(--cat-border); border-radius: var(--cat-radius-md); overflow: hidden; cursor: pointer; padding: 0; background: var(--cat-bg); }
.thumb.active { border-color: var(--cat-thumb-active-border); }
.thumb img { width: 100%; height: 100%; object-fit: cover; }
</style>
