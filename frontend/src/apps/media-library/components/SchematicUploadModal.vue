<!-- apps/media-library/components/SchematicUploadModal.vue -->
<template>
  <BaseModal :show="show" title="📐 Загрузить схему подключения" :closable="false" width="700px" @close="$emit('close')">
    <div class="sum-body" v-if="!uploading">
      <!-- Шаг 1: выбор файла -->
      <div class="sum-step" v-if="!previewUrl">
        <div class="sum-drop"
          @dragover.prevent @drop.prevent="onDrop"
          @click="fileInput?.click()">
          <span v-if="!file">📁 Выбрать файл (PDF, JPG, PNG)</span>
          <span v-else>{{ file.name }} ({{ fmtSize(file.size) }})</span>
        </div>
        <input ref="fileInput" type="file" accept=".pdf,.jpg,.jpeg,.png" hidden @change="onFileSelect" />
        <p class="sum-hint" v-if="file">Загружается...</p>
      </div>

      <!-- Шаг 2: превью + выделение кода -->
      <div class="sum-step" v-else>
        <div class="sum-preview-wrap">
          <div class="sum-preview-inner" :style="{ position: 'relative', display: 'inline-block' }">
            <img :src="previewUrl" class="sum-preview-img" @load="onImgLoad" ref="previewImg" />

            <!-- Рамка выделения кода -->
            <div
              v-if="codeRegionActive"
              class="sum-code-region"
              :style="regionStyle"
              @mousedown="startDrag"
            >
              <div class="sum-handle br" @mousedown.stop="startResize($event, 'br')"></div>
            </div>
          </div>
        </div>

        <div class="sum-code-area">
          <div class="sum-code-header">
            <strong>Код схемы</strong>
            <span class="sum-hint">(правый нижний угол)</span>
          </div>

          <!-- Кропнутая область кода, если выделена -->
          <div v-if="codeCropUrl" class="sum-code-crop">
            <img :src="codeCropUrl" class="sum-code-crop-img" />
          </div>

          <div class="sum-code-actions">
            <button class="btn-sm" @click="toggleCodeRegion" :class="{ active: codeRegionActive }">
              {{ codeRegionActive ? '✓ Область выбрана' : '🖱 Выделить область кода' }}
            </button>
            <button v-if="codeRegionActive" class="btn-sm btn-reset" @click="resetCodeRegion">✕ Сбросить</button>
          </div>

          <input
            v-model="form.code"
            class="sum-code-input"
            placeholder="Введите код схемы (с нижнего правого угла)"
            :class="{ filled: form.code }"
          />
        </div>

        <!-- Автозаполненные поля -->
        <div class="sum-meta">
          <div class="sum-meta-row">
            <label>Название</label>
            <input v-model="form.name" class="field" />
          </div>
          <div class="sum-meta-row">
            <label>Ключевые слова</label>
            <input v-model="form.keywords" class="field" />
          </div>
          <div class="sum-meta-row sum-meta-readonly">
            <label>Категория</label>
            <span class="readonly-val">🔌 Схема</span>
          </div>
          <div class="sum-meta-row sum-meta-readonly">
            <label>Бренд</label>
            <span class="readonly-val">Архимед</span>
          </div>
          <div class="sum-meta-row sum-meta-readonly">
            <label>Тип оборудования</label>
            <span class="readonly-val">Электропривод</span>
          </div>
        </div>
      </div>

      <div v-if="error" class="sum-error">{{ error }}</div>

      <div class="sum-actions" v-if="previewUrl">
        <button class="btn-pri" :disabled="!canSubmit || submitting" @click="doSubmit">
          {{ submitting ? 'Создание...' : '📤 Создать запись' }}
        </button>
        <button class="btn-cancel" @click="$emit('close')">Отмена</button>
      </div>
    </div>
    <Spinner v-else text="Загрузка..." />
  </BaseModal>
</template>

<script setup>
import { ref, reactive, computed, nextTick, watch } from 'vue'
import BaseModal from '@/shared/components/BaseModal.vue'
import Spinner from '@/shared/components/Spinner.vue'
import mediaApi from '../api'

const props = defineProps({
  show: Boolean,
  categories: { type: Array, default: () => [] },
  brands: { type: Array, default: () => [] },
  equipmentTypes: { type: Array, default: () => [] },
})
const emit = defineEmits(['close', 'uploaded'])

const fileInput = ref(null)
const file = ref(null)
const previewUrl = ref('')
const previewImg = ref(null)
const imgNaturalW = ref(0); const imgNaturalH = ref(0)
const imgDisplayW = ref(0); const imgDisplayH = ref(0)
const scale = ref(1)
const uploading = ref(false)
const submitting = ref(false)
const error = ref('')
const sessionId = ref(null)

// Код-регион
const codeRegionActive = ref(false)
const codeRegion = reactive({ x: 0, y: 0, w: 200, h: 60 })
const codeCropUrl = ref('')
const dragging = ref(false); const resizing = ref(false)
const regionStart = { x: 0, y: 0, w: 0, h: 0 }
const dragStart = { x: 0, y: 0 }

const form = reactive({
  name: '',
  code: '',
  keywords: '',
})

const canSubmit = computed(() => file.value && form.name.trim() && form.code.trim())

const regionStyle = computed(() => ({
  left: codeRegion.x + 'px', top: codeRegion.y + 'px',
  width: codeRegion.w + 'px', height: codeRegion.h + 'px',
}))

// ── File selection ──
async function onFileSelect(e) { if (e.target.files[0]) await processFile(e.target.files[0]) }
async function onDrop(e) { if (e.dataTransfer.files[0]) await processFile(e.dataTransfer.files[0]) }

async function processFile(f) {
  file.value = f
  uploading.value = true
  error.value = ''
  const base = f.name.replace(/\.[^.]+$/, '')
  form.name = base
  form.keywords = `Электропривод, схема, ${base}`
  form.code = ''

  // Загружаем для превью через svg-converter
  const fd = new FormData(); fd.append('file', f)
  const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || ''
  try {
    const r = await fetch('/api/svg-converter/upload/', {
      method: 'POST', body: fd,
      headers: { 'X-CSRFToken': csrf }, credentials: 'include',
    })
    const data = await r.json()
    if (data.session_id) {
      sessionId.value = data.session_id
      const pr = await fetch('/api/svg-converter/preview/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
        credentials: 'include',
        body: JSON.stringify({ session_id: data.session_id }),
      })
      if (!pr.ok) {
        const text = await pr.text()
        error.value = `Preview error ${pr.status}: ${text.slice(0, 200)}`
        return
      }
      const prev = await pr.json()
      if (prev.preview) previewUrl.value = prev.preview
      else error.value = prev.error || 'Ошибка загрузки превью'
    }
  } catch (e) {
    error.value = 'Ошибка загрузки: ' + e.message
  }
  uploading.value = false
}

function onImgLoad() {
  const img = previewImg.value
  if (img) {
    imgNaturalW.value = img.naturalWidth
    imgNaturalH.value = img.naturalHeight
    imgDisplayW.value = img.clientWidth
    imgDisplayH.value = img.clientHeight
    scale.value = imgNaturalW.value / imgDisplayW.value
  }
}

// ── Code region ──
function toggleCodeRegion() {
  if (codeRegionActive.value) { codeRegionActive.value = false; return }
  // Размещаем в правом нижнем углу
  const w = Math.round(imgDisplayW.value * 0.25)
  const h = Math.round(imgDisplayH.value * 0.08)
  codeRegion.x = imgDisplayW.value - w - 10
  codeRegion.y = imgDisplayH.value - h - 10
  codeRegion.w = w
  codeRegion.h = h
  codeRegionActive.value = true
  nextTick(() => fetchCodeCrop())
}

function resetCodeRegion() { codeRegionActive.value = false; codeCropUrl.value = '' }

function startDrag(e) {
  dragging.value = true
  dragStart.x = e.clientX; dragStart.y = e.clientY
  regionStart.x = codeRegion.x; regionStart.y = codeRegion.y
}
function startResize(e, corner) {
  e.stopPropagation()
  resizing.value = true
  dragStart.x = e.clientX; dragStart.y = e.clientY
  regionStart.x = codeRegion.x; regionStart.y = codeRegion.y
  regionStart.w = codeRegion.w; regionStart.h = codeRegion.h
}
function onMouseMove(e) {
  if (!dragging.value && !resizing.value) return
  const dx = e.clientX - dragStart.x; const dy = e.clientY - dragStart.y
  if (dragging.value) {
    codeRegion.x = Math.max(0, regionStart.x + dx)
    codeRegion.y = Math.max(0, regionStart.y + dy)
  } else if (resizing.value) {
    codeRegion.w = Math.max(40, regionStart.w + dx)
    codeRegion.h = Math.max(20, regionStart.h + dy)
  }
}
function onMouseUp() {
  if (dragging.value || resizing.value) { dragging.value = false; resizing.value = false; fetchCodeCrop() }
}
async function fetchCodeCrop() {
  if (!previewUrl.value || !codeRegionActive.value) return
  if (!sessionId.value) return
  const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || ''
  const r = await fetch('/api/svg-converter/preview/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
    body: JSON.stringify({
      session_id: sessionId.value,
      region_x: Math.round(codeRegion.x * scale.value),
      region_y: Math.round(codeRegion.y * scale.value),
      region_w: Math.round(codeRegion.w * scale.value),
      region_h: Math.round(codeRegion.h * scale.value),
    }),
  })
  const data = await r.json()
  if (data.preview) codeCropUrl.value = data.preview
}
// Костыль: получаем session_id повторно (можно было сохранить, но для простоты ок)
let _sessionId = null
async function getSessionId() {
  if (_sessionId) return _sessionId
  const fd = new FormData(); fd.append('file', file.value)
  const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || ''
  const r = await fetch('/api/svg-converter/upload/', {
    method: 'POST', body: fd, headers: { 'X-CSRFToken': csrf }, credentials: 'include',
  })
  const data = await r.json()
  _sessionId = data.session_id
  return _sessionId
}

// ── Submit ──
async function doSubmit() {
  if (!canSubmit.value) return
  submitting.value = true; error.value = ''

  // Найти ID бренда «Архимед» и типа «Электропривод»
  const archBrand = props.brands.find(b => b.name === 'Архимед' || b.name?.toLowerCase().includes('архимед'))
  const eaType = props.equipmentTypes.find(t => t.name === 'Электропривод' || t.name?.toLowerCase().includes('электропривод'))

  const fd = new FormData()
  // Найти ID категории SCHEMA
  const schemaCat = props.categories.find(c => c.code === 'SCHEMA')
  if (!schemaCat) { error.value = 'Категория SCHEMA не найдена'; submitting.value = false; return }

  fd.append('file', file.value)
  fd.append('category_id', schemaCat.id)
  fd.append('name', form.name)
  fd.append('code', form.code)
  fd.append('category_code', 'SCHEMA')
  fd.append('keywords', form.keywords)
  fd.append('is_active', 'true')
  fd.append('is_public', 'true')
  if (archBrand) fd.append('brand_id', archBrand.id)
  if (eaType) fd.append('equipment_type_id', eaType.id)

  try {
    await mediaApi.upload(fd)
    emit('uploaded')
    emit('close')
  } catch (e) {
    error.value = e.response?.data?.error || e.message || 'Ошибка создания'
  }
  submitting.value = false
}

function fmtSize(b) {
  if (!b) return '—'
  if (b < 1024) return b + ' B'
  if (b < 1048576) return (b / 1024).toFixed(1) + ' KB'
  return (b / 1048576).toFixed(1) + ' MB'
}

// ── Сброс при открытии ──
watch(() => props.show, (val) => {
  if (val) {
    file.value = null
    previewUrl.value = ''
    sessionId.value = null
    codeRegionActive.value = false
    codeCropUrl.value = ''
    error.value = ''
    uploading.value = false
    submitting.value = false
    form.name = ''; form.code = ''; form.keywords = ''
    codeRegion.x = 0; codeRegion.y = 0; codeRegion.w = 200; codeRegion.h = 60
  }
})

// ── Глобальные обработчики мыши ──
import { onMounted, onBeforeUnmount } from 'vue'
onMounted(() => { document.addEventListener('mousemove', onMouseMove); document.addEventListener('mouseup', onMouseUp) })
onBeforeUnmount(() => { document.removeEventListener('mousemove', onMouseMove); document.removeEventListener('mouseup', onMouseUp) })
</script>

<style scoped>
.sum-body { display: flex; flex-direction: column; gap: 16px; }
.sum-step { }
.sum-drop {
  border: 2px dashed #9ca3af; border-radius: 8px; padding: 40px 20px;
  text-align: center; cursor: pointer; color: #6b7280; font-size: 15px;
}
.sum-drop:hover { border-color: #3b82f6; color: #3b82f6; }
.sum-hint { font-size: 12px; color: #9ca3af; margin: 4px 0 0; }

.sum-preview-wrap { max-height: 400px; overflow: auto; border: 1px solid #e5e7eb; border-radius: 6px; margin-bottom: 12px; }
.sum-preview-img { max-width: 100%; display: block; }
.sum-code-region {
  position: absolute; border: 2px dashed #f59e0b; background: rgba(245, 158, 11, 0.1); cursor: move;
}
.sum-handle { position: absolute; width: 8px; height: 8px; background: #f59e0b; border: 1px solid #fff; }
.sum-handle.br { bottom: -4px; right: -4px; cursor: se-resize; }

.sum-code-area { background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 12px; }
.sum-code-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.sum-code-crop { margin-bottom: 8px; min-height: 40px; background: #fff; border-radius: 4px; padding: 4px; }
.sum-code-crop-img { max-height: 60px; display: block; }
.sum-code-actions { display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.btn-sm {
  padding: 4px 12px; border: 1px solid #d1d5db; border-radius: 4px; background: #fff;
  cursor: pointer; font-size: 13px;
}
.btn-sm.active { border-color: #f59e0b; background: #fef3c7; }
.btn-reset { color: #dc2626; border-color: #fecaca; }
.sum-code-input {
  width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px;
  font-size: 16px; font-family: monospace; letter-spacing: 1px;
}
.sum-code-input.filled { border-color: #10b981; background: #f0fdf4; }

.sum-meta { display: flex; flex-direction: column; gap: 8px; }
.sum-meta-row { display: flex; align-items: center; gap: 8px; }
.sum-meta-row label { width: 140px; font-size: 13px; color: #6b7280; text-align: right; flex-shrink: 0; }
.field { flex: 1; padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px; }
.sum-meta-readonly .readonly-val { font-size: 13px; color: #374151; }

.sum-error { color: #dc2626; font-size: 13px; background: #fef2f2; padding: 8px 12px; border-radius: 6px; }
.sum-actions { display: flex; gap: 12px; justify-content: flex-end; }
.btn-pri { padding: 8px 24px; background: #2563eb; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
.btn-pri:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-cancel { padding: 8px 24px; background: #e5e7eb; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
</style>