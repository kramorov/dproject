<template>
  <BaseModal :show="show" :title="'Редактировать: ' + (item?.title || '')" :closable="false" @close="$emit('close')">
    <div v-if="item" class="edit-form">
      <div class="edit-preview">
        <img
          v-if="isPreviewable(item)"
          :src="previewUrl(item.id)" class="preview-img"
          @click.stop="$emit('preview', item)"
        />
        <div v-else class="preview-placeholder">📁 {{ item.file_name || '—' }}</div>
      </div>

      <label>Название</label>
      <input v-model="form.title" class="field" />
      <label>Категория</label>
      <select v-model="form.category_id" class="field">
        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.icon }} {{ c.name }}</option>
      </select>
      <label>Бренд</label>
      <select v-model="form.brand_id" class="field">
        <option :value="null">— Не указан —</option>
        <option v-for="b in brands" :key="b.id" :value="b.id">{{ b.name }}</option>
      </select>
      <label>Тип оборудования</label>
      <select v-model="form.equipment_type_id" class="field">
        <option :value="null">— Не указан —</option>
        <option v-for="e in equipmentTypes" :key="e.id" :value="e.id">{{ e.name }}</option>
      </select>
      <label>Ключевые слова</label>
      <input v-model="form.keywords" class="field" />
      <label>Описание</label>
      <textarea v-model="form.description" class="field" rows="2" />
      <label>Порядок сортировки</label>
      <input v-model.number="form.sorting_order" type="number" class="field" />
      <div class="form-row">
        <label><input type="checkbox" v-model="form.is_public" /> Публичный</label>
        <label><input type="checkbox" v-model="form.is_active" /> Активен</label>
        <label><input type="checkbox" v-model="form.is_default" /> По умолчанию</label>
      </div>

      <label>Заменить файл</label>
      <input type="file" @change="onFileChange" class="field" />

      <div v-if="saveError" class="error-msg">{{ saveError }}</div>

      <div class="edit-actions">
        <button class="btn-primary" :disabled="saving" @click="save">
          {{ saving ? 'Сохранение...' : 'Сохранить' }}
        </button>
        <button class="btn-copy" :disabled="copying" @click="doCopy">
          {{ copying ? 'Копирование...' : 'Копировать' }}
        </button>
        <button class="btn-preview" :disabled="recreating" @click="doRecreatePreview">
          {{ recreating ? 'Обновление...' : '🔄 Обновить превью' }}
        </button>
        <button class="btn-danger" :disabled="deleting" @click="doDelete">
          {{ deleting ? 'Удаление...' : 'Удалить' }}
        </button>
        <button class="btn-cancel" @click="$emit('close')">Отмена</button>
      </div>
    </div>
  </BaseModal>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import BaseModal from '@/shared/components/BaseModal.vue'
import mediaApi from '../api'

const props = defineProps({
  show: Boolean,
  item: { type: Object, default: null },
  categories: { type: Array, default: () => [] },
  brands: { type: Array, default: () => [] },
  equipmentTypes: { type: Array, default: () => [] },
})
const emit = defineEmits(['close', 'updated', 'deleted', 'preview', 'copied'])

const form = reactive({
  title: '', category_id: null, brand_id: null, equipment_type_id: null,
  keywords: '', description: '',
  sorting_order: 0, is_public: true, is_active: true, is_default: false,
})
const newFile = ref(null)
const saving = ref(false)
const deleting = ref(false)
const copying = ref(false)
const recreating = ref(false)
const saveError = ref(null)

function previewUrl(id) { return mediaApi.previewUrl(id) }
function isImage(mime) { return mime && mime.startsWith('image/') }
function isPreviewable(item) {
  return item.has_file && (isImage(item.mime_type) || item.mime_type === 'application/pdf')
}

function extractId(value) {
  if (value === null || value === undefined) return null
  return typeof value === 'object' ? value.id : value
}

watch(() => props.item, (val) => {
  if (val) {
    form.title = val.title || ''
    form.category_id = extractId(val.category)
    form.brand_id = extractId(val.brand)
    form.equipment_type_id = extractId(val.equipment_type)
    form.keywords = val.keywords || ''
    form.description = val.description || ''
    form.sorting_order = val.sorting_order || 0
    form.is_public = val.is_public !== false
    form.is_active = val.is_active !== false
    form.is_default = val.is_default || false
    newFile.value = null
    saveError.value = null
  }
}, { immediate: true })

function onFileChange(e) { newFile.value = e.target.files[0] || null }

async function save() {
  saving.value = true; saveError.value = null
  try {
    const payload = { ...form }
    if (newFile.value) {
      const fd = new FormData()
      Object.entries(payload).forEach(([k, v]) => {
        if (v !== null && v !== undefined && v !== '') fd.append(k, v)
      })
      fd.append('file', newFile.value)
      await mediaApi.replaceFile(props.item.id, fd)
    } else {
      await mediaApi.patch(props.item.id, payload)
    }
    emit('updated')
  } catch (e) {
    saveError.value = e.displayMessage || 'Ошибка сохранения'
  } finally {
    saving.value = false
  }
}

async function doDelete() {
  if (!confirm('Удалить безвозвратно?')) return
  deleting.value = true; saveError.value = null
  try {
    await mediaApi.remove(props.item.id)
    emit('deleted')
  } catch (e) {
    if (e.response?.status === 409 && e.response?.data?.references) {
      const refs = e.response.data.references.join('\n')
      if (confirm(`Объект используется:\n\n${refs}\n\nВсё равно удалить? Связи будут разорваны.`)) {
        try {
          await mediaApi.remove(props.item.id, true)
          emit('deleted')
        } catch (e2) {
          saveError.value = e2.displayMessage || 'Ошибка удаления'
        }
      }
    } else {
      saveError.value = e.displayMessage || 'Ошибка удаления'
    }
  } finally {
    deleting.value = false
  }
}

async function doRecreatePreview() {
  recreating.value = true; saveError.value = null
  try {
    const { data } = await mediaApi.recreatePreview(props.item.id)
    if (data.success) {
      emit('updated')  // перечитает список и обновит preview URL
    } else {
      saveError.value = data.message || 'Не удалось обновить превью'
    }
  } catch (e) {
    saveError.value = e.displayMessage || 'Ошибка обновления превью'
  } finally {
    recreating.value = false
  }
}

async function doCopy() {
  copying.value = true; saveError.value = null
  try {
    const { data } = await mediaApi.copy(props.item.id)
    emit('copied', data)
  } catch (e) {
    saveError.value = e.displayMessage || 'Ошибка копирования'
  } finally {
    copying.value = false
  }
}
</script>

<style scoped>
.edit-form { display: flex; flex-direction: column; gap: 8px; font-size: 14px; }
.edit-form label { font-weight: 500; margin-top: 4px; }
.edit-preview {
  width: 100%; height: 150px; background: #f9fafb;
  border-radius: 6px; display: flex; align-items: center; justify-content: center;
  overflow: hidden; margin-bottom: 8px;
}
.preview-img { max-width: 100%; max-height: 100%; object-fit: contain; }
.preview-placeholder { font-size: 32px; color: #9ca3af; }
.field { padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; }
.form-row { display: flex; gap: 16px; font-size: 13px; flex-wrap: wrap; }
.form-row label { display: flex; align-items: center; gap: 4px; margin: 0; }
.edit-actions { display: flex; gap: 8px; margin-top: 12px; }
.error-msg { color: #dc2626; font-size: 13px; }
.btn-primary, .btn-danger, .btn-copy, .btn-cancel {
  padding: 6px 16px; border: none; border-radius: 6px; font-size: 14px; cursor: pointer;
}
.btn-primary { background: #2563eb; color: #fff; }
.btn-danger  { background: #dc2626; color: #fff; }
.btn-copy    { background: #059669; color: #fff; }
.btn-preview { background: #d97706; color: #fff; }
.btn-cancel  { background: #e5e7eb; color: #374151; }
.btn-primary:disabled, .btn-danger:disabled, .btn-copy:disabled, .btn-preview:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
