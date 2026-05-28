<!-- shared/components/MediaUploadModal.vue — модалка загрузки в медиатеку -->
<template>
  <BaseModal :show="show" :title="title" :closable="false" width="480px" @close="$emit('close')">
    <div class="mum-form" v-if="ready">
      <div class="mum-drop" :class="{ drag: dragging }"
        @dragover.prevent="dragging=true" @dragleave="dragging=false"
        @drop.prevent="onDrop" @click="fileInput?.click()">
        <span v-if="!file">Перетащите файл или кликните</span>
        <span v-else>{{ file.name }} ({{ formatSize(file.size) }})</span>
      </div>
      <input ref="fileInput" type="file" hidden @change="onFileSelect" />

      <div class="mum-fields">
        <input v-model="form.name" placeholder="Название *" class="field" />
        <select v-if="brands.length" v-model="form.brand_id" class="field">
          <option :value="null">Бренд (не указан)</option>
          <option v-for="b in brands" :key="b.id" :value="b.id">{{ b.name }}</option>
        </select>
        <select v-if="equipmentTypes.length" v-model="form.equipment_type_id" class="field">
          <option :value="null">Тип оборудования (не указан)</option>
          <option v-for="e in equipmentTypes" :key="e.id" :value="e.id">{{ e.name }}</option>
        </select>
      </div>

      <div v-if="error" class="mum-error">{{ error }}</div>

      <div class="mum-actions">
        <button class="btn-pri" :disabled="!canUpload || uploading" @click="doUpload">
          {{ uploading ? 'Загрузка...' : 'Загрузить' }}
        </button>
        <button class="btn-cancel" @click="$emit('close')">Отмена</button>
      </div>
    </div>
    <Spinner v-else />
  </BaseModal>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import BaseModal from '@/shared/components/BaseModal.vue'
import Spinner from '@/shared/components/Spinner.vue'
import api from '@/shared/api'
import mediaApi from '@/apps/media-library/api'

const props = defineProps({
  show: Boolean,
  categoryCode: { type: String, required: true },  // 'IMAGE' | 'TECH_DOC'
  brandId: { type: Number, default: null },
  equipmentTypeId: { type: Number, default: null },
  brands: { type: Array, default: () => [] },
  equipmentTypes: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'uploaded'])

const LABELS = { IMAGE: 'Загрузить изображение', TECH_DOC: 'Загрузить документацию' }
const title = computed(() => LABELS[props.categoryCode] || 'Загрузить в медиатеку')

const ready = ref(false)
const fileInput = ref(null)
const file = ref(null)
const dragging = ref(false)
const uploading = ref(false)
const error = ref(null)
const categoryId = ref(null)

const form = reactive({
  name: '',
  brand_id: null,
  equipment_type_id: null,
})

const canUpload = computed(() => file.value && form.name.trim() && categoryId.value)

watch(() => props.show, async (val) => {
  if (!val) return
  form.name = ''
  form.brand_id = props.brandId
  form.equipment_type_id = props.equipmentTypeId
  file.value = null
  error.value = null
})

onMounted(async () => {
  try {
    const r = await api.get('/core/', {
      params: { model: 'media_library.MediaCategory', fmt: 'compact', code: props.categoryCode },
    })
    const cat = Array.isArray(r.data?.data) ? r.data.data[0] : null
    if (cat) categoryId.value = cat.id
    else error.value = 'Категория не найдена: ' + props.categoryCode
  } catch {
    error.value = 'Не удалось загрузить категорию'
  }
  ready.value = true
})

function onDrop(e) { dragging.value = false; const f = e.dataTransfer.files[0]; if (f) file.value = f }
function onFileSelect(e) { const f = e.target.files[0]; if (f) file.value = f }

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

async function doUpload() {
  if (!canUpload.value) return
  uploading.value = true; error.value = null
  try {
    const fd = new FormData()
    fd.append('file', file.value)
    fd.append('name', form.name.trim())
    fd.append('category_id', categoryId.value)
    if (form.brand_id) fd.append('brand_id', form.brand_id)
    if (form.equipment_type_id) fd.append('equipment_type_id', form.equipment_type_id)

    const { data } = await mediaApi.upload(fd)
    emit('uploaded', data)
    emit('close')
  } catch (e) {
    error.value = e.displayMessage || e.response?.data?.error || 'Ошибка загрузки'
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.mum-form { font-size: 13px; }
.mum-drop {
  border: 2px dashed #d1d5db; border-radius: 8px; padding: 28px;
  text-align: center; cursor: pointer; color: #6b7280; font-size: 14px;
}
.mum-drop.drag { border-color: #2563eb; background: #eff6ff; }
.mum-fields { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }
.field { padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; }
.mum-error { color: #dc2626; font-size: 12px; margin-top: 8px; }
.mum-actions { display: flex; gap: 8px; margin-top: 14px; }
.btn-pri { padding: 7px 20px; background: #2563eb; color: #fff; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; }
.btn-pri:disabled { opacity: .5; cursor: not-allowed; }
.btn-cancel { padding: 7px 16px; background: #e5e7eb; color: #374151; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; }
</style>
