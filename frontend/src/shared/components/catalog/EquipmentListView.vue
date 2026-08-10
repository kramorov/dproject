<!-- shared/components/catalog/EquipmentListView.vue — Универсальный список: сетка/строки -->
<template>
  <div class="elv">
    <!-- Переключатель сетка/список -->
    <div class="elv-toolbar" v-if="showModeSwitch">
      <button class="elv-mode-btn" :class="{ active: mode === 'grid' }" @click="$emit('update:mode', 'grid')" title="Сетка">▦</button>
      <button class="elv-mode-btn" :class="{ active: mode === 'list' }" @click="$emit('update:mode', 'list')" title="Список">☰</button>
    </div>

    <!-- Сетка -->
    <div v-if="mode === 'grid'" class="elv-grid">
      <div v-for="item in items" :key="item.id" class="elv-card" @click="onSelect(item)">
        <ProductCard
          :item="toCardItem(item)"
          :price="toPrice(item)"
          :skuId="item.sku_id"
        />
        <div class="elv-card__footer" v-if="showControls" @click.stop>
          <slot name="controls" :item="item">
            <div class="elv-card__price" v-if="item.price != null">{{ item.price }} ₽</div>
          </slot>
        </div>
      </div>
    </div>

    <!-- Список (строки) -->
    <div v-else class="elv-list">
      <div v-for="item in items" :key="item.id" class="elv-row" @click="onSelect(item)">
        <div class="elv-row__image">
          <img v-if="item.images?.[0]?.preview_url" :src="item.images[0].preview_url" :alt="item.equipment_summary?.code" />
          <span v-else class="elv-row__no-img">📦</span>
        </div>
        <div class="elv-row__body">
          <h3 class="elv-row__title">{{ item.equipment_summary?.name }}</h3>
          <span class="elv-row__code">{{ item.equipment_summary?.code }}</span>
          <span class="elv-row__brand" v-if="item.equipment_summary?.brand">{{ item.equipment_summary.brand }}</span>
        </div>
        <div class="elv-row__right" v-if="showControls" @click.stop>
          <slot name="controls" :item="item">
            <div class="elv-row__price" v-if="item.price != null">{{ item.price }} ₽</div>
          </slot>
        </div>
      </div>
    </div>

    <div v-if="empty && !items.length" class="elv-empty">{{ emptyText }}</div>
  </div>
</template>

<script setup>
import ProductCard from '@/shared/components/ProductCard.vue'

defineProps({
  items: { type: Array, default: () => [] },
  mode: { type: String, default: 'grid' },       // 'grid' | 'list'
  showModeSwitch: { type: Boolean, default: false },
  showControls: { type: Boolean, default: true },
  empty: { type: Boolean, default: false },
  emptyText: { type: String, default: 'Нет данных' },
})

const emit = defineEmits(['select', 'update:mode'])

/** Преобразовать cart-элемент в формат ProductCard */
function toCardItem(item) {
  return {
    id: item.id,
    code: item.equipment_summary?.code,
    name: item.equipment_summary?.name,
    title: item.equipment_summary?.name,
    images: item.images || [],
  }
}

/** Преобразовать цену в формат ProductCard */
function toPrice(item) {
  if (item.price == null) return null
  return { price: item.price, symbol: '₽', currency: 'RUB' }
}

function onSelect(item) {
  emit('select', item.id)
}
</script>

<style scoped>
.elv { width: 100%; }

/* ── Toolbar ── */
.elv-toolbar { display: flex; justify-content: flex-end; gap: 4px; margin-bottom: 12px; }
.elv-mode-btn {
  background: none; border: 1px solid var(--cat-border, #d1d5db); border-radius: 6px;
  padding: 4px 10px; cursor: pointer; font-size: 16px; color: var(--cat-muted, #6b7280);
  transition: all .15s;
}
.elv-mode-btn:hover { border-color: var(--cat-primary, #3b82f6); }
.elv-mode-btn.active { background: var(--cat-primary, #3b82f6); color: #fff; border-color: var(--cat-primary, #3b82f6); }

/* ── Grid ── */
.elv-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }
.elv-card { border: 1px solid var(--cat-border, #e5e7eb); border-radius: var(--cat-radius-lg, 10px); overflow: hidden; background: #fff; cursor: pointer; transition: box-shadow .2s, border-color .2s; display: flex; flex-direction: column; }
.elv-card:hover { box-shadow: var(--cat-shadow-card-hover, 0 4px 12px rgba(0,0,0,.08)); border-color: var(--cat-primary, #3b82f6); }
.elv-card :deep(.product-card) { border: none; box-shadow: none; border-radius: 0; }
.elv-card :deep(.product-card:hover) { transform: none; box-shadow: none; }
.elv-card__footer { padding: 8px 12px; border-top: 1px solid var(--cat-border, #f3f4f6); display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-shrink: 0; }
.elv-card__price { font-size: 15px; font-weight: 600; color: var(--cat-price-color, #059669); }

/* ── List ── */
.elv-list { display: flex; flex-direction: column; gap: 8px; }
.elv-row { display: flex; align-items: center; gap: 14px; padding: 12px 16px; border: 1px solid var(--cat-border, #e5e7eb); border-radius: 10px; background: #fff; cursor: pointer; transition: border-color .15s; }
.elv-row:hover { border-color: var(--cat-primary, #3b82f6); }
.elv-row__image { width: 56px; height: 56px; flex-shrink: 0; border-radius: 6px; background: var(--cat-bg, #f9fafb); display: flex; align-items: center; justify-content: center; overflow: hidden; }
.elv-row__image img { width: 100%; height: 100%; object-fit: contain; }
.elv-row__no-img { font-size: 20px; color: var(--cat-border, #d1d5db); }
.elv-row__body { flex: 1; min-width: 0; }
.elv-row__title { margin: 0; font-size: 15px; font-weight: 600; color: var(--cat-text, #1f2937); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.elv-row__code { font-size: 12px; color: var(--cat-muted, #6b7280); font-family: var(--cat-font-mono, monospace); display: block; margin-top: 2px; }
.elv-row__brand { font-size: 12px; color: var(--cat-muted, #6b7280); }
.elv-row__right { flex-shrink: 0; text-align: right; }
.elv-row__price { font-size: 15px; font-weight: 600; color: var(--cat-price-color, #059669); }

/* ── Empty ── */
.elv-empty { text-align: center; padding: 40px 0; color: var(--cat-muted, #6b7280); }
</style>
