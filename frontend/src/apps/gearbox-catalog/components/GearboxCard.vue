<template>
  <div class="card" @click="$emit('click')">
    <div class="card-image">
      <img
        v-if="mainImage"
        :src="mainImage"
        :alt="item.image_alt || 'Редуктор'"
        loading="lazy"
      />
      <div v-else class="placeholder">
        <span>Нет фото</span>
      </div>
    </div>
    <div class="card-body">
      <div class="card-name">{{ item.name || item.code || '—' }}</div>
      <div class="card-meta">
        <span v-if="item.model_line?.brand?.name">{{ item.model_line.brand.name }}</span>
        <span v-if="item.model_line?.gearbox_variety">{{ item.model_line.gearbox_variety }}</span>
      </div>
      <div class="card-price" v-if="price">
        {{ formatPrice(price.price) }} {{ price.currency_symbol || '$' }}
      </div>
      <div class="card-price placeholder-price" v-else>
        Цена по запросу
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  item: Object,
  price: Object,
})
defineEmits(['click'])

const mainImage = computed(() => {
  const imgs = props.item.images || []
  if (imgs.length === 0) return null
  // Ищем default или берём первую
  const def = imgs.find(i => i.is_default)
  const img = def || imgs[0]
  return img.url || img.preview_url || null
})

function formatPrice(val) {
  if (val == null) return ''
  const n = Number(val)
  if (isNaN(n)) return ''
  return n.toLocaleString('ru-RU', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}
</script>

<style scoped>
.card{
  background:#fff;
  border-radius:12px;
  overflow:hidden;
  cursor:pointer;
  transition:box-shadow .2s,transform .15s;
  display:flex;
  flex-direction:column;
}
.card:hover{box-shadow:0 4px 24px rgba(0,0,0,.1);transform:translateY(-2px)}
.card-image{
  position:relative;
  width:100%;
  padding-top:75%;
  background:#f9fafb;
  overflow:hidden;
}
.card-image img{
  position:absolute;
  top:0;left:0;
  width:100%;
  height:100%;
  object-fit:contain;
  padding:16px;
}
.placeholder{
  position:absolute;
  top:0;left:0;
  width:100%;height:100%;
  display:flex;
  align-items:center;
  justify-content:center;
  color:#d1d5db;
  font-size:14px;
  background:#f3f4f6;
}
.card-body{padding:14px 16px 16px;flex:1;display:flex;flex-direction:column;gap:6px}
.card-name{font-size:15px;font-weight:500;line-height:1.4;color:#1a1a1a;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.card-meta{display:flex;gap:8px;font-size:12px;color:#9ca3af;flex-wrap:wrap}
.card-meta span{background:#f3f4f6;padding:2px 8px;border-radius:4px}
.card-price{font-size:18px;font-weight:700;color:#dc2626;margin-top:auto;padding-top:4px}
.placeholder-price{font-size:13px;font-weight:400;color:#9ca3af}
</style>
