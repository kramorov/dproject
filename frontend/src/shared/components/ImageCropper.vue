<!-- shared/components/ImageCropper.vue
     Рамка фиксирована. Изображение двигается мышью и масштабируется колёсиком.
-->
<template>
  <div class="image-cropper">
    <div v-if="!sessionId" class="cropper-upload">
      <Spinner v-if="initialLoading" text="Загрузка изображения…" />
      <template v-else-if="!initialUrl">
        <label class="upload-btn">
          <input type="file" accept="image/*" @change="onFileSelected" hidden />
          <span>📁 Выбрать изображение</span>
        </label>
      </template>
      <p v-if="uploadError" class="error">{{ uploadError }}</p>
    </div>

    <div v-else class="cropper-workspace">
      <div class="cropper-toolbar">
        <label class="bg-mode-select">
          Фон:
          <select v-model="bgMode">
            <option value="remove">Убрать фон</option>
            <option value="fill">Наложить фон</option>
          </select>
          <span v-if="hasAlpha" class="alpha-note">🫧 альфа-канал</span>
        </label>
        <label class="bg-picker" v-if="bgMode === 'fill'">
          <input type="color" v-model="bgColor" />
          {{ bgColor }}
        </label>
        <button @click="resetImage" class="btn-ghost">Сбросить</button>
        <button @click="doCrop" class="btn-primary" :disabled="processing">
          {{ processing ? 'Обработка...' : 'Применить обрезку' }}
        </button>
      </div>

      <div class="cropper-canvas-wrap" ref="wrapRef"
           @mousedown="onMouseDown" @mousemove="onMouseMove"
           @mouseup="onMouseUp" @mouseleave="onMouseUp"
           @wheel.prevent="onWheel">
        <canvas ref="canvasRef"></canvas>
      </div>

      <p class="hint">Двигайте изображение мышью. Колёсико — масштаб. Рамка на месте.</p>

      <div v-if="log.length" class="cropper-log">
        <div v-for="(entry, i) in log" :key="i" class="log-line">
          <span class="log-time">{{ entry.time }}</span>
          <span :class="['log-msg', entry.err ? 'log-err' : '']">{{ entry.msg }}</span>
        </div>
      </div>

      <div v-if="previewUrl" class="cropper-preview">
        <h4>Результат:</h4>
        <img :src="previewUrl" alt="Preview" />
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/shared/api'
import Spinner from '@/shared/components/Spinner.vue'
export default {
  components: { Spinner },
  name: 'ImageCropper',
  props: {
    categoryCode: { type: String, default: '' },
    initialUrl: { type: String, default: '' },
  },
  emits: ['crop-complete'],

  data() {
    return {
      sessionId: null, originalUrl: null,
      imgW: 0, imgH: 0,
      bgColor: '#F0F0F0',
      bgMode: 'remove',
      hasAlpha: false,

      // Позиция и масштаб изображения на canvas
      imgX: 0, imgY: 0, zoom: 1,

      // Рамка (фиксирована)
      frameX: 0, frameY: 0, frameSize: 300,

      // Интеракция
      dragging: false,
      dragStartX: 0, dragStartY: 0,
      dragStartImgX: 0, dragStartImgY: 0,

      uploadError: '', processing: false, previewUrl: null,
      initialLoading: !!this.initialUrl,
      log: [],
      img: null, canvasScale: 1,
    }
  },

  mounted() {
    if (this.initialUrl) {
      this.autoLoadExisting()
    }
  },

  methods: {
    async autoLoadExisting() {
      this.initialLoading = true
      this.uploadError = ''; this.processing = true; this.log = []
      this.addLog(`Загрузка существующего изображения…`)
      try {
        const resp = await fetch(this.initialUrl)
        const blob = await resp.blob()
        const file = new File([blob], 'existing_image.' + (blob.type === 'image/webp' ? 'webp' : 'jpg'), { type: blob.type })
        const fakeE = { target: { files: [file] } }
        await this.onFileSelected(fakeE)
        this.initialLoading = false
      } catch (err) {
        this.addLog(err.message || 'Failed to load image', true)
        this.uploadError = err.message || 'Failed to load image'
        this.processing = false
        this.initialLoading = false
      }
    },
    addLog(msg, err) {
      const t = new Date().toLocaleTimeString()
      this.log.push({ time: t, msg, err: !!err })
    },

    async onFileSelected(e) {
      const file = e.target.files[0]
      if (!file) return
      this.uploadError = ''; this.processing = true; this.log = []
      this.addLog(`Загрузка: ${file.name} (${(file.size/1024).toFixed(1)} KB)`)
      try {
        const form = new FormData(); form.append('file', file)
        const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || ''
        const r = await fetch('/api/image-processor/upload/', {
          method: 'POST', body: form,
          headers: { 'X-CSRFToken': csrf }, credentials: 'include',
        })
        const data = await r.json()
        if (r.ok && data.session_id) {
          this.addLog(`Загружено: ${data.width}×${data.height}, сессия #${data.session_id}`)
          this.sessionId = data.session_id
          this.originalUrl = data.original_url
          this.imgW = data.width; this.imgH = data.height
          this.$nextTick(() => this.initCanvas())
        } else { this.addLog(data.error || 'Upload failed', true); this.uploadError = data.error || 'Upload failed' }
        if (data.has_alpha) {
          this.hasAlpha = true; this.addLog('🫧 Альфа-канал — фон уже прозрачный')
        }
      } catch (err) { this.addLog(err.message || 'Upload error', true); this.uploadError = err.message }
      this.processing = false
    },

    initCanvas() {
      const canvas = this.$refs.canvasRef
      const wrap = this.$refs.wrapRef
      if (!canvas || !wrap) return

      const maxW = Math.min(wrap.clientWidth - 20, 900)
      this.canvasScale = Math.min(maxW / this.imgW, 600 / this.imgH, 1)
      canvas.width = Math.round(this.imgW * this.canvasScale)
      canvas.height = Math.round(this.imgH * this.canvasScale)

      // Рамка: квадрат по короткой стороне холста, по центру
      this.frameSize = Math.min(canvas.width, canvas.height) - 20
      this.frameX = Math.round((canvas.width - this.frameSize) / 2)
      this.frameY = Math.round((canvas.height - this.frameSize) / 2)

      // Изображение: вписать в рамку
      this.zoom = this.frameSize / Math.max(this.imgW, this.imgH)
      this.imgX = this.frameX + (this.frameSize - this.imgW * this.zoom) / 2
      this.imgY = this.frameY + (this.frameSize - this.imgH * this.zoom) / 2

      this.img = new Image()
      this.img.onload = () => this.draw()
      this.img.onerror = () => { this.uploadError = 'Не удалось загрузить изображение' }
      this.img.src = this.originalUrl
    },

    draw() {
      const canvas = this.$refs.canvasRef
      if (!canvas) return
      const ctx = canvas.getContext('2d')

      // 1. Фон
      ctx.fillStyle = this.bgColor
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // 2. Изображение (только внутри рамки)
      ctx.save()
      ctx.beginPath()
      ctx.rect(this.frameX, this.frameY, this.frameSize, this.frameSize)
      ctx.clip()
      if (this.img) {
        const w = this.imgW * this.zoom, h = this.imgH * this.zoom
        ctx.drawImage(this.img, this.imgX, this.imgY, w, h)
      }
      ctx.restore()

      // 3. Затемнение вне рамки
      ctx.fillStyle = 'rgba(0,0,0,0.40)'
      // верх
      ctx.fillRect(0, 0, canvas.width, this.frameY)
      // низ
      ctx.fillRect(0, this.frameY + this.frameSize, canvas.width, canvas.height - this.frameY - this.frameSize)
      // лево
      ctx.fillRect(0, this.frameY, this.frameX, this.frameSize)
      // право
      ctx.fillRect(this.frameX + this.frameSize, this.frameY, canvas.width - this.frameX - this.frameSize, this.frameSize)

      // 4. Рамка
      ctx.strokeStyle = '#3b82f6'; ctx.lineWidth = 2
      ctx.strokeRect(this.frameX, this.frameY, this.frameSize, this.frameSize)

      // 5. Ручки по углам рамки
      const r = 6
      const corners = [
        [this.frameX, this.frameY],
        [this.frameX + this.frameSize, this.frameY],
        [this.frameX, this.frameY + this.frameSize],
        [this.frameX + this.frameSize, this.frameY + this.frameSize],
      ]
      ctx.fillStyle = '#3b82f6'
      for (const [cx, cy] of corners) ctx.fillRect(cx - r, cy - r, r * 2, r * 2)
    },

    onMouseDown(e) {
      const rect = this.$refs.canvasRef.getBoundingClientRect()
      const mx = e.clientX - rect.left, my = e.clientY - rect.top
      // Перетаскивание — в любом месте холста
      this.dragging = true
      this.dragStartX = mx; this.dragStartY = my
      this.dragStartImgX = this.imgX; this.dragStartImgY = this.imgY
    },

    onMouseMove(e) {
      if (!this.dragging) return
      const rect = this.$refs.canvasRef.getBoundingClientRect()
      const mx = e.clientX - rect.left, my = e.clientY - rect.top
      this.imgX = this.dragStartImgX + (mx - this.dragStartX)
      this.imgY = this.dragStartImgY + (my - this.dragStartY)
      this.draw()
    },

    onMouseUp() { this.dragging = false },

    onWheel(e) {
      const d = e.deltaY > 0 ? -0.05 : 0.05
      const newZoom = Math.max(0.1, this.zoom + d * this.zoom)
      // Масштабировать относительно центра рамки
      const cx = this.frameX + this.frameSize / 2
      const cy = this.frameY + this.frameSize / 2
      this.imgX = cx - (cx - this.imgX) * (newZoom / this.zoom)
      this.imgY = cy - (cy - this.imgY) * (newZoom / this.zoom)
      this.zoom = newZoom
      this.draw()
    },

    resetImage() {
      this.zoom = this.frameSize / Math.max(this.imgW, this.imgH)
      this.imgX = this.frameX + (this.frameSize - this.imgW * this.zoom) / 2
      this.imgY = this.frameY + (this.frameSize - this.imgH * this.zoom) / 2
      this.previewUrl = null
      this.draw()
    },

    async doCrop() {
      this.processing = true; this.previewUrl = null; this.log = []
      this.addLog(`Обрезка: ${Math.round(this.frameSize/this.zoom)}×${Math.round(this.frameSize/this.zoom)} px`)
      if (this.bgMode === 'remove') this.addLog('Удаление фона нейросетью (rembg)…')
      const origCropX = (this.frameX - this.imgX) / this.zoom
      const origCropY = (this.frameY - this.imgY) / this.zoom
      const origCropSize = this.frameSize / this.zoom
      const body = {
        session_id: this.sessionId,
        crop_x: origCropX, crop_y: origCropY, crop_size: origCropSize,
        background_color: this.bgColor,
        remove_background: this.bgMode === 'remove',
        category_code: this.categoryCode || undefined,
      }
      try {
        this.addLog('Запрос превью…')
        const t0 = Date.now()
        const prevR = await api.post('/image-processor/preview/', body, { timeout: 120000 })
        if (prevR.data.preview) {
          this.previewUrl = prevR.data.preview
          this.addLog(`Превью готово (${(Date.now()-t0)/1000|0}с)`)
        }
        this.addLog('Генерация WebP…')
        const cropR = await api.post('/image-processor/crop/', body, { timeout: 120000 })
        if (cropR.data.results || cropR.data.variants) {
          if (cropR.data.results) {
            const info = [`SM: ${cropR.data.results.sm?.size||'?'}`, `MD: ${cropR.data.results.md?.size||'?'}`, `LG: ${cropR.data.results.lg?.size||'?'}`]
            if (cropR.data.bg_removed_full_pct !== undefined) {
              info.push(`фон: ${cropR.data.bg_removed_full_pct}% / в кадре ${cropR.data.bg_removed_crop_pct}%`)
            }
            this.addLog(`Готово! ${info.join(', ')}`)
          } else {
            const roleCount = Object.keys(cropR.data.variants).length
            this.addLog(`Готово! Профиль «${cropR.data.category}», ролей: ${roleCount}`)
          }
          this.$emit('crop-complete', cropR.data)
        } else if (cropR.data.error) {
          this.addLog(cropR.data.error, true)
        }
      } catch (err) {
        this.addLog(err.displayMessage || err.message || 'Ошибка', true)
        console.error('Crop failed:', err)
      }
      this.processing = false
    },
  },
}
</script>

<style scoped>
.image-cropper { font-family: var(--cat-font, system-ui, sans-serif); max-width: 960px; margin: 0 auto; }
.cropper-upload { text-align: center; padding: 40px; }
.upload-btn { display: inline-block; padding: 12px 32px; background: var(--cat-primary, #3b82f6); color: #fff; border-radius: 8px; cursor: pointer; font-size: 16px; }
.error { color: #ef4444; margin-top: 8px; }
.cropper-toolbar { display: flex; align-items: center; gap: 16px; padding: 12px 0; flex-wrap: wrap; }
.bg-picker { display: flex; align-items: center; gap: 6px; font-size: 14px; }
.bg-picker input[type="color"] { width: 32px; height: 28px; border: none; cursor: pointer; }
.bg-mode-select { display: flex; align-items: center; gap: 4px; font-size: 14px; }
.bg-mode-select select { padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; }
.alpha-note { font-size: 12px; color: #22c55e; background: #dcfce7; padding: 1px 6px; border-radius: 3px; white-space: nowrap; }
.btn-primary { padding: 8px 24px; background: var(--cat-primary, #3b82f6); color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-ghost { padding: 8px 16px; background: transparent; border: 1px solid #ccc; border-radius: 6px; cursor: pointer; font-size: 14px; }
.cropper-canvas-wrap { position: relative; border: 1px solid #ddd; border-radius: 4px; overflow: hidden; background: #f5f5f5; cursor: grab; user-select: none; }
.cropper-canvas-wrap:active { cursor: grabbing; }
.cropper-canvas-wrap canvas { display: block; max-width: 100%; }
.hint { font-size: 13px; color: #888; margin-top: 8px; }
.cropper-log { margin-top: 12px; padding: 10px 14px; background: #1e1e2e; border-radius: 6px; font-family: 'Consolas', 'Courier New', monospace; font-size: 12px; max-height: 200px; overflow-y: auto; }
.log-line { padding: 2px 0; }
.log-time { color: #6c7086; margin-right: 8px; }
.log-msg { color: #a6e3a1; }
.log-err { color: #f38ba8; }
.cropper-preview { margin-top: 20px; padding: 16px; border: 1px solid #e5e7eb; border-radius: 8px; }
.cropper-preview h4 { margin: 0 0 8px; font-size: 14px; }
.cropper-preview img { max-width: 400px; max-height: 400px; border-radius: 4px; }
</style>