<!-- pages/TableOcrTool.vue -->
<template>
  <div class="page">
    <h1>🔎 Распознавание (OCR) → Word / Excel</h1>
    <p class="subtitle">
      Выберите файл с диска (изображение или PDF). По умолчанию распознаётся
      страница целиком; для изображения можно выделить нужный блок (таблицу).
    </p>

    <div class="panel">
      <div class="row">
        <label class="upload-btn">
          <input type="file" accept="image/*,.pdf" @change="onFileSelected" hidden ref="fileInput" />
          <span>{{ file ? '📎 ' + file.name : '📁 Выбрать файл' }}</span>
        </label>

        <label class="field">
          <span>OCR-движок</span>
          <select v-model="backend" class="input select">
            <option value="">По умолчанию</option>
            <option v-for="b in backends" :key="b" :value="b">{{ b }}</option>
          </select>
        </label>

        <label class="field checkbox">
          <input v-model="borderless" type="checkbox" />
          <span>Таблицы без линий</span>
        </label>

        <label class="field checkbox">
          <input v-model="useHeader" type="checkbox" />
          <span>Первая строка — шапка</span>
        </label>
      </div>

      <div class="row actions">
        <button class="btn-primary" :disabled="!file || recognizing" @click="recognize">
          {{ recognizing ? '⏳ Распознаю…' : '🔎 Распознать' }}
        </button>
        <template v-if="resultId">
          <select v-model="saveFormat" class="input select small">
            <option value="xlsx">Excel (.xlsx)</option>
            <option value="docx">Word (.docx)</option>
          </select>
          <button class="btn-success" :disabled="downloading" @click="download">
            {{ downloading ? '⏳ Скачиваю…' : '💾 Скачать' }}
          </button>
        </template>
      </div>

      <div v-if="error" class="error">{{ error }}</div>

      <div v-if="srcUrl && isImage" class="preview-area">
        <div class="preview-wrapper">
          <img ref="previewImg" :src="srcUrl" alt="preview" class="preview-img"
            @load="onImgLoad" @mousedown="onImgMouseDown" />
          <div v-if="regionActive" class="region-overlay" :style="regionStyle" @mousedown.stop="startDrag">
            <div class="region-handle tl" @mousedown.stop="startResize($event, 'tl')"></div>
            <div class="region-handle tr" @mousedown.stop="startResize($event, 'tr')"></div>
            <div class="region-handle bl" @mousedown.stop="startResize($event, 'bl')"></div>
            <div class="region-handle br" @mousedown.stop="startResize($event, 'br')"></div>
          </div>
        </div>
        <div class="region-bar">
          <span v-if="!regionActive" class="hint">Зажмите кнопку мыши и растяните область (по умолчанию — страница целиком).</span>
          <button v-else class="btn-secondary" @click="clearRegion">✕ Сбросить область</button>
        </div>
      </div>
      <div v-else-if="srcUrl" class="hint">PDF: распознаются все страницы целиком (выделение области недоступно).</div>
    </div>

    <div v-if="result" class="results">
      <div class="summary">
        Страниц: {{ result.page_count }} · таблиц: {{ result.count }} · OCR: {{ result.ocr_backend }}
      </div>

      <div v-for="page in result.pages" :key="page.n" class="page-block">
        <div v-if="result.page_count > 1" class="page-title">Страница {{ page.n }}</div>

        <div v-if="page.text" class="text-block">
          <div class="block-title">Текст</div>
          <pre class="text-pre">{{ page.text }}</pre>
        </div>

        <div v-for="t in page.tables" :key="t.index" class="table-block">
          <div class="table-title">Таблица {{ t.index + 1 }} · {{ t.n_rows }}×{{ t.n_columns }}</div>
          <div class="table-scroll">
            <table class="grid">
              <thead>
                <tr>
                  <th v-for="(c, ci) in t.columns" :key="ci">{{ c }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, ri) in t.rows" :key="ri">
                  <td v-for="(cell, ci) in row" :key="ci">{{ cell ?? '' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div v-if="!result.count && !hasText" class="hint">Ничего не распознано.</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import api from '@/shared/api'

const file = ref(null)
const isImage = ref(true)
const srcUrl = ref('')
const backend = ref('')
const borderless = ref(false)
const useHeader = ref(true)
const saveFormat = ref('xlsx')

const recognizing = ref(false)
const downloading = ref(false)
const error = ref('')
const result = ref(null)
const resultId = ref('')

// Регион выделения
const previewImg = ref(null)
const regionActive = ref(false)
const region = ref({ x: 0, y: 0, w: 0, h: 0 })
const imgNaturalW = ref(0)
const imgNaturalH = ref(0)
const imgDisplayW = ref(0)
const imgDisplayH = ref(0)
const scale = ref(1)

const drawing = ref(false)   // тянем новое выделение
const dragging = ref(false)  // двигаем готовое выделение
const resizing = ref(false)  // тянем угол
const resizeCorner = ref('')
const dragStart = ref({ x: 0, y: 0 })
const regionStart = ref({ x: 0, y: 0, w: 0, h: 0 })

const backends = ['tesseract', 'rapidocr', 'surya', 'paddle', 'easyocr', 'doctr']

const hasText = computed(() =>
  (result.value?.pages || []).some(p => (p.text || '').trim()),
)

const regionStyle = computed(() => ({
  left: region.value.x + 'px',
  top: region.value.y + 'px',
  width: region.value.w + 'px',
  height: region.value.h + 'px',
}))

function onFileSelected(e) {
  const f = e.target.files?.[0]
  if (!f) return
  file.value = f
  error.value = ''
  result.value = null
  resultId.value = ''

  isImage.value = (f.type || '').startsWith('image/')
  if (srcUrl.value) URL.revokeObjectURL(srcUrl.value)
  if (isImage.value) {
    srcUrl.value = URL.createObjectURL(f)
  } else {
    srcUrl.value = ''
  }
  resetRegion()
}

function resetRegion() {
  regionActive.value = false
  region.value = { x: 0, y: 0, w: 0, h: 0 }
  drawing.value = false
  dragging.value = false
  resizing.value = false
  imgNaturalW.value = 0
  imgNaturalH.value = 0
  imgDisplayW.value = 0
  imgDisplayH.value = 0
  scale.value = 1
}

function onImgLoad() {
  const img = previewImg.value
  if (!img) return
  imgNaturalW.value = img.naturalWidth
  imgNaturalH.value = img.naturalHeight
  imgDisplayW.value = img.clientWidth
  imgDisplayH.value = img.clientHeight
  if (imgDisplayW.value > 0) scale.value = imgNaturalW.value / imgDisplayW.value
}

function imagePoint(e) {
  const img = previewImg.value
  if (!img) return null
  const rect = img.getBoundingClientRect()
  return {
    x: Math.min(Math.max(0, e.clientX - rect.left), rect.width),
    y: Math.min(Math.max(0, e.clientY - rect.top), rect.height),
  }
}

function onImgMouseDown(e) {
  if (drawing.value || resizing.value || dragging.value) return
  const p = imagePoint(e)
  if (!p) return
  drawing.value = true
  dragStart.value = { x: p.x, y: p.y }
  region.value = { x: p.x, y: p.y, w: 0, h: 0 }
  regionActive.value = true
}

function startDrag(e) {
  dragging.value = true
  dragStart.value = { x: e.clientX, y: e.clientY }
  regionStart.value = { ...region.value }
}

function startResize(e, corner) {
  e.stopPropagation()
  resizing.value = true
  resizeCorner.value = corner
  dragStart.value = { x: e.clientX, y: e.clientY }
  regionStart.value = { ...region.value }
}

function onMouseMove(e) {
  if (drawing.value) {
    const p = imagePoint(e)
    if (!p) return
    const sx = dragStart.value.x
    const sy = dragStart.value.y
    region.value = {
      x: Math.min(sx, p.x),
      y: Math.min(sy, p.y),
      w: Math.abs(p.x - sx),
      h: Math.abs(p.y - sy),
    }
    return
  }

  if (dragging.value) {
    const dx = e.clientX - dragStart.value.x
    const dy = e.clientY - dragStart.value.y
    region.value.x = Math.max(0, regionStart.value.x + dx)
    region.value.y = Math.max(0, regionStart.value.y + dy)
    return
  }

  if (resizing.value) {
    const dx = e.clientX - dragStart.value.x
    const dy = e.clientY - dragStart.value.y
    const r = { ...regionStart.value }
    if (resizeCorner.value.includes('r')) r.w = Math.max(10, r.w + dx)
    if (resizeCorner.value.includes('l')) { r.x = Math.max(0, r.x + dx); r.w = Math.max(10, r.w - dx) }
    if (resizeCorner.value.includes('b')) r.h = Math.max(10, r.h + dy)
    if (resizeCorner.value.includes('t')) { r.y = Math.max(0, r.y + dy); r.h = Math.max(10, r.h - dy) }
    region.value = r
  }
}

function onMouseUp() {
  if (drawing.value) {
    drawing.value = false
    if (region.value.w < 5 || region.value.h < 5) {
      clearRegion()
    }
  }
  dragging.value = false
  resizing.value = false
}

function clearRegion() {
  regionActive.value = false
  region.value = { x: 0, y: 0, w: 0, h: 0 }
  drawing.value = false
  dragging.value = false
  resizing.value = false
}

async function recognize() {
  if (!file.value) return
  recognizing.value = true
  error.value = ''
  result.value = null
  resultId.value = ''

  const fd = new FormData()
  fd.append('file', file.value)
  fd.append('borderless_tables', borderless.value ? 'true' : 'false')
  fd.append('use_first_row_as_header', useHeader.value ? 'true' : 'false')
  if (backend.value) fd.append('ocr', backend.value)
  if (regionActive.value) {
    fd.append('region_x', Math.round(region.value.x * scale.value))
    fd.append('region_y', Math.round(region.value.y * scale.value))
    fd.append('region_w', Math.round(region.value.w * scale.value))
    fd.append('region_h', Math.round(region.value.h * scale.value))
  }

  try {
    const { data } = await api.post('/admin/media/ocr/recognize/', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    result.value = data
    resultId.value = data.result_id
  } catch (e) {
    error.value = e?.displayMessage || e?.message || 'Ошибка распознавания'
  } finally {
    recognizing.value = false
  }
}

async function download() {
  if (!resultId.value) return
  downloading.value = true
  error.value = ''

  try {
    const resp = await api.post(
      '/admin/media/ocr/export/',
      { result_id: resultId.value, format: saveFormat.value },
      { responseType: 'blob' },
    )
    const dispo = resp.headers?.['content-disposition'] || ''
    const match = dispo.match(/filename="?([^";]+)"?/)
    const base = (file.value?.name || 'ocr').replace(/\.[^.]+$/, '')
    const filename = match ? match[1] : `${base}.${saveFormat.value}`

    const url = URL.createObjectURL(resp.data)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    error.value = e?.displayMessage || e?.message || 'Ошибка при скачивании'
  } finally {
    downloading.value = false
  }
}

onMounted(() => {
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
})
onBeforeUnmount(() => {
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
  if (srcUrl.value) URL.revokeObjectURL(srcUrl.value)
})
</script>

<style scoped>
.page { max-width: 1100px; margin: 0 auto; padding: 24px 16px; font-family: system-ui, sans-serif; }
h1 { font-size: 22px; margin: 0 0 8px; }
.subtitle { color: #6b7280; font-size: 14px; margin: 0 0 20px; }

.panel { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin-bottom: 20px; }
.row { display: flex; gap: 16px; flex-wrap: wrap; align-items: flex-end; margin-bottom: 12px; }
.field { display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: #374151; }
.field span { font-weight: 600; }
.input { padding: 8px 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 14px; }
.select { min-width: 180px; }
.select.small { min-width: 140px; }
.checkbox { flex-direction: row; align-items: center; gap: 8px; margin-top: 18px; }
.actions { margin-bottom: 0; }

.upload-btn { cursor: pointer; padding: 10px 20px; background: #fff; border: 1px dashed #999; border-radius: 8px; display: inline-block; font-size: 14px; }
.upload-btn:hover { background: #eef2ff; }

.btn-primary { padding: 9px 18px; background: #3b82f6; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-success { padding: 9px 18px; background: #16a34a; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
.btn-success:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { padding: 8px 16px; background: #e5e7eb; border: 1px solid #ccc; border-radius: 6px; cursor: pointer; font-size: 13px; }

.hint { color: #6b7280; font-size: 13px; margin-top: 8px; }
.error { color: #dc2626; font-size: 14px; margin-top: 10px; background: #fef2f2; padding: 8px 12px; border-radius: 6px; }

.preview-area { margin-top: 14px; }
.preview-wrapper { position: relative; display: inline-block; }
.preview-img { max-width: 100%; max-height: 480px; border: 1px solid #e5e7eb; border-radius: 6px; display: block; cursor: crosshair; user-select: none; }
.region-bar { margin-top: 6px; min-height: 24px; }

.region-overlay { position: absolute; border: 2px dashed #3b82f6; background: rgba(59, 130, 246, 0.12); cursor: move; }
.region-handle { position: absolute; width: 12px; height: 12px; background: #3b82f6; border: 1px solid #fff; }
.region-handle.tl { top: -6px; left: -6px; cursor: nw-resize; }
.region-handle.tr { top: -6px; right: -6px; cursor: ne-resize; }
.region-handle.bl { bottom: -6px; left: -6px; cursor: sw-resize; }
.region-handle.br { bottom: -6px; right: -6px; cursor: se-resize; }

.results { margin-top: 8px; }
.summary { font-size: 14px; color: #374151; margin-bottom: 16px; }
.page-block { margin-bottom: 20px; }
.page-title { font-size: 16px; font-weight: 700; margin: 0 0 12px; color: #111827; }
.text-block { margin-bottom: 20px; }
.block-title { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
.text-pre { white-space: pre-wrap; font-family: inherit; font-size: 13px; background: #fff; border: 1px solid #e5e7eb; border-radius: 6px; padding: 10px; max-height: 300px; overflow: auto; }

.table-block { margin-bottom: 24px; }
.table-title { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
.table-scroll { overflow: auto; max-height: 480px; border: 1px solid #e5e7eb; border-radius: 6px; }
.grid { border-collapse: collapse; font-size: 13px; min-width: 100%; }
.grid th, .grid td { border: 1px solid #e5e7eb; padding: 6px 10px; white-space: nowrap; text-align: left; }
.grid th { background: #f3f4f6; position: sticky; top: 0; }
.grid tbody tr:nth-child(even) { background: #fafafa; }
</style>
