<!-- shared/components/catalog/CatalogSection.vue -->
<!-- DEBUG: CatalogSection -->
<template>
  <div class="catalog-section">
    <span class="debug-tag" v-if="debug">CatalogSection</span>
    <PageTitle :title="labels.title" :subtitle="labels.subtitle" />
    <div class="series-grid" v-if="series.length">
      <div v-for="s in series" :key="s.id" class="series-card" @click="$emit('selectSeries', s.id)">
        <div class="series-image"><img v-if="s.image" :src="s.image" :alt="s.name" loading="lazy" /><span v-else class="no-image">{{ labels.icon }}</span></div>
        <div class="series-body"><h3>Серия {{ s.name }}</h3><p class="series-desc" v-if="s.description">{{ s.description }}</p></div>
      </div>
    </div>
    <div class="empty" v-else-if="loaded">Нет доступных серий</div>
    <Spinner v-else />
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { debug } from '@/shared/config'
import Breadcrumbs from '@/shared/components/Breadcrumbs.vue'
import PageTitle from '@/shared/components/PageTitle.vue'
import Spinner from '@/shared/components/Spinner.vue'
const props = defineProps({ api:{type:Object,required:true}, labels:{type:Object,required:true} })
defineEmits(['selectSeries','navigate'])
const series = ref([])
const loaded = ref(false)
const eqLabel = computed(() => props.labels.breadcrumbName || props.labels.title)
const breadcrumbs = computed(() => [
  { name: 'Каталог', to: '/' },
  { name: eqLabel.value },
  { name: 'Просмотр по сериям' },
])
onMounted(async () => {
  try {
    if (props.api.getSections) {
      const r = await props.api.getSections()
      series.value = (r.data || []).sort((a, b) => a.name.localeCompare(b.name))
    } else {
      const r = await props.api.list({ limit: 1000 })
      const items = r.data?.data || []
      const map = {}
      for (const item of items) {
        const ml = item.model_line
        if (!ml || map[ml.id]) continue
        map[ml.id] = { id: ml.id, name: ml.name, code: ml.code || '', image: item.images?.[0]?.preview_url || item.images?.[0]?.url || null, count: 0 }
      }
      for (const item of items) {
        const ml = item.model_line
        if (ml && map[ml.id]) map[ml.id].count++
      }
      series.value = Object.values(map).sort((a, b) => a.name.localeCompare(b.name))
    }
  } catch (e) {
    console.error('[CatalogSection] error:', e?.response?.status, e?.response?.data || e?.message || e)
  }
  loaded.value = true
})
</script>
<style scoped>
.catalog-section{max-width:1200px;margin:0 auto;padding:var(--cat-gap-xl,16px)} .series-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:var(--cat-gap-2xl,20px)} .series-card{background:var(--cat-surface,#fff);border:1px solid var(--cat-border,#e5e7eb);border-radius:var(--cat-radius-lg,12px);overflow:hidden;cursor:pointer;transition:box-shadow .15s,border-color .15s} .series-card:hover{box-shadow:var(--cat-shadow-card,0 4px 20px rgba(0,0,0,.06));border-color:var(--cat-primary,#2563eb)} .series-image{aspect-ratio:16/9;background:var(--cat-bg,#f9fafb);display:flex;align-items:center;justify-content:center;overflow:hidden} .series-image img{width:100%;height:100%;object-fit:contain} .no-image{font-size:48px} .series-body{padding:var(--cat-gap-xl,16px)} .series-body h3{font-size:var(--cat-text-lg,16px);font-weight:600;margin:0 0 4px;color:var(--cat-text,#1f2937)} .series-desc{font-size:var(--cat-text-sm,13px);color:var(--cat-muted,#6b7280);margin:0;line-height:1.5;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden} .empty{text-align:center;padding:60px 20px;color:var(--cat-muted-light,#9ca3af);font-size:var(--cat-text-md,16px)} @media(max-width:768px){.series-grid{grid-template-columns:repeat(2,1fr)}} @media(max-width:480px){.series-grid{grid-template-columns:1fr}}
</style>
