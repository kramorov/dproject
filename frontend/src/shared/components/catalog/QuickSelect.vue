<!-- shared/components/catalog/QuickSelect.vue -->
<!-- DEBUG: QuickSelect -->
<template>
  <div class="qs-page">
    <span class="debug-tag" v-if="debug">QuickSelect</span>
    <PageTitle :title="pageTitle" />
    <div class="chip-group" v-if="modelLines.length"><div class="chip-label">Серия</div><div class="chip-row"><button v-for="ml in modelLines" :key="ml.id" class="chip" :class="{active:selectedML===ml.id}" @click="selectSeries(ml.id)">{{ ml.name }}</button></div></div>
    <div v-if="filterGroups.length" class="filter-chips"><div v-for="group in filterGroups" :key="group.key" class="chip-group"><div class="chip-label">{{ group.label }}</div><div class="chip-row"><button v-for="opt in group.options" :key="opt.value||opt.id" class="chip" :class="{active:String(activeFilters[group.key])===String(opt.value??opt.id)}" @click="toggleFilter(group.key,opt.value??opt.id)">{{ opt.label||opt.name }}<span class="chip-count" v-if="opt.count!=null">({{ opt.count }})</span></button></div></div></div>
    <div v-if="product" class="product-area"><ProductDetail :product="product" :price="product.price" :breadcrumbs="detailBreadcrumbs" @navigate="$emit('navigate', $event)" /></div>
    <div class="empty" v-else-if="loaded">Модель не найдена — измените фильтры</div>
    <Spinner v-else-if="!loaded && modelLines.length" />
  </div>
</template>
<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { debug } from '@/shared/config'
import PageTitle from '@/shared/components/PageTitle.vue'
import ProductDetail from '@/shared/components/ProductDetail.vue'
import Spinner from '@/shared/components/Spinner.vue'
const props = defineProps({ api:{type:Object,required:true}, labels:{type:Object,default:()=>({})}, brandId:{type:[Number,String],default:null}, filterLabels:{type:Object,default:()=>({})}, autoSelectRules:{type:Object,default:()=>({})} })
defineEmits(['select','navigate'])
const modelLines=ref([]); const selectedML=ref(null); const filterGroups=ref([]); const activeFilters=reactive({}); const product=ref(null); const loaded=ref(false)
const pageTitle=computed(()=>props.labels.title||'Быстрый подбор')
const eqLabel = computed(() => props.labels.breadcrumbName || 'Каталог')
const breadcrumbs=computed(()=>[
  { name: 'Каталог' },
  { name: eqLabel.value },
  { name: 'Быстрый подбор' },
])
const detailBreadcrumbs=computed(()=>[
  { name: 'Каталог', to: '/' },
  { name: eqLabel.value },
  { name: 'Быстрый подбор' },
  { name: product.value?.model_line?.name||'' },
])
onMounted(async()=>{try{const params={limit:1000};if(props.brandId)params.brand_id=props.brandId;const r=await props.api.list(params);const items=r.data?.data||[];const mlMap={};for(const item of items){const ml=item.model_line;if(ml&&!mlMap[ml.id])mlMap[ml.id]=ml}modelLines.value=Object.values(mlMap).sort((a,b)=>a.name.localeCompare(b.name));if(modelLines.value.length){selectedML.value=modelLines.value[0].id;await initSeries()}loaded.value=true}catch(e){loaded.value=true}})
function selectSeries(id){if(selectedML.value===id)return;selectedML.value=id;for(const k of Object.keys(activeFilters))delete activeFilters[k];product.value=null;filterGroups.value=[];initSeries()}
async function initSeries(){if(!selectedML.value)return;loaded.value=false;try{const r=await props.api.getQuickSelect(selectedML.value,{});const data=r.data;const groups=[];const flabels=data.filter_labels||{};for(const[key,options]of Object.entries(data.filters||{})){if(!options||!options.length)continue;groups.push({key,label:flabels[key]||props.filterLabels[key]||key,options})}filterGroups.value=groups;    const defaults=data.defaults||{};for(const group of groups){const rule=defaults[group.key]||props.autoSelectRules[group.key];if(!rule)continue;const opts=group.options;if(!opts.length)continue;if(rule==='first'){activeFilters[group.key]=opts[0].value??opts[0].id}else if(rule==='max'){const sorted=[...opts].sort((a,b)=>(b.value||0)-(a.value||0));activeFilters[group.key]=sorted[0].value??sorted[0].id}else if(rule==='min'){const sorted=[...opts].sort((a,b)=>(a.value||0)-(b.value||0));activeFilters[group.key]=sorted[0].value??sorted[0].id}}await fetchProduct()}catch(e){}loaded.value=true}
async function fetchProduct(){if(!selectedML.value)return;try{const r=await props.api.getQuickSelect(selectedML.value,{...activeFilters});product.value=r.data?.items?.[0]||null}catch(e){}}
async function toggleFilter(key,value){if(String(activeFilters[key])===String(value)){delete activeFilters[key]}else{activeFilters[key]=value}for(const group of filterGroups.value){if(group.key===key)continue;const otherFilters={...activeFilters};delete otherFilters[group.key];const r=await props.api.getQuickSelect(selectedML.value,otherFilters);const opts=r.data?.filters?.[group.key]||[];if(!opts.length){delete activeFilters[group.key];continue}const curVal=activeFilters[group.key];if(curVal!==undefined&&curVal!==null){const valid=opts.some(o=>String(o.value??o.id)===String(curVal));if(!valid)activeFilters[group.key]=opts[0].value??opts[0].id}}await fetchProduct()}
</script>
<style scoped>
.qs-page{max-width:1200px;margin:0 auto;padding:var(--cat-gap-xl,16px)} .chip-group{margin-bottom:12px} .chip-label{font-weight:500;font-size:13px;margin-bottom:4px;color:var(--cat-muted-dark,#374151)} .chip-row{display:flex;flex-wrap:wrap;gap:4px} .chip{padding:4px 12px;font-size:12px;border:1px solid var(--cat-border,#d1d5db);border-radius:16px;background:var(--cat-surface,#fff);cursor:pointer;transition:all .12s;white-space:nowrap;color:var(--cat-text,#1f2937)} .chip:hover{border-color:var(--cat-primary,#2563eb);color:var(--cat-primary,#2563eb)} .chip.active{background:var(--cat-primary,#2563eb);color:#fff;border-color:var(--cat-primary,#2563eb)} .chip-count{font-size:10px;opacity:.7;margin-left:2px} .filter-chips{display:flex;flex-direction:column;gap:10px;margin-bottom:20px} .product-area{margin-top:20px} .empty{text-align:center;padding:60px 20px;color:var(--cat-muted-light,#9ca3af);font-size:var(--cat-text-md,16px)}
</style>
