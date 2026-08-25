<!-- apps/limit-switch-admin/components/LimitSwitchForm.vue — форма LimitSwitchBox с табами -->
<template>
  <div class="lsf-grid" v-if="ready">
    <!-- Табы -->
    <div class="lsf-tabs">
      <button :class="{ act: tab === 'main' }" @click="tab = 'main'">Основное</button>
      <button :class="{ act: tab === 'gallery' }" @click="tab = 'gallery'">Галерея</button>
      <button :class="{ act: tab === 'docs' }" @click="tab = 'docs'">Техдокументация</button>
      <button :class="{ act: tab === 'extra' }" @click="tab = 'extra'">Дополнительно</button>
    </div>

    <div class="lsf-panels">
      <!-- Основное -->
      <div :class="['lsf-panel', { 'lsf-panel--active': tab === 'main' }]">
    <div class="fg fw"><label>Название *</label><input v-model="form.name" class="field" /></div>
    <div class="fg fw"><label>Описание</label><textarea v-model="form.description" class="field" rows="2" /></div>
    <div class="lsf-row-3">
      <div class="fg"><label>Код</label><input v-model="form.code" class="field" /></div>
      <div class="fg"><label>Сортировка</label><input v-model.number="form.sorting_order" type="number" class="field" /></div>
      <div class="fg"><label>Активно</label><label class="chk" style="margin-top:6px"><input type="checkbox" v-model="form.is_active" /> Да</label></div>
    </div>

    <!-- Серия и корпус -->
    <div class="lsf-row">
      <div class="fg"><FkSelect v-model="form.model_line_id" :options="opts.modelLines" label="Серия *" placeholder="Выберите серию" /></div>
      <div class="fg"><FkSelect v-model="form.body_id" :options="opts.bodies" label="Корпус" placeholder="—" /></div>
    </div>

    <!-- Характеристики -->
    <h4 class="lsf-sec">Характеристики</h4>
    <div class="lsf-row">
      <div class="fg"><FkSelect v-model="form.sensor_variety_id" :options="opts.sensorVarieties" label="Тип сенсора" placeholder="—" /></div>
      <div class="fg">
        <label>Кол-во датчиков</label>
        <select v-model.number="form.points" class="field">
          <option :value="1">1 датчик</option>
          <option :value="2">2 датчика</option>
          <option :value="3">3 датчика</option>
          <option :value="4">4 датчика</option>
        </select>
      </div>
    </div>
    <div class="lsf-row">
      <div class="fg"><FkSelect v-model="form.ip_id" :options="opts.ipOptions" label="IP" placeholder="—" /></div>
      <div class="fg"><FkSelect v-model="form.body_material_id" :options="opts.bodyMaterials" label="Материал корпуса" placeholder="—" /></div>
      <div class="fg"><FkSelect v-model="form.body_material_specified_id" :options="opts.specifiedMaterials" label="Материал (уточн.)" placeholder="—" /></div>
    </div>
    <div class="lsf-row">
      <div class="fg"><label>Т раб. мин, °С</label><input v-model.number="form.work_temp_min" type="number" class="field" /></div>
      <div class="fg"><label>Т раб. макс, °С</label><input v-model.number="form.work_temp_max" type="number" class="field" /></div>
    </div>

    <!-- Датчики -->
    <h4 class="lsf-sec">Датчики</h4>
    <div class="lsf-row">
      <div class="fg"><FkSelect v-model="form.primary_sensor_id" :options="opts.sensors" label="Основной датчик" placeholder="—" /></div>
    </div>
    <div class="fg fw"><FkSelect v-model="form.signal_profile_id" :options="signalProfileOptions" label="Профиль сигналов" placeholder="—" /></div>
    <div v-if="selectedSignalProfile" class="lsf-profile">
      <div class="lsf-profile-head">
        {{ selectedSignalProfile.name }}
        <span class="lsf-profile-code">{{ selectedSignalProfile.code }}</span>
      </div>
      <div v-if="selectedSignalProfile.entries && selectedSignalProfile.entries.length" class="lsf-profile-entries">
        <div v-for="(e, i) in selectedSignalProfile.entries" :key="i" class="lsf-profile-row">
          <span class="lsf-role">{{ e.role }}</span>
          <span class="lsf-dir" :class="'dir-' + e.direction">{{ e.direction === 'input' ? 'Вход' : e.direction === 'output' ? 'Выход' : e.direction === 'bidirectional' ? 'Вх/Вых' : e.direction }}</span>
          <span class="lsf-comp">{{ e.component }}</span>
        </div>
      </div>
      <div v-else class="lsf-empty">Нет записей в профиле</div>
    </div>

    <!-- Взрывозащита -->
    <h4 class="lsf-sec">Взрывозащита и флаги</h4>
    <M2MDualList v-model="form.exd_ids" :options="opts.exdOptions" label="Взрывозащита" />
    <div class="lsf-row-3">
      <label class="chk"><input type="checkbox" v-model="form.is_pneumatic" /> Пневматический</label>
      <label class="chk"><input type="checkbox" v-model="form.has_namur_interface" /> NAMUR интерфейс</label>
      <div class="fg"><FkSelect v-model="form.visual_indicator_type_id" :options="opts.visualIndicators" label="Вид визуального индикатора" placeholder="—" /></div>
    </div>
      </div>

      <!-- Галерея -->
      <div :class="['lsf-panel', { 'lsf-panel--active': tab === 'gallery' }]">
        <div class="fg"><FkSelect v-model="form.image_gallery_id" :options="opts.imageGalleries" label="Набор изображений" placeholder="—" /></div>
      </div>

      <!-- Техдокументация -->
      <div :class="['lsf-panel', { 'lsf-panel--active': tab === 'docs' }]">
        <div class="lsf-media-toolbar">
          <span class="lsf-media-label">Техдокументация</span>
          <button class="btn-new" @click="showDocUpload = true">+ Новый</button>
        </div>
        <ChipList :items="techDocItems" pickLabel="Подбор"
          @pick="showDocPicker = true" @remove="removeDoc" @removeBatch="removeDocBatch" />
      </div>

      <!-- Дополнительно -->
      <div :class="['lsf-panel', { 'lsf-panel--active': tab === 'extra' }]">
        <JsonFieldsEditor v-model="form.extra_params" label="Доп. параметры" />
      </div>
    </div>

    <BasePicker :show="showDocPicker" title="Подбор техдокументации"
      :fetchFn="fetchTechDocItems"
      :filterDefs="mediaFilterDefs"
      :defaultFilters="mediaDefaultFilters"
      :preselected="techDocItems.map(i => i.id)"
      :columns="[{key:'code',label:'Код'},{key:'name',label:'Название'}]"
      @close="showDocPicker = false" @selected="onDocsSelected" />

    <MediaUploadModal :show="showDocUpload" categoryCode="TECH_DOC"
      @close="showDocUpload = false" @uploaded="onDocUploaded" />

  </div>
  <Spinner v-else />
</template>

<script setup>
import { reactive, ref, watch, onMounted, computed } from 'vue'
import FkSelect from '@/shared/components/FkSelect.vue'
import M2MDualList from '@/shared/components/M2MDualList.vue'
import JsonFieldsEditor from '@/shared/components/JsonFieldsEditor.vue'
import BasePicker from '@/shared/components/BasePicker.vue'
import ChipList from '@/shared/components/ChipList.vue'
import Spinner from '@/shared/components/Spinner.vue'
import MediaUploadModal from '@/shared/components/MediaUploadModal.vue'
import api from '@/shared/api'
import { refsApi } from '../api'

const props = defineProps({
  item: { type: Object, default: null },
})

const tab = ref('main')
const ready = ref(false)
const showDocPicker = ref(false)
const showDocUpload = ref(false)
const techDocItems = ref([])
const opts = reactive({
  modelLines: [], bodies: [], sensorVarieties: [], sensors: [],
  ipOptions: [], exdOptions: [], bodyMaterials: [], specifiedMaterials: [],
  imageGalleries: [], signalProfiles: [], visualIndicators: [],
})

const form = reactive({
  name: '', code: '', description: '', sorting_order: 0, is_active: true,
  model_line_id: null, body_id: null,
  sensor_variety_id: null, points: 2,
  primary_sensor_id: null, signal_profile_id: null,
  ip_id: null, exd_ids: [],
  work_temp_min: -40, work_temp_max: 120,
  body_material_id: null, body_material_specified_id: null,
  is_pneumatic: false, has_namur_interface: false,
  visual_indicator_type_id: null,
  image_gallery_id: null,
  extra_params: [],
})

function extractId(v) { return v && typeof v === 'object' ? v.id : v || null }
function extractIds(arr) { return (arr || []).map(v => typeof v === 'object' ? v.id : v) }

const signalProfileOptions = computed(() =>
  opts.signalProfiles.map(p => ({ id: p.id, name: p.name }))
)
const selectedSignalProfile = computed(() =>
  opts.signalProfiles.find(p => p.id === form.signal_profile_id) || null
)

watch(() => props.item, (val) => {
  if (val) {
    form.name = val.name || ''
    form.code = val.code || ''
    form.description = val.description || ''
    form.sorting_order = val.sorting_order || 0
    form.is_active = val.is_active !== false
    form.model_line_id = extractId(val.model_line)
    form.body_id = extractId(val.body)
    form.sensor_variety_id = extractId(val.sensor_variety)
    form.points = val.points || 2
    form.primary_sensor_id = extractId(val.primary_sensor)
    form.signal_profile_id = extractId(val.signal_profile)
    form.ip_id = extractId(val.ip)
    form.exd_ids = extractIds(val.exd) || []
    form.work_temp_min = val.work_temp_min ?? -40
    form.work_temp_max = val.work_temp_max ?? 120
    form.body_material_id = extractId(val.body_material)
    form.body_material_specified_id = extractId(val.body_material_specified)
    form.is_pneumatic = !!val.is_pneumatic
    form.has_namur_interface = !!val.has_namur_interface
    form.visual_indicator_type_id = extractId(val.visual_indicator_type)
    form.image_gallery_id = extractId(val.image_gallery)
    form.extra_params = Array.isArray(val.extra_params) ? val.extra_params : []
  } else {
    Object.assign(form, {
      name: '', code: '', description: '', sorting_order: 0, is_active: true,
      model_line_id: null, body_id: null,
      sensor_variety_id: null, points: 2,
      primary_sensor_id: null, signal_profile_id: null,
      ip_id: null, exd_ids: [],
      work_temp_min: -40, work_temp_max: 120,
      body_material_id: null, body_material_specified_id: null,
      is_pneumatic: false, has_namur_interface: false,
      visual_indicator_type_id: null,
      image_gallery_id: null,
      extra_params: [],
    })
  }
}, { immediate: true })

function getFormData() {
    return {
    name: form.name,
    code: form.code || null,
    description: form.description || '',
    sorting_order: form.sorting_order,
    is_active: form.is_active,
    model_line_id: form.model_line_id || null,
    body_id: form.body_id || null,
    sensor_variety_id: form.sensor_variety_id || null,
    points: form.points,
    primary_sensor_id: form.primary_sensor_id || null,
    signal_profile_id: form.signal_profile_id || null,
    ip_id: form.ip_id || null,
    exd: form.exd_ids,
    image_gallery_id: form.image_gallery_id || null,
    tech_docs: techDocItems.value.map(i => i.id),
    work_temp_min: form.work_temp_min,
    work_temp_max: form.work_temp_max,
    body_material_id: form.body_material_id || null,
    body_material_specified_id: form.body_material_specified_id || null,
    is_pneumatic: form.is_pneumatic,
    has_namur_interface: form.has_namur_interface,
    visual_indicator_type_id: form.visual_indicator_type_id || null,
    extra_params: form.extra_params,
  }
}

defineExpose({ getFormData })

function onDocsSelected(items) {
  techDocItems.value = items
}

function onDocUploaded(item) {
  techDocItems.value.push({ id: item.id, code: item.code || '', name: item.name || '' })
}

function removeDoc(id) {
  techDocItems.value = techDocItems.value.filter(i => i.id !== id)
}
function removeDocBatch(ids) {
  techDocItems.value = techDocItems.value.filter(i => !ids.includes(i.id))
}

const mediaFilterDefs = [{ key: 'search', type: 'text', label: 'Поиск' }]
const mediaDefaultFilters = {}

async function fetchTechDocItems(params) {
  const q = { model: 'media_library.MediaLibraryItem', fmt: 'compact', limit: params.limit || 25, offset: params.offset || 0 }
  if (params.search) q.search = params.search
  q.category__code = 'TECH_DOC'
  return api.get('/core/', { params: q })
}

// Populate tech_docs when editing
watch(() => props.item, (val) => {
  techDocItems.value = []
  if (!val) return
  if (val.tech_docs) {
    const arr = Array.isArray(val.tech_docs) ? val.tech_docs : []
    if (arr.length && typeof arr[0] === 'object') {
      techDocItems.value = arr.map(d => ({ id: d.id, code: d.code || '', name: d.name || '' }))
    }
  }
}, { immediate: true })

onMounted(async () => {
  const [ml, bd, sv, sn, ip, ex, bm, sm, ig, vi] = await Promise.all([
    refsApi.modelLines(), refsApi.bodies(), refsApi.sensorVarieties(),
    refsApi.sensors(), refsApi.ipOptions(), refsApi.exdOptions(),
    refsApi.bodyMaterials(), refsApi.specifiedMaterials(),
    api.get('/core/', { params: { model: 'media_library.ImageGallerySet', fmt: 'compact', limit: 200 } }).then(r => (r.data?.data || [])),
    refsApi.visualIndicators(),
  ])
  opts.modelLines = ml; opts.bodies = bd; opts.sensorVarieties = sv
  opts.sensors = sn; opts.ipOptions = ip; opts.exdOptions = ex
  opts.bodyMaterials = bm; opts.specifiedMaterials = sm
  opts.imageGalleries = ig.map(g => ({ id: g.id, name: g.name || g.code || `#${g.id}` }))
  opts.visualIndicators = vi
  try {
    const sp = await api.get('/pa-controls/signal-profiles/')
    opts.signalProfiles = Array.isArray(sp.data) ? sp.data : (sp.data?.data || [])
  } catch (e) { opts.signalProfiles = [] }
  ready.value = true
})
</script>

<style scoped>
.lsf-grid { display: flex; flex-direction: column; gap: 10px; }
.lsf-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.lsf-row-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; align-items: end; }
.fg { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.fg.fw { grid-column: 1 / -1; }
.fg label { font-size: 13px; color: #374151; }
.field { padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; font-family: inherit; }
.field:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,.15); }
.chk { font-size: 13px; display: flex; align-items: center; gap: 6px; cursor: pointer; }
.lsf-sec { margin: 4px 0 2px; font-size: 14px; color: #374151; border-bottom: 1px solid #e5e7eb; padding-bottom: 4px; }
.lsf-tabs { display: flex; gap: 4px; margin-bottom: 8px; }
.lsf-tabs button { padding: 6px 18px; border: 1px solid #d1d5db; border-radius: 6px; background: #fff; cursor: pointer; font-size: 13px; transition: all .15s; }
.lsf-tabs button.act { background: #2563eb; color: #fff; border-color: #2563eb; }
.lsf-tabs button:hover:not(.act) { background: #f3f4f6; }
.lsf-panels { display: grid; grid-template-areas: "panel"; }
.lsf-panel { grid-area: panel; visibility: hidden; }
.lsf-panel--active { visibility: visible; }
.lsf-media-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.lsf-media-label { font-weight: 500; font-size: 13px; color: #374151; }
.btn-new { padding: 4px 14px; background: #2563eb; color: #fff; border: none; border-radius: 5px; font-size: 12px; cursor: pointer; }
.btn-new:hover { background: #1d4ed8; }
.lsf-profile { border: 1px solid #e5e7eb; border-radius: 6px; padding: 8px 10px; background: #f9fafb; }
.lsf-profile-head { font-size: 13px; font-weight: 600; color: #1f2937; display: flex; align-items: center; gap: 8px; }
.lsf-profile-code { font-size: 11px; color: #6b7280; font-weight: 400; }
.lsf-profile-entries { margin-top: 6px; display: flex; flex-direction: column; gap: 4px; }
.lsf-profile-row { display: grid; grid-template-columns: minmax(0,1fr) auto minmax(0,1.6fr); gap: 8px; font-size: 12px; align-items: baseline; }
.lsf-role { color: #374151; }
.lsf-comp { color: #6b7280; }
.lsf-dir { font-size: 10px; padding: 1px 6px; border-radius: 10px; background: #e5e7eb; color: #374151; white-space: nowrap; }
.lsf-dir.dir-output { background: #dbeafe; color: #1d4ed8; }
.lsf-dir.dir-input { background: #fef3c7; color: #92400e; }
.lsf-dir.dir-bidirectional { background: #ede9fe; color: #5b21b6; }
.lsf-empty { font-size: 12px; color: #9ca3af; margin-top: 4px; }
</style>