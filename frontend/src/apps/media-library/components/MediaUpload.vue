<template>
  <div class="upload-form">
    <h4>Загрузить файл</h4>

    <div
      class="drop-zone" :class="{ dragging }"
      @dragover.prevent="dragging = true"
      @dragleave="dragging = false"
      @drop.prevent="onDrop"
      @click="fileInput?.click()"
    >
      <div v-if="!file">Перетащите файл сюда или кликните для выбора</div>
      <div v-else>{{ file.name }} ({{ formatSize(file.size) }})</div>
    </div>
    <input ref="fileInput" type="file" hidden @change="onFileSelect" />

    <div class="form-fields">
      <input v-model="form.name" placeholder="Название *" class="field" />
      <input v-model="form.code" placeholder="Код" class="field" />
      <select v-model="form.category_id" class="field">
        <option :value="null">Категория *</option>
        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.icon }} {{ c.name }}</option>
      </select>
      <select v-model="form.brand_id" class="field">
        <option :value="null">Бренд (не указан)</option>
        <option v-for="b in brands" :key="b.id" :value="b.id">{{ b.name }}</option>
      </select>
      <select v-model="form.equipment_type_id" class="field">
        <option :value="null">Тип оборудования (не указан)</option>
        <option v-for="e in equipmentTypes" :key="e.id" :value="e.id">{{ e.name }}</option>
      </select>
      <input v-model="form.keywords" placeholder="Ключевые слова (через запятую)" class="field" />
      <textarea v-model="form.description" placeholder="Описание" class="field" rows="2" />
      <div class="form-row">
        <label><input type="checkbox" v-model="form.is_public" /> Публичный</label>
        <label><input type="checkbox" v-model="form.is_active" /> Активен</label>
      </div>
    </div>

    <div v-if="uploadError" class="upload-error">{{ uploadError }}</div>

    <button class="btn-primary" :disabled="!canUpload || uploading" @click="upload">
      {{ uploading ? 'Загрузка...' : 'Загрузить' }}
    </button>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import mediaApi from '../api'

const props = defineProps({
  categories: { type: Array, default: () => [] },
  brands: { type: Array, default: () => [] },
  equipmentTypes: { type: Array, default: () => [] },
})
const emit = defineEmits(['uploaded'])

const fileInput = ref(null)
const file = ref(null)
const dragging = ref(false)
const uploading = ref(false)
const uploadError = ref(null)

const form = reactive({
  name: '', code: '', category_id: null, brand_id: null, equipment_type_id: null,
  keywords: '', description: '',
  is_public: true, is_active: true,
})

const canUpload = computed(() => file.value && form.name.trim() && form.category_id)

function onDrop(e) { dragging.value = false; const f = e.dataTransfer.files[0]; if (f) file.value = f }
function onFileSelect(e) { const f = e.target.files[0]; if (f) file.value = f }

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

async function upload() {
  if (!canUpload.value) return
  uploading.value = true; uploadError.value = null
  try {
    const fd = new FormData()
    fd.append('file', file.value)
    fd.append('name', form.name.trim())
    if (form.code.trim()) fd.append('code', form.code.trim())
    fd.append('category_id', form.category_id)
    if (form.brand_id) fd.append('brand_id', form.brand_id)
    if (form.equipment_type_id) fd.append('equipment_type_id', form.equipment_type_id)
    if (form.keywords) fd.append('keywords', form.keywords)
    if (form.description) fd.append('description', form.description)
    fd.append('is_public', form.is_public)
    fd.append('is_active', form.is_active)

    await mediaApi.upload(fd)
    file.value = null
    Object.assign(form, { name: '', code: '', category_id: null, brand_id: null, equipment_type_id: null, keywords: '', description: '' })
    emit('uploaded')
  } catch (e) {
    uploadError.value = e.displayMessage || 'Ошибка загрузки'
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.upload-form { padding: 16px; }
.upload-form h4 { margin: 0 0 12px; }
.drop-zone {
  border: 2px dashed #d1d5db; border-radius: 8px; padding: 32px;
  text-align: center; cursor: pointer; color: #6b7280; font-size: 14px;
}
.drop-zone.dragging { border-color: #2563eb; background: #eff6ff; }
.form-fields { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }
.field { padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; }
.form-row { display: flex; gap: 16px; font-size: 13px; }
.form-row label { display: flex; align-items: center; gap: 4px; }
.upload-error { color: #dc2626; font-size: 13px; margin: 8px 0; }
.btn-primary {
  padding: 8px 24px; background: #2563eb; color: #fff;
  border: none; border-radius: 6px; font-size: 14px; cursor: pointer; margin-top: 8px;
}
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
