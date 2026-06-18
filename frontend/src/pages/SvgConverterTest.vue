<!-- pages/SvgConverterTest.vue -->
<template>
  <div class="page">
    <h1>🔧 SVG Converter — перевод схем и чертежей в вектор</h1>

    <!-- Загрузка -->
    <div class="upload-bar">
      <label class="upload-btn">
        <input type="file" accept=".jpg,.jpeg,.png,.pdf" @change="onFileSelected" hidden ref="fileInput" />
        <span>{{ fileUploaded ? '📎 ' + filename : '📁 Выбрать файл' }}</span>
      </label>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <!-- Инструменты -->
    <div v-if="fileUploaded" class="tools-bar">
      <div class="tool-group">
        <label>Режим:</label>
        <select v-model="colorMode" class="tool-select">
          <option value="bw">Чёрно-белый</option>
          <option value="color">Цветной</option>
        </select>
      </div>
      <div class="tool-group" v-if="colorMode === 'bw'">
        <label>Порог: {{ threshold }}</label>
        <input type="range" v-model.number="threshold" min="50" max="240" class="threshold-slider" />
      </div>
      <button @click="convertToSvg" class="btn-primary" :disabled="converting">
        {{ converting ? '⏳ Векторизация...' : '⚡ Конвертировать в SVG' }}
      </button>
      <button v-if="regionActive" @click="clearRegion" class="btn-secondary">✕ Сбросить область</button>
    </div>

    <!-- Превью оригинала + область выделения -->
    <div v-if="previewUrl" class="preview-area" ref="previewContainer">
      <div class="preview-wrapper" :style="{ position: 'relative', display: 'inline-block' }">
        <img :src="previewUrl" :alt="filename" class="preview-img"
          @load="onImgLoad"
          @click="onImgClick"
          ref="previewImg"
        />
        <!-- Рамка выделения -->
        <div
          v-if="regionActive"
          class="region-overlay"
          :style="regionStyle"
          @mousedown="startDrag"
        >
          <div class="region-handle tl" @mousedown.stop="startResize($event, 'tl')"></div>
          <div class="region-handle tr" @mousedown.stop="startResize($event, 'tr')"></div>
          <div class="region-handle bl" @mousedown.stop="startResize($event, 'bl')"></div>
          <div class="region-handle br" @mousedown.stop="startResize($event, 'br')"></div>
        </div>
      </div>
      <p class="hint" v-if="!regionActive">Кликните по изображению, чтобы выделить область</p>
    </div>

    <!-- Результат SVG -->
    <div v-if="svgResult" class="results">
      <h3>✅ Результат — {{ svgFilename }}</h3>
      <div class="svg-actions">
        <button @click="downloadSvg" class="btn-primary">💾 Скачать SVG</button>
      </div>
      <div class="svg-preview" v-html="svgResult"></div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SvgConverterTest',
  data() {
    return {
      sessionId: null,
      filename: '',
      fileUploaded: false,
      previewUrl: '',
      imgNaturalW: 0,
      imgNaturalH: 0,
      imgDisplayW: 0,
      imgDisplayH: 0,
      scale: 1,
      colorMode: 'bw',
      threshold: 128,
      svgResult: '',
      svgFilename: '',
      converting: false,
      error: '',
      // Регион
      regionActive: false,
      region: { x: 0, y: 0, w: 0, h: 0 },
      dragging: false,
      resizing: false,
      resizeCorner: '',
      dragStart: { x: 0, y: 0 },
      regionStart: { x: 0, y: 0, w: 0, h: 0 },
    }
  },
  computed: {
    regionStyle() {
      return {
        left: this.region.x + 'px',
        top: this.region.y + 'px',
        width: this.region.w + 'px',
        height: this.region.h + 'px',
      }
    },
  },
  mounted() {
    document.addEventListener('mousemove', this.onMouseMove)
    document.addEventListener('mouseup', this.onMouseUp)
  },
  beforeUnmount() {
    document.removeEventListener('mousemove', this.onMouseMove)
    document.removeEventListener('mouseup', this.onMouseUp)
  },
  methods: {
    async onFileSelected(e) {
      const file = e.target.files[0]
      if (!file) return
      this.error = ''; this.svgResult = ''; this.regionActive = false
      const form = new FormData(); form.append('file', file)
      const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || ''
      try {
        const r = await fetch('/api/svg-converter/upload/', {
          method: 'POST', body: form,
          headers: { 'X-CSRFToken': csrf }, credentials: 'include',
        })
        const data = await r.json()
        if (r.ok && data.session_id) {
          this.sessionId = data.session_id
          this.filename = data.filename
          this.fileUploaded = true
          // Получаем превью через preview endpoint
          await this.loadPreview()
        } else {
          this.error = data.error || 'Upload failed'
        }
      } catch (err) {
        this.error = err.message || 'Upload error'
      }
    },
    async loadPreview(regionData = {}) {
      if (!this.sessionId) return
      const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || ''
      const r = await fetch('/api/svg-converter/preview/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
        body: JSON.stringify({ session_id: this.sessionId, ...regionData }),
      })
      const data = await r.json()
      if (data.preview) {
        this.previewUrl = data.preview
      }
    },
    onImgLoad() {
      const img = this.$refs.previewImg
      if (img) {
        this.imgNaturalW = img.naturalWidth
        this.imgNaturalH = img.naturalHeight
        this.imgDisplayW = img.clientWidth
        this.imgDisplayH = img.clientHeight
        this.scale = this.imgNaturalW / this.imgDisplayW
      }
    },
    onImgClick(e) {
      if (this.regionActive) return
      const rect = this.$refs.previewImg.getBoundingClientRect()
      const cx = e.clientX - rect.left
      const cy = e.clientY - rect.top
      const size = Math.min(this.imgDisplayW, this.imgDisplayH) * 0.4
      this.region = {
        x: Math.max(0, cx - size / 2),
        y: Math.max(0, cy - size / 2),
        w: size, h: size,
      }
      this.regionActive = true
    },
    startDrag(e) {
      this.dragging = true
      this.dragStart = { x: e.clientX, y: e.clientY }
      this.regionStart = { ...this.region }
    },
    startResize(e, corner) {
      e.stopPropagation()
      this.resizing = true
      this.resizeCorner = corner
      this.dragStart = { x: e.clientX, y: e.clientY }
      this.regionStart = { ...this.region }
    },
    onMouseMove(e) {
      if (!this.dragging && !this.resizing) return
      const dx = e.clientX - this.dragStart.x
      const dy = e.clientY - this.dragStart.y

      if (this.dragging) {
        this.region.x = Math.max(0, this.regionStart.x + dx)
        this.region.y = Math.max(0, this.regionStart.y + dy)
      } else if (this.resizing) {
        const r = { ...this.regionStart }
        if (this.resizeCorner.includes('r')) r.w = Math.max(20, r.w + dx)
        if (this.resizeCorner.includes('l')) { r.x = Math.max(0, r.x + dx); r.w = Math.max(20, r.w - dx) }
        if (this.resizeCorner.includes('b')) r.h = Math.max(20, r.h + dy)
        if (this.resizeCorner.includes('t')) { r.y = Math.max(0, r.y + dy); r.h = Math.max(20, r.h - dy) }
        this.region = r
      }
    },
    onMouseUp() {
      this.dragging = false
      this.resizing = false
    },
    clearRegion() {
      this.regionActive = false
      this.region = { x: 0, y: 0, w: 0, h: 0 }
      this.loadPreview()
    },
    async convertToSvg() {
      if (!this.sessionId) return
      this.converting = true; this.error = ''; this.svgResult = ''
      const body = {
        session_id: this.sessionId,
        color_mode: this.colorMode,
        threshold: this.threshold,
      }
      if (this.regionActive) {
        body.region_x = Math.round(this.region.x * this.scale)
        body.region_y = Math.round(this.region.y * this.scale)
        body.region_w = Math.round(this.region.w * this.scale)
        body.region_h = Math.round(this.region.h * this.scale)
      }
      const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || ''
      try {
        const r = await fetch('/api/svg-converter/convert/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
          body: JSON.stringify(body),
        })
        const data = await r.json()
        if (data.svg) {
          this.svgResult = data.svg
          this.svgFilename = data.filename
        } else {
          this.error = data.error || 'Conversion failed'
        }
      } catch (err) {
        this.error = err.message || 'Conversion error'
      }
      this.converting = false
    },
    downloadSvg() {
      const blob = new Blob([this.svgResult], { type: 'image/svg+xml' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = this.svgFilename; a.click()
      URL.revokeObjectURL(url)
    },
  },
}
</script>

<style scoped>
.page { max-width: 1000px; margin: 0 auto; padding: 24px 16px; font-family: system-ui, sans-serif; }
h1 { font-size: 22px; margin-bottom: 20px; }
h3 { font-size: 16px; margin-bottom: 12px; }

.upload-bar { margin-bottom: 16px; }
.upload-btn { cursor: pointer; padding: 10px 20px; background: #f3f4f6; border: 1px dashed #999; border-radius: 8px; display: inline-block; font-size: 14px; }
.upload-btn:hover { background: #e5e7eb; }

.tools-bar { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; margin-bottom: 16px; padding: 10px; background: #f9fafb; border-radius: 8px; }
.tool-group { display: flex; align-items: center; gap: 6px; font-size: 13px; }
.tool-select { padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px; }
.threshold-slider { width: 100px; }

.btn-primary { padding: 8px 20px; background: #3b82f6; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { padding: 8px 16px; background: #e5e7eb; border: 1px solid #ccc; border-radius: 6px; cursor: pointer; font-size: 13px; }

.error { color: #dc2626; font-size: 14px; margin-bottom: 12px; background: #fef2f2; padding: 8px 12px; border-radius: 6px; }

.preview-area { margin-bottom: 20px; }
.preview-wrapper { cursor: crosshair; }
.preview-img { max-width: 100%; max-height: 500px; border: 1px solid #e5e7eb; border-radius: 4px; display: block; }
.hint { font-size: 13px; color: #999; margin-top: 6px; }

.region-overlay {
  position: absolute;
  border: 2px dashed #3b82f6;
  background: rgba(59, 130, 246, 0.1);
  cursor: move;
}
.region-handle {
  position: absolute; width: 10px; height: 10px; background: #3b82f6; border: 1px solid #fff;
}
.region-handle.tl { top: -5px; left: -5px; cursor: nw-resize; }
.region-handle.tr { top: -5px; right: -5px; cursor: ne-resize; }
.region-handle.bl { bottom: -5px; left: -5px; cursor: sw-resize; }
.region-handle.br { bottom: -5px; right: -5px; cursor: se-resize; }

.results { margin-top: 28px; }
.svg-actions { margin-bottom: 12px; display: flex; gap: 10px; }
.svg-preview {
  border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px;
  background: #fff; overflow: auto; max-height: 600px;
}
.svg-preview :deep(svg) { max-width: 100%; height: auto; }
</style>