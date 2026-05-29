<!-- apps/limit-switch-admin/components/ModelLineForm.vue — форма LimitSwitchModelLine с табами -->
<template>
  <div class="mlf-grid" v-if="ready">
    <!-- Табы -->
    <div class="mlf-tabs">
      <button :class="{ act: tab === 'main' }" @click="tab = 'main'">Основное</button>
      <button :class="{ act: tab === 'gallery' }" @click="tab = 'gallery'">Галерея</button>
      <button :class="{ act: tab === 'docs' }" @click="tab = 'docs'">Техдокументация</button>
      <button :class="{ act: tab === 'certs' }" @click="tab = 'certs'">Сертификаты</button>
      <button :class="{ act: tab === 'extra' }" @click="tab = 'extra'">Дополнительно</button>
    </div>

    <div class="mlf-panels">
      <!-- Основное -->
      <div :class="['mlf-panel', { 'mlf-panel--active': tab === 'main' }]">
        <div class="fg fw"><label>Название *</label><input v-model="form.name" class="field" /></div>
        <div class="fg fw"><label>Описание</label><textarea v-model="form.description" class="field" rows="2" /></div>
        <div class="mlf-row">
          <div class="fg"><label>Код</label><input v-model="form.code" class="field" /></div>
          <div class="fg"><label>Сортировка</label><input v-model.number="form.sorting_order" type="number" class="field" /></div>
        </div>
        <div class="mlf-row">
          <div class="fg"><FkSelect v-model="form.equipment_type_id" :options="opts.equipmentTypes" label="Тип оборудования *" placeholder="Выберите тип" /></div>
        </div>
        <div class="mlf-row">
          <div class="fg"><FkSelect v-model="form.producer_id" :options="opts.producers" label="Производитель" placeholder="—" /></div>
          <div class="fg"><FkSelect v-model="form.brand_id" :options="opts.brands" label="Бренд" placeholder="—" /></div>
        </div>
        <div class="fg fw"><label>Шаблон названия</label><textarea v-model="form.name_template" class="field" rows="2" /></div>
        <div class="fg fw"><label>Шаблон описания</label><textarea v-model="form.description_template" class="field" rows="2" /></div>
        <label class="chk"><input type="checkbox" v-model="form.is_active" /> Активно</label>
      </div>

      <!-- Галерея -->
      <div :class="['mlf-panel', { 'mlf-panel--active': tab === 'gallery' }]">
        <div class="fg"><FkSelect v-model="form.image_gallery_id" :options="opts.imageGalleries" label="Набор изображений" placeholder="—" /></div>
      </div>

      <!-- Техдокументация -->
      <div :class="['mlf-panel', { 'mlf-panel--active': tab === 'docs' }]">
        <div class="mlf-cert-toolbar">
          <span class="mlf-section-label">Техдокументация</span>
          <button class="btn-new" @click="showDocUpload = true">+ Новый</button>
        </div>
        <ChipList :items="techDocItems" pickLabel="Подбор"
          @pick="showDocPicker = true" @remove="removeDoc" @removeBatch="removeDocBatch" />
      </div>

      <!-- Сертификаты -->
      <div :class="['mlf-panel', { 'mlf-panel--active': tab === 'certs' }]">
        <div class="mlf-cert-toolbar">
          <span class="mlf-section-label">Сертификаты</span>
          <button class="btn-new" @click="showCertForm = true">+ Новый</button>
        </div>
        <ChipList :items="certItems" pickLabel="Подбор"
          @pick="showCertPicker = true" @remove="removeCert" @removeBatch="removeCertBatch" />
      </div>

      <!-- Дополнительно -->
      <div :class="['mlf-panel', { 'mlf-panel--active': tab === 'extra' }]">
        <JsonFieldsEditor v-model="form.extra_params" label="Доп. параметры" />
      </div>
    </div>

    <!-- Пикеры -->
    <BasePicker :show="showDocPicker" title="Подбор техдокументации"
      :fetchFn="fetchMediaDocs" :filterDefs="mediaFilterDefs" :defaultFilters="{}"
      :preselected="techDocItems.map(i => i.id)"
      :columns="[{key:'code',label:'Код'},{key:'name',label:'Название'}]"
      @close="showDocPicker = false" @selected="onDocsSelected" />
    <BasePicker :show="showCertPicker" title="Подбор сертификатов"
      :fetchFn="fetchCerts" :filterDefs="certFilterDefs" :defaultFilters="{}"
      :preselected="certItems.map(i => i.id)"
      :columns="[{key:'code',label:'Код'},{key:'name',label:'Название'}]"
      @close="showCertPicker = false" @selected="onCertsSelected" />

    <CertEdit :show="showCertForm" :item="newCertPreset" :opts="certOpts"
      @saved="onCertSaved" @cancel="showCertForm = false" />

    <MediaUploadModal :show="showDocUpload" categoryCode="TECH_DOC"
      :brandId="form.brand_id" :equipmentTypeId="form.equipment_type_id"
      :brands="opts.brands" :equipmentTypes="opts.equipmentTypes"
      @close="showDocUpload = false" @uploaded="onDocUploaded" />
  </div>
  <Spinner v-else />
</template>

<script setup>
import { reactive, ref, watch, onMounted, computed } from 'vue'
import FkSelect from '@/shared/components/FkSelect.vue'
import BasePicker from '@/shared/components/BasePicker.vue'
import ChipList from '@/shared/components/ChipList.vue'
import Spinner from '@/shared/components/Spinner.vue'
import CertEdit from '@/apps/cert-docs/components/CertEdit.vue'
import MediaUploadModal from '@/shared/components/MediaUploadModal.vue'
import JsonFieldsEditor from '@/shared/components/JsonFieldsEditor.vue'
import api from '@/shared/api'
import { refsApi } from '../api'

const props = defineProps({
  item: { type: Object, default: null },
})

const tab = ref('main')
const ready = ref(false)
const showDocPicker = ref(false)
const showCertPicker = ref(false)
const showDocUpload = ref(false)
const techDocItems = ref([])
const certItems = ref([])
const showCertForm = ref(false)
const certVarieties = ref([])

const opts = reactive({
  producers: [], brands: [], equipmentTypes: [],
  imageGalleries: [],
})

const form = reactive({
  name: '', code: '', description: '', name_template: '', description_template: '',
  sorting_order: 0, is_active: true,
  equipment_type_id: null, producer_id: null, brand_id: null,
  image_gallery_id: null,
  extra_params: [],
})

function extractId(v) { return v && typeof v === 'object' ? v.id : v || null }

const certOpts = computed(() => ({
  varieties: certVarieties.value,
  brands: opts.brands,
  equipmentTypes: opts.equipmentTypes,
}))

const newCertPreset = computed(() => ({
  name: form.name || '',
  brand: opts.brands.find(b => b.id === form.brand_id) || null,
  equipment_types: opts.equipmentTypes.filter(e => e.id === form.equipment_type_id),
}))

watch(() => props.item, (val) => {
  if (val) {
    form.name = val.name || ''
    form.code = val.code || ''
    form.description = val.description || ''
    form.name_template = val.name_template || ''
    form.description_template = val.description_template || ''
    form.sorting_order = val.sorting_order || 0
    form.is_active = val.is_active !== false
    form.equipment_type_id = extractId(val.equipment_type)
    form.producer_id = extractId(val.producer)
    form.brand_id = extractId(val.brand)
    form.image_gallery_id = extractId(val.image_gallery)
    form.extra_params = Array.isArray(val.extra_params) ? val.extra_params : []
  } else {
    Object.assign(form, {
      name: '', code: '', description: '', name_template: '', description_template: '',
      sorting_order: 0, is_active: true,
      equipment_type_id: null, producer_id: null, brand_id: null,
      image_gallery_id: null,
      extra_params: [],
    })
  }
}, { immediate: true })

function normalizeItems(arr) {
  if (!arr || !arr.length) return []
  if (typeof arr[0] === 'object') {
    return arr.map(i => ({ id: i.id, code: i.code || '', name: i.name || '' }))
  }
  return arr.map(id => ({ id, code: '', name: '' }))
}

// Populate M2M items (tech_docs, cert_docs)
watch(() => props.item, (val) => {
  techDocItems.value = []
  certItems.value = []
  if (!val) return
  if (val.tech_docs) {
    const arr = Array.isArray(val.tech_docs) ? val.tech_docs : []
    if (arr.length && typeof arr[0] === 'object') techDocItems.value = normalizeItems(arr)
  }
  if (val.cert_docs) {
    const arr = Array.isArray(val.cert_docs) ? val.cert_docs : []
    if (arr.length && typeof arr[0] === 'object') certItems.value = normalizeItems(arr)
  }
}, { immediate: true })


function removeDoc(id) { techDocItems.value = techDocItems.value.filter(i => i.id !== id) }
function removeDocBatch(ids) { techDocItems.value = techDocItems.value.filter(i => !ids.includes(i.id)) }
function removeCert(id) { certItems.value = certItems.value.filter(i => i.id !== id) }
function removeCertBatch(ids) { certItems.value = certItems.value.filter(i => !ids.includes(i.id)) }

function onDocsSelected(items) { techDocItems.value = items }
function onCertsSelected(items) { certItems.value = items }

function onDocUploaded(item) {
  techDocItems.value.push({ id: item.id, code: item.code || '', name: item.name || '' })
}

function onCertSaved() {
  showCertForm.value = false
}

const mediaFilterDefs = [{ key: 'search', type: 'text', label: 'Поиск' }]
const certFilterDefs = [{ key: 'search', type: 'text', label: 'Поиск' }]

async function fetchMediaDocs(params) {
  const q = { model: 'media_library.MediaLibraryItem', fmt: 'compact', limit: params.limit || 25, offset: params.offset || 0 }
  if (params.search) q.search = params.search
  q.category__code = 'TECH_DOC'
  return api.get('/core/', { params: q })
}
async function fetchCerts(params) {
  const q = { model: 'cert_doc.CertData', fmt: 'compact', limit: params.limit || 25, offset: params.offset || 0 }
  if (params.search) q.search = params.search
  return api.get('/core/', { params: q })
}

function getFormData() {
  return {
    name: form.name, code: form.code || null,
    description: form.description,
    name_template: form.name_template || null,
    description_template: form.description_template || null,
    sorting_order: form.sorting_order,
    is_active: form.is_active,
    equipment_type_id: form.equipment_type_id || null,
    producer_id: form.producer_id || null,
    brand_id: form.brand_id || null,
    image_gallery_id: form.image_gallery_id || null,
    extra_params: form.extra_params,
    tech_docs: techDocItems.value.map(i => i.id),
    cert_docs: certItems.value.map(i => i.id),
  }
}

defineExpose({ getFormData })

onMounted(async () => {
  const [producers, brands, equipmentTypes, varieties, ig] = await Promise.all([
    refsApi.producers(), refsApi.brands(), refsApi.equipmentTypes(), refsApi.certVarieties(),
    api.get('/core/', { params: { model: 'media_library.ImageGallerySet', fmt: 'compact', limit: 200 } }).then(r => (r.data?.data || [])),
  ])
  opts.producers = producers
  opts.brands = brands
  opts.equipmentTypes = equipmentTypes
  certVarieties.value = varieties
  opts.imageGalleries = ig.map(g => ({ id: g.id, name: g.name || g.code || `#${g.id}` }))
  ready.value = true
})
</script>

<style scoped>
.mlf-grid { display: flex; flex-direction: column; gap: 10px; }
.mlf-tabs { display: flex; gap: 4px; margin-bottom: 4px; }
.mlf-tabs button { padding: 6px 18px; border: 1px solid #d1d5db; border-radius: 6px; background: #fff; cursor: pointer; font-size: 13px; transition: all .15s; }
.mlf-tabs button.act { background: #2563eb; color: #fff; border-color: #2563eb; }
.mlf-tabs button:hover:not(.act) { background: #f3f4f6; }
.mlf-panels { display: grid; grid-template-areas: "panel"; }
.mlf-panel { grid-area: panel; visibility: hidden; }
.mlf-panel--active { visibility: visible; }
.mlf-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.fg { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.fg.fw { grid-column: 1 / -1; }
.fg label { font-size: 13px; color: #374151; }
.field { padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; font-family: inherit; }
.field:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,.15); }
.chk { font-size: 13px; display: flex; align-items: center; gap: 6px; cursor: pointer; }
.mlf-cert-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.mlf-section-label { font-weight: 500; font-size: 13px; color: #374151; }
.btn-new { padding: 4px 14px; background: #2563eb; color: #fff; border: none; border-radius: 5px; font-size: 12px; cursor: pointer; }
.btn-new:hover { background: #1d4ed8; }
</style>