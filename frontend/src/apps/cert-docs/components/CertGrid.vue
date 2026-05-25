<template>
  <div class="cert-grid">
    <div class="filters">
      <input v-model="search" placeholder="Поиск..." class="fi" @input="onFilter" />
      <select v-model="selVariety" class="fs" @change="onFilter">
        <option :value="null">Все типы</option>
        <option v-for="v in varieties" :key="v.id" :value="v.id">{{ v.name || v.code }}</option>
      </select>
      <select v-model="selBrand" class="fs" @change="onFilter">
        <option :value="null">Все бренды</option>
        <option v-for="b in brands" :key="b.id" :value="b.id">{{ b.name }}</option>
      </select>
      <select v-model="selEqType" class="fs" @change="onFilter">
        <option :value="null">Тип оборудования</option>
        <option v-for="e in equipmentTypes" :key="e.id" :value="e.id">{{ e.name }}</option>
      </select>
    </div>

    <div v-if="loading" class="status">Загрузка...</div>
    <div v-else-if="error" class="status error">{{ error }}</div>

    <table v-else class="tbl">
      <thead><tr>
        <th>Название / Код</th><th>Тип</th><th>Бренд</th><th>Срок</th><th>Файл</th>
      </tr></thead>
      <tbody>
        <tr v-for="item in items" :key="item.id" class="row" :class="{ina:!item.is_active}" @click="$emit('select',item)">
          <td><div class="nm">{{ item.name||'—' }}</div><div class="cd" v-if="item.code">{{ item.code }}</div></td>
          <td><span v-if="item.cert_variety" class="badge">{{ typeof item.cert_variety==='object'?item.cert_variety.name:item.cert_variety }}</span></td>
          <td>{{ typeof item.brand==='object'?item.brand?.name:item.brand||'—' }}</td>
          <td>
            <span v-if="item.valid_until" :class="['db',new Date(item.valid_until)<new Date()?'ex':'ok']">{{ fmt(item.valid_until) }}</span>
            <span v-else>—</span>
          </td>
          <td class="cf">
            <span v-if="item.has_media" class="fl" @click.stop="$emit('view-media',item.media_item?.id||item.media_item)">📎</span>
            <span v-else-if="item.public_url"><a :href="item.public_url" target="_blank" @click.stop>🔗</a></span>
            <span v-else class="nf">—</span>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="items.length===0&&!loading" class="status">Ничего не найдено</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import certApi from '../api'

const props = defineProps({ opts:{type:Object,default:()=>({varieties:[],brands:[],equipmentTypes:[]})} })
defineEmits(['select','view-media'])
defineExpose({fetchData})

const items=ref([]), search=ref(''), selVariety=ref(null), selBrand=ref(null), selEqType=ref(null)
const loading=ref(false), error=ref(null)
const varieties=ref([]), brands=ref([]), equipmentTypes=ref([])

function fmt(iso){return iso?new Date(iso).toLocaleDateString('ru-RU'):''}
let t=null
function onFilter(){clearTimeout(t);t=setTimeout(fetchData,200)}

async function fetchData(){
  loading.value=true;error.value=null
  try{
    const p={}
    if(selVariety.value)p.cert_variety_id=selVariety.value
    if(selBrand.value)p.brand_id=selBrand.value
    if(selEqType.value)p.equipment_types=selEqType.value
    if(search.value)p.search=search.value
    const {data}=await certApi.list(p)
    items.value=Array.isArray(data.data)?data.data:[]
  }catch(e){error.value=e.displayMessage||'Ошибка'}finally{loading.value=false}
}

async function loadFilterOptions() {
  try {
    const { data } = await certApi.filterOptions()
    varieties.value = data.cert_variety_id || []
    brands.value = data.brand_id || []
    equipmentTypes.value = data.equipment_type_id || []
  } catch {}
}

onMounted(() => { loadFilterOptions(); fetchData() })
</script>

<style scoped>
.cert-grid{width:100%}
.filters{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.fi{flex:1;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:13px;min-width:140px}
.fs{padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:13px;min-width:150px}
.tbl{width:100%;border-collapse:collapse;font-size:13px}
.tbl th{text-align:left;padding:8px 10px;background:#f9fafb;border-bottom:2px solid #e5e7eb;color:#6b7280;font-weight:500}
.tbl td{padding:8px 10px;border-bottom:1px solid #f3f4f6}
.row{cursor:pointer;transition:background .1s}
.row:hover{background:#f0f9ff}
.row.ina{opacity:.5}
.nm{font-weight:500;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;max-height:2.6em}
.cd{font-size:11px;color:#6b7280}
.badge{display:inline-block;padding:1px 8px;background:#e5e7eb;border-radius:10px;font-size:12px}
.db{display:inline-block;padding:1px 8px;border-radius:10px;font-size:12px}
.db.ok{background:#d1fae5;color:#065f46}
.db.ex{background:#fee2e2;color:#991b1b}
.cf .fl{cursor:pointer;font-size:16px}
.cf a{text-decoration:none;font-size:16px}
.nf{color:#d1d5db}
.status{text-align:center;padding:40px;color:#6b7280}
.status.error{color:#dc2626}
</style>
