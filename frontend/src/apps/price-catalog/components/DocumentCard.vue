<template>
  <div class="doc-edit">
    <button class="btn-back" @click="$emit('close')">← К списку</button>

    <SharedDocumentCard
      :doc="doc"
      :loading="loading"
      :saving="saving"
      :error="error"
      :form="form"
      :isDraft="isDraft"
      :isPosted="isPosted"
      :isDeleted="isDeleted"
      :features="cardFeatures"
      :canSave="canSave"
      :canRegister="canRegister"
      :canUnregister="canUnregister"
      :canMarkDeleted="canMarkDeleted"
      :canRestore="canRestore"
      :availableExports="availableExports"
      @save="onSave"
      @register="register"
      @unregister="unregister"
      @mark-deleted="markDeleted"
      @restore="restore"
      @export="onExport"
      @import-file="onImportFile"
    >
      <template #form-extra>
        <div class="form-extra-row">
          <label class="fe-label">
            <span>Тип цены</span>
            <select v-if="isDraft" v-model="priceVarietyId" class="fe-select" @change="saveExtraFields">
              <option :value="null">—</option>
              <option v-for="v in opts.varieties" :key="v.id" :value="v.id">{{ v.name }}</option>
            </select>
            <span v-else class="fe-val">{{ doc.default_price_variety_name || '—' }}</span>
          </label>
          <label class="fe-label">
            <span>Валюта</span>
            <select v-if="isDraft" v-model="currencyId" class="fe-select" @change="saveExtraFields">
              <option :value="null">—</option>
              <option v-for="c in opts.currencies" :key="c.id" :value="c.id">{{ c.code }}</option>
            </select>
            <span v-else class="fe-val">{{ doc.default_currency_name || doc.default_currency_symbol || '—' }}</span>
          </label>
          <span :class="statusBadgeClass" class="fe-status">{{ statusLabel }}</span>
        </div>
      </template>
      <template #items>
        <!-- Таблица позиций -->
        <table v-if="docItems.length" class="items-tb">
          <thead>
            <tr>
              <th class="it-num">#</th>
              <th class="it-code">Код</th>
              <th class="it-name">Товар</th>
              <th class="it-variety">Вид цены</th>
              <th class="it-curr">Валюта</th>
              <th class="it-price">Цена</th>
              <th class="it-act"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, i) in docItems" :key="item.id">
              <td class="it-num">{{ i + 1 }}</td>
              <td class="it-code">{{ item.product_code || '—' }}</td>
              <td class="it-name">{{ item.product_name || '—' }}</td>
              <td class="it-variety">{{ item.price_variety_name || doc.default_price_variety_name || '—' }}</td>
              <td class="it-curr">{{ item.currency_name || doc.default_currency_name || '—' }}</td>
              <td class="it-price" @click="startEditPrice(item)">
                <input
                  v-if="editingPriceId === item.id"
                  v-model.number="editPriceVal"
                  type="number" step="0.01"
                  class="fi-price"
                  @blur="savePrice(item)"
                  @keyup.enter="savePrice(item)"
                  @keyup.escape="editingPriceId = null"
                  @click.stop
                />
                <span v-else class="price-val">{{ item.price }}</span>
              </td>
              <td class="it-act">
                <button v-if="item.sku_id" title="Редактировать SKU" class="btn-icon" @click.stop="openSkuEdit(item)">📝</button>
                <button v-if="isDraft" title="Удалить" class="btn-icon btn-del" @click.stop="doDeleteItem(item.id)">✕</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="items-empty">Нет позиций</div>

        <!-- Добавление позиции -->
        <div v-if="isDraft" class="add-form">
          <div class="add-row">
            <div class="search-wrap">
              <input
                v-model="prodSearch"
                placeholder="Поиск SKU (код/название)..."
                class="fi fi-lg"
                @input="onProdSearch"
                @focus="onProdSearch"
              />
              <div v-if="prodResults.length" class="search-drop">
                <div
                  v-for="p in prodResults" :key="p.id"
                  class="search-item"
                  @click="pickProduct(p)"
                >{{ p.code }} — {{ p.name }}</div>
              </div>
            </div>
            <span v-if="pickedProduct" class="picked">{{ pickedProduct.code }} {{ pickedProduct.name }}</span>
            <input v-model.number="newPrice" type="number" step="0.01" placeholder="Цена" class="fi fi-n" />
            <button class="btn-add" :disabled="!canAddItem" @click="doAddItem">Добавить</button>
            <button class="btn-icon" title="Создать SKU" @click="showNewSku = true">＋</button>
          </div>
        </div>

        <!-- Fill by filter -->
        <div v-if="isDraft" style="margin-top:8px">
          <button class="btn-fill" @click="openFillByFilter">📋 Заполнить по фильтру</button>
        </div>
      </template>
    </SharedDocumentCard>

    <!-- Fill modal -->
    <div v-if="showFillModal" class="modal-bg">
      <div class="modal-box">
        <h4>Подбор SKU в документ</h4>
        <div class="fill-filters fl">
          <input v-model="fillCode" placeholder="Код/название" class="fi" @keyup.enter="doFillSearch" />
          <select v-model="fillEqType" class="fi"><option value="">Все типы</option>
            <option v-for="t in opts.equipmentTypes" :key="t.id" :value="t.id">{{ t.name }}</option>
          </select>
          <select v-model="fillBrand" class="fi"><option value="">Все бренды</option>
            <option v-for="b in opts.brands" :key="b.id" :value="b.id">{{ b.name }}</option>
          </select>
          <button class="btn-fill" @click="doFillSearch">Искать</button>
        </div>
        <div v-if="fillLoading" class="st">Поиск...</div>
        <div v-else-if="fillItems.length" class="fill-list">
          <div class="fill-row sel" @click="toggleFillAll">
            <input type="checkbox" :checked="fillAllSelected" /> <strong>Выбрать все ({{ fillItems.length }})</strong>
          </div>
          <div
            v-for="item in fillItems" :key="item.id"
            class="fill-row" :class="{ sel: fillSelected.has(item.id) }"
            @click="toggleFillOne(item.id)"
          >
            <input type="checkbox" :checked="fillSelected.has(item.id)" />
            <span class="code">{{ item.code }}</span>
            <span class="name">{{ item.name }}</span>
            <span class="meta">{{ item.equipment_type_name }} / {{ item.brand_name }}</span>
          </div>
        </div>
        <div v-else-if="!fillLoading && fillCode" class="st">Ничего не найдено</div>
        <div v-if="fillErr" class="er">{{ fillErr }}</div>
        <div class="modal-btns">
          <button
            class="btn-fill" :disabled="fillAdding || !fillSelected.size"
            @click="doFillAdd"
          >{{ fillAdding ? 'Добавление...' : 'Перенести в документ (' + fillSelected.size + ')' }}</button>
          <button class="btn-cancel" @click="showFillModal = false">Закрыть</button>
        </div>
      </div>
    </div>

    <!-- Create SKU modal -->
    <div v-if="showNewSku" class="modal-bg">
      <div class="modal-box">
        <h4>Создать номенклатуру</h4>
        <div class="sku-body">
          <label>Код * <input v-model="newSku.code" class="inp" /></label>
          <label>Название <input v-model="newSku.name" class="inp" /></label>
          <label>Описание <textarea v-model="newSku.description" class="inp" rows="3"></textarea></label>
          <div class="sku-row">
            <label>Тип <select v-model="newSku.equipment_type_id" class="inp"><option :value="null">--</option>
              <option v-for="t in opts.equipmentTypes" :key="t.id" :value="t.id">{{ t.name }}</option></select></label>
            <label>Бренд <select v-model="newSku.brand_id" class="inp"><option :value="null">--</option>
              <option v-for="b in opts.brands" :key="b.id" :value="b.id">{{ b.name }}</option></select></label>
          </div>
        </div>
        <div class="modal-btns">
          <button @click="showNewSku = false" class="btn-cancel">Отмена</button>
          <button @click="createAndAddSku" class="btn-create" :disabled="newSkuSaving || !newSku.code">{{ newSkuSaving ? '...' : 'Создать и добавить' }}</button>
        </div>
        <div v-if="newSkuErr" class="er">{{ newSkuErr }}</div>
      </div>
    </div>

    <!-- Edit SKU modal -->
    <div v-if="skuEditItem" class="modal-bg">
      <div class="modal-box">
        <h4>SKU: {{ skuEditItem.product_code }}</h4>
        <div class="sku-body">
          <label>Код <input v-model="skuForm.code" class="inp" /></label>
          <label>Название <input v-model="skuForm.name" class="inp" /></label>
          <label>Описание <textarea v-model="skuForm.description" class="inp" rows="3"></textarea></label>
          <div class="sku-row">
            <label>Тип <select v-model="skuForm.equipment_type_id" class="inp"><option :value="null">--</option>
              <option v-for="t in opts.equipmentTypes" :key="t.id" :value="t.id">{{ t.name }}</option></select></label>
            <label>Бренд <select v-model="skuForm.brand_id" class="inp"><option :value="null">--</option>
              <option v-for="b in opts.brands" :key="b.id" :value="b.id">{{ b.name }}</option></select></label>
          </div>
          <label><input type="checkbox" v-model="skuForm.is_active" /> Активно</label>
        </div>
        <div class="modal-btns">
          <button @click="skuEditItem = null" class="btn-cancel">Отмена</button>
          <button @click="saveSkuEdit" class="btn-create" :disabled="skuEditSaving">{{ skuEditSaving ? '...' : 'Сохранить' }}</button>
        </div>
        <div v-if="skuEditErr" class="er">{{ skuEditErr }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, inject, watch, onBeforeUnmount, nextTick } from 'vue'
import SharedDocumentCard from '@/shared/components/documents/DocumentCard.vue'
import { useDocumentCard } from '@/shared/composables/useDocumentCard'
import { useDocumentItems } from '@/shared/composables/useDocumentItems'
import priceApi from '../api'

const props = defineProps({ docId: { type: Number, required: true } })
const emit = defineEmits(['close', 'changed'])

const opts = inject('opts')

// ── Card composable ──
const cardApi = {
  getDetail: (id) => priceApi.getDocument(id),
  update: (id, data) => priceApi.updateDocument(id, data),
  register: (id) => priceApi.applyDocument(id),
  unregister: (id) => priceApi.unapplyDocument(id),
  markDeleted: (id) => priceApi.deleteDocument(id),
}

const card = useDocumentCard(cardApi, {
  onSave: async (id, data) => {
    await priceApi.updateDocument(id, {
      ...data,
      default_price_variety_id: priceVarietyId.value || undefined,
      default_currency_id: currencyId.value || undefined,
    })
  },
})

const {
  doc, loading, saving, error,
  form, isDraft, isPosted, isDeleted,
  canSave, canRegister, canUnregister, canMarkDeleted, canRestore,
  availableExports,
  loadDocument, save, register, unregister, markDeleted, restore,
} = card

// ── Items composable ──
const itemsApi = {
  getItems: (docId) => priceApi.getItems(docId),
  addItem: (docId, data) => priceApi.addItem(docId, data),
  deleteItem: (docId, itemId) => priceApi.deleteItem(docId, itemId),
  updateItem: (docId, itemId, data) => fetch('/api/core/', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: 'price.PriceDocumentItem', id: itemId, ...data }),
  }).then(r => r.json()),
}

const docItemsComposable = useDocumentItems(itemsApi)
const { items: docItems, loadItems } = docItemsComposable

// Features override — price docs don't have print
const cardFeatures = computed(() => ({
  print: false,
  export_excel: true,
  import: true,
}))

// Status badge (mirrors shared card's internals for form-extra slot)
const statusLabel = computed(() => doc.value?.status_label || doc.value?.status || '')
const statusBadgeClass = computed(() => 'status-badge status-' + (doc.value?.status || 'draft'))

// ── Extra fields (price_variety, currency) ──
const priceVarietyId = ref(null)
const currencyId = ref(null)

watch(doc, (d) => {
  if (d) {
    d.features = { print: false, export_excel: true, import: true }
    priceVarietyId.value = d.default_price_variety_id || null
    currencyId.value = d.default_currency_id || null
  }
})

async function saveExtraFields() {
  if (!doc.value || !isDraft.value) return
  try {
    await priceApi.updateDocument(props.docId, {
      default_price_variety_id: priceVarietyId.value || undefined,
      default_currency_id: currencyId.value || undefined,
    })
    emit('changed')
  } catch {}
}

// ── Save override ──
async function onSave() {
  await save()
  emit('changed')
}

// ── Export ──
function onExport(fmt) {
  if (fmt === 'excel') doExportExcel()
}

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
  } catch (e) { error.value = e?.displayMessage || 'Export error' }
}

// ── Import ──
async function onImportFile(file) {
  try {
    const r = await priceApi.importDocument(props.docId, file)
    await loadDocument(props.docId)
    await loadItems(props.docId)
    emit('changed')
    const d = r.data
    const msg = [`Создано: ${d.created || 0}`, `Обновлено: ${d.updated || 0}`]
    if (d.errors?.length) msg.push('Ошибки: ' + d.errors.join('; '))
    alert(msg.join('\n'))
  } catch (e) { error.value = e?.displayMessage || 'Import error' }
}

// ── Items: add ──
const prodSearch = ref(''), prodResults = ref([]), pickedProduct = ref(null)
const newPrice = ref(0)
let prodTimer = null

const canAddItem = computed(() => pickedProduct.value && doc.value?.default_price_variety_id && doc.value?.default_currency_id)

function onProdSearch() {
  clearTimeout(prodTimer)
  const q = prodSearch.value.trim()
  if (!q) { prodResults.value = []; return }
  prodTimer = setTimeout(async () => {
    try {
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
  if (!canAddItem.value) return
  try {
    await itemsApi.addItem(props.docId, { sku_id: pickedProduct.value.id, price: newPrice.value })
    newPrice.value = 0; pickedProduct.value = null; prodSearch.value = ''; prodResults.value = []
    await loadItems(props.docId); emit('changed')
  } catch {}
}

// ── Items: inline price edit ──
const editingPriceId = ref(null), editPriceVal = ref(0)

function startEditPrice(item) {
  if (!isDraft.value) return
  editingPriceId.value = item.id
  editPriceVal.value = item.price
  nextTick(() => { try { document.querySelector('.fi-price')?.focus() } catch {} })
}

async function savePrice(item) {
  const newVal = editPriceVal.value
  editingPriceId.value = null
  if (newVal === item.price) return
  try {
    await itemsApi.updateItem(props.docId, item.id, { price: newVal })
    item.price = newVal
  } catch {}
}

async function doDeleteItem(itemId) {
  if (!confirm('Удалить позицию?')) return
  try {
    await itemsApi.deleteItem(props.docId, itemId)
    await loadItems(props.docId); emit('changed')
  } catch {}
}

// ── Fill by filter ──
const showFillModal = ref(false)
const fillCode = ref(''), fillEqType = ref(''), fillBrand = ref('')
const fillItems = ref([]), fillLoading = ref(false), fillAdding = ref(false)
const fillSelected = ref(new Set()), fillErr = ref('')
const fillAllSelected = computed(() => fillItems.value.length > 0 && fillSelected.value.size === fillItems.value.length)

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
    fillItems.value = d.data || []; fillSelected.value = new Set()
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
  try {
    for (const skuId of fillSelected.value) {
      try { await itemsApi.addItem(props.docId, { sku_id: skuId, price: 0 }) } catch {}
    }
    showFillModal.value = false
    await loadItems(props.docId); emit('changed')
  } catch (e) { fillErr.value = 'Error adding items' }
  finally { fillAdding.value = false }
}

// ── SKU create ──
const showNewSku = ref(false)
const newSku = reactive({ code: '', name: '', description: '', equipment_type_id: null, brand_id: null })
const newSkuSaving = ref(false), newSkuErr = ref('')

async function createAndAddSku() {
  newSkuSaving.value = true; newSkuErr.value = ''
  try {
    const r = await fetch('/api/core/', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: 'sku.SKU', ...newSku }),
    })
    const d = await r.json()
    if (!d.success) { newSkuErr.value = d.error || 'Error'; return }
    await itemsApi.addItem(props.docId, { sku_id: d.id, price: 0 })
    showNewSku.value = false
    Object.assign(newSku, { code: '', name: '', description: '', equipment_type_id: null, brand_id: null })
    await loadItems(props.docId); emit('changed')
  } catch (e) { newSkuErr.value = 'Error creating SKU' }
  finally { newSkuSaving.value = false }
}

// ── SKU edit ──
const skuEditItem = ref(null)
const skuForm = reactive({ code: '', name: '', description: '', equipment_type_id: null, brand_id: null, is_active: true })
const skuEditSaving = ref(false), skuEditErr = ref('')

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
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: 'sku.SKU', id: skuEditItem.value.sku_id, ...skuForm }),
    })
    const d = await r.json()
    if (!d.success) { skuEditErr.value = d.error || 'Error'; return }
    skuEditItem.value.product_code = skuForm.code
    skuEditItem.value.product_name = skuForm.name
    skuEditItem.value = null
  } catch (e) { skuEditErr.value = 'Save error' }
  finally { skuEditSaving.value = false }
}

// ── Init ──
watch(() => props.docId, async (id) => {
  if (id) {
    await loadDocument(id)
    await loadItems(id)
  }
}, { immediate: true })

onBeforeUnmount(() => clearTimeout(prodTimer))
</script>

<style scoped>
.doc-edit { font-family: var(--cat-font); font-size: var(--cat-text-sm); }
.btn-back {
  padding: 2px 10px;
  border: 1px solid var(--cat-border);
  border-radius: var(--cat-radius-sm);
  background: var(--cat-surface);
  cursor: pointer;
  font-size: var(--cat-text-sm);
  font-family: var(--cat-font);
  margin-bottom: var(--cat-gap-md);
}

/* Form-extra (price_variety + currency + status in form grid) */
.form-extra-row {
  display: flex;
  gap: var(--cat-gap-sm);
  align-items: flex-end;
  height: 100%;
}
.fe-label { display: flex; flex-direction: column; gap: 2px; font-size: var(--cat-text-xs); color: var(--cat-muted); }
.fe-select, .fe-val { font-size: var(--cat-text-sm); }
.fe-select {
  padding: 2px 4px;
  border: 1px solid var(--cat-input-border, var(--cat-border));
  border-radius: var(--cat-radius-sm);
  background: var(--cat-input-bg, #fff);
  font-family: var(--cat-font);
  height: 26px; box-sizing: border-box;
}
.fe-val { color: var(--cat-text); padding: 2px 0; }
.fe-status { margin-left: auto; align-self: center; white-space: nowrap; }

/* Items table */
.items-tb { width: 100%; border-collapse: collapse; font-size: var(--cat-text-sm); margin-bottom: var(--cat-gap-sm); }
.items-tb th {
  text-align: left; padding: 2px 6px;
  border-bottom: 2px solid var(--cat-header-border, var(--cat-border));
  background: var(--cat-header-bg, var(--cat-bg));
  color: var(--cat-text-soft); font-weight: 600; font-size: var(--cat-text-xs);
}
.items-tb td { padding: 2px 6px; border-bottom: 1px solid var(--cat-border-light); }
.it-num { width: 30px; text-align: center; color: var(--cat-muted); font-size: var(--cat-text-xs); }
.it-code { font-family: var(--cat-font-mono); font-size: var(--cat-text-xs); width: 100px; }
.it-name { min-width: 150px; }
.it-variety, .it-curr { width: 100px; font-size: var(--cat-text-xs); color: var(--cat-muted); }
.it-price { width: 90px; text-align: right; cursor: pointer; }
.it-price:hover .price-val { color: var(--cat-primary); }
.it-act { width: 56px; text-align: center; white-space: nowrap; }
.price-val { display: inline-block; min-width: 50px; font-weight: 500; }
.fi-price {
  width: 80px; padding: 1px 4px;
  border: 1px solid var(--cat-primary);
  border-radius: var(--cat-radius-sm);
  font-size: var(--cat-text-sm); text-align: right;
  font-family: var(--cat-font);
}
.items-empty { text-align: center; padding: var(--cat-gap-xl); color: var(--cat-muted); }

/* Add form */
.add-form { margin-top: var(--cat-gap-sm); }
.add-row { display: flex; gap: var(--cat-gap-sm); align-items: center; flex-wrap: wrap; }
.search-wrap { position: relative; }
.search-drop {
  position: absolute; top: 100%; left: 0; right: 0;
  max-height: 180px; overflow-y: auto;
  background: var(--cat-surface); border: 1px solid var(--cat-border);
  border-radius: 0 0 var(--cat-radius-sm) var(--cat-radius-sm);
  z-index: 10; box-shadow: var(--cat-shadow-card);
}
.search-item { padding: 4px 8px; font-size: var(--cat-text-sm); cursor: pointer; border-bottom: 1px solid var(--cat-border-light); }
.search-item:hover { background: var(--cat-primary-light); }
.picked { font-size: var(--cat-text-sm); color: var(--cat-status-posted); font-weight: 500; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Buttons */
.fi {
  padding: 2px 6px; border: 1px solid var(--cat-input-border, var(--cat-border));
  border-radius: var(--cat-radius-sm); font-size: var(--cat-text-sm);
  font-family: var(--cat-font); background: var(--cat-input-bg, #fff);
  height: 26px; box-sizing: border-box;
}
.fi-lg { min-width: 180px; }
.fi-n { width: 80px; }
.btn-add {
  padding: 2px 10px; border: none; border-radius: var(--cat-radius-sm);
  background: var(--cat-primary); color: #fff; cursor: pointer;
  font-size: var(--cat-text-sm); font-family: var(--cat-font); height: 26px;
}
.btn-add:disabled { opacity: 0.5; cursor: default; }
.btn-icon {
  padding: 0 4px; border: 1px solid var(--cat-border);
  border-radius: var(--cat-radius-sm); background: var(--cat-surface);
  cursor: pointer; font-size: var(--cat-text-sm); height: 26px;
}
.btn-del { color: var(--cat-status-deleted); }
.btn-fill {
  padding: 2px 10px; border: 1px solid var(--cat-border);
  border-radius: var(--cat-radius-sm); background: var(--cat-surface);
  cursor: pointer; font-size: var(--cat-text-sm); font-family: var(--cat-font);
}
.btn-create {
  padding: 2px 12px; border: none; border-radius: var(--cat-radius-sm);
  background: var(--cat-primary); color: #fff; cursor: pointer;
  font-size: var(--cat-text-sm); font-family: var(--cat-font); height: 26px;
}
.btn-create:disabled { opacity: 0.5; cursor: default; }
.btn-cancel {
  padding: 2px 12px; border: 1px solid var(--cat-border);
  border-radius: var(--cat-radius-sm); background: var(--cat-surface);
  cursor: pointer; font-size: var(--cat-text-sm); font-family: var(--cat-font); height: 26px;
}

/* Modals */
.modal-bg {
  position: fixed; inset: 0; background: rgba(0,0,0,.4);
  display: flex; align-items: center; justify-content: center; z-index: 200;
}
.modal-box {
  background: var(--cat-surface); border-radius: var(--cat-radius-md);
  padding: var(--cat-gap-md); width: 520px; max-height: 85vh; overflow-y: auto;
  box-shadow: var(--cat-shadow-card);
  font-family: var(--cat-font); font-size: var(--cat-text-sm);
}
.modal-box h4 { margin: 0 0 var(--cat-gap-sm); font-size: var(--cat-text-base); }
.modal-btns { display: flex; gap: var(--cat-gap-sm); justify-content: flex-end; margin-top: var(--cat-gap-sm); }

/* Fill */
.fill-filters { margin-bottom: var(--cat-gap-sm); }
.fill-list { max-height: 260px; overflow-y: auto; border: 1px solid var(--cat-border); border-radius: var(--cat-radius-sm); margin-bottom: var(--cat-gap-sm); }
.fill-row { display: flex; align-items: center; gap: var(--cat-gap-sm); padding: 4px 8px; border-bottom: 1px solid var(--cat-border-light); font-size: var(--cat-text-sm); cursor: pointer; }
.fill-row:hover { background: var(--cat-row-hover, #fdfcf9); }
.fill-row.sel { background: var(--cat-primary-light); }
.fill-row .code { font-family: var(--cat-font-mono); font-weight: 500; min-width: 90px; }
.fill-row .name { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.fill-row .meta { color: var(--cat-muted); font-size: var(--cat-text-xs); white-space: nowrap; }

/* SKU modals */
.sku-body { display: flex; flex-direction: column; gap: var(--cat-gap-sm); }
.sku-body label { font-size: var(--cat-text-xs); color: var(--cat-text); display: flex; flex-direction: column; gap: 2px; }
.sku-body .inp { padding: 3px 6px; border: 1px solid var(--cat-input-border, var(--cat-border)); border-radius: var(--cat-radius-sm); font-size: var(--cat-text-sm); font-family: var(--cat-font); }
.sku-body textarea.inp { resize: vertical; min-height: 50px; }
.sku-row { display: flex; gap: var(--cat-gap-sm); }
.sku-row label { flex: 1; }

/* Shared */
.fl { display: flex; gap: var(--cat-gap-sm); flex-wrap: wrap; align-items: center; }
.st { text-align: center; padding: var(--cat-gap-xl); color: var(--cat-muted); font-size: var(--cat-text-sm); }
.er { color: var(--cat-status-deleted); font-size: var(--cat-text-xs); margin-top: var(--cat-gap-xs); }
</style>
