<!-- shared/components/ProductGallery.vue -->
<template>
  <div class="product-gallery" v-if="images.length">
    <div class="main-image" v-if="images[activeIndex]">
      <!-- preview_url показывается сразу, url подменяется после загрузки фоном -->
      <img
        :src="mainSrc"
        :alt="alt"
        :class="{ loading: mainLoading }"
        @load="onMainLoaded"
        loading="eager"
      />
    </div>
    <div class="thumbnails" v-if="images.length > 1">
      <button
        v-for="(img, i) in images"
        :key="img.id"
        class="thumb"
        :class="{ active: i === activeIndex }"
        @click="selectImage(i)"
      >
        <img :src="img.thumb_url || img.preview_url || img.url" :alt="img.name || alt" loading="lazy" />
      </button>
    </div>
  </div>
  <div class="product-gallery empty" v-else>
    <div class="main-image placeholder">Нет изображений</div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  images: { type: Array, default: () => [] },
  alt: { type: String, default: '' },
})

const activeIndex = ref(0)
const mainLoading = ref(false)
// Кэш загруженных full-url по индексу
const loadedFull = ref(new Set())

watch(() => props.images, () => {
  activeIndex.value = 0
  loadedFull.value = new Set()
})

function selectImage(i) {
  activeIndex.value = i
  // Если full ещё не загружен — инициируем загрузку
  if (!loadedFull.value.has(i)) {
    preloadFull(i)
  }
}

// Превью показывается всегда, full — только если уже загружен
const mainSrc = computed(() => {
  const img = props.images[activeIndex.value]
  if (!img) return ''
  return loadedFull.value.has(activeIndex.value) ? (img.url || img.preview_url) : (img.preview_url || img.url)
})

// Фоновая загрузка full-size
function preloadFull(i) {
  const img = props.images[i]
  if (!img || !img.url || loadedFull.value.has(i)) return
  const loader = new Image()
  loader.onload = () => {
    loadedFull.value.add(i)
    loadedFull.value = new Set(loadedFull.value) // trigger reactivity
    mainLoading.value = false
  }
  loader.onerror = () => {
    // fallback: считаем загруженным (остаёмся на preview)
    loadedFull.value.add(i)
    loadedFull.value = new Set(loadedFull.value)
    mainLoading.value = false
  }
  mainLoading.value = true
  loader.src = img.url
}

function onMainLoaded() {
  mainLoading.value = false
}

// При старте: загружаем full для первого, затем фоном — все остальные
watch(() => props.images.length, (len) => {
  if (len > 0) {
    preloadFull(0)
    // Фоновая предзагрузка остальных с небольшой задержкой
    setTimeout(() => {
      for (let i = 1; i < len; i++) preloadFull(i)
    }, 500)
  }
}, { immediate: true })

// При смене активного: грузим full если ещё нет (обычно уже в кэше)
watch(activeIndex, (i) => {
  if (!loadedFull.value.has(i)) preloadFull(i)
})
</script>

<style scoped>
.product-gallery { margin-bottom: 24px; }
.main-image {
  border-radius: var(--cat-radius-md); overflow: hidden;
  background: var(--cat-gallery-bg);
  aspect-ratio: var(--cat-gallery-ratio);
  display: flex; align-items: center; justify-content: center;
  position: relative;
}
.main-image img {
  max-width: 100%; max-height: 100%; object-fit: contain;
  transition: opacity 0.3s;
}
.main-image img.loading { opacity: 0.6; }
.main-image.placeholder { color: var(--cat-muted-light); font-size: var(--cat-text-base); }
.thumbnails { display: flex; gap: var(--cat-thumb-gap); margin-top: 12px; }
.thumb {
  width: var(--cat-thumb-size); height: var(--cat-thumb-size);
  border: 2px solid var(--cat-border); border-radius: var(--cat-radius-md);
  overflow: hidden; cursor: pointer; padding: 0; background: var(--cat-bg);
}
.thumb.active { border-color: var(--cat-thumb-active-border); }
.thumb img { width: 100%; height: 100%; object-fit: cover; }
</style>
