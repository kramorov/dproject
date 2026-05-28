<!-- shared/components/ProgressiveImage.vue -->
<template>
  <img
    :src="currentSrc"
    :alt="alt"
    :class="{ loading: transitioning }"
    loading="lazy"
    @load="onLoad"
    @error="onError"
  />
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  preview: { type: String, default: '' },   // быстрый preview_url
  full: { type: String, default: '' },       // полный url
  alt: { type: String, default: '' },
})

const currentSrc = ref(props.preview || props.full)
const transitioning = ref(false)

function swapToFull() {
  if (!props.full || props.full === props.preview) return
  transitioning.value = true
  const loader = new Image()
  loader.onload = () => {
    currentSrc.value = props.full
    transitioning.value = false
  }
  loader.onerror = () => {
    transitioning.value = false
  }
  loader.src = props.full
}

function onLoad() {
  transitioning.value = false
}

function onError() {
  transitioning.value = false
}

onMounted(() => {
  if (props.preview && props.full && props.preview !== props.full) {
    // Небольшая задержка чтобы не грузить все карточки одновременно
    setTimeout(swapToFull, 100 + Math.random() * 300)
  }
})

watch(() => props.full, () => {
  if (props.full && props.full !== currentSrc.value) {
    swapToFull()
  }
})
</script>

<style scoped>
img { transition: opacity 0.3s; }
img.loading { opacity: 0.6; }
</style>
