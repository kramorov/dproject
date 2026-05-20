<template>
  <div class="app">
    <h1>💰 Цены</h1>
    <div class="tabs">
      <button :class="{act:tab==='catalog'}" @click="tab='catalog'">Каталог цен</button>
      <button :class="{act:tab==='docs'}" @click="tab='docs'">Документы</button>
    </div>

    <!-- КАТАЛОГ ЦЕН -->
    <div v-if="tab==='catalog'">
      <div class="fl">
        <input v-model="pSearch" placeholder="Поиск..." @input="loadPrices" class="fi" />
        <select v-model="pVariety" @change="loadPrices" class="fi"><option value="">Вид цены</option>
          <option v-for="v in opts.varieties" :key="v.id" :value="v.id">{{ v.name }}</option></select>
        <select v-model="pCurrency" @change="loadPrices" class="fi"><option value="">Валюта</option>
          <option v-for="c in opts.currencies" :key="c.id" :value="c.id">{{ c.code }}</option></select>
        <input v-model="pDateFrom" type="date" @change="loadPrices" class="fi" />
        <input v-model="pDateTo" type="date" @change="loadPrices" class="fi" />
        <label class="cb"><input type="checkbox" v-model="pCurrent" @change="loadPrices"/> Актуальные</label>
      </div>
      <div v-if="loading" class="st">Загрузка...</div>
      <table v-else class="tb">
        <thead><tr><th>Название</th><th>Код</th><th>Вид</th><th>Валюта</th><th>Цена</th><th>Дата</th><th>Акт.</th></tr></thead>
        <tbody>
          <tr v-for="p in prices" :key="p.id">
            <td>{{ p.name||'—' }}</td><td>{{ p.code||'—' }}</td>
            <td>{{ p.price_variety?.name||'—' }}</td><td>{{ p.currency?.symbol }} {{ p.currency?.name }}</td>
            <td class="pr">{{ p.price }}</td><td>{{ p.price_date?.slice(0,10)||'—' }}</td>
            <td>{{ p.is_current?'✓':'' }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="prices.length===0" class="st">Ничего не найдено</div>
    </div>

    <!-- ДОКУМЕНТЫ -->
    <div v-if="tab==='docs'">
      <div class="fl">
        <input v-model="dSearch" placeholder="Поиск..." @input="loadDocs" class="fi" />
        <input v-model="dDateFrom" type="date" @change="loadDocs" class="fi" />
        <input v-model="dDateTo" type="date" @change="loadDocs" class="fi" />
        <button class="btn" @click="showCreate=true">+ Документ</button>
      </div>

      <!-- Создание -->
      <div v-if="showCreate" class="card">
        <h4>Новый документ</h4>
        <input v-model="newDoc.name" placeholder="Название" class="fi" />
        <select v-model="newDoc.ct" class="fi"><option :value="null">Тип товаров</option>
          <option v-for="c in contentTypes" :key="c.id" :value="c.id">{{ c.name }}</option></select>
        <input v-model="newDoc.date" type="date" class="fi" />
        <button class="btn" @click="doCreate">Создать</button>
        <button class="btn-c" @click="showCreate=false">Отмена</button>
        <div v-if="err" class="er">{{ err }}</div>
      </div>

      <div v-if="loading" class="st">Загрузка...</div>
      <table v-else class="tb">
        <thead><tr><th>Название</th><th>Тип</th><th>Дата</th><th>Позиций</th><th>Статус</th><th></th></tr></thead>
        <tbody>
          <tr v-for="d in docs" :key="d.id">
            <td class="lnk" @click="openDoc(d.id)">{{ d.name }}</td>
            <td>{{ d.content_type_name||'—' }}</td>
            <td>{{ d.document_date?.slice(0,10)||'—' }}</td>
            <td>{{ d.items_count }}</td>
            <td>{{ d.is_applied?'✓ Применён':'✎ Черновик' }}</td>
            <td>
              <button v-if="!d.is_applied" class="btn-s" @click="doApply(d.id)">Применить</button>
              <button class="btn-d" @click="doDeleteDoc(d.id)">✕</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import priceApi from './api'

const tab = ref('catalog')
const loading = ref(false), err = ref(null)

// Каталог
const prices = ref([]), pSearch=ref(''), pVariety=ref(''), pCurrency=ref(''), pDateFrom=ref(''), pDateTo=ref(''), pCurrent=ref(false)
const opts = ref({varieties:[], currencies:[]})

// Документы
const docs = ref([]), dSearch=ref(''), dDateFrom=ref(''), dDateTo=ref(''), showCreate=ref(false)
const newDoc = ref({name:'', ct:null, date:''})
const contentTypes = ref([])

onMounted(async ()=>{
  try {
    const {data} = await priceApi.filterOptions()
    opts.value.varieties = data.price_variety_id || []
    opts.value.currencies = data.currency_id || []
    // загружаем ContentTypes для создания документа
    const api = (await import('@/shared/api')).default
    const ctRes = await api.get('/core/', {params:{model:'contenttypes.ContentType', app_label__in:'pneumatic_fittings,electric_actuators,pneumatic_actuators,gearbox'}})
    contentTypes.value = ctRes.data.data || []
  } catch {}
  loadPrices(); loadDocs()
})

async function loadPrices(){
  loading.value=true
  try {
    const p={}
    if(pSearch.value)p.search=pSearch.value
    if(pVariety.value)p.price_variety_id=pVariety.value
    if(pCurrency.value)p.currency_id=pCurrency.value
    if(pDateFrom.value)p.date_from=pDateFrom.value
    if(pDateTo.value)p.date_to=pDateTo.value
    if(pCurrent.value)p.is_current='true'
    const {data}=await priceApi.listPrices(p)
    prices.value=data.data||[]
  }catch(e){err.value=e.displayMessage}finally{loading.value=false}
}

async function loadDocs(){
  loading.value=true
  try {
    const p={}
    if(dSearch.value)p.search=dSearch.value
    if(dDateFrom.value)p.date_from=dDateFrom.value
    if(dDateTo.value)p.date_to=dDateTo.value
    const {data}=await priceApi.listDocuments(p)
    docs.value=data.data||[]
  }catch(e){err.value=e.displayMessage}finally{loading.value=false}
}

async function doCreate(){
  if(!newDoc.value.name||!newDoc.value.ct)return
  try{await priceApi.createDocument({name:newDoc.value.name,item_content_type_id:newDoc.value.ct,document_date:newDoc.value.date||undefined}); showCreate.value=false; loadDocs()}
  catch(e){err.value=e.displayMessage}
}
async function doDeleteDoc(id){if(!confirm('Удалить?'))return; try{await priceApi.deleteDocument(id);loadDocs()}catch(e){err.value=e.displayMessage}}
async function doApply(id){try{await priceApi.applyDocument(id);loadDocs()}catch(e){err.value=e.displayMessage}}
function openDoc(id){/* позже — редактор документа */}
</script>

<style scoped>
.app{max-width:1300px;margin:0 auto;padding:20px;font-family:-apple-system,BlinkMacSystemFont,sans-serif}
h1{margin:0 0 12px;font-size:24px}
.tabs{display:flex;gap:4px;margin-bottom:16px}
.tabs button{padding:6px 16px;border:1px solid #d1d5db;border-radius:4px;background:#fff;cursor:pointer;font-size:14px}
.tabs button.act{background:#2563eb;color:#fff;border-color:#2563eb}
.fl{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;align-items:center}
.fi{padding:5px 8px;border:1px solid #d1d5db;border-radius:5px;font-size:13px}
.cb{font-size:13px;display:flex;align-items:center;gap:4px}
.tb{width:100%;border-collapse:collapse;font-size:13px}
.tb th{text-align:left;padding:6px 10px;background:#f9fafb;border-bottom:2px solid #e5e7eb;color:#6b7280;font-weight:500}
.tb td{padding:6px 10px;border-bottom:1px solid #f3f4f6}
.pr{text-align:right;font-weight:500}
.lnk{cursor:pointer;color:#2563eb}
.st{text-align:center;padding:40px;color:#6b7280}
.er{color:#dc2626;font-size:12px;margin-top:4px}
.card{margin-bottom:12px;padding:12px;border:1px solid #e5e7eb;border-radius:6px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.card h4{margin:0;font-size:14px}
.btn,.btn-s,.btn-d,.btn-c{padding:4px 12px;border:none;border-radius:4px;font-size:12px;cursor:pointer}
.btn{background:#2563eb;color:#fff}
.btn-s{background:#059669;color:#fff}
.btn-d{background:#dc2626;color:#fff}
.btn-c{background:#e5e7eb;color:#374151}
</style>
