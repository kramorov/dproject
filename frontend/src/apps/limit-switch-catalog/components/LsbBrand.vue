<!-- limit-switch-catalog/components/GearboxBrand.vue -->
<template>
  <div class="brand-page">
    <button class="back-btn" @click="$emit('close')">← К сериям</button>
    <h1 class="page-title" v-if="modelLineName">{{ modelLineName }}</h1>

    <div v-if="loading" class="status">Загрузка...</div>
    <div v-else class="cards-grid">
      <div v-for="item in items" :key="item.id" class="card" @click="$emit('select', item.id)">
        <div class="card-image">
          <img v-if="item.images?.[0]?.preview_url" :src="item.images[0].preview_url" :alt="item.name" loading="lazy" />
          <span v-else class="no-image">🔌</span>
        </div>
        <div class="card-body">
          <h3>{{ item.name }}</h3>
          <p class="card-code" v-if="item.code">{{ item.code }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import lsbApi from '../api'

const props = defineProps({
  modelLineId: [Number, String],
})
defineEmits(['select', 'close'])

const items = ref([])
const modelLineName = ref('')
const loading = ref(false)

async function fetchData() {
  if (!props.modelLineId) return
  loading.value = true
  try {
    const r = await lsbApi.list({ model_line_id: props.modelLineId, limit: 1000 })
    items.value = r.data?.data || []
    if (items.value.length) {
      modelLineName.value = items.value[0].model_line?.name || ''
    }
  } catch (e) { console.error('Failed to load brand items', e) }
  finally { loading.value = false }
}

onMounted(fetchData)
watch(() => props.modelLineId, fetchData)
</script>

<style scoped>
.brand-page { max-width: 1200px; margin: 0 auto; padding: 16px; }
.back-btn {
  padding: 8px 16px; font-size: 14px;
  background: var(--cat-surface, #fff);
  border: 1px solid var(--cat-border, #d1d5db);
  border-radius: var(--cat-radius-md, 6px);
  cursor: pointer; margin-bottom: 16px;
  color: var(--cat-text, #1f2937);
}
.back-btn:hover { border-color: var(--cat-primary, #2563eb); color: var(--cat-primary, #2563eb); }
.page-title { font-size: var(--cat-text-2xl, 24px); font-weight: 700; margin: 0 0 16px; color: var(--cat-text, #1f2937); }
.cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: var(--cat-gap-2xl, 16px); }
.card { background: var(--cat-surface, #fff); border: 1px solid var(--cat-border, #e5e7eb); border-radius: var(--cat-radius-lg, 10px); overflow: hidden; cursor: pointer; transition: box-shadow .15s; }
.card:hover { box-shadow: var(--cat-shadow-card, 0 4px 20px rgba(0,0,0,.06)); }
.card-image { aspect-ratio: 4/3; background: var(--cat-bg, #f9fafb); display: flex; align-items: center; justify-content: center; }
.card-image img { width: 100%; height: 100%; object-fit: contain; }
.no-image { font-size: 40px; }
.card-body { padding: 12px; }
.card-body h3 { font-size: var(--cat-text-base, 14px); font-weight: 600; margin: 0 0 4px; color: var(--cat-text, #1f2937); }
.card-code { font-size: 12px; color: var(--cat-muted, #6b7280); font-family: monospace; margin: 0; }
.status { text-align: center; padding: 40px; color: var(--cat-muted-light, #9ca3af); }
</style>
