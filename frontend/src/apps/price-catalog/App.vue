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
      <div v-if="catalogLoading" class="st">Загрузка...</div>
      <table v-else class="tb">
        <thead><tr><th>Название</th><th>Код</th><th>Вид</th><th>Валюта</th><th>Цена</th><th>Дата</th><th>Акт.</th></tr></thead>
        <tbody>
          <tr v-for="p in prices" :key="p.id">
            <td>{{ p.name||'—' }}</td><td>{{ p.code||'—' }}</td>
            <td>{{ p.price_variety_name||p.price_variety?.name||'—' }}</td><td>{{ p.currency_symbol||p.currency?.symbol||'' }} {{ p.currency_name||p.currency?.name||'' }}</td>
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
        <select v-model="newDoc.ct" class="fi"><option :value="null">Тип оборудования</option>
          <option v-for="e in contentTypes" :key="e.id" :value="e.content_type_id">{{ e.name }}</option></select>
        <input v-model="newDoc.date" type="date" class="fi" />
        <button class="btn" @click="doCreate">Создать</button>
        <button class="btn-c" @click="showCreate=false">Отмена</button>
        <div v-if="err" class="er">{{ err }}</div>
      </div>

      <div v-if="docsLoading" class="st">Загрузка...</div>
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

    <!-- ═══ РЕДАКТОР ДОКУМЕНТА ═══ -->
    <div v-if="tab==='docs' && selectedDoc" class="doc-edit">
      <button class="btn-c" @click="selectedDoc=null">← К списку</button>
      <div class="doc-header">
        <h3>{{ docData?.name }}</h3>
        <div class="doc-meta">
          <span>Тип: {{ docData?.item_content_type_name||'—' }}</span>
          <span>Дата: {{ docData?.document_date?.slice(0,10)||'—' }}</span>
          <span>{{ docData?.is_applied?'✓ Применён':'✎ Черновик' }}</span>
        </div>
        <div v-if="!docData?.is_applied" class="doc-actions">
          <button class="btn-s" @click="doApply(docData.id); selectedDoc=null">Применить</button>
          <button class="btn-d" @click="doDeleteDoc(docData.id); selectedDoc=null">Удалить</button>
        </div>
      </div>

      <div v-if="!docData?.is_applied" class="add-form">
        <h4>Добавить позицию</h4>
        <div class="add-row">
          <div class="search-wrap">
            <input v-model="prodSearch" placeholder="Код товара..." class="fi fi-lg"
              @input="onProdSearch" @focus="onProdSearch" />
            <div v-if="prodResults.length" class="search-drop">
              <div v-for="p in prodResults" :key="p.id" class="search-item" @click="pickProduct(p)">
                <b>{{ p.code||'—' }}</b> {{ p.name }}
              </div>
            </div>
          </div>
          <span v-if="pickedProduct" class="picked">{{ pickedProduct.code }} {{ pickedProduct.name }}</span>
          <select v-model="newItem.price_variety_id" class="fi"><option :value="null">Вид цены</option>
            <option v-for="v in opts.varieties" :key="v.id" :value="v.id">{{ v.name }}</option></select>
          <select v-model="newItem.currency_id" class="fi"><option :value="null">Валюта</option>
            <option v-for="c in opts.currencies" :key="c.id" :value="c.id">{{ c.code }}</option></select>
          <input v-model.number="newItem.price" type="number" step="0.01" placeholder="Цена" class="fi fi-sm" />
          <button class="btn" :disabled="!canAdd" @click="doAddItem">+ Добавить</button>
        </div>
        <div v-if="err" class="er">{{ err }}</div>
      </div>

      <table class="tb">
        <thead><tr><th>#</th><th>Код</th><th>Товар</th><th>Вид цены</th><th>Валюта</th><th>Цена</th><th></th></tr></thead>
        <tbody>
          <tr v-for="(item, i) in docData?.items||[]" :key="item.id">
            <td>{{ i+1 }}</td>
            <td>{{ getProductCode(item.object_id) }}</td>
            <td>{{ getProductName(item.object_id) }}</td>
            <td>{{ item.price_variety_name||'—' }}</td>
            <td>{{ item.currency_name||'—' }}</td>
            <td class="pr">{{ item.price }}</td>
            <td><button v-if="!docData?.is_applied" class="btn-d btn-sm" @click="doDeleteItem(item.id)">✕</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import priceApi from './api'

const tab = ref('catalog')
const catalogLoading = ref(false), docsLoading = ref(false), err = ref(null)

// Каталог
const prices = ref([]), pSearch=ref(''), pVariety=ref(''), pCurrency=ref(''), pDateFrom=ref(''), pDateTo=ref(''), pCurrent=ref(false)
const opts = ref({varieties:[], currencies:[]})

// Документы
const docs = ref([]), dSearch=ref(''), dDateFrom=ref(''), dDateTo=ref(''), showCreate=ref(false)
const newDoc = ref({name:'', ct:null, date:new Date().toISOString().slice(0,10)})
const contentTypes = ref([])

// Документ — редактор
const selectedDoc = ref(null), docData = ref(null)
const prodSearch = ref(''), prodResults = ref([]), pickedProduct = ref(null)
const newItem = ref({object_id:null, price_variety_id:null, currency_id:null, price:0})
const canAdd = computed(() => pickedProduct.value && newItem.value.price_variety_id && newItem.value.currency_id)

onMounted(async ()=>{
  try {
    const {data} = await priceApi.filterOptions()
    opts.value.varieties = data.price_variety_id || []
    opts.value.currencies = data.currency_id || []
    // загружаем EquipmentTypes с content_type для создания документа
    const api = (await import('@/shared/api')).default
    const etRes = await api.get('/core/', {params:{model:'core.EquipmentType', fmt:'compact'}})
    contentTypes.value = (etRes.data.data || []).filter(e => e.content_type_id)
  } catch {}
  loadPrices(); loadDocs()
})

async function loadPrices(){
  catalogLoading.value=true
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
  }catch(e){err.value=e.displayMessage}finally{catalogLoading.value=false}
}

async function loadDocs(){
  docsLoading.value=true
  try {
    const p={}
    if(dSearch.value)p.search=dSearch.value
    if(dDateFrom.value)p.date_from=dDateFrom.value
    if(dDateTo.value)p.date_to=dDateTo.value
    const {data}=await priceApi.listDocuments(p)
    docs.value=data.data||[]
  }catch(e){err.value=e.displayMessage}finally{docsLoading.value=false}
}

async function doCreate(){
  if(!newDoc.value.name||!newDoc.value.ct)return
  try{await priceApi.createDocument({name:newDoc.value.name,item_content_type_id:newDoc.value.ct,document_date:newDoc.value.date}); showCreate.value=false; loadDocs()}
  catch(e){err.value=e.displayMessage}
}
async function doDeleteDoc(id){if(!confirm('Удалить?'))return; try{await priceApi.deleteDocument(id);loadDocs()}catch(e){err.value=e.displayMessage}}
async function doApply(id){try{await priceApi.applyDocument(id);loadDocs()}catch(e){err.value=e.displayMessage}}

// ═══ Редактор документа ═══
async function openDoc(id){
  docsLoading.value=true; err.value=null
  try {
    const {data} = await priceApi.getDocument(id)
    docData.value = data; selectedDoc.value = id
  } catch(e) { err.value=e.displayMessage }
  finally { docsLoading.value=false }
}

let prodTimer = null
async function onProdSearch(){
  pickedProduct.value = null
  clearTimeout(prodTimer)
  const q = prodSearch.value.trim()
  if(!q || !docData.value?.content_type_app){ prodResults.value=[]; return }
  prodTimer = setTimeout(async ()=>{
    try {
      const modelName = `${docData.value.content_type_app}.${docData.value.content_type_model}`
      console.log('onProdSearch model:', modelName, 'search:', q)
      const api = (await import('@/shared/api')).default
      const r = await api.get('/core/', {params:{model:modelName, search:q, fmt:'compact', limit:15}})
      console.log('onProdSearch results:', r.data.data?.length, 'items, first:', r.data.data?.[0])
      prodResults.value = (r.data.data || []).filter(p => (p.code||'').toLowerCase().includes(q.toLowerCase()))
    } catch { prodResults.value=[] }
  }, 250)
}

function pickProduct(p){
  pickedProduct.value = p
  prodSearch.value = (p.code||'') + ' ' + (p.name||'')
  prodResults.value = []
}

function getProductCode(oid){ return pickedProduct.value?.id===oid ? pickedProduct.value.code : '#'+oid }
function getProductName(oid){ return pickedProduct.value?.id===oid ? pickedProduct.value.name : '#'+oid }

async function doAddItem(){
  if(!canAdd.value) return
  err.value=null
  try {
    await priceApi.addItem(docData.value.id, {
      object_id: pickedProduct.value.id,
      price_variety_id: newItem.value.price_variety_id,
      currency_id: newItem.value.currency_id,
      price: newItem.value.price,
    })
    newItem.value = {object_id:null, price_variety_id:null, currency_id:null, price:0}
    pickedProduct.value = null; prodSearch.value = ''; prodResults.value = []
    await openDoc(docData.value.id)
  } catch(e) { err.value=e.displayMessage }
}

async function doDeleteItem(itemId){
  if(!confirm('Удалить позицию?')) return
  try { await priceApi.deleteItem(docData.value.id, itemId); await openDoc(docData.value.id) }
  catch(e) { err.value=e.displayMessage }
}
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
.btn-sm{padding:2px 8px;font-size:11px}
.doc-edit{margin-top:4px}
.doc-header{padding:12px 16px;background:#f9fafb;border-radius:8px;margin:10px 0;border:1px solid #e5e7eb}
.doc-meta{display:flex;gap:16px;font-size:13px;color:#6b7280;flex-wrap:wrap}
.doc-actions{display:flex;gap:8px;margin-top:8px}
.add-form{padding:12px;background:#f0fdf4;border-radius:8px;margin-bottom:8px;border:1px solid #bbf7d0}
.add-row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.search-wrap{position:relative}
.search-drop{position:absolute;top:100%;left:0;right:0;max-height:180px;overflow-y:auto;background:#fff;border:1px solid #d1d5db;border-radius:0 0 5px 5px;z-index:10;box-shadow:0 4px 8px rgba(0,0,0,.1)}
.search-item{padding:6px 10px;font-size:13px;cursor:pointer;border-bottom:1px solid #f3f4f6}
.search-item:hover{background:#f0f9ff}
.picked{font-size:13px;color:#059669;font-weight:500;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
</style>