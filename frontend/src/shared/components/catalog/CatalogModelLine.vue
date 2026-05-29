<!-- shared/components/catalog/CatalogModelLine.vue -->
<template>
  <div class="catalog-model-line">
    <Breadcrumbs :items="breadcrumbs" @navigate="$emit('navigate', $event)" />
    <PageTitle :title="labels.title" :context="mlName" context-label="Серия" />
    <p class="page-count" v-if="total">{{ labels.countLabel || 'Товаров:' }} {{ total }}</p>
    <div class="content" v-if="!loading || items.length">
      <FilterSidebar v-if="filtersLoaded && showFilters" :filters="filterData" @change="onFilterChange" @reset="resetFilters" />
      <main class="main">
        <div class="grid" v-if="items.length"><ProductCard v-for="item in items" :key="item.id" :item="item" :price="item.price||null" @select="id=>emit('select',id)" /></div>
        <div class="empty" v-else-if="!loading">{{ labels.emptyLabel || 'Нет товаров' }}</div>
        <div class="pagination" v-if="total>limit"><button :disabled="offset===0" @click="goPage(offset-limit)">← Назад</button><span>{{ offset+1 }}–{{ Math.min(offset+limit,total) }} из {{ total }}</span><button :disabled="offset+limit>=total" @click="goPage(offset+limit)">Вперёд →</button></div>
      </main>
    </div>
    <Spinner v-else-if="loading" />
  </div>
</template>
<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import Breadcrumbs from '@/shared/components/Breadcrumbs.vue'
import PageTitle from '@/shared/components/PageTitle.vue'
import FilterSidebar from '@/shared/components/FilterSidebar.vue'
import ProductCard from '@/shared/components/ProductCard.vue'
import Spinner from '@/shared/components/Spinner.vue'
import { useCatalog } from '@/shared/composables/useCatalog.js'
const props = defineProps({ api:{type:Object,required:true}, labels:{type:Object,default:()=>({})}, idProp:{type:String,default:'model_line_id'}, idValue:{type:[Number,String],default:null}, showFilters:{type:Boolean,default:true} })
const emit = defineEmits(['select'])
const mlName = ref('')
const fixedParams = computed(() => props.idValue ? { [props.idProp]: props.idValue } : {})
const { items,total,loading,limit,offset, filterData,filtersLoaded, loadFilters,fetchData, onFilterChange,resetFilters,goPage } = useCatalog(props.api,{ fixedParams, filterScope:'model_line', withSearch:false, onData(items){ if(items.length&&!mlName.value) mlName.value=items[0]?.model_line?.name||'' } })
const eqLabel = computed(() => props.labels.breadcrumbName || 'Каталог')
const breadcrumbs = computed(() => [
  { name: 'Каталог' },
  { name: eqLabel.value },
  { name: mlName.value || 'Серия' },
])
watch(() => props.idValue, (newVal) => {
  if (newVal) {
    onFilterChange(props.idProp, newVal)
  } else {
    resetFilters()
    fetchData()
  }
})
onMounted(async () => {
  await loadFilters()
  if (props.idValue) {
    onFilterChange(props.idProp, props.idValue)
  } else {
    fetchData()
  }
})
</script>
<style scoped>
.catalog-model-line{max-width:1200px;margin:0 auto;padding:var(--cat-gap-xl,16px)} .page-count{font-size:var(--cat-text-md,15px);color:var(--cat-muted,#6b7280);margin:0 0 20px} .content{display:flex;gap:24px} .main{flex:1;min-width:0} .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px} .empty{text-align:center;padding:60px 20px;color:var(--cat-muted-light,#9ca3af);font-size:var(--cat-text-md,16px)} .pagination{display:flex;justify-content:center;align-items:center;gap:16px;margin-top:32px;padding:16px 0} .pagination button{padding:8px 20px;font-size:var(--cat-text-base,14px);background:var(--cat-surface,#fff);border:1px solid var(--cat-border,#d1d5db);border-radius:var(--cat-radius-md,6px);cursor:pointer;color:var(--cat-text,#1f2937)} .pagination button:disabled{opacity:.4;cursor:default} .pagination button:not(:disabled):hover{border-color:var(--cat-primary,#2563eb);color:var(--cat-primary,#2563eb)} .pagination span{font-size:var(--cat-text-base,14px);color:var(--cat-muted,#6b7280)} @media(max-width:768px){.content{flex-direction:column}.grid{grid-template-columns:1fr}}
</style>
