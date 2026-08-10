<!-- shared/components/ProductDetail.vue -->
<!-- Оркестратор страницы товара. Компонует: JsonLd, ProductGallery, ProductHeader, ProductTabs. -->
<template>
  <div class="product-detail">
    <span class="debug-tag" v-if="debug">ProductDetail</span>
    <JsonLd :schema="product.schema" />

    <div class="detail-layout">
      <div class="detail-gallery">
        <ProductGallery :images="galleryImages" :alt="product.image_alt || product.code" />
      </div>

      <div class="detail-info">
        <ProductHeader :name="product.title || product.name" :code="product.code" :price="price" />
        <div class="detail-actions" v-if="product.sku?.id">
          <AddToCartButton :skuId="product.sku.id" />
        </div>

        <ProductTabs :tabs="tabItems">
          <template #default="{ activeTab }">
            <template v-for="section in product.sections" :key="section.key">
              <div v-if="activeTab === section.key">
                <TabSpecs v-if="section.type === 'specs'" :groups="section.groups" />
                <FileList v-else-if="section.type === 'files'" :files="section.data" />
                <div v-else-if="section.type === 'text'" class="section-text" v-html="section.data"></div>
              </div>
            </template>
          </template>
        </ProductTabs>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { debug } from '@/shared/config'
import JsonLd from './JsonLd.vue'
import ProductGallery from './ProductGallery.vue'
import ProductHeader from './ProductHeader.vue'
import ProductTabs from './ProductTabs.vue'
import TabSpecs from './TabSpecs.vue'
import FileList from './FileList.vue'
import AddToCartButton from './AddToCartButton.vue'

const props = defineProps({
  product: { type: Object, required: true },
  price: { type: Object, default: null },
  breadcrumbs: { type: Array, default: () => [] },
})

const tabItems = computed(() =>
  (props.product.sections || [])
    .filter(s => s.type !== 'gallery')
    .sort((a, b) => (a.order || 99) - (b.order || 99))
)

const galleryImages = computed(() => {
  const s = (props.product.sections || []).find(s => s.type === 'gallery')
  return s?.data || []
})
</script>

<style scoped>
.product-detail { max-width: 1200px; margin: 0 auto; padding: 16px; }
.detail-layout { display: flex; gap: 32px; margin-top: 16px; }
.detail-gallery { width: 460px; flex-shrink: 0; }
.detail-info { flex: 1; min-width: 0; }
.detail-actions { margin: 12px 0; }
.section-text { font-size: var(--cat-text-base); line-height: 1.6; color: var(--cat-text-soft); }

@media (max-width: 768px) {
  .detail-layout { flex-direction: column; }
  .detail-gallery { width: 100%; }
}
</style>
