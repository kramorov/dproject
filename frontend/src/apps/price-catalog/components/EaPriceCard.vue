<template>
  <div class="ea-card-wrap">
    <div class="ea-top-bar">
      <button class="btn-back" @click="$emit('close')">← К списку</button>
      <button v-if="isDraft" class="btn-fill" @click="onFill" :disabled="filling">{{ filling ? 'Заполнение...' : '📥 Заполнить' }}</button>
    </div>

    <div v-if="loading" class="st">Загрузка...</div>

    <SharedDocumentCard
      v-if="doc"
      :doc="doc"
      :loading="false"
      :saving="saving"
      :error="error"
      :form="form"
      :isDraft="isDraft"
      :isPosted="isPosted"
      :isDeleted="false"
      :features="cardFeatures"
      :canSave="canSave"
      :canRegister="canRegister"
      :canUnregister="canUnregister"
      :canMarkDeleted="canMarkDeleted"
      :canRestore="false"
      :availableExports="availableExports"
      @save="onSave"
      @register="register"
      @unregister="unregister"
      @mark-deleted="onMarkDeleted"
      @print="onPrint"
      @export="onExport"
      @import-file="onImportFile"
    >
      <template #form-extra>
        <div class="form-extra-row">
          <span class="fe-label">Тип цены: <strong>{{ doc.price_variety?.name || '—' }}</strong></span>
          <span class="fe-label">Валюта: <strong>{{ doc.currency?.code || '—' }}</strong></span>
          <span :class="statusBadgeClass" class="fe-status">{{ statusLabel }}</span>
        </div>
      </template>
      <template #items>
        <div class="ea-info">
          <span class="ea-info-item">Серия: <strong>{{ doc.model_line?.name || '—' }}</strong></span>
          <span class="ea-info-item">Напряжение: <strong>{{ doc.power_supply?.name || '—' }}</strong></span>
        </div>

        <div v-if="msg" class="msg">{{ msg }}</div>

        <div v-if="matrix.length" class="matrix-wrap">
          <table class="mtx">
            <thead>
              <tr>
                <th class="rown-col">Модель</th>
                <th class="base-col">Базовая цена</th>
                <th v-for="col in columns" :key="col.key" class="opt-col">{{ col.label }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in matrix" :key="row.id">
                <td class="rown-col">
                  <strong>{{ row.label || row.code }}</strong>
                  <div class="sub">{{ row.name }}</div>
                </td>
                <td class="base-col">
                  <input v-model.number="row.basePrice" type="number" step="0.01" class="ci" :disabled="!isDraft" />
                </td>
                <td v-for="col in columns" :key="col.key" class="opt-col">
                  <span v-if="!row._avail.has(col.key)" class="na-cell">—</span>
                  <input v-else v-model.number="row.options[col.key]" type="number" step="0.01" class="ci" placeholder="0" :disabled="!isDraft" />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else-if="!loading" class="items-empty">Нет моделей для этого напряжения</div>
      </template>
    </SharedDocumentCard>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import SharedDocumentCard from '@/shared/components/documents/DocumentCard.vue'
import { useDocumentCard } from '@/shared/composables/useDocumentCard'
import priceApi from '../api'

const props = defineProps({
  docId: { type: [Number, String], default: null },
})
const emit = defineEmits(['close'])

// ── Card composable ──
const cardApi = {
  getDetail: (id) => priceApi.getEaConfigDoc(id),
  update: () => ({}),
  register: (id) => {
    return priceApi.postEaConfigDoc(id, {
      rows: buildRows(),
      currency_id: doc.value?.currency?.id,
      price_variety_id: doc.value?.price_variety?.id,
    })
  },
  unregister: (id) => priceApi.unpostEaConfigDoc(id),
  markDeleted: (id) => priceApi.deleteEaConfigDoc(id),
}

const card = useDocumentCard(cardApi)
const {
  doc, loading: cardLoading, saving, error, form,
  isDraft, isPosted, canRegister, canUnregister, canMarkDeleted,
  loadDocument, register, unregister, markDeleted,
} = card

const cardFeatures = computed(() => ({ print: true, export_excel: true, import: true }))
const availableExports = computed(() => [{ key: 'excel', label: 'Excel' }])

const statusLabel = computed(() => doc.value?.status_label || doc.value?.status || '')
const statusBadgeClass = computed(() => 'status-badge status-' + (doc.value?.status || 'draft'))

const canSave = computed(() => isDraft.value && matrix.value.length > 0)
const DEFAULT_NAME = 'Конфигуратор цен'

// ── Helpers ──
function buildRows() {
  return matrix.value.map(row => ({
    model_line_item_id: row.id,
    base_price: row.basePrice || 0,
    options: Object.fromEntries(
      Object.entries(row.options).filter(([k]) => row._avail.has(k) && row.options[k] > 0)
    ),
  }))
}

// ── State ──
const loading = computed(() => cardLoading.value || matrixLoading.value)
const matrix = ref([])
const columns = ref([])
const matrixLoading = ref(false)
const msg = ref('')
const filling = ref(false)

// ── Load ──
onMounted(async () => {
  if (props.docId) await loadDoc()
})

async function loadDoc() {
  try {
    await loadDocument(props.docId)
    const d = doc.value
    if (d.power_supply) await buildMatrix()
    fillSaved(d.rows || [])
  } catch (e) { error.value = 'Ошибка загрузки'; console.error(e) }
}

async function buildMatrix() {
  matrixLoading.value = true; error.value = ''
  try {
    const psId = doc.value?.power_supply?.id
    if (!psId) return
    const r = await priceApi.getEaConfigOptions(psId)
    const items = r.data.model_items || []
    const colMap = new Map()
    const availByModel = {}
    for (const item of items) {
      const avail = new Set()
      for (const grp of item.option_groups || []) {
        for (const opt of grp.items || []) {
          if (opt.is_default) continue
          const key = `${grp.field}_${opt.option_id}`
          avail.add(key)
          if (!colMap.has(key)) {
            colMap.set(key, { key, label: opt.encoding || opt.name?.substring(0, 6) || key })
          }
        }
      }
      availByModel[item.id] = avail
    }
    columns.value = [...colMap.values()]
    const psEncoding = r.data.power_supply?.encoding || ''
    matrix.value = items.map(item => {
      const opts = {}
      for (const grp of item.option_groups || []) {
        for (const opt of grp.items || []) {
          if (opt.is_default) continue
          opts[`${grp.field}_${opt.option_id}`] = 0
        }
      }
      const label = `${item.model_line_code || ''}${item.code}.${psEncoding}`
      return { id: item.id, label, name: item.name, code: item.code, basePrice: 0, options: opts, _avail: availByModel[item.id] || new Set() }
    })
  } catch (e) { error.value = 'Ошибка загрузки'; console.error(e) }
  finally { matrixLoading.value = false }
}

function fillSaved(rows) {
  for (const row of rows) {
    const idx = matrix.value.findIndex(m => m.id === row.model_line_item?.id)
    if (idx >= 0) {
      matrix.value[idx].basePrice = row.base_price || 0
      for (const [key, val] of Object.entries(row.options || {})) {
        if (matrix.value[idx].options.hasOwnProperty(key)) {
          matrix.value[idx].options[key] = val
        }
      }
    }
  }
}

async function onSave() {
  saving.value = true; error.value = ''; msg.value = ''
  try {
    const data = {
      name: form.name || doc.value?.name || DEFAULT_NAME,
      price_variety_id: doc.value?.price_variety?.id,
      currency_id: doc.value?.currency?.id,
      model_line_id: doc.value?.model_line?.id,
      power_supply_id: doc.value?.power_supply?.id,
      rows: buildRows(),
    }
    if (doc.value?.id) {
      await priceApi.updateEaConfigDoc(doc.value.id, data)
    } else {
      await priceApi.createEaConfigDoc(data)
    }
    msg.value = 'Сохранено'
    emit('close')
  } catch (e) { error.value = 'Ошибка сохранения'; console.error(e) }
  finally { saving.value = false }
}

async function onMarkDeleted() {
  await markDeleted()
  emit('close')
}

async function onExport(fmt) {
  if (fmt !== 'excel' || !doc.value) return
  try {
    const rows = matrix.value.map(row => ({
      model_line_item_id: row.id,
      label: row.label || row.code,
      base_price: row.basePrice || 0,
      options: Object.fromEntries(
        Object.entries(row.options).filter(([k]) => row._avail.has(k) && row.options[k] > 0)
      ),
    }))
    const r = await priceApi.exportEaConfigDoc(doc.value.id, { rows })
    const blob = r.data
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ea_config_${doc.value.id}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (e) { console.error('Export error:', e) }
}

async function onImportFile(file) {
  if (!doc.value) return
  try {
    const r = await priceApi.importEaConfigDoc(doc.value.id, file)
    const { rows } = r.data
    if (rows?.length) {
      for (const row of rows) {
        const idx = matrix.value.findIndex(m => m.id === row.model_line_item_id)
        if (idx >= 0) {
          matrix.value[idx].basePrice = row.base_price
          Object.assign(matrix.value[idx].options, row.options || {})
        }
      }
      msg.value = `Импортировано строк: ${rows.length}`

      // Сохраняем импортированные данные в документ
      await priceApi.updateEaConfigDoc(doc.value.id, {
        name: form.name || doc.value?.name || DEFAULT_NAME,
        currency_id: doc.value?.currency?.id,
        price_variety_id: doc.value?.price_variety?.id,
        rows: buildRows(),
      })
    }
  } catch (e) { console.error('Import error:', e) }
}

async function onPrint() {
  if (!doc.value) return
  try {
    const rows = matrix.value.map(row => ({
      model_line_item_id: row.id,
      label: row.label || row.code,
      base_price: row.basePrice || 0,
      options: Object.fromEntries(
        Object.entries(row.options).filter(([k]) => row._avail.has(k) && row.options[k] > 0)
      ),
    }))
    const r = await priceApi.printEaConfigDoc(doc.value.id, { rows })
    const html = r.data?.html || ''
    const w = window.open('', '_blank')
    if (w) { w.document.write(html); w.document.close() }
  } catch (e) { console.error('Print error:', e) }
}

async function onFill() {
  if (!doc.value) return
  filling.value = true; msg.value = ''
  try {
    const r = await priceApi.fillEaConfigDoc(doc.value.id)
    const rows = r.data.rows || []
    for (const row of rows) {
      const idx = matrix.value.findIndex(m => m.id === row.model_line_item_id)
      if (idx >= 0) {
        matrix.value[idx].basePrice = row.base_price
        Object.assign(matrix.value[idx].options, row.options || {})
      }
    }
    msg.value = `Заполнено строк: ${rows.length}`

      // Сохраняем заполненные данные в документ
    await priceApi.updateEaConfigDoc(doc.value.id, {
      name: form.name || doc.value?.name || DEFAULT_NAME,
      currency_id: doc.value?.currency?.id,
      price_variety_id: doc.value?.price_variety?.id,
      rows: buildRows(),
    })
  } catch (e) {
    msg.value = 'Ошибка заполнения: ' + (e.response?.data?.error || e.message)
  } finally { filling.value = false }
}
</script>

<style scoped>
.ea-card-wrap { font-family: var(--cat-font); font-size: var(--cat-text-sm); }
.ea-top-bar { display: flex; gap: var(--cat-gap-sm); margin-bottom: var(--cat-gap-md); }
.btn-back {
  padding: 2px 10px;
  border: 1px solid var(--cat-border);
  border-radius: var(--cat-radius-sm);
  background: var(--cat-surface);
  cursor: pointer;
  font-size: var(--cat-text-sm);
  font-family: var(--cat-font);
}
.btn-fill {
  padding: 2px 10px;
  border: none;
  border-radius: var(--cat-radius-sm);
  background: #059669;
  color: #fff;
  cursor: pointer;
  font-size: var(--cat-text-sm);
  font-family: var(--cat-font);
}
.btn-fill:disabled { opacity: .5; cursor: default; }

.form-extra-row {
  display: flex;
  gap: var(--cat-gap-sm);
  align-items: flex-end;
  height: 100%;
}
.fe-label { font-size: var(--cat-text-xs); color: var(--cat-muted); }
.fe-status { margin-left: auto; align-self: center; white-space: nowrap; }

.ea-info {
  display: flex;
  gap: var(--cat-gap-md);
  padding: var(--cat-gap-xs) 0;
  border-bottom: 1px solid var(--cat-border-light);
  margin-bottom: var(--cat-gap-sm);
}
.ea-info-item { font-size: var(--cat-text-sm); }

.matrix-wrap { overflow-x: auto; max-height: 60vh; overflow-y: auto; }
.mtx { border-collapse: collapse; font-size: 12px; min-width: 100%; }
.mtx th {
  position: sticky; top: 0; background: var(--cat-header-bg, #f1f5f9);
  padding: 4px 4px; border: 1px solid var(--cat-border);
  font-weight: 600; white-space: nowrap; z-index: 1;
  font-size: var(--cat-text-xs);
}
.mtx td { padding: 2px 4px; border: 1px solid var(--cat-border-light); }
.rown-col { min-width: 130px; max-width: 160px; }
.rown-col strong { display: block; font-size: 13px; }
.rown-col .sub { font-size: 10px; color: var(--cat-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.base-col { min-width: 95px; }
.opt-col { min-width: 70px; }
.ci {
  width: 100%; padding: 3px 4px;
  border: 1px solid transparent; border-radius: var(--cat-radius-sm);
  font-size: 12px; text-align: right; box-sizing: border-box;
  font-family: var(--cat-font); background: var(--cat-input-bg, #fff);
}
.ci:focus { border-color: var(--cat-primary); outline: none; }
.ci:hover { border-color: var(--cat-border); }
.ci:disabled { background: var(--cat-input-disabled-bg, #f5f5f5); color: var(--cat-muted); cursor: not-allowed; }

.items-empty { text-align: center; padding: var(--cat-gap-xl); color: var(--cat-muted); }
.st { text-align: center; padding: var(--cat-gap-xl); color: var(--cat-muted); }
.msg { color: var(--cat-status-posted); font-size: var(--cat-text-sm); margin: var(--cat-gap-xs) 0; }
</style>
