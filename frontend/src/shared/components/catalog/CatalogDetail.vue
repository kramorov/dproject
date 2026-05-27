<!-- shared/components/catalog/CatalogDetail.vue -->
<template>
  <div class="catalog-detail">
    <button class="back-btn" @click="$emit('close')">← {{ labels.backLabel || 'Назад к каталогу' }}</button>
    <ProductDetail v-if="product" :product="product" :price="price" :breadcrumbs="breadcrumbs" />
    <Spinner v-else-if="loading" />
    <div class="error" v-else>{{ labels.errorLabel || 'Товар не найден' }}</div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import ProductDetail from '@/shared/components/ProductDetail.vue'
import Spinner from '@/shared/components/Spinner.vue'
const props = defineProps({ api:{type:Object,required:true}, labels:{type:Object,default:()=>({})}, id:{type:[Number,String],default:null} })
const emit = defineEmits(['close','navigate'])
const product = ref(null); const price = ref(null); const loading = ref(true)
const breadcrumbs = computed(() => [
  { name:'Каталог', url:'#' },
  { name:props.labels.breadcrumbName||'Каталог', url:'#' },
  { name:product.value?.name||product.value?.code||'...' },
])
async function fetchDetail(){ if(!props.id) return; loading.value=true; try{ const r=await props.api.getDetail(props.id); const data=r.data||{}; product.value={...data,image_alt:data.name||data.code||''}; price.value=data.price||null } catch(e){ product.value=null } loading.value=false }
onMounted(fetchDetail); watch(()=>props.id,fetchDetail)
</script>
<style scoped>
.catalog-detail{max-width:1200px;margin:0 auto;padding:var(--cat-gap-xl,16px)} .back-btn{padding:8px 16px;font-size:var(--cat-text-base,14px);background:var(--cat-surface,#fff);border:1px solid var(--cat-border,#d1d5db);border-radius:var(--cat-radius-md,6px);cursor:pointer;margin-bottom:16px;color:var(--cat-text,#1f2937)} .back-btn:hover{border-color:var(--cat-primary,#2563eb);color:var(--cat-primary,#2563eb)} .error{text-align:center;padding:60px 20px;color:var(--cat-muted-light,#9ca3af);font-size:var(--cat-text-lg,16px)}
</style>