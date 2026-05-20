<template>
  <BaseModal :show="show" :title="isNew ? 'Создать сертификат' : item?.name || 'Редактировать'"
    :closable="false" width="800px" @close="$emit('cancel')">

    <div class="cert-edit" v-if="show">
      <!-- Полноширинные поля -->
      <div class="fg fw"><label>Название *</label><input v-model="form.name" class="field" /></div>
      <div class="fg fw"><label>Описание</label><textarea v-model="form.description" class="field" rows="3" /></div>
      <div class="fg fw"><label>Код / Номер</label><input v-model="form.code" class="field" /></div>
      <div class="fg fw"><label>Кем выдан</label><input v-model="form.issued_by" class="field" /></div>

      <!-- Две колонки -->
      <div class="edit-grid">
        <div class="fg"><label>Тип сертификата *</label>
          <select v-model="form.cert_variety_id" class="field">
            <option :value="null">—</option>
            <option v-for="v in opts.varieties" :key="v.id" :value="v.id">{{ v.name || v.code }}</option>
          </select>
        </div>
        <div class="fg"><label>Бренд</label>
          <select v-model="form.brand_id" class="field">
            <option :value="null">—</option>
            <option v-for="b in opts.brands" :key="b.id" :value="b.id">{{ b.name }}</option>
          </select>
        </div>
        <div class="fg"><label>Действует с</label><input v-model="form.valid_from" type="date" class="field" /></div>
        <div class="fg"><label>Действует до</label><input v-model="form.valid_until" type="date" class="field" /></div>
        <div class="fg"><label>Ссылка (URL)</label><input v-model="form.public_url" class="field" /></div>
        <div class="fg"><label><input type="checkbox" v-model="form.is_active" /> Активен</label></div>
      </div>

      <!-- Блок медиафайла -->
      <div class="media-block">
        <div class="media-title">📎 Файл сертификата</div>

        <!-- Файл привязан -->
        <div v-if="linkedMedia" class="media-linked">
          <span>📄 {{ linkedMedia.title || linkedMedia.file_name }}</span>
          <button class="btn-sm" @click="$emit('view-media', linkedMedia.id)">👁️</button>
          <button class="btn-sm" @click="replaceMode = !replaceMode">{{ replaceMode ? 'Отмена' : '🔄' }}</button>
          <button class="btn-sm btn-unlink" @click="unlinkMedia">✕</button>
        </div>

        <!-- Замена файла -->
        <div v-if="linkedMedia && replaceMode" class="media-upload">
          <div class="drop-zone" :class="{ drag: dragging }"
            @dragover.prevent="dragging=true" @dragleave="dragging=false"
            @drop.prevent="onReplaceDrop" @click="fileInput?.click()">
            <span v-if="!uploadFile">Перетащите новый PDF</span>
            <span v-else>{{ uploadFile.name }}</span>
          </div>
          <input ref="fileInput" type="file" accept=".pdf" hidden @change="onFileSelect" />
          <button class="btn-sm btn-primary" :disabled="!canUpload || uploading" @click="doReplace">
            {{ uploading ? 'Замена...' : 'Заменить файл' }}
          </button>
        </div>

        <!-- Нет файла: загрузка или выбор из медиатеки -->
        <div v-if="!linkedMedia">
          <div class="media-upload">
            <div class="drop-zone" :class="{ drag: dragging }"
              @dragover.prevent="dragging=true" @dragleave="dragging=false"
              @drop.prevent="onDrop" @click="fileInput?.click()">
              <span v-if="!uploadFile">Перетащите PDF или кликните</span>
              <span v-else>{{ uploadFile.name }}</span>
            </div>
            <input ref="fileInput" type="file" accept=".pdf" hidden @change="onFileSelect" />
            <button class="btn-sm btn-primary" :disabled="!canUpload || uploading" @click="doUpload">
              {{ uploading ? 'Загрузка...' : 'Загрузить в медиатеку' }}
            </button>
          </div>

          <div class="media-pick">
            <div class="pick-label">или выберите существующий:</div>
            <div class="pick-filters">
              <input v-model="mediaSearch" placeholder="Ключевое слово..." class="pick-input"
                @input="onMediaSearch" @focus="showMediaList=true" />
              <select v-model="mediaEqType" class="pick-select" @change="onMediaSearch">
                <option :value="null">Тип оборуд.</option>
                <option v-for="e in opts.equipmentTypes" :key="e.id" :value="e.id">{{ e.name }}</option>
              </select>
              <select v-model="mediaBrand" class="pick-select" @change="onMediaSearch">
                <option :value="null">Бренд</option>
                <option v-for="b in opts.brands" :key="b.id" :value="b.id">{{ b.name }}</option>
              </select>
            </div>
            <div v-if="showMediaList && mediaResults.length" class="pick-drop">
              <div v-for="m in mediaResults" :key="m.id" class="pick-item" @click="pickMedia(m)">
                <span class="pi-name">📄 {{ m.title || m.file_name || m.id }}</span>
                <span class="pi-meta" v-if="m.brand || m.equipment_type">
                  {{ m.brand?.name || '' }}{{ m.brand && m.equipment_type ? ' · ' : '' }}{{ m.equipment_type?.name || '' }}
                </span>
              </div>
            </div>
            <div v-if="showMediaList && !mediaResults.length && !mediaLoading" class="pick-empty">
              {{ mediaSearch || mediaEqType || mediaBrand ? 'Ничего не найдено' : 'Начните поиск' }}
            </div>
          </div>
        </div>

        <div v-if="mediaError" class="error-msg">{{ mediaError }}</div>
      </div>

      <!-- Типы оборудования — в самом низу -->
      <div class="fg fw" style="margin-top:10px">
        <label>Типы оборудования</label>
        <div class="check-grid">
          <label v-for="e in opts.equipmentTypes" :key="e.id" class="chi">
            <input type="checkbox" :value="e.id" v-model="form.equipment_type_ids" />{{ e.name }}
          </label>
        </div>
      </div>

      <div v-if="formError" class="error-msg">{{ formError }}</div>

      <div class="actions">
        <button class="btn-primary" :disabled="saving" @click="save">
          {{ saving ? 'Сохранение...' : (isNew ? 'Создать' : 'Сохранить') }}
        </button>
        <button v-if="!isNew" class="btn-copy" :disabled="copying" @click="doCopy">
          {{ copying ? 'Копирование...' : 'Копировать' }}
        </button>
        <button v-if="!isNew" class="btn-danger" :disabled="deleting" @click="doDelete">
          {{ deleting ? 'Удаление...' : 'Удалить' }}
        </button>
        <button class="btn-cancel" @click="$emit('cancel')">Отмена</button>
      </div>
    </div>
  </BaseModal>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import BaseModal from '@/shared/components/BaseModal.vue'
import certApi from '../api'

const props = defineProps({
  show: Boolean,
  item: { type: Object, default: null },
  opts: { type: Object, default: () => ({ varieties:[], brands:[], equipmentTypes:[] }) },
})
const emit = defineEmits(['saved', 'deleted', 'cancel', 'view-media', 'copied'])

const isNew = computed(() => !props.item)

const form = reactive({
  name:'', code:'', description:'', cert_variety_id:null,
  brand_id:null, issued_by:'', public_url:'',
  valid_from:null, valid_until:null,
  equipment_type_ids:[], media_item_id:null,
  is_active:true,
})

const linkedMedia = ref(null)
const uploadFile = ref(null)
const dragging = ref(false)
const uploading = ref(false)
const replaceMode = ref(false)
const mediaError = ref(null)
const fileInput = ref(null)
const saving = ref(false)
const deleting = ref(false)
const copying = ref(false)
const formError = ref(null)

// Поиск по медиатеке
const mediaSearch = ref('')
const mediaEqType = ref(null)
const mediaBrand = ref(null)
const mediaResults = ref([])
const mediaLoading = ref(false)
const showMediaList = ref(false)

const canUpload = computed(() => uploadFile.value)

function buildMediaTitle() {
  const parts = []
  if (form.cert_variety_id) {
    const v = props.opts.varieties.find(x => x.id === form.cert_variety_id)
    if (v) parts.push(v.name || v.code)
  }
  const etNames = props.opts.equipmentTypes
    .filter(e => form.equipment_type_ids.includes(e.id))
    .map(e => e.name)
  if (etNames.length) parts.push(etNames.join(', '))
  if (form.name.trim()) parts.push(form.name.trim())
  return parts.join(' — ') || 'Сертификат'
}

function extractId(v) { return v && typeof v === 'object' ? v.id : v || null }

watch(() => props.item, (val) => {
  if (val) {
    form.name = val.name || ''
    form.code = val.code || ''
    form.description = val.description || ''
    form.cert_variety_id = extractId(val.cert_variety)
    form.brand_id = extractId(val.brand)
    form.issued_by = val.issued_by || ''
    form.public_url = val.public_url || ''
    form.valid_from = val.valid_from?.slice(0,10) || null
    form.valid_until = val.valid_until?.slice(0,10) || null
    form.equipment_type_ids = Array.isArray(val.equipment_types)
      ? val.equipment_types.map(e => typeof e==='object'?e.id:e) : []
    form.media_item_id = extractId(val.media_item)
    form.is_active = val.is_active !== false
    linkedMedia.value = val.media_item && typeof val.media_item === 'object' ? val.media_item : null
  } else {
    Object.assign(form, {
      name:'', code:'', description:'', cert_variety_id:null, brand_id:null,
      issued_by:'', public_url:'', valid_from:null, valid_until:null,
      equipment_type_ids:[], media_item_id:null, is_active:true,
    })
    linkedMedia.value = null
  }
  uploadFile.value = null; formError.value = null; mediaError.value = null
  replaceMode.value = false; mediaSearch.value = ''; mediaEqType.value = null; mediaBrand.value = null; mediaResults.value = []; showMediaList.value = false
}, { immediate: true })

function onDrop(e) { dragging.value=false; const f=e.dataTransfer.files[0]; if(f) uploadFile.value=f }
function onReplaceDrop(e) { replaceMode.value=true; onDrop(e) }
function onFileSelect(e) { const f=e.target.files[0]; if(f) uploadFile.value=f }

async function doUpload() {
  if(!uploadFile.value) return
  uploading.value=true; mediaError.value=null
  try {
    const fd = new FormData()
    fd.append('file', uploadFile.value)
    fd.append('title', buildMediaTitle())
    if (form.equipment_type_ids.length) fd.append('equipment_type_id', form.equipment_type_ids[0])
    if (form.brand_id) fd.append('brand_id', form.brand_id)
    const { data } = await certApi.uploadMedia(fd)
    linkedMedia.value = data
    form.media_item_id = data.id
    uploadFile.value = null
  } catch(e) {
    mediaError.value = e.displayMessage || 'Ошибка загрузки'
  } finally { uploading.value = false }
}

function unlinkMedia() {
  linkedMedia.value = null
  form.media_item_id = null
  replaceMode.value = false
}

async function doReplace() {
  if (!uploadFile.value || !linkedMedia.value) return
  uploading.value = true; mediaError.value = null
  try {
    const fd = new FormData()
    fd.append('file', uploadFile.value)
    await certApi.replaceMediaFile(linkedMedia.value.id, fd)
    linkedMedia.value = { ...linkedMedia.value, title: uploadFile.value.name }
    uploadFile.value = null
    replaceMode.value = false
  } catch (e) {
    mediaError.value = e.displayMessage || 'Ошибка замены файла'
  } finally { uploading.value = false }
}

// Поиск по медиатеке
let searchTimer = null
function onMediaSearch() {
  clearTimeout(searchTimer)
  showMediaList.value = true
  const q = mediaSearch.value.trim()
  if (!q && !mediaEqType.value && !mediaBrand.value) { mediaResults.value = []; return }
  searchTimer = setTimeout(async () => {
    mediaLoading.value = true
    try {
      mediaResults.value = await certApi.searchMedia({
        query: q,
        equipment_type_id: mediaEqType.value,
        brand_id: mediaBrand.value,
      })
    } catch { mediaResults.value = [] }
    finally { mediaLoading.value = false }
  }, 300)
}

function pickMedia(item) {
  linkedMedia.value = item
  form.media_item_id = item.id
  mediaSearch.value = ''
  mediaEqType.value = null
  mediaBrand.value = null
  mediaResults.value = []
  showMediaList.value = false
  uploadFile.value = null
}

async function save() {
  if(!form.name.trim() || !form.cert_variety_id) {
    formError.value = 'Название и тип сертификата обязательны'
    return
  }
  saving.value=true; formError.value=null
  try {
    const p = { ...form, equipment_type_ids: [...form.equipment_type_ids] }
    isNew.value ? await certApi.create(p) : await certApi.patch(props.item.id, p)
    emit('saved')
  } catch(e) {
    formError.value = e.displayMessage || 'Ошибка'
  } finally { saving.value=false }
}

async function doDelete() {
  if(!confirm('Удалить?')) return
  deleting.value=true; formError.value=null
  try { await certApi.remove(props.item.id); emit('deleted') }
  catch(e) { formError.value = e.displayMessage || e.response?.data?.error || 'Ошибка удаления' }
  finally { deleting.value=false }
}

async function doCopy() {
  copying.value=true; formError.value=null
  try {
    const { data } = await certApi.copy(props.item.id)
    emit('copied', data)
  } catch(e) { formError.value = e.displayMessage || 'Ошибка' }
  finally { copying.value=false }
}
</script>

<style scoped>
.cert-edit { font-size: 13px; }
.edit-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.fg { display: flex; flex-direction: column; gap: 3px; }
.fw { grid-column: 1 / -1; }
.fg label { font-weight: 500; font-size: 12px; color: #374151; }
.field { padding: 5px 8px; border:1px solid #d1d5db; border-radius:5px; font-size:13px; width:100%; box-sizing:border-box; }
.check-grid { display:grid; grid-template-columns:1fr 1fr; gap:2px; max-height:120px; overflow-y:auto; border:1px solid #d1d5db; border-radius:5px; padding:6px; }
.chi { display:flex; align-items:center; gap:3px; font-size:12px; }
.media-block { margin-top:14px; padding:12px; background:#f9fafb; border-radius:8px; border:1px solid #e5e7eb; }
.media-title { font-weight:600; margin-bottom:8px; }
.media-linked { display:flex; align-items:center; gap:8px; }
.drop-zone { border:2px dashed #d1d5db; border-radius:6px; padding:16px; text-align:center; cursor:pointer; font-size:13px; color:#6b7280; margin-bottom:6px; }
.drop-zone.drag { border-color:#2563eb; background:#eff6ff; }
.btn-sm { padding:3px 10px; border:1px solid #d1d5db; border-radius:4px; background:#fff; cursor:pointer; font-size:12px; }
.btn-sm.btn-primary { background:#2563eb; color:#fff; border-color:#2563eb; margin-top:4px; }
.btn-sm.btn-primary:disabled { opacity:.5; cursor:not-allowed; }
.btn-sm.btn-unlink { color:#dc2626; border-color:#fca5a5; }
.media-pick { margin-top: 10px; }
.pick-label { font-size: 11px; color: #6b7280; margin-bottom: 4px; }
.pick-filters { display: flex; gap: 4px; margin-bottom: 4px; }
.pick-input { flex: 1; padding: 5px 8px; border: 1px solid #d1d5db; border-radius: 5px; font-size: 13px; min-width: 0; }
.pick-select { padding: 5px 6px; border: 1px solid #d1d5db; border-radius: 5px; font-size: 12px; max-width: 130px; }
.pick-drop { max-height: 180px; overflow-y: auto; border: 1px solid #d1d5db; border-radius: 5px; margin-top: 2px; }
.pick-item { padding: 6px 10px; cursor: pointer; font-size: 12px; border-bottom: 1px solid #f3f4f6; display: flex; justify-content: space-between; align-items: center; }
.pick-item:hover { background: #f0f9ff; }
.pi-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pi-meta { font-size: 10px; color: #9ca3af; margin-left: 8px; white-space: nowrap; }
.pick-empty { padding: 8px 10px; font-size: 12px; color: #9ca3af; }
.actions { display:flex; gap:8px; margin-top:14px; }
.error-msg { color:#dc2626; font-size:12px; margin-top:6px; }
.btn-primary,.btn-danger,.btn-copy,.btn-cancel { padding:6px 16px; border:none; border-radius:6px; font-size:14px; cursor:pointer; }
.btn-primary { background:#2563eb; color:#fff; }
.btn-danger  { background:#dc2626; color:#fff; }
.btn-copy    { background:#059669; color:#fff; }
.btn-cancel  { background:#e5e7eb; color:#374151; }
.btn-primary:disabled,.btn-danger:disabled,.btn-copy:disabled { opacity:.5; cursor:not-allowed; }
</style>
