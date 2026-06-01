<!-- apps/media-library/components/MediaVariantsPreview.vue
     Показывает сгенерированные MediaVariant для элемента медиабиблиотеки.
     Изображения: группировка по ролям (icon, thumb, card).
     PDF: группировка по страницам.
-->
<template>
  <div v-if="hasVariants" class="variants-preview">
    <h4>📐 Варианты</h4>

    <!-- Изображения: роли -->
    <template v-if="!isPdf">
      <div v-for="(sizes, role) in variants" :key="role" class="variant-role">
        <h5>{{ roleLabel(role) }}</h5>
        <div class="variant-row">
          <a v-for="(url, width) in sizes" :key="width" :href="url" target="_blank" class="variant-card">
            <img :src="url" :alt="`${role} ${width}px`" class="variant-img" />
            <span class="variant-size">{{ width }}px</span>
          </a>
        </div>
      </div>
    </template>

    <!-- PDF: страницы -->
    <template v-else>
      <div class="pdf-info">Страниц: {{ variants.total_pages }}</div>
      <div v-for="page in variants.pages" :key="page.n" class="pdf-page">
        <h5>Страница {{ page.n }}</h5>
        <div v-for="(sizes, role) in page" :key="role" class="variant-role">
          <template v-if="role !== 'n'">
            <h6>{{ roleLabel(role) }}</h6>
            <div class="variant-row">
              <a v-for="(url, width) in sizes" :key="width" :href="url" target="_blank" class="variant-card">
                <img :src="url" :alt="`стр.${page.n} ${role} ${width}px`" class="variant-img" />
                <span class="variant-size">{{ width }}px</span>
              </a>
            </div>
          </template>
        </div>
      </div>
    </template>
  </div>
  <div v-else-if="item?.has_file && isImageOrPdf" class="variants-empty">
    <p>⏳ Варианты не сгенерированы. Нажмите «Сохранить» или «🔄 Обновить превью».</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  item: { type: Object, default: null },
})

const variants = computed(() => props.item?.variants || {})
const hasVariants = computed(() => {
  const v = variants.value
  if (!v || typeof v !== 'object') return false
  if (v.pages) return v.pages.length > 0
  return Object.keys(v).length > 0
})
const isPdf = computed(() => !!variants.value?.pages)
const isImageOrPdf = computed(() => {
  const m = props.item?.mime_type || ''
  return m.startsWith('image/') || m === 'application/pdf'
})

function roleLabel(role) {
  const labels = { icon: 'Иконка', thumb: 'Миниатюра', card: 'Карточка', full: 'Полный', page: 'Страница', email: 'Email' }
  return labels[role] || role
}
</script>

<style scoped>
.variants-preview { margin-top: 8px; padding: 8px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; }
.variants-preview h4 { margin: 0 0 6px; font-size: 12px; color: #334155; }
.variant-role { margin-bottom: 6px; }
.variant-role h5 { margin: 0 0 3px; font-size: 11px; color: #64748b; text-transform: uppercase; }
.variant-role h6 { margin: 0 0 2px; font-size: 10px; color: #94a3b8; }
.variant-row { display: flex; gap: 4px; flex-wrap: wrap; }
.variant-card {
  display: flex; flex-direction: column; align-items: center;
  padding: 4px; background: #fff; border: 1px solid #e2e8f0; border-radius: 6px;
  text-decoration: none; color: inherit; cursor: pointer;
}
.variant-card:hover { border-color: #3b82f6; }
.variant-img { width: 44px; height: 44px; object-fit: contain; border-radius: 3px; }
.variant-size { font-size: 9px; color: #94a3b8; margin-top: 1px; }
.pdf-info { font-size: 11px; color: #475569; margin-bottom: 4px; }
.pdf-page { margin-bottom: 8px; padding: 6px; background: #fff; border-radius: 4px; }
.pdf-page h5 { margin: 0 0 4px; font-size: 11px; color: #334155; }
.variants-empty { margin-top: 8px; padding: 8px; background: #fffbeb; border: 1px solid #fde68a; border-radius: 4px; }
.variants-empty p { margin: 0; font-size: 12px; color: #92400e; }
</style>
