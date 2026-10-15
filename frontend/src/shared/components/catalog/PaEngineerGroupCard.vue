<!-- shared/components/catalog/PaEngineerGroupCard.vue -->
<!-- Расширенная карточка результата подбора ПП: одна карточка на model_line_item.
     Сверху — чипсы вариантов опций; ниже — блок информации о модели
     (PaModelInfoBlock) и «Блок купить» (PaBuyBlock) справа. Клик по карточке
     открывает карточку просмотра товара (SKU) выбранного варианта. -->
<template>
  <div class="pa-group-card" @click="open">
    <!-- Чипсы вариантов опций (сверху) -->
    <div v-if="group.chips.length" class="pa-group-card__chips" @click.stop>
      <div v-for="chip in group.chips" :key="chip.key" class="pa-chip-group">
        <span class="pa-chip-group__label">{{ chip.label }}</span>
        <div class="pa-chip-row">
          <button
            v-for="v in chip.variants"
            :key="v.value"
            type="button"
            class="pa-chip"
            :class="{ 'pa-chip--active': selected[chip.key] === v.value }"
            @click="selectChip(chip.key, v.value)"
          >{{ v.label }}</button>
        </div>
      </div>
    </div>

    <!-- Контент: изображение + информация о модели + блок купить -->
    <div class="pa-group-card__content">
      <div class="pa-group-card__image">
        <ProgressiveImage
          v-if="imagePreview || imageFull"
          :preview="imagePreview"
          :full="imageFull"
          :alt="activeItem.code"
        />
        <span v-else class="pa-group-card__no-img">🈚</span>
      </div>

      <PaModelInfoBlock :item="activeItem" class="pa-group-card__info" />
      <PaBuyBlock :sku-id="activeItem.sku_id" :price="activeItem.price" class="pa-group-card__buy" />
    </div>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'
import ProgressiveImage from '@/shared/components/ProgressiveImage.vue'
import PaModelInfoBlock from '@/shared/components/catalog/PaModelInfoBlock.vue'
import PaBuyBlock from '@/shared/components/catalog/PaBuyBlock.vue'

const props = defineProps({
  group: { type: Object, required: true },
})

const emit = defineEmits(['select'])

// По умолчанию выделяем чипсы, соответствующие выводимой модели (первый вариант),
// чтобы при первичном выводе списка было видно, какое исполнение показано.
const firstOptions = (props.group.items?.[0]?.options) || {}
const selected = reactive(
  Object.fromEntries(
    Object.entries(firstOptions).map(([key, opt]) => [key, opt.value])
  )
)

const activeItem = computed(() => {
  const items = props.group.items || []
  if (!items.length) return {}
  const keys = Object.keys(selected)
  if (!keys.length) return items[0]
  const matched = items.find(it => {
    const opts = it.options || {}
    return keys.every(k => opts[k] && opts[k].value === selected[k])
  })
  return matched || items[0]
})

const imgs = computed(() => activeItem.value.images || [])
const imagePreview = computed(() => imgs.value[0]?.preview_url || imgs.value[0]?.url || null)
const imageFull = computed(() => {
  const first = imgs.value[0]
  if (!first) return null
  return first.url !== first.preview_url ? (first.url || null) : null
})

function selectChip(key, value) {
  if (selected[key] === value) {
    delete selected[key]
  } else {
    selected[key] = value
  }
}

function open() {
  emit('select', activeItem.value.sku_id)
}
</script>

<style scoped>
.pa-group-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: var(--cat-surface, #fff);
  border: 1px solid var(--cat-border, #e5e7eb);
  border-radius: var(--cat-radius-lg, 12px);
  padding: 16px;
  cursor: pointer;
  transition: box-shadow .15s, border-color .15s;
}
.pa-group-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,.06);
  border-color: var(--cat-primary, #2563eb);
}

/* ── Chips ── */
.pa-group-card__chips {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.pa-chip-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}
.pa-chip-group__label {
  font-size: var(--cat-text-xs, 12px);
  font-weight: 600;
  color: var(--cat-muted, #6b7280);
  min-width: 120px;
}
.pa-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.pa-chip {
  padding: 4px 12px;
  font-size: var(--cat-text-xs, 12px);
  border: 1px solid var(--cat-border, #d1d5db);
  border-radius: 16px;
  background: var(--cat-surface, #fff);
  color: var(--cat-text, #1f2937);
  cursor: pointer;
  transition: all .12s;
  white-space: nowrap;
}
.pa-chip:hover {
  border-color: var(--cat-primary, #2563eb);
  color: var(--cat-primary, #2563eb);
}
.pa-chip--active {
  background: var(--cat-primary, #2563eb);
  color: #fff;
  border-color: var(--cat-primary, #2563eb);
}

/* ── Content ── */
.pa-group-card__content {
  display: flex;
  align-items: stretch;
  gap: 16px;
}
.pa-group-card__image {
  flex: 0 0 96px;
  height: 96px;
  border-radius: var(--cat-radius-md, 8px);
  background: var(--cat-bg, #f9fafb);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.pa-group-card__image :deep(img) {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.pa-group-card__no-img {
  font-size: 28px;
  color: var(--cat-border, #d1d5db);
}
.pa-group-card__info {
  flex: 1;
  min-width: 0;
}
.pa-group-card__buy {
  flex: 0 0 auto;
  align-self: stretch;
}
</style>
