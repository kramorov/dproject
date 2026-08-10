<!-- shared/components/catalog/EngineerProductCard.vue -->
<!-- Card for EngineerSelection list — compact horizontal layout with key specs. -->
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
    <div class="eng-card__body">
      <div class="eng-card__header">
        <h3 class="eng-card__title">{{ item.title || item.name || item.code }}</h3>
        <span class="eng-card__code">{{ item.code }}</span>
      </div>
      <div class="eng-card__specs" v-if="specs.length">
        <span v-for="s in specs" :key="s.label" class="eng-card__spec">
          <span class="eng-card__spec-label">{{ s.label }}</span>
          <span class="eng-card__spec-value">{{ s.value }}</span>
        </span>
      </div>
      <div class="eng-card__footer">
        <div class="eng-card__cart" v-if="item.sku_id" @click.stop>
          <AddToCartButton :skuId="item.sku_id" />
        </div>
        <div class="eng-card__price" v-if="price && price.price != null && price.price !== '0' && price.price !== '0.00'">
          <span class="eng-card__price-val">{{ price.price }}</span>
          <span class="eng-card__price-cur">{{ price.symbol || price.currency }}</span>
        </div>
        <span v-else class="eng-card__price eng-card__price--na">Цена по запросу</span>
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
})

const emit = defineEmits(['select'])

const imgs = computed(() => props.item.images || [])
const imagePreview = computed(() => imgs.value[0]?.preview_url || imgs.value[0]?.url || null)
const imageFull = computed(() => {
  const first = imgs.value[0]
  if (!first) return null
  return first.url !== first.preview_url ? (first.url || null) : null
})

// Dynamic specs — extract key engineering params from item
const specs = computed(() => {
  const result = []
  const i = props.item

  // IP rating
  if (i.ip) {
    result.push({ label: 'IP', value: typeof i.ip === 'object' ? (i.ip.name || i.ip.code || '') : String(i.ip) })
  }
  // Body material
  if (i.body_material) {
    result.push({ label: 'Корпус', value: typeof i.body_material === 'object' ? (i.body_material.name || i.body_material.code || '') : String(i.body_material) })
  }
  // Temperature
  if (i.work_temp_min != null || i.work_temp_max != null) {
    const tmin = i.work_temp_min != null ? i.work_temp_min : '…'
    const tmax = i.work_temp_max != null ? i.work_temp_max : '…'
    result.push({ label: 't, °C', value: `${tmin}…${tmax}` })
  }
  // Torque (gearbox)
  if (i.torque != null) {
    result.push({ label: 'Mкр, Нм', value: i.torque })
  }
  // Flow rate (filter-regulator)
  if (i.flow_rate != null) {
    result.push({ label: 'Расход, л/мин', value: i.flow_rate })
  }
  // Thread (filter-regulator)
  if (i.thread) {
    result.push({ label: 'Резьба', value: typeof i.thread === 'object' ? (i.thread.name || i.thread.code || '') : String(i.thread) })
  }
  // Sensor variety (limit-switch)
  if (i.sensor_variety) {
    result.push({ label: 'Датчики', value: typeof i.sensor_variety === 'object' ? (i.sensor_variety.name || '') : String(i.sensor_variety) })
  }
  // Points (limit-switch)
  if (i.points != null) {
    result.push({ label: 'Контакты', value: i.points })
  }
  // Fitting variety (pneumatic fittings)
  if (i.fitting_variety) {
    result.push({ label: 'Тип фитинга', value: typeof i.fitting_variety === 'object' ? (i.fitting_variety.name || '') : String(i.fitting_variety) })
  }
  // Thread name (pneumatic fittings use thread_name)
  if (i.thread_name) {
    result.push({ label: 'Резьба', value: String(i.thread_name) })
  }
  // Thread inner/outer (pneumatic fittings)
  if (i.thread_inner_outer_name) {
    result.push({ label: 'Нар./внут.', value: String(i.thread_inner_outer_name) })
  }
  // Pipe material (pneumatic fittings)
  if (i.pipe_material) {
    result.push({ label: 'Материал трубки', value: typeof i.pipe_material === 'object' ? (i.pipe_material.name || '') : String(i.pipe_material) })
  }

  return result
})
</script>

<style scoped>
/* ── Card root ── */
.eng-card {
  display: flex;
  gap: 16px;
  background: var(--cat-surface, #fff);
  border: 1px solid var(--cat-border, #e5e7eb);
  border-radius: var(--cat-radius-lg, 10px);
  padding: 16px;
  cursor: pointer;
  transition: box-shadow .15s, border-color .15s;
}
.eng-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,.06);
  border-color: var(--cat-primary, #2563eb);
}

/* ── Image ── */
.eng-card__image {
  flex: 0 0 100px;
  height: 100px;
  border-radius: var(--cat-radius-md, 6px);
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

/* ── Body ── */
.eng-card__body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* ── Header ── */
.eng-card__header {
  display: flex;
  align-items: baseline;
  gap: 12px;
}
.eng-card__title {
  font-size: var(--cat-text-md, 15px);
  font-weight: 600;
  color: var(--cat-text, #1f2937);
  margin: 0;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.eng-card__code {
  flex-shrink: 0;
  font-size: var(--cat-text-xs, 11px);
  color: var(--cat-muted, #6b7280);
  font-family: var(--cat-font-mono, monospace);
  background: var(--cat-bg, #f3f4f6);
  padding: 2px 8px;
  border-radius: 4px;
}

/* ── Specs row ── */
.eng-card__specs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
}
.eng-card__spec {
  display: inline-flex;
  gap: 4px;
  font-size: var(--cat-text-sm, 12px);
}
.eng-card__spec-label {
  color: var(--cat-muted, #9ca3af);
}
.eng-card__spec-value {
  color: var(--cat-text, #374151);
  font-weight: 500;
}

/* ── Footer (cart + price) ── */
.eng-card__footer {
  margin-top: auto;
  display: flex;
  align-items: center;
  gap: 12px;
}
.eng-card__cart {
  flex-shrink: 0;
}
.eng-card__price {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
}
.eng-card__price-val {
  font-size: var(--cat-price-size, 18px);
  font-weight: var(--cat-price-weight, 700);
  color: var(--cat-price-color, #059669);
}
.eng-card__price-cur {
  font-size: var(--cat-text-xs, 12px);
  color: var(--cat-muted, #6b7280);
}
.eng-card__price--na {
  font-size: var(--cat-text-sm, 13px);
  color: var(--cat-muted, #9ca3af);
  font-weight: 400;
}

/* ── Responsive ── */
@media (max-width: 640px) {
  .eng-card {
    gap: 12px;
    padding: 12px;
  }
  .eng-card__image {
    flex: 0 0 72px;
    height: 72px;
  }
  .eng-card__specs {
    gap: 4px 12px;
  }
}
</style>