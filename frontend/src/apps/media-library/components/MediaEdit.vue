<template>
  <BaseModal :show="show" :title="'Редактировать: ' + (item?.name || '')" :closable="false" width="860px" @close="$emit('close')">
    <div v-if="item" class="edit-layout">
      <!-- Левая колонка: форма -->
      <div class="edit-left">
        <label>Название</label>
        <input v-model="form.name" class="field" />
        <label>Код</label>
        <input v-model="form.code" class="field" />
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
          <button class="btn-cancel" @click="$emit('close')">Отмена</button>
        </div>
        <div class="edit-actions-secondary">
          <button class="btn-copy" :disabled="copying" @click="doCopy">
            {{ copying ? 'Копирование...' : 'Копировать' }}
          </button>
          <button class="btn-preview" :disabled="recreating" @click="doRecreatePreview">
            {{ recreating ? 'Обновление...' : '🔄 Варианты' }}
          </button>
          <button class="btn-danger" :disabled="deleting" @click="doDelete">
            {{ deleting ? 'Удаление...' : 'Удалить' }}
          </button>
        </div>
      </div>

      <!-- Правая колонка: превью + варианты + редактор -->
      <div class="edit-right">
        <div class="edit-preview">
          <img v-if="isPreviewable(item)" :src="previewUrl(item.id)" class="preview-img" />
          <div v-else-if="!item?.has_file" class="preview-placeholder">
            <span class="preview-placeholder-icon">📁</span>
            <span class="preview-placeholder-text">{{ item.file_name || '—' }}</span>
          </div>
          <div v-else class="preview-placeholder">
            <span class="preview-placeholder-icon">{{ iconFor(item?.mime_type) }}</span>
            <span class="preview-placeholder-text">{{ item.file_name || '—' }}</span>
          </div>
          <a v-if="item?.has_file" :href="downloadUrl(item.id)" target="_blank" class="preview-open-link">Открыть в новом окне</a>
        </div>

        <MediaVariantsPreview :item="item" />

        <div v-if="isImageEditable(item)" class="image-editor-section">
          <button class="btn-crop-toggle" @click="showCropper = true">
            ✂️ Обрезать / убрать фон
          </button>
        </div>

        <!-- Модалка кроппера -->
        <div v-if="showCropper" class="cropper-overlay" @click.self="showCropper = false">
          <div class="cropper-modal">
            <div class="cropper-modal-header">
              <h3>✂️ Редактор изображения</h3>
              <button class="cropper-modal-close" @click="showCropper = false">✕</button>
            </div>
            <div class="cropper-modal-body">
              <ImageCropper
                :categoryCode="item.category?.code || ''"
                :initialUrl="previewUrl(item.id) + '?proxy=1'"
                @crop-complete="onCropComplete"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </BaseModal>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import BaseModal from '@/shared/components/BaseModal.vue'
import ImageCropper from '@/shared/components/ImageCropper.vue'
import MediaVariantsPreview from './MediaVariantsPreview.vue'
import mediaApi from '../api'

const props = defineProps({
  show: Boolean,
  item: { type: Object, default: null },
  categories: { type: Array, default: () => [] },
  brands: { type: Array, default: () => [] },
  equipmentTypes: { type: Array, default: () => [] },
})
const emit = defineEmits(['close', 'updated', 'deleted', 'copied'])

const form = reactive({
  name: '', code: '', category_id: null, brand_id: null, equipment_type_id: null,
  keywords: '', description: '',
  sorting_order: 0, is_public: true, is_active: true, is_default: false,
})
const newFile = ref(null)
const saving = ref(false)
const deleting = ref(false)
const copying = ref(false)
const recreating = ref(false)
const saveError = ref(null)
const showCropper = ref(false)

const IMAGE_CATEGORIES = ['PHOTO', 'PRODUCT_GALLERY']

function previewUrl(id) { return mediaApi.previewUrl(id) }
function downloadUrl(id) { return mediaApi.downloadUrl(id) }
function isImage(mime) { return mime && mime.startsWith('image/') }
function iconFor(mime) {
  if (!mime) return '📁'
  if (mime.startsWith('image/')) return '🖼️'
  if (mime.includes('pdf')) return '📄'
  return '📁'
}
function isPreviewable(item) {
  return item.has_file && (isImage(item.mime_type) || item.mime_type === 'application/pdf')
}
function isImageEditable(item) {
  if (!item.has_file || !isImage(item.mime_type)) return false
  const code = item.category?.code || ''
  return IMAGE_CATEGORIES.includes(code)
}

function extractId(value) {
  if (value === null || value === undefined) return null
  return typeof value === 'object' ? value.id : value
}

watch(() => props.item, (val) => {
  if (val) {
    form.name = val.name || ''
    form.code = val.code || ''
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
    showCropper.value = false
  }
}, { immediate: true })

function onFileChange(e) { newFile.value = e.target.files[0] || null }

async function onCropComplete(cropData) {
  // Обрезанное изображение → генерируем варианты, оригинал не трогаем
  showCropper.value = false
  saveError.value = null

  let dataUrl = null
  if (cropData.variants?.card) {
    dataUrl = cropData.variants.card['400']?.data || cropData.variants.card['800']?.data
  }
  if (!dataUrl && cropData.variants?.thumb) {
    dataUrl = cropData.variants.thumb['150']?.data || cropData.variants.thumb['80']?.data
  }
  if (!dataUrl && cropData.results?.md) {
    dataUrl = cropData.results.md.url
  }

  if (!dataUrl) {
    saveError.value = 'Не удалось получить обрезанное изображение'
    return
  }

  try {
    const resp = await fetch(dataUrl)
    const blob = await resp.blob()
    const ext = blob.type === 'image/webp' ? 'webp' : 'jpg'
    const file = new File([blob], `cropped_${Date.now()}.${ext}`, { type: blob.type })

    // Отправляем на сервер для генерации вариантов (оригинал media_file не меняется)
    const fd = new FormData()
    fd.append('file', file)
    const { data } = await mediaApi.regenerateVariants(props.item.id, fd)
    if (data.success) {
      emit('updated')  // обновит карточку и покажет новые варианты
    } else {
      saveError.value = data.message || 'Ошибка генерации вариантов'
    }
  } catch (e) {
    saveError.value = e.displayMessage || 'Ошибка сохранения обрезанного изображения'
    console.error('Crop variant generation failed:', e)
  }
}

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
      emit('updated')
    } else {
      saveError.value = data.message || 'Не удалось обновить варианты'
    }
  } catch (e) {
    saveError.value = e.displayMessage || 'Ошибка обновления вариантов'
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
.edit-layout {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
  max-height: 70vh; margin: -12px -12px;
}
.edit-left { display: flex; flex-direction: column; gap: 3px; overflow-y: auto; }
.edit-right {
  display: flex; flex-direction: column; gap: 6px;
  overflow-y: auto; border-left: 1px solid #e5e7eb; padding-left: 16px;
}
.edit-layout label { font-size: 12px; font-weight: 600; color: #374151; margin: 0; }
.field { padding: 4px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px; }
.edit-preview {
  text-align: center; padding: 6px; background: #f8fafc;
  border: 1px solid #e2e8f0; border-radius: 6px;
}
.preview-img { max-width: 100%; max-height: 160px; border-radius: 4px; object-fit: contain; display: block; margin: 0 auto 4px; }
.preview-open-link { font-size: 12px; color: #2563eb; text-decoration: none; }
.preview-open-link:hover { text-decoration: underline; }
.preview-placeholder {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 4px; padding: 12px;
}
.preview-placeholder-icon { font-size: 32px; }
.preview-placeholder-text { font-size: 12px; color: #6b7280; word-break: break-all; }
.form-row { display: flex; gap: 8px; flex-wrap: wrap; font-size: 12px; }
.form-row label { display: flex; align-items: center; gap: 3px; font-weight: 400; }
.edit-actions { display: flex; gap: 6px; margin-top: 4px; }
.edit-actions-secondary {
  display: flex; gap: 4px; margin-top: 2px; padding-top: 4px;
  border-top: 1px solid #e5e7eb; flex-wrap: wrap;
}
.btn-primary { padding: 5px 16px; background: #2563eb; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-copy { padding: 5px 10px; background: #8b5cf6; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }
.btn-copy:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-preview { padding: 5px 10px; background: #10b981; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }
.btn-preview:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger { padding: 5px 10px; background: #dc2626; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-cancel { padding: 5px 16px; background: #e5e7eb; color: #374151; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-crop-toggle {
  padding: 5px 10px; background: #f59e0b; color: #fff; border: none;
  border-radius: 4px; cursor: pointer; font-size: 12px; width: 100%;
}
.image-editor-section { margin: 4px 0; }
.cropper-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 2000;
  display: flex; align-items: center; justify-content: center;
}
.cropper-modal {
  background: #fff; border-radius: 8px; width: 95vw; max-width: 960px;
  max-height: 90vh; display: flex; flex-direction: column; overflow: hidden;
}
.cropper-modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 20px; border-bottom: 1px solid #e5e7eb; flex-shrink: 0;
}
.cropper-modal-header h3 { margin: 0; font-size: 16px; }
.cropper-modal-close {
  background: none; border: none; font-size: 22px; cursor: pointer; color: #6b7280;
}
.cropper-modal-body {
  padding: 16px; overflow-y: auto; flex: 1;
}
.error-msg { color: #dc2626; font-size: 12px; margin-top: 2px; }
</style>
