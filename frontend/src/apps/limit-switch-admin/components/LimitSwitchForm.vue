<!-- apps/limit-switch-admin/components/LimitSwitchForm.vue — форма LimitSwitchBox -->
<template>
  <div class="lsf-grid" v-if="ready">
    <!-- Основные -->
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
    <div class="fg fw"><M2MSelect v-model="form.additional_sensor_ids" :options="opts.sensors" label="Доп. датчики" placeholder="—" /></div>

    <!-- Взрывозащита -->
    <h4 class="lsf-sec">Взрывозащита и флаги</h4>
    <div class="fg fw"><M2MSelect v-model="form.exd_ids" :options="opts.exdOptions" label="Взрывозащита" placeholder="—" /></div>
    <div class="lsf-row-3">
      <label class="chk"><input type="checkbox" v-model="form.is_pneumatic" /> Пневматический</label>
      <label class="chk"><input type="checkbox" v-model="form.has_namur_interface" /> NAMUR интерфейс</label>
      <label class="chk"><input type="checkbox" v-model="form.has_visual_indicator" /> Визуальный индикатор</label>
    </div>

    <!-- Изображения и документация -->
    <h4 class="lsf-sec">Медиа</h4>
    <div class="lsf-media-row">
      <div class="lsf-media-col">
        <ChipList label="Изображения" :items="imageItems"
          pickLabel="Подбор"
          @pick="showImagePicker = true"
          @remove="removeImage"
          @removeBatch="removeImageBatch" />
      </div>
      <div class="lsf-media-col">
        <ChipList label="Техдокументация" :items="techDocItems"
          pickLabel="Подбор"
          @pick="showDocPicker = true"
          @remove="removeDoc"
          @removeBatch="removeDocBatch" />
      </div>
    </div>

    <BasePicker :show="showImagePicker" title="Подбор изображений"
      :fetchFn="fetchMediaItems"
      :filterDefs="mediaFilterDefs"
      :defaultFilters="mediaDefaultFilters"
      :preselected="imageItems.map(i => i.id)"
      :columns="[{key:'code',label:'Код'},{key:'name',label:'Название'}]"
      @close="showImagePicker = false" @selected="onImagesSelected" />
    <BasePicker :show="showDocPicker" title="Подбор техдокументации"
      :fetchFn="fetchTechDocItems"
      :filterDefs="mediaFilterDefs"
      :defaultFilters="mediaDefaultFilters"
      :preselected="techDocItems.map(i => i.id)"
      :columns="[{key:'code',label:'Код'},{key:'name',label:'Название'}]"
      @close="showDocPicker = false" @selected="onDocsSelected" />

    <!-- JSON -->
    <div class="fg fw"><label>Доп. параметры (JSON)</label><textarea v-model="form.extra_params_json" class="field" rows="3" placeholder='{}' /></div>
  </div>
  <Spinner v-else />
</template>

<script setup>
import { reactive, ref, watch, onMounted } from 'vue'
import FkSelect from '@/shared/components/FkSelect.vue'
import M2MSelect from '@/shared/components/M2MSelect.vue'
import BasePicker from '@/shared/components/BasePicker.vue'
import ChipList from '@/shared/components/ChipList.vue'
import Spinner from '@/shared/components/Spinner.vue'
import api from '@/shared/api'
import { refsApi } from '../api'

const props = defineProps({
  item: { type: Object, default: null },
})

const ready = ref(false)
const showImagePicker = ref(false)
const showDocPicker = ref(false)
const imageItems = ref([])
const techDocItems = ref([])
const opts = reactive({
  modelLines: [], bodies: [], sensorVarieties: [], sensors: [],
  ipOptions: [], exdOptions: [], bodyMaterials: [], specifiedMaterials: [],
})

const form = reactive({
  name: '', code: '', description: '', sorting_order: 0, is_active: true,
  model_line_id: null, body_id: null,
  sensor_variety_id: null, points: 2,
  primary_sensor_id: null, additional_sensor_ids: [],
  ip_id: null, exd_ids: [],
  work_temp_min: -40, work_temp_max: 120,
  body_material_id: null, body_material_specified_id: null,
  is_pneumatic: false, has_namur_interface: false, has_visual_indicator: false,
  extra_params_json: '{}',
})

function extractId(v) { return v && typeof v === 'object' ? v.id : v || null }
function extractIds(arr) { return (arr || []).map(v => typeof v === 'object' ? v.id : v) }

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
    form.additional_sensor_ids = extractIds(val.additional_sensor)
    form.ip_id = extractId(val.ip)
    form.exd_ids = extractIds(val.exd) || extractIds(val.exd_all) || []
    form.work_temp_min = val.work_temp_min ?? -40
    form.work_temp_max = val.work_temp_max ?? 120
    form.body_material_id = extractId(val.body_material)
    form.body_material_specified_id = extractId(val.body_material_specified)
    form.is_pneumatic = !!val.is_pneumatic
    form.has_namur_interface = !!val.has_namur_interface
    form.has_visual_indicator = !!val.has_visual_indicator
    form.extra_params_json = val.extra_params ? JSON.stringify(val.extra_params, null, 2) : '{}'
  } else {
    Object.assign(form, {
      name: '', code: '', description: '', sorting_order: 0, is_active: true,
      model_line_id: null, body_id: null,
      sensor_variety_id: null, points: 2,
      primary_sensor_id: null, additional_sensor_ids: [],
      ip_id: null, exd_ids: [],
      work_temp_min: -40, work_temp_max: 120,
      body_material_id: null, body_material_specified_id: null,
      is_pneumatic: false, has_namur_interface: false, has_visual_indicator: false,
      extra_params_json: '{}',
    })
  }
}, { immediate: true })

function getFormData() {
  let ep = {}
  try { ep = JSON.parse(form.extra_params_json || '{}') } catch {}
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
    additional_sensor: form.additional_sensor_ids,
    ip_id: form.ip_id || null,
    exd: form.exd_ids,
    images: imageItems.value.map(i => i.id),
    tech_docs: techDocItems.value.map(i => i.id),
    work_temp_min: form.work_temp_min,
    work_temp_max: form.work_temp_max,
    body_material_id: form.body_material_id || null,
    body_material_specified_id: form.body_material_specified_id || null,
    is_pneumatic: form.is_pneumatic,
    has_namur_interface: form.has_namur_interface,
    has_visual_indicator: form.has_visual_indicator,
    extra_params: ep,
  }
}

defineExpose({ getFormData })

function onImagesSelected(items) {
  imageItems.value = items
}
function onDocsSelected(items) {
  techDocItems.value = items
}
function removeImage(id) {
  imageItems.value = imageItems.value.filter(i => i.id !== id)
}
function removeDoc(id) {
  techDocItems.value = techDocItems.value.filter(i => i.id !== id)
}
function removeImageBatch(ids) {
  imageItems.value = imageItems.value.filter(i => !ids.includes(i.id))
}
function removeDocBatch(ids) {
  techDocItems.value = techDocItems.value.filter(i => !ids.includes(i.id))
}

// ── Media filter config + fetch functions ──
const mediaFilterDefs = [
  { key: 'search', type: 'text', label: 'Поиск' },
]

const mediaDefaultFilters = {}

async function fetchMediaItems(params) {
  const q = { model: 'media_library.MediaLibraryItem', fmt: 'compact', limit: params.limit || 25, offset: params.offset || 0 }
  if (params.search) q.search = params.search
  // Фильтр по категории IMAGE
  q.category__code = 'IMAGE'
  return api.get('/core/', { params: q })
}

async function fetchTechDocItems(params) {
  const q = { model: 'media_library.MediaLibraryItem', fmt: 'compact', limit: params.limit || 25, offset: params.offset || 0 }
  if (params.search) q.search = params.search
  q.category__code = 'TECH_DOC'
  return api.get('/core/', { params: q })
}

// Populate media items when editing
watch(() => props.item, async (val) => {
  imageItems.value = []
  techDocItems.value = []
  if (!val) return
  if (val.images) {
    const arr = Array.isArray(val.images) ? val.images : []
    if (arr.length && typeof arr[0] === 'object') {
      imageItems.value = arr.map(i => ({ id: i.id, code: i.code || '', name: i.name || '' }))
    } else if (arr.length && typeof arr[0] === 'number') {
      imageItems.value = await loadM2mDetails(arr, 'media_library.MediaLibraryItem')
    }
  }
  if (val.tech_docs) {
    const arr = Array.isArray(val.tech_docs) ? val.tech_docs : []
    if (arr.length && typeof arr[0] === 'object') {
      techDocItems.value = arr.map(d => ({ id: d.id, code: d.code || '', name: d.name || '' }))
    } else if (arr.length && typeof arr[0] === 'number') {
      techDocItems.value = await loadM2mDetails(arr, 'media_library.MediaLibraryItem')
    }
  }
}, { immediate: true })

async function loadM2mDetails(ids, model) {
  if (!ids || !ids.length) return []
  try {
    const res = await api.get('/pa-controls/m2m-items/', { params: { model, ids: ids.join(',') } })
    return (res.data?.data || []).map(i => ({ id: i.id, code: i.code || '', name: i.name || '' }))
  } catch { return ids.map(id => ({ id, code: '', name: '' })) }
}

onMounted(async () => {
  const [ml, bd, sv, sn, ip, ex, bm, sm] = await Promise.all([
    refsApi.modelLines(), refsApi.bodies(), refsApi.sensorVarieties(),
    refsApi.sensors(), refsApi.ipOptions(), refsApi.exdOptions(),
    refsApi.bodyMaterials(), refsApi.specifiedMaterials(),
  ])
  opts.modelLines = ml; opts.bodies = bd; opts.sensorVarieties = sv
  opts.sensors = sn; opts.ipOptions = ip; opts.exdOptions = ex
  opts.bodyMaterials = bm; opts.specifiedMaterials = sm
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
.lsf-media-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.lsf-media-col { display: flex; flex-direction: column; gap: 6px; }
</style>