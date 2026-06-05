<template>
  <div class="doc-edit">
    <button class="btn-c" @click="$emit('close')">← К списку</button>

    <div class="doc-card">
      <!-- Шапка -->
      <div class="doc-card-header">
        <div class="doc-header-row">
          <div class="doc-field">
            <label>Название</label>
            <input v-if="isDraft" v-model="edit.name" class="fi fi-w" @blur="saveHeader" />
            <span v-else class="doc-val">{{ doc?.name }}</span>
          </div>
          <span :class="badge(doc?.status)">{{ doc?.status_label||'—' }}</span>
        </div>

        <div class="doc-fields">
          <div class="doc-field">
            <label>Тип цены</label>
            <select v-if="isDraft" v-model="edit.priceVariety" class="fi" @change="saveHeader">
              <option :value="null">—</option>
              <option v-for="v in opts.varieties" :key="v.id" :value="v.id">{{ v.name }}</option>
            </select>
            <span v-else class="doc-val">{{ doc?.default_price_variety_name||'—' }}</span>
          </div>

          <div class="doc-field">
            <label>Валюта</label>
            <select v-if="isDraft" v-model="edit.currency" class="fi" @change="saveHeader">
              <option :value="null">—</option>
              <option v-for="c in opts.currencies" :key="c.id" :value="c.id">{{ c.code }}</option>
            </select>
            <span v-else class="doc-val">{{ doc?.default_currency_name||doc?.default_currency_symbol||'—' }}</span>
          </div>

          <div class="doc-field">
            <label>Дата</label>
            <input v-if="isDraft" v-model="edit.date" type="date" class="fi" @change="saveHeader" />
            <span v-else class="doc-val">{{ doc?.document_date?.slice(0,10)||'—' }}</span>
          </div>
        </div>
      </div>

      <!-- Таблица позиций -->
      <div class="doc-table-wrap">
        <table v-if="doc?.items?.length" class="tb">
          <thead><tr><th>#</th><th>Код</th><th>Товар</th><th>Вид цены</th><th>Валюта</th><th>Цена</th><th></th></tr></thead>
          <tbody>
            <tr v-for="(item, i) in doc.items" :key="item.id">
              <td>{{ i+1 }}</td>
              <td class="code-cell">{{ item.product_code||'—' }}</td>
              <td>{{ item.product_name||'—' }}</td>
              <td>{{ item.price_variety_name||doc.default_price_variety_name||'—' }}</td>
              <td>{{ item.currency_name||doc.default_currency_name||'—' }}</td>
                            <td class="pr" @click="startEditPrice(item)">
                <input v-if="editingId===item.id" v-model.number="editPrice" type="number" step="0.01"
                  class="fi-price" @blur="savePrice(item)" @keyup.enter="savePrice(item)"
                  @keyup.escape="editingId=null" @click.stop ref="priceInput" />
                <span v-else class="price-val">{{ item.price }}</span>
              </td>
              <td class="act-cell">
                <button v-if="item.sku_id" class="btn-e" title="Edit SKU" @click.stop="openSkuEdit(item)">📝</button>
                <button v-if="isDraft" class="btn-d btn-sm" @click="doDeleteItem(item.id)">✕</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="st">Нет позиций</div>

        <!-- Форма добавления (только draft) -->
        <div v-if="isDraft" class="add-form">
          <div class="add-row">
            <div class="search-wrap">
              <input v-model="prodSearch" placeholder="Код товара..." class="fi fi-lg"
                @input="onProdSearch" @focus="onProdSearch" />
              <div v-if="prodResults.length" class="search-drop">
                <div v-for="p in prodResults" :key="p.id" class="search-item" @click="pickProduct(p)">
                  {{ p.code }} — {{ p.name?.substring(0,60) }}
                </div>
              </div>
            </div>
            <span v-if="pickedProduct" class="picked">{{ pickedProduct.code }} {{ pickedProduct.name }}</span>
            <input v-model.number="newPrice" type="number" step="0.01" class="fi fi-n" placeholder="Цена" />
            <button class="btn" :disabled="!canAdd" @click="doAddItem">+ Добавить</button>
            <button class="btn-o" @click="showNewSku=true">+ Создать и добавить</button>
            <button class="btn-o" @click="openFillByFilter">Заполнить по фильтрам</button>
            <div v-if="err" class="er">{{ err }}</div>
          </div>
        </div>
      </div>

      <!-- Действия -->
      <div class="doc-actions">
        <button v-if="doc?.status==='draft'" class="btn-o" @click="doSetStatus('on_approval')">На согласование</button>
        <button v-if="doc?.status==='draft'||doc?.status==='on_approval'" class="btn-s" @click="doApply">Провести</button>
        <button v-if="doc?.status==='posted'" class="btn-w" @click="doUnapply">Отмена проведения</button>
        <button v-if="doc?.status!=='posted'" class="btn-d" @click="doDelete">Удалить</button>
        <span class="doc-actions-sep"></span>
        <button class="btn-c" @click="doExportExcel">📥 Экспорт Excel</button>
        <button v-if="isDraft" class="btn-c" @click="triggerImport">📤 Импорт Excel</button>
        <input ref="fileInput" type="file" accept=".xlsx,.xls" style="display:none" @change="doImportExcel" />
      </div>
    </div>
  </div>

    <!-- Заполнить по фильтрам -->
    <div v-if="showFillModal" class="sku-edit-bg">
      <div class="sku-edit-modal" style="width:700px">
        <h4>Подбор номенклатуры</h4>
        <div class="fl">
          <input v-model="fillCode" placeholder="Код (подстрока)..." class="fi" style="width:160px" @keyup.enter="doFillSearch" />
          <select v-model="fillEqType" class="fi"><option value="">Тип оборудования</option>
            <option value="null">— Не указано</option>
            <option v-for="t in opts.equipmentTypes" :key="t.id" :value="t.id">{{ t.name }}</option></select>
          <select v-model="fillBrand" class="fi"><option value="">Бренд</option>
            <option value="null">— Не указано</option>
            <option v-for="b in opts.brands" :key="b.id" :value="b.id">{{ b.name }}</option></select>
          <button @click="doFillSearch" class="btn-sm">Отобрать</button>
        </div>
        <div class="act-bar">
          <button @click="toggleFillAll" class="btn-sm">{{ fillAllSelected ? 'Снять выделение' : 'Выделить всё' }}</button>
          <span class="sel-info">Выделено: {{ fillSelected.size }} / {{ fillItems.length }}</span>
        </div>
        <div v-if="fillLoading" class="st">Загрузка...</div>
        <div v-else-if="fillItems.length" class="fill-list">
          <div v-for="s in fillItems" :key="s.id" class="fill-row" :class="{sel:fillSelected.has(s.id)}">
            <input type="checkbox" :checked="fillSelected.has(s.id)" @change="toggleFillOne(s.id)" />
            <span class="code">{{ s.code }}</span>
            <span class="name">{{ s.name?.substring(0,80)||'—' }}</span>
            <span class="meta">{{ s.equipment_type_name||'' }} {{ s.brand_name||'' }}</span>
          </div>
        </div>
        <div v-if="fillItems.length===0 && !fillLoading" class="st">Ничего не найдено</div>
        <div class="sku-edit-btns">
          <button @click="showFillModal=false" class="btn-c">Отмена</button>
          <button @click="doFillAdd" class="btn-s" :disabled="fillSelected.size===0||fillAdding">
            {{ fillAdding ? 'Добавление...' : 'Перенести в документ ('+fillSelected.size+')' }}
          </button>
        </div>
        <div v-if="fillErr" class="er">{{ fillErr }}</div>
      </div>
    </div>
    <!-- Создание новой номенклатуры -->
    <div v-if="showNewSku" class="sku-edit-bg">
      <div class="sku-edit-modal">
        <h4>Создать номенклатуру</h4>
        <div class="sku-edit-body">
          <label>Код * <input v-model="newSku.code" class="inp" /></label>
          <label>Название <input v-model="newSku.name" class="inp" /></label>
          <label>Описание <textarea v-model="newSku.description" class="inp" rows="3"></textarea></label>
          <div class="sku-edit-row">
            <label>Тип <select v-model="newSku.equipment_type_id" class="inp"><option :value="null">--</option>
              <option v-for="t in opts.equipmentTypes" :key="t.id" :value="t.id">{{ t.name }}</option></select></label>
            <label>Бренд <select v-model="newSku.brand_id" class="inp"><option :value="null">--</option>
              <option v-for="b in opts.brands" :key="b.id" :value="b.id">{{ b.name }}</option></select></label>
          </div>
        </div>
        <div class="sku-edit-btns">
          <button @click="showNewSku=false" class="btn-c">Отмена</button>
          <button @click="createAndAddSku" class="btn-s" :disabled="newSkuSaving||!newSku.code">{{ newSkuSaving?'...':'Создать и добавить' }}</button>
        </div>
        <div v-if="newSkuErr" class="er">{{ newSkuErr }}</div>
      </div>
    </div>
    <!-- Редактирование SKU -->
    <div v-if="skuEditItem" class="sku-edit-bg">
      <div class="sku-edit-modal">
        <h4>SKU: {{ skuEditItem.product_code }}</h4>
        <div class="sku-edit-body">
          <label>Код <input v-model="skuForm.code" class="inp" /></label>
          <label>Название <input v-model="skuForm.name" class="inp" /></label>
          <label>Описание <textarea v-model="skuForm.description" class="inp" rows="3"></textarea></label>
          <div class="sku-edit-row">
            <label>Тип <select v-model="skuForm.equipment_type_id" class="inp"><option :value="null">--</option>
              <option v-for="t in opts.equipmentTypes" :key="t.id" :value="t.id">{{ t.name }}</option></select></label>
            <label>Бренд <select v-model="skuForm.brand_id" class="inp"><option :value="null">--</option>
              <option v-for="b in opts.brands" :key="b.id" :value="b.id">{{ b.name }}</option></select></label>
          </div>
          <label><input type="checkbox" v-model="skuForm.is_active" /> Активно</label>
        </div>
        <div class="sku-edit-btns">
          <button @click="skuEditItem=null" class="btn-c">Отмена</button>
          <button @click="saveSkuEdit" class="btn" :disabled="skuEditSaving">{{ skuEditSaving?'...':'Сохранить' }}</button>
        </div>
        <div v-if="skuEditErr" class="er">{{ skuEditErr }}</div>
      </div>
    </div>
</template>

<script setup>
import { ref, reactive, computed, inject, watch, onBeforeUnmount } from 'vue'
import priceApi from '../api'

const props = defineProps({ docId: { type: Number, required: true } })
const emit = defineEmits(['close', 'changed'])

const opts = inject('opts')

const doc = ref(null)
const err = ref(null)
const isDraft = computed(() => doc.value?.status === 'draft')

const edit = reactive({ name: '', priceVariety: null, currency: null, date: '' })

// Поиск товара через SKU
const prodSearch = ref(''), prodResults = ref([]), pickedProduct = ref(null)
const newPrice = ref(0)
const editingId = ref(null), editPrice = ref(0)
const priceInput = ref(null)

// SKU edit
const skuEditItem = ref(null)
const skuForm = reactive({ code: '', name: '', description: '', equipment_type_id: null, brand_id: null, is_active: true })
const skuEditSaving = ref(false)
const skuEditErr = ref('')

const fileInput = ref(null)

// Create new SKU
const showNewSku = ref(false)
const newSku = reactive({ code: '', name: '', description: '', equipment_type_id: null, brand_id: null })
const newSkuSaving = ref(false)
const newSkuErr = ref('')

// Fill by filter
const showFillModal = ref(false)
const fillCode = ref(''), fillEqType = ref(''), fillBrand = ref('')
const fillItems = ref([]), fillLoading = ref(false), fillAdding = ref(false)
const fillSelected = ref(new Set()), fillErr = ref('')
const fillAllSelected = computed(() => fillItems.value.length > 0 && fillSelected.value.size === fillItems.value.length)
const canAdd = computed(() => pickedProduct.value && doc.value?.default_price_variety_id && doc.value?.default_currency_id)

let prodTimer = null

function badge(s) {
  const map = { draft: 'badge-draft', on_approval: 'badge-approval', posted: 'badge-posted' }
  return 'badge ' + (map[s] || '')
}

async function fetchDoc() {
  err.value = null
  try {
    const r = await priceApi.getDocument(props.docId)
    doc.value = r.data
    edit.name = r.data.name
    edit.priceVariety = r.data.default_price_variety_id
    edit.currency = r.data.default_currency_id
    edit.date = r.data.document_date?.slice(0, 10) || ''
    pickedProduct.value = null; prodSearch.value = ''; prodResults.value = []; newPrice.value = 0
  } catch (e) { err.value = e.displayMessage }
}

async function saveHeader() {
  if (!isDraft.value) return
  try {
    await priceApi.updateDocument(props.docId, {
      name: edit.name.trim(),
      default_price_variety_id: edit.priceVariety,
      default_currency_id: edit.currency,
      document_date: edit.date,
    })
    fetchDoc()
    emit('changed')
  } catch (e) { err.value = e.displayMessage }
}

async function doSetStatus(newStatus) {
  try {
    await priceApi.updateDocument(props.docId, { status: newStatus })
    fetchDoc()
    emit('changed')
  } catch (e) { err.value = e.displayMessage }
}

async function doApply() {
  try { await priceApi.applyDocument(props.docId); fetchDoc(); emit('changed') }
  catch (e) { err.value = e.displayMessage }
}

async function doUnapply() {
  if (!confirm('Отменить проведение?')) return
  try { await priceApi.unapplyDocument(props.docId); fetchDoc(); emit('changed') }
  catch (e) { err.value = e.displayMessage }
}

async function doDelete() {
  if (!confirm('Удалить документ?')) return
  try { await priceApi.deleteDocument(props.docId); emit('close') }
  catch (e) { err.value = e.displayMessage }
}

// Поиск товара через SKU API
function onProdSearch() {
  clearTimeout(prodTimer)
  const q = prodSearch.value.trim()
  if (!q) { prodResults.value = []; return }
  prodTimer = setTimeout(async () => {
    try {
      const r = await priceApi.listPrices({}) // using price API just as HTTP client
      // Use the SKU admin API for search
      const resp = await fetch(`/api/admin/sku/?search=${encodeURIComponent(q)}&limit=15`)
      const data = await resp.json()
      prodResults.value = data.data || []
    } catch { prodResults.value = [] }
  }, 250)
}

function pickProduct(p) {
  pickedProduct.value = p
  prodSearch.value = (p.code || '') + ' ' + (p.name || '')
  prodResults.value = []
}

async function doAddItem() {
  if (!canAdd.value) return
  err.value = null
  try {
    await priceApi.addItem(props.docId, { sku_id: pickedProduct.value.id, price: newPrice.value })
    newPrice.value = 0; pickedProduct.value = null; prodSearch.value = ''; prodResults.value = []
    fetchDoc(); emit('changed')
  } catch (e) { err.value = e.displayMessage }
}

function startEditPrice(item) {
  if (!isDraft.value) return
  editingId.value = item.id
  editPrice.value = item.price
  setTimeout(() => { try { document.querySelector('.fi-price')?.focus() } catch {} }, 50)
}
function openFillByFilter() {
  showFillModal.value = true; fillCode.value = ''; fillEqType.value = ''; fillBrand.value = ''
  fillItems.value = []; fillSelected.value = new Set(); fillErr.value = ''
}
async function doFillSearch() {
  fillLoading.value = true; fillErr.value = ''
  try {
    const p = new URLSearchParams()
    if (fillCode.value) p.set('search', fillCode.value)
    if (fillEqType.value) p.set('equipment_type_id', fillEqType.value)
    if (fillBrand.value) p.set('brand_id', fillBrand.value)
    p.set('limit', '100')
    const r = await fetch('/api/admin/sku/?' + p.toString())
    const d = await r.json()
    fillItems.value = d.data || []
    fillSelected.value = new Set()
  } catch (e) { fillErr.value = 'Search error' }
  finally { fillLoading.value = false }
}
function toggleFillOne(id) {
  const s = new Set(fillSelected.value)
  s.has(id) ? s.delete(id) : s.add(id)
  fillSelected.value = s
}
function toggleFillAll() {
  fillSelected.value = fillAllSelected.value ? new Set() : new Set(fillItems.value.map(x => x.id))
}
async function doFillAdd() {
  fillAdding.value = true; fillErr.value = ''
  let added = 0
  try {
    for (const skuId of fillSelected.value) {
      try { await priceApi.addItem(props.docId, { sku_id: skuId, price: 0 }); added++ } catch {}
    }
    showFillModal.value = false
    fetchDoc(); emit('changed')
  } catch (e) { fillErr.value = 'Error adding items' }
  finally { fillAdding.value = false }
}

async function createAndAddSku() {
  newSkuSaving.value = true; newSkuErr.value = ''
  try {
    const r = await fetch('/api/core/', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ model: 'sku.SKU', ...newSku }),
    })
    const d = await r.json()
    if (!d.success) { newSkuErr.value = d.error||'Error'; return }
    const skuId = d.id
    // Add to document
    await priceApi.addItem(props.docId, { sku_id: skuId, price: 0 })
    showNewSku.value = false
    Object.assign(newSku, { code: '', name: '', description: '', equipment_type_id: null, brand_id: null })
    fetchDoc(); emit('changed')
  } catch (e) { newSkuErr.value = 'Error creating SKU' }
  finally { newSkuSaving.value = false }
}

async function openSkuEdit(item) {
  skuEditItem.value = item
  try {
    const r = await fetch('/api/core/?model=sku.SKU&id=' + item.sku_id + '&fmt=compact')
    const d = await r.json()
    const s = d.data || {}
    skuForm.code = s.code || item.product_code || ''
    skuForm.name = s.name || item.product_name || ''
    skuForm.description = s.description || ''
    skuForm.equipment_type_id = s.equipment_type_id || null
    skuForm.brand_id = s.brand_id || null
    skuForm.is_active = s.is_active !== false
  } catch { skuEditErr.value = 'Load error' }
}
async function saveSkuEdit() {
  skuEditSaving.value = true; skuEditErr.value = ''
  try {
    const r = await fetch('/api/core/', {
      method: 'PUT', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ model: 'sku.SKU', id: skuEditItem.value.sku_id, ...skuForm }),
    })
    const d = await r.json()
    if (!d.success) { skuEditErr.value = d.error||'Error'; return }
    skuEditItem.value.product_code = skuForm.code
    skuEditItem.value.product_name = skuForm.name
    skuEditItem.value = null
  } catch (e) { skuEditErr.value = 'Save error' }
  finally { skuEditSaving.value = false }
}

async function savePrice(item) {
  const newVal = editPrice.value
  editingId.value = null
  if (newVal === item.price) return
  err.value = null
  try {
    await fetch('/api/core/', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: 'price.PriceDocumentItem', id: item.id, price: newVal }),
    })
    item.price = newVal
  } catch (e) {
    err.value = 'Error saving price'
  }
}

// ── Excel export ──
async function doExportExcel() {
  try {
    const r = await priceApi.exportDocument(props.docId)
    const blob = r.data
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const disposition = r.headers?.['content-disposition'] || ''
    const m = disposition.match(/filename[^;=\n]*=["']?([^"';\n]*)["']?/)
    a.download = (m?.[1]) || `price_doc_${props.docId}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (e) { err.value = e.displayMessage||'Export error' }
}

// ── Excel import ──
function triggerImport() { fileInput.value?.click() }

async function doImportExcel(e) {
  const file = e.target.files?.[0]
  if (!file) return
  try {
    const r = await priceApi.importDocument(props.docId, file)
    const d = r.data
    const msg = [`Создано: ${d.created||0}`, `Обновлено: ${d.updated||0}`]
    if (d.errors?.length) msg.push('Ошибки: ' + d.errors.join('; '))
    alert(msg.join('\n'))
    fetchDoc(); emit('changed')
  } catch (e) { err.value = e.displayMessage||'Import error' }
  finally { e.target.value = '' }
}

async function doDeleteItem(itemId) {
  if (!confirm('Удалить позицию?')) return
  try { await priceApi.deleteItem(props.docId, itemId); fetchDoc(); emit('changed') }
  catch (e) { err.value = e.displayMessage }
}

watch(() => props.docId, fetchDoc, { immediate: true })
onBeforeUnmount(() => clearTimeout(prodTimer))
</script>

<style scoped>
.doc-edit{margin-top:4px}
.doc-card{border:1px solid #e5e7eb;border-radius:8px;overflow:hidden}
.doc-card-header{padding:16px 20px;background:#f9fafb;border-bottom:1px solid #e5e7eb}
.doc-header-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
.doc-fields{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-end}
.doc-field{display:flex;flex-direction:column;gap:2px}
.doc-field label{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.5px}
.doc-field .fi{min-width:140px}
.doc-val{font-size:14px;color:#374151;padding:5px 0}
.doc-table-wrap{padding:16px 20px}
.doc-actions{display:flex;gap:8px;justify-content:flex-end;padding:12px 20px;border-top:1px solid #e5e7eb;background:#fafafa}
.add-form{padding:8px 0 0}
.add-row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.search-wrap{position:relative}
.search-drop{position:absolute;top:100%;left:0;right:0;max-height:180px;overflow-y:auto;background:#fff;border:1px solid #d1d5db;border-radius:0 0 5px 5px;z-index:10;box-shadow:0 4px 8px rgba(0,0,0,.1)}
.search-item{padding:6px 10px;font-size:13px;cursor:pointer;border-bottom:1px solid #f3f4f6}
.search-item:hover{background:#f0f9ff}
.picked{font-size:13px;color:#059669;font-weight:500;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

.fi{padding:5px 8px;border:1px solid #d1d5db;border-radius:5px;font-size:13px}
.fi-lg{min-width:160px}
.fi-w{min-width:200px}
.fi-n{width:100px}
.tb{width:100%;border-collapse:collapse;font-size:13px}
.tb th{text-align:left;padding:6px 10px;background:#f9fafb;border-bottom:2px solid #e5e7eb;color:#6b7280;font-weight:500}
.tb td{padding:6px 10px;border-bottom:1px solid #f3f4f6}
.code-cell{font-family:monospace;font-size:12px}
.pr{text-align:right;font-weight:500}
.st{text-align:center;padding:40px;color:#6b7280}
.er{color:#dc2626;font-size:12px;margin-top:4px}
.btn,.btn-s,.btn-d,.btn-c,.btn-o,.btn-w{padding:4px 12px;border:none;border-radius:4px;font-size:12px;cursor:pointer}
.btn{background:#2563eb;color:#fff}
.btn-s{background:#059669;color:#fff}
.btn-d{background:#dc2626;color:#fff}
.btn-c{background:#e5e7eb;color:#374151}
.btn-o{background:#f59e0b;color:#fff}
.btn-w{background:#9333ea;color:#fff}
.fi-price{width:90px;padding:2px 4px;border:1px solid #3b82f6;border-radius:3px;font-size:13px;text-align:right}
.act-cell{display:flex;gap:3px;align-items:center}
.price-val{display:inline-block;min-width:60px}
.pr:hover .price-val{color:#2563eb}
.btn-e{padding:2px 6px;border:1px solid #d1d5db;border-radius:3px;background:#fff;cursor:pointer;font-size:12px;text-decoration:none;color:#374151}
.btn-e:hover{background:#f0f9ff;border-color:#2563eb}
.sku-edit-bg{position:fixed;inset:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;z-index:200}
.sku-edit-modal{background:#fff;border-radius:8px;padding:20px;width:480px;max-height:90vh;overflow-y:auto;box-shadow:0 4px 24px rgba(0,0,0,.15)}
.sku-edit-modal h4{margin:0 0 12px;font-size:15px}
.sku-edit-body{display:flex;flex-direction:column;gap:6px}
.sku-edit-body label{font-size:12px;color:#374151;display:flex;flex-direction:column;gap:2px}
.sku-edit-body .inp{padding:5px 8px;border:1px solid #d1d5db;border-radius:4px;font-size:13px}
.sku-edit-body textarea.inp{resize:vertical;min-height:50px}
.sku-edit-row{display:flex;gap:8px}
.sku-edit-row label{flex:1}
.sku-edit-btns{display:flex;gap:8px;margin-top:12px;justify-content:flex-end}
.fill-list{max-height:300px;overflow-y:auto;border:1px solid #e5e7eb;border-radius:4px;margin:8px 0}
.fill-row{display:flex;align-items:center;gap:8px;padding:4px 8px;border-bottom:1px solid #f3f4f6;font-size:13px}
.fill-row:hover{background:#f9fafb}
.fill-row.sel{background:#eff6ff}
.fill-row .code{font-family:monospace;font-weight:500;min-width:100px}
.fill-row .name{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.fill-row .meta{color:#9ca3af;font-size:11px;white-space:nowrap}
.btn-sm{padding:2px 8px;font-size:11px;background:#fff;border:1px solid #d1d5db;border-radius:4px;cursor:pointer}
.btn-sm:hover{background:#f3f4f6}
.fl{display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap;align-items:center}
.act-bar{display:flex;gap:8px;margin-bottom:8px;align-items:center}
.sel-info{font-size:13px;color:#6b7280}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:500}
.badge-draft{background:#e5e7eb;color:#374151}
.badge-approval{background:#fef3c7;color:#92400e}
.badge-posted{background:#d1fae5;color:#065f46}
.doc-actions-sep{flex:1}
</style>