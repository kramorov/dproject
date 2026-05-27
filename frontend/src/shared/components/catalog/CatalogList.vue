<!-- shared/components/catalog/CatalogList.vue -->
<template>
  <div class="catalog-list">
    <h1 v-if="labels.title" class="page-title">{{ labels.title }}</h1>
    <div class="search-bar" v-if="withSearch"><input v-model="search" :placeholder="labels.searchPlaceholder||'Поиск...'" @input="onSearchInput" /></div>
    <div class="content">
      <FilterSidebar v-if="filtersLoaded" :filters="filterData" @change="onFilterChange" @reset="resetFilters" />
      <main class="main">
        <div class="results-info" v-if="total>=0">{{ labels.resultsLabel||'Найдено:' }} {{ total }}</div>
        <div class="grid" v-if="items.length"><ProductCard v-for="item in items" :key="item.id" :item="item" :price="item.price||null" @select="id=>$emit('select',id)" /></div>
        <div class="empty" v-else-if="!loading">{{ labels.emptyLabel||'Ничего не найдено' }}</div>
        <div class="pagination" v-if="total>limit"><button :disabled="offset===0" @click="goPage(offset-limit)">← Назад</button><span>{{ offset+1 }}–{{ Math.min(offset+limit,total) }} из {{ total }}</span><button :disabled="offset+limit>=total" @click="goPage(offset+limit)">Вперёд →</button></div>
      </main>
    </div>
  </div>
</template>
<script setup>
import { onMounted } from 'vue'
import FilterSidebar from '@/shared/components/FilterSidebar.vue'
import ProductCard from '@/shared/components/ProductCard.vue'
import { useCatalog } from '@/shared/composables/useCatalog.js'
const props = defineProps({ api:{type:Object,required:true}, labels:{type:Object,default:()=>({})}, withSearch:{type:Boolean,default:true}, fixedParams:{type:[Object,Function],default:null} })
defineEmits(['select'])
const { items,total,loading,limit,offset, filterData,filtersLoaded,search, loadFilters,fetchData, onFilterChange,resetFilters, onSearchInput,goPage } = useCatalog(props.api,{ withSearch:props.withSearch, fixedParams:props.fixedParams })
onMounted(async()=>{ await loadFilters(); fetchData() })
</script>
<style scoped>
.catalog-list{max-width:1440px;margin:0 auto} .page-title{font-size:var(--cat-text-2xl,24px);font-weight:700;margin:0 0 16px;color:var(--cat-text,#1f2937)} .search-bar{margin-bottom:20px} .search-bar input{width:100%;padding:12px 16px;font-size:var(--cat-text-lg,16px);border:1px solid var(--cat-border,#d1d5db);border-radius:var(--cat-radius-lg,8px);background:var(--cat-surface,#fff);outline:none;color:var(--cat-text,#1f2937)} .search-bar input:focus{border-color:var(--cat-primary,#2563eb);box-shadow:0 0 0 3px rgba(37,99,235,.1)} .content{display:flex;gap:24px} .main{flex:1;min-width:0} .results-info{font-size:var(--cat-text-base,14px);color:var(--cat-muted,#6b7280);margin-bottom:16px} .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px} .empty{text-align:center;padding:60px 20px;color:var(--cat-muted-light,#9ca3af);font-size:var(--cat-text-lg,16px)} .pagination{display:flex;justify-content:center;align-items:center;gap:16px;margin-top:32px;padding:16px 0} .pagination button{padding:8px 20px;font-size:var(--cat-text-base,14px);background:var(--cat-surface,#fff);border:1px solid var(--cat-border,#d1d5db);border-radius:var(--cat-radius-md,6px);cursor:pointer;color:var(--cat-text,#1f2937)} .pagination button:disabled{opacity:.4;cursor:default} .pagination button:not(:disabled):hover{border-color:var(--cat-primary,#2563eb);color:var(--cat-primary,#2563eb)} .pagination span{font-size:var(--cat-text-base,14px);color:var(--cat-muted,#6b7280)} @media(max-width:1100px){.grid{grid-template-columns:repeat(2,1fr)}} @media(max-width:768px){.content{flex-direction:column}.grid{grid-template-columns:1fr}}
</style>
