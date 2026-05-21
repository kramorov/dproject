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
            <label>Тип оборудования</label>
            <select v-if="isDraft" v-model="edit.ctId" class="fi" @change="saveHeader">
              <option v-for="e in contentTypes" :key="e.id" :value="e.content_type_id">{{ e.name }}</option>
            </select>
            <span v-else class="doc-val">{{ doc?.item_content_type_name||'—' }}</span>
          </div>

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
              <td class="pr">{{ item.price }}</td>
              <td><button v-if="isDraft" class="btn-d btn-sm" @click="doDeleteItem(item.id)">✕</button></td>
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
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, inject, watch, onBeforeUnmount } from 'vue'
import priceApi from '../api'

const props = defineProps({ docId: { type: Number, required: true } })
const emit = defineEmits(['close', 'changed'])

const opts = inject('opts')
const contentTypes = inject('contentTypes')

const doc = ref(null)
const err = ref(null)
const isDraft = computed(() => doc.value?.status === 'draft')

const edit = reactive({ name: '', ctId: null, priceVariety: null, currency: null, date: '' })

// Поиск товара
const prodSearch = ref(''), prodResults = ref([]), pickedProduct = ref(null)
const newPrice = ref(0)
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
    edit.ctId = r.data.item_content_type_id
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
      item_content_type_id: edit.ctId,
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

// Поиск товара
function onProdSearch() {
  clearTimeout(prodTimer)
  const q = prodSearch.value.trim()
  if (!q || !doc.value?.content_type_app) { prodResults.value = []; return }
  prodTimer = setTimeout(async () => {
    try {
      const modelName = `${doc.value.content_type_app}.${doc.value.content_type_model}`
      const api = (await import('@/shared/api')).default
      const r = await api.get('/core/', { params: { model: modelName, search: q, fmt: 'compact', limit: 15 } })
      prodResults.value = (r.data.data || []).filter(p => (p.code || '').toLowerCase().includes(q.toLowerCase()))
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
    await priceApi.addItem(props.docId, { object_id: pickedProduct.value.id, price: newPrice.value })
    newPrice.value = 0; pickedProduct.value = null; prodSearch.value = ''; prodResults.value = []
    fetchDoc(); emit('changed')
  } catch (e) { err.value = e.displayMessage }
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
.btn-sm{padding:2px 8px;font-size:11px}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:500}
.badge-draft{background:#e5e7eb;color:#374151}
.badge-approval{background:#fef3c7;color:#92400e}
.badge-posted{background:#d1fae5;color:#065f46}
</style>
