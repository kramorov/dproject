<!-- shared/components/catalog/CatalogSection.vue -->
<!-- DEBUG: CatalogSection -->
<template>
  <div class="catalog-section">
    <span class="debug-tag" v-if="debug">CatalogSection</span>
    <PageTitle :title="labels.title" :subtitle="labels.subtitle" />

    <!-- Чипсы-фильтры (опционально, напр. конструкция у ПП) -->
    <div v-if="filters.length" class="filter-groups">
      <div v-for="f in filters" :key="f.field" class="filter-group">
        <span class="filter-label">{{ f.label }}</span>
        <div class="chips">
          <button
            v-for="opt in f.options" :key="opt.value"
            class="chip"
            :class="{ active: (activeFilter[f.field] ?? f.default) === opt.value }"
            @click="selectFilter(f, opt.value)"
          >{{ opt.label }}</button>
        </div>
      </div>
    </div>

    <Spinner v-if="loading && !series.length" />
    <div v-if="loading && series.length" class="loading-hint">Обновление…</div>

    <div class="series-grid" v-if="series.length">
      <div v-for="s in series" :key="s.id" class="series-card" @click="$emit('selectSeries', s.id)">
        <div class="series-image"><img v-if="s.image" :src="s.image" :alt="s.name" loading="lazy" /><span v-else class="no-image">{{ labels.icon }}</span></div>
        <div class="series-body"><h3>Серия {{ s.name }}</h3><p class="series-desc" v-if="s.description">{{ s.description }}</p></div>
      </div>
    </div>
    <div class="empty" v-else-if="loaded && !loading">Нет доступных серий</div>
  </div>
</template>
<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { debug } from '@/shared/config'
import PageTitle from '@/shared/components/PageTitle.vue'
import Spinner from '@/shared/components/Spinner.vue'
const props = defineProps({
  api:{type:Object,required:true},
  labels:{type:Object,required:true},
  filters:{type:Array,default:()=>[]},
})
defineEmits(['selectSeries','navigate'])
const series = ref([])
const loaded = ref(false)
const loading = ref(false)
const activeFilter = reactive({})
let loadSeq = 0

function buildParams() {
  const params = {}
  for (const f of props.filters) {
    if (!f.param) continue
    const val = activeFilter[f.field] ?? f.default
    if (val !== null && val !== undefined && val !== '') {
      params[f.param] = val
    }
  }
  return params
}

async function loadSeries() {
  const seq = ++loadSeq
  loading.value = true
  try {
    if (props.api.getSections) {
      const r = await props.api.getSections(buildParams())
      if (seq !== loadSeq) return
      series.value = (r.data || []).sort((a, b) => a.name.localeCompare(b.name))
    } else {
      const r = await props.api.list({ limit: 1000 })
      if (seq !== loadSeq) return
      const items = r.data?.data || []
      const map = {}
      for (const item of items) {
        const ml = item.model_line
        if (!ml || map[ml.id]) continue
        map[ml.id] = { id: ml.id, name: ml.name, code: ml.code || '', description: ml.description || '', image: item.images?.[0]?.preview_url || item.images?.[0]?.url || null, count: 0 }
      }
      for (const item of items) {
        const ml = item.model_line
        if (ml && map[ml.id]) map[ml.id].count++
      }
      series.value = Object.values(map).sort((a, b) => a.name.localeCompare(b.name))
    }
  } catch (e) {
    console.error('[CatalogSection] error:', e?.response?.status, e?.response?.data || e?.message || e)
  } finally {
    if (seq === loadSeq) loading.value = false
    loaded.value = true
  }
}

function selectFilter(f, value) {
  activeFilter[f.field] = value
  loadSeries()
}

watch(() => props.filters, () => { loadSeries() })

onMounted(loadSeries)
</script>
<style scoped>
.catalog-section{max-width:1200px;margin:0 auto;padding:var(--cat-gap-xl,16px)} .series-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:var(--cat-gap-2xl,20px)} .series-card{background:var(--cat-surface,#fff);border:1px solid var(--cat-border,#e5e7eb);border-radius:var(--cat-radius-lg,12px);overflow:hidden;cursor:pointer;transition:box-shadow .15s,border-color .15s} .series-card:hover{box-shadow:var(--cat-shadow-card,0 4px 20px rgba(0,0,0,.06));border-color:var(--cat-primary,#2563eb)} .series-image{aspect-ratio:16/9;background:var(--cat-bg,#f9fafb);display:flex;align-items:center;justify-content:center;overflow:hidden} .series-image img{width:100%;height:100%;object-fit:contain} .no-image{font-size:48px} .series-body{padding:var(--cat-gap-xl,16px)} .series-body h3{font-size:var(--cat-text-lg,16px);font-weight:600;margin:0 0 4px;color:var(--cat-text,#1f2937)} .series-desc{font-size:var(--cat-text-sm,13px);color:var(--cat-muted,#6b7280);margin:0;line-height:1.5;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden} .empty{text-align:center;padding:60px 20px;color:var(--cat-muted-light,#9ca3af);font-size:var(--cat-text-md,16px)} @media(max-width:768px){.series-grid{grid-template-columns:repeat(2,1fr)}} @media(max-width:480px){.series-grid{grid-template-columns:1fr}}
.filter-groups{display:flex;flex-direction:column;gap:var(--cat-gap-sm,8px);margin-bottom:var(--cat-gap-xl,16px)}
.filter-group{display:flex;align-items:center;gap:var(--cat-gap-sm,8px);flex-wrap:wrap}
.filter-label{font-size:var(--cat-text-sm,13px);color:var(--cat-muted,#6b7280);font-weight:500}
.chips{display:flex;flex-wrap:wrap;gap:var(--cat-gap-xs,6px)}
.chip{padding:4px 12px;border:1px solid var(--cat-border,#e5e7eb);border-radius:999px;background:var(--cat-surface,#fff);color:var(--cat-text,#1f2937);cursor:pointer;font-size:var(--cat-text-sm,13px);transition:border-color .15s,color .15s,background .15s}
.chip:hover{border-color:var(--cat-primary,#2563eb);color:var(--cat-primary,#2563eb)}
.chip.active{background:var(--cat-primary,#2563eb);color:#fff;border-color:var(--cat-primary,#2563eb)}
.loading-hint{font-size:var(--cat-text-sm,13px);color:var(--cat-muted,#6b7280);margin-bottom:var(--cat-gap-sm,8px)}
</style>
