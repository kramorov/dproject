<!-- pages/ImageProcessorTest.vue -->
<template>
  <div class="page">
    <h1>🖼️ Обрезка изображений</h1>
    <ImageCropper @crop-complete="onCropComplete" />

    <div v-if="cropData" class="results">
      <h3>Размеры файлов</h3>
      <div class="sizes-summary">
        <div class="size-row">
          <span>Исходный</span>
          <strong>{{ fmtSize(cropData.original_size) }}</strong>
        </div>
        <div class="size-row">
          <span>Обрезанный (full)</span>
          <strong>{{ fmtSize(cropData.cropped_size) }}</strong>
          <span class="saving" v-if="cropData.original_size && cropData.cropped_size">
            –{{ pct(cropData.cropped_size, cropData.original_size) }}%
          </span>
        </div>
      </div>

      <h3>WebP-варианты</h3>
      <div class="variants">
        <div v-for="(v, size) in cropData.results" :key="size" class="variant-card">
          <p class="size-label">{{ size.toUpperCase() }} ({{ dims[size] }})</p>
          <img :src="v.url" :alt="size" />
          <p class="file-size">{{ fmtSize(v.size) }}</p>
          <p class="saving" v-if="cropData.original_size && v.size">
            –{{ pct(v.size, cropData.original_size) }}% от исходного
          </p>
          <a :href="v.url" target="_blank" class="link">Открыть</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import ImageCropper from '@/shared/components/ImageCropper.vue'

const SIZES = { sm: '150×150', md: '400×400', lg: '800×800' }

export default {
  name: 'ImageProcessorTest',
  components: { ImageCropper },
  data() {
    return { cropData: null, dims: SIZES }
  },
  methods: {
    onCropComplete(data) { this.cropData = data },
    fmtSize(b) {
      if (!b) return '—'
      if (b < 1024) return b + ' B'
      if (b < 1048576) return (b / 1024).toFixed(1) + ' KB'
      return (b / 1048576).toFixed(1) + ' MB'
    },
    pct(small, big) {
      if (!big) return '0'
      return (100 - Math.round((small / big) * 100))
    },
  },
}
</script>

<style scoped>
.page { max-width: 1000px; margin: 0 auto; padding: 24px 16px; }
h1 { font-size: 22px; margin-bottom: 24px; }
.results { margin-top: 32px; }
.results h3 { font-size: 16px; margin: 20px 0 12px; }
.sizes-summary { margin-bottom: 16px; }
.size-row {
  display: flex; align-items: center; gap: 12px;
  padding: 6px 0; font-size: 14px;
}
.size-row span:first-child { color: #666; min-width: 140px; }
.size-row strong { color: #111; min-width: 70px; }
.saving { color: #16a34a; font-size: 13px; }
.variants { display: flex; gap: 16px; flex-wrap: wrap; }
.variant-card {
  border: 1px solid #e5e7eb; border-radius: 8px;
  padding: 12px; text-align: center; width: 200px;
}
.variant-card img { max-width: 100%; max-height: 200px; border-radius: 4px; }
.size-label { font-size: 12px; color: #888; margin-bottom: 4px; }
.file-size { font-size: 13px; color: #111; margin: 4px 0; }
.link { font-size: 12px; color: var(--cat-primary, #3b82f6); display: block; margin-top: 4px; }
</style>
