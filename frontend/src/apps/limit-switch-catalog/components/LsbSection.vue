<!-- limit-switch-catalog/components/GearboxSection.vue -->
<template>
  <div class="section-page">
    <h1 class="page-title">Блоки концевых выключателей</h1>
    <p class="page-subtitle">
      Выберите серию
      <button class="show-all-btn" @click="$emit('select')">Показать все</button>
    </p>

    <div class="series-grid" v-if="series.length">
      <div v-for="s in series" :key="s.id" class="series-card" @click="$emit('selectSeries', s.id)">
        <div class="series-image">
          <img v-if="s.image" :src="s.image" :alt="s.name" loading="lazy" />
          <span v-else class="no-image">🔌</span>
        </div>
        <div class="series-body">
          <h3>{{ s.name }}</h3>
          <p class="series-code" v-if="s.code">{{ s.code }}</p>
          <p class="series-count" v-if="s.count">{{ s.count }} моделей</p>
        </div>
      </div>
    </div>
    <div class="empty" v-else-if="loaded">Нет доступных серий</div>
    <div class="loading" v-else>Загрузка...</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import lsbApi from '../api'

defineEmits(['selectSeries', 'select'])

const series = ref([])
const loaded = ref(false)

onMounted(async () => {
  try {
    const r = await lsbApi.list({ limit: 1000 })
    const items = r.data?.data || []
    const map = {}
    for (const item of items) {
      const ml = item.model_line
      if (!ml) continue
      if (!map[ml.id]) {
        map[ml.id] = {
          id: ml.id,
          name: ml.name,
          code: ml.code || '',
          image: item.images?.[0]?.preview_url || item.images?.[0]?.url || null,
          count: 0,
        }
      }
      map[ml.id].count++
    }
    series.value = Object.values(map).sort((a, b) => a.name.localeCompare(b.name))
  } catch (e) { console.error('Failed to load series', e) }
  loaded.value = true
})
</script>

<style scoped>
.section-page { max-width: 1200px; margin: 0 auto; padding: 16px; }
.page-title { font-size: var(--cat-text-3xl, 28px); font-weight: 700; margin: 8px 0 4px; color: var(--cat-text, #1f2937); }
.page-subtitle { font-size: var(--cat-text-md, 15px); color: var(--cat-muted, #6b7280); margin: 0 0 var(--cat-gap-2xl, 24px); display: flex; align-items: center; gap: 12px; }
.show-all-btn { padding: 4px 16px; font-size: 13px; background: var(--cat-primary, #2563eb); color: #fff; border: none; border-radius: var(--cat-radius-sm, 4px); cursor: pointer; }
.show-all-btn:hover { background: var(--cat-primary-hover, #1d4ed8); }
.series-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--cat-gap-2xl, 20px); }
.series-card { background: var(--cat-surface, #fff); border: 1px solid var(--cat-border, #e5e7eb); border-radius: var(--cat-radius-lg, 12px); overflow: hidden; cursor: pointer; transition: box-shadow .15s, border-color .15s; }
.series-card:hover { box-shadow: var(--cat-shadow-card, 0 4px 20px rgba(0,0,0,.06)); border-color: var(--cat-primary, #2563eb); }
.series-image { aspect-ratio: 16/9; background: var(--cat-bg, #f9fafb); display: flex; align-items: center; justify-content: center; overflow: hidden; }
.series-image img { width: 100%; height: 100%; object-fit: contain; }
.no-image { font-size: 48px; }
.series-body { padding: var(--cat-gap-xl, 16px); }
.series-body h3 { font-size: var(--cat-text-lg, 16px); font-weight: 600; margin: 0 0 4px; color: var(--cat-text, #1f2937); }
.series-code { font-size: var(--cat-text-sm, 13px); color: var(--cat-muted, #6b7280); font-family: monospace; margin: 0 0 8px; }
.series-count { font-size: var(--cat-text-sm, 13px); color: var(--cat-primary, #2563eb); font-weight: 500; margin: 0; }
.empty, .loading { text-align: center; padding: 60px 20px; color: var(--cat-muted-light, #9ca3af); font-size: var(--cat-text-md, 16px); }
@media (max-width: 768px) { .series-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 480px) { .series-grid { grid-template-columns: 1fr; } }
</style>
