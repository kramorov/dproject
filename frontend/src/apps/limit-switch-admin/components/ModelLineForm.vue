<!-- apps/limit-switch-admin/components/ModelLineForm.vue — форма LimitSwitchModelLine с табами -->
<template>
  <div class="mlf-grid" v-if="ready">
    <!-- Табы -->
    <div class="mlf-tabs">
      <button :class="{ act: tab === 'main' }" @click="tab = 'main'">Основное</button>
      <button :class="{ act: tab === 'images' }" @click="tab = 'images'">Изображения</button>
      <button :class="{ act: tab === 'docs' }" @click="tab = 'docs'">Техдокументация</button>
      <button :class="{ act: tab === 'certs' }" @click="tab = 'certs'">Сертификаты</button>
    </div>

    <!-- Основное -->
    <template v-if="tab === 'main'">
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
      <div class="fg fw"><label>Доп. параметры (JSON)</label><textarea v-model="form.extra_params_json" class="field" rows="3" placeholder='{}' /></div>
      <label class="chk"><input type="checkbox" v-model="form.is_active" /> Активно</label>
    </template>

    <!-- Изображения -->
    <template v-if="tab === 'images'">
      <ChipList label="Изображения" :items="imageItems" pickLabel="Подбор"
        @pick="showImagePicker = true" @remove="removeImage" @removeBatch="removeImageBatch" />
    </template>

    <!-- Техдокументация -->
    <template v-if="tab === 'docs'">
      <ChipList label="Техдокументация" :items="techDocItems" pickLabel="Подбор"
        @pick="showDocPicker = true" @remove="removeDoc" @removeBatch="removeDocBatch" />
    </template>

    <!-- Сертификаты -->
    <template v-if="tab === 'certs'">
      <ChipList label="Сертификаты" :items="certItems" pickLabel="Подбор"
        @pick="showCertPicker = true" @remove="removeCert" @removeBatch="removeCertBatch" />
    </template>

    <!-- Пикеры (рендерятся всегда, вне табов) -->
    <BasePicker :show="showImagePicker" title="Подбор изображений"
      :fetchFn="fetchMediaImages" :filterDefs="mediaFilterDefs" :defaultFilters="{}"
      :preselected="imageItems.map(i => i.id)"
      :columns="[{key:'code',label:'Код'},{key:'name',label:'Название'}]"
      @close="showImagePicker = false" @selected="onImagesSelected" />
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
  </div>
  <Spinner v-else />
</template>

<script setup>
import { reactive, ref, watch, onMounted } from 'vue'
import FkSelect from '@/shared/components/FkSelect.vue'
import BasePicker from '@/shared/components/BasePicker.vue'
import ChipList from '@/shared/components/ChipList.vue'
import Spinner from '@/shared/components/Spinner.vue'
import api from '@/shared/api'
import { refsApi } from '../api'

const props = defineProps({
  item: { type: Object, default: null },
})

const tab = ref('main')
const ready = ref(false)
const showImagePicker = ref(false)
const showDocPicker = ref(false)
const showCertPicker = ref(false)
const imageItems = ref([])
const techDocItems = ref([])
const certItems = ref([])

const opts = reactive({
  producers: [],
  brands: [],
  equipmentTypes: [],
})

const form = reactive({
  name: '', code: '', description: '', name_template: '', description_template: '',
  sorting_order: 0, is_active: true,
  equipment_type_id: null, producer_id: null, brand_id: null,
  extra_params_json: '{}',
})

function extractId(v) { return v && typeof v === 'object' ? v.id : v || null }

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
    form.extra_params_json = val.extra_params ? JSON.stringify(val.extra_params, null, 2) : '{}'
  } else {
    Object.assign(form, {
      name: '', code: '', description: '', name_template: '', description_template: '',
      sorting_order: 0, is_active: true,
      equipment_type_id: null, producer_id: null, brand_id: null,
      extra_params_json: '{}',
    })
  }
}, { immediate: true })

// populate M2M items (supports both nested objects and ID arrays)
function normalizeItems(arr) {
  if (!arr || !arr.length) return []
  if (typeof arr[0] === 'object') {
    return arr.map(i => ({ id: i.id, code: i.code || '', name: i.name || '' }))
  }
  return arr.map(id => ({ id, code: '', name: '' }))
}
async function loadM2mDetails(ids, model) {
  if (!ids || !ids.length) return []
  try {
    const res = await api.get('/pa-controls/m2m-items/', { params: { model, ids: ids.join(',') } })
    return (res.data?.data || []).map(i => ({ id: i.id, code: i.code || '', name: i.name || '' }))
  } catch { return ids.map(id => ({ id, code: '', name: '' })) }
}

watch(() => props.item, async (val) => {
  imageItems.value = []
  techDocItems.value = []
  certItems.value = []
  if (!val) return
  if (val.images) {
    const arr = Array.isArray(val.images) ? val.images : []
    if (arr.length && typeof arr[0] === 'object') imageItems.value = normalizeItems(arr)
    else if (arr.length && typeof arr[0] === 'number') imageItems.value = await loadM2mDetails(arr, 'media_library.MediaLibraryItem')
  }
  if (val.tech_docs) {
    const arr = Array.isArray(val.tech_docs) ? val.tech_docs : []
    if (arr.length && typeof arr[0] === 'object') techDocItems.value = normalizeItems(arr)
    else if (arr.length && typeof arr[0] === 'number') techDocItems.value = await loadM2mDetails(arr, 'media_library.MediaLibraryItem')
  }
  if (val.cert_docs) {
    const arr = Array.isArray(val.cert_docs) ? val.cert_docs : []
    if (arr.length && typeof arr[0] === 'object') certItems.value = normalizeItems(arr)
    else if (arr.length && typeof arr[0] === 'number') certItems.value = await loadM2mDetails(arr, 'cert_doc.CertData')
  }
}, { immediate: true })


function removeImage(id) { imageItems.value = imageItems.value.filter(i => i.id !== id) }
function removeImageBatch(ids) { imageItems.value = imageItems.value.filter(i => !ids.includes(i.id)) }
function removeDoc(id) { techDocItems.value = techDocItems.value.filter(i => i.id !== id) }
function removeDocBatch(ids) { techDocItems.value = techDocItems.value.filter(i => !ids.includes(i.id)) }
function removeCert(id) { certItems.value = certItems.value.filter(i => i.id !== id) }
function removeCertBatch(ids) { certItems.value = certItems.value.filter(i => !ids.includes(i.id)) }

function onImagesSelected(items) { imageItems.value = items }
function onDocsSelected(items) { techDocItems.value = items }
function onCertsSelected(items) { certItems.value = items }

const mediaFilterDefs = [{ key: 'search', type: 'text', label: 'Поиск' }]
const certFilterDefs = [{ key: 'search', type: 'text', label: 'Поиск' }]

async function fetchMediaImages(params) {
  const q = { model: 'media_library.MediaLibraryItem', fmt: 'compact', limit: params.limit || 25, offset: params.offset || 0 }
  if (params.search) q.search = params.search
  q.category__code = 'IMAGE'
  return api.get('/core/', { params: q })
}
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
  let ep = {}
  try { ep = JSON.parse(form.extra_params_json || '{}') } catch {}
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
    extra_params: ep,
    images: imageItems.value.map(i => i.id),
    tech_docs: techDocItems.value.map(i => i.id),
    cert_docs: certItems.value.map(i => i.id),
  }
}

defineExpose({ getFormData })

onMounted(async () => {
  const [producers, brands, equipmentTypes] = await Promise.all([
    refsApi.producers(), refsApi.brands(), refsApi.equipmentTypes(),
  ])
  opts.producers = producers
  opts.brands = brands
  opts.equipmentTypes = equipmentTypes
  ready.value = true
})
</script>

<style scoped>
.mlf-grid { display: flex; flex-direction: column; gap: 10px; }
.mlf-tabs { display: flex; gap: 4px; margin-bottom: 4px; }
.mlf-tabs button { padding: 6px 18px; border: 1px solid #d1d5db; border-radius: 6px; background: #fff; cursor: pointer; font-size: 13px; transition: all .15s; }
.mlf-tabs button.act { background: #2563eb; color: #fff; border-color: #2563eb; }
.mlf-tabs button:hover:not(.act) { background: #f3f4f6; }
.mlf-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.fg { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.fg.fw { grid-column: 1 / -1; }
.fg label { font-size: 13px; color: #374151; }
.field { padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; font-family: inherit; }
.field:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,.15); }
.chk { font-size: 13px; display: flex; align-items: center; gap: 6px; cursor: pointer; }
.mlf-media-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
</style>
