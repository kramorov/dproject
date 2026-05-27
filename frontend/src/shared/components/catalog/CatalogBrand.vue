<!-- shared/components/catalog/CatalogBrand.vue -->
<template>
  <div class="catalog-brand">
    <Breadcrumbs :items="breadcrumbs" />
    <div class="brand-header"><h1 class="page-title">{{ brandName || labels.title || 'Бренд' }}</h1><p class="page-count" v-if="total">{{ labels.countLabel || 'Товаров:' }} {{ total }}</p></div>
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
import FilterSidebar from '@/shared/components/FilterSidebar.vue'
import ProductCard from '@/shared/components/ProductCard.vue'
import Spinner from '@/shared/components/Spinner.vue'
import { useCatalog } from '@/shared/composables/useCatalog.js'
const props = defineProps({ api:{type:Object,required:true}, labels:{type:Object,default:()=>({})}, idProp:{type:String,default:'brandId'}, idValue:{type:[Number,String],default:null}, showFilters:{type:Boolean,default:true} })
const emit = defineEmits(['select'])
const brandName = ref('')
const fixedParams = computed(() => props.idValue ? { [props.idProp]: props.idValue } : {})
const { items,total,loading,limit,offset, filterData,filtersLoaded, loadFilters,fetchData, onFilterChange,resetFilters,goPage } = useCatalog(props.api,{ fixedParams, withSearch:false, onData(items){ if(items.length&&!brandName.value) brandName.value=items[0]?.model_line?.brand?.name||items[0]?.model_line?.name||'' } })
const breadcrumbs = computed(() => [{ name:'Каталог', url:'#' }, { name:props.labels.breadcrumbName||props.labels.title||'Каталог', url:'#' }, { name:brandName.value||'Бренд' }])
watch(()=>props.idValue,()=>{ offset.value=0; fetchData() })
onMounted(async()=>{ await loadFilters(); if(props.idValue) fetchData() })
</script>
<style scoped>
.catalog-brand{max-width:1200px;margin:0 auto;padding:var(--cat-gap-xl,16px)} .brand-header{margin-bottom:20px} .page-title{font-size:var(--cat-text-3xl,28px);font-weight:700;margin:8px 0 4px;color:var(--cat-text,#1f2937)} .page-count{font-size:var(--cat-text-md,15px);color:var(--cat-muted,#6b7280);margin:0} .content{display:flex;gap:24px} .main{flex:1;min-width:0} .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px} .empty{text-align:center;padding:60px 20px;color:var(--cat-muted-light,#9ca3af);font-size:var(--cat-text-md,16px)} .pagination{display:flex;justify-content:center;align-items:center;gap:16px;margin-top:32px;padding:16px 0} .pagination button{padding:8px 20px;font-size:var(--cat-text-base,14px);background:var(--cat-surface,#fff);border:1px solid var(--cat-border,#d1d5db);border-radius:var(--cat-radius-md,6px);cursor:pointer;color:var(--cat-text,#1f2937)} .pagination button:disabled{opacity:.4;cursor:default} .pagination button:not(:disabled):hover{border-color:var(--cat-primary,#2563eb);color:var(--cat-primary,#2563eb)} .pagination span{font-size:var(--cat-text-base,14px);color:var(--cat-muted,#6b7280)} @media(max-width:768px){.content{flex-direction:column}.grid{grid-template-columns:1fr}}
</style>
