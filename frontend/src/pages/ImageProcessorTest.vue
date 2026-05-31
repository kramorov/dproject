<!-- pages/ImageProcessorTest.vue -->
<template>
  <div class="page">
    <h1>🖼️ Image Processor — тест профилей</h1>

    <!-- Выбор категории -->
    <div class="category-bar">
      <label>Категория:</label>
      <select v-model="categoryCode" class="cat-select">
        <option value="">— стандарт (sm/md/lg) —</option>
        <option v-for="c in categories" :key="c.code" :value="c.code">
          {{ c.icon }} {{ c.name }}
        </option>
      </select>
    </div>

    <!-- Профиль -->
    <div v-if="profile" class="profile-card">
      <strong>Профиль «{{ categoryCode }}»</strong>
      <div class="profile-roles">
        <div v-for="vs in profile.variants" :key="vs.role" class="profile-role">
          <span class="role-name">{{ vs.role }}</span>
          <span v-for="w in vs.widths" :key="w" class="chip">{{ w }}px {{ vs.format }}</span>
        </div>
      </div>
      <div class="profile-meta">
        multi_page: {{ profile.multi_page }} |
        dpi: {{ profile.render_dpi }} |
        alpha: {{ profile.keep_alpha }}
      </div>
    </div>

    <!-- PDF upload (for CERTIFICATE etc.) -->
    <div v-if="isPdfCategory" class="pdf-upload">
      <label class="upload-btn">
        <input type="file" accept=".pdf" @change="onPdfSelected" hidden ref="pdfInput" />
        <span>📄 {{ pdfUploaded ? 'Заменить PDF' : 'Выбрать PDF' }}</span>
      </label>
      <button v-if="sessionId" @click="processPdf" class="btn-primary" :disabled="pdfProcessing">
        {{ pdfProcessing ? 'Обработка...' : 'Обработать PDF' }}
      </button>
      <p v-if="pdfError" class="error">{{ pdfError }}</p>
    </div>

    <!-- Кроппер (для изображений) -->
    <ImageCropper v-if="!isPdfCategory"
      :categoryCode="categoryCode"
      @crop-complete="onCropComplete"
    />

    <!-- Старый формат: sm/md/lg -->
    <div v-if="cropData && !profileResult" class="results">
      <h3>Результаты (стандартный режим)</h3>
      <div class="sizes-summary">
        <div class="size-row">
          <span>Исходный</span>
          <strong>{{ fmtSize(cropData.original_size) }}</strong>
        </div>
        <div class="size-row">
          <span>Обрезанный</span>
          <strong>{{ fmtSize(cropData.cropped_size) }}</strong>
          <span class="saving" v-if="cropData.original_size && cropData.cropped_size">
            –{{ pct(cropData.cropped_size, cropData.original_size) }}%
          </span>
        </div>
      </div>
      <div class="variants-row">
        <div v-for="(v, size) in cropData.results" :key="size" class="variant-card">
          <p class="size-label">{{ size.toUpperCase() }} ({{ dims[size] }})</p>
          <img :src="v.url" :alt="size" />
          <p class="file-size">{{ fmtSize(v.size) }}</p>
          <a :href="v.url" target="_blank" class="link">Открыть</a>
        </div>
      </div>
    </div>

    <!-- Новый формат: профиль -->
    <div v-if="profileResult" class="results">
      <h3>Результаты — профиль «{{ profileResult.category }}»</h3>
      <div v-for="(roleVariants, role) in profileResult.variants" :key="role" class="role-group">
        <h4>{{ role }}</h4>
        <div class="variants-row">
          <div v-for="(v, width) in roleVariants" :key="width" class="variant-card">
            <p class="size-label">{{ width }}px {{ v.format }}</p>
            <img :src="v.data" :alt="`${role} ${width}px`" />
            <p class="file-size">{{ fmtSize(v.size) }}</p>
            <a href="#" @click.prevent="openImage($event, v.data)" class="link">Открыть</a>
          </div>
        </div>
      </div>
    </div>

    <!-- PDF results -->
    <div v-if="pdfResult" class="results">
      <h3>Результаты — профиль «{{ pdfResult.category }}» ({{ pdfResult.total_pages }} стр.)</h3>

      <!-- Email: combined PDF -->
      <div v-if="pdfResult.email_pdf" class="email-card">
        <h4>📧 Email — PDF (все страницы)</h4>
        <p class="email-size-info" v-if="pdfResult.original_size">
          Исходный PDF: {{ fmtSize(pdfResult.original_size) }}
          <span v-for="(v, key) in pdfResult.email_pdf" :key="key">
            → сжатый ({{ v.dpi }} dpi): {{ fmtSize(v.size) }}
            ({{ (100 - v.size / pdfResult.original_size * 100).toFixed(0) }}%)
          </span>
        </p>
        <div class="variants-row">
          <div v-for="(v, key) in pdfResult.email_pdf" :key="key" class="variant-card email-pdf-card">
            <p class="size-label">{{ v.dpi }} dpi PDF</p>
            <div class="pdf-icon">📄 {{ v.pages }} стр.</div>
            <p class="file-size">{{ fmtSize(v.size) }}</p>
            <a href="#" @click.prevent="openImage($event, v.data)" class="link">Открыть PDF</a>
          </div>
        </div>
      </div>

      <div v-for="page in pdfResult.pages" :key="page.n" class="pdf-page">
        <h4>Страница {{ page.n }}</h4>
        <template v-for="(roleVariants, role) in page" :key="role">
          <div v-if="role !== 'n'" class="role-group">
            <h5>{{ role }}</h5>
            <div class="variants-row">
              <div v-for="(v, width) in roleVariants" :key="width" class="variant-card">
                <p class="size-label">{{ width }}px {{ v.format }}</p>
                <img :src="v.data" :alt="`стр.${page.n} ${role} ${width}px`" />
                <p class="file-size">{{ fmtSize(v.size) }}</p>
                <a href="#" @click.prevent="openImage($event, v.data)" class="link">Открыть</a>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import ImageCropper from '@/shared/components/ImageCropper.vue'

// Список категорий с непустыми профилями
const CATEGORIES = [
  { code: 'PRODUCT_GALLERY', name: 'Галерея товара', icon: '📷' },
  { code: 'BANNER',          name: 'Баннер',         icon: '🖼️' },
  { code: 'CERTIFICATE',     name: 'Сертификат',     icon: '🏆' },
  { code: 'SCHEMA',          name: 'Схема',          icon: '🔌' },
  { code: 'DRAWING',         name: 'Чертёж',         icon: '📐' },
  { code: 'DIAGRAM',         name: 'Диаграмма',      icon: '📊' },
  { code: 'TECH_DOC',        name: 'Техдокументация', icon: '📋' },
]

// Профили (зеркало MediaCategory.PRESENTATION_PROFILES — для отображения до загрузки)
const PROFILES = {
  PRODUCT_GALLERY: { variants: [{role:'icon',widths:[50],format:'webp',quality:80},{role:'thumb',widths:[80,150],format:'webp',quality:80},{role:'card',widths:[400,800],format:'webp',quality:80}], multi_page:false, render_dpi:72,  keep_alpha:true },
  BANNER:          { variants: [{role:'full',widths:[1200,1920],format:'webp',quality:85}], multi_page:false, render_dpi:72,  keep_alpha:false },
  CERTIFICATE: { variants: [{role:'icon',widths:[50],format:'webp',quality:80},{role:'page',widths:[600],format:'webp',quality:85},{role:'email',widths:[800],format:'webp',quality:80}], multi_page:true,  render_dpi:150, keep_alpha:false },
  SCHEMA:      { variants: [{role:'icon',widths:[50],format:'webp',quality:80},{role:'card',widths:[150,400],format:'webp',quality:80},{role:'full',widths:[800,1600],format:'webp',quality:80}], multi_page:false, render_dpi:150, keep_alpha:false },
  DRAWING:     { variants: [{role:'icon',widths:[50],format:'webp',quality:80},{role:'full',widths:[800,1600],format:'webp',quality:85}], multi_page:false, render_dpi:150, keep_alpha:false },
  DIAGRAM:     { variants: [{role:'icon',widths:[50],format:'webp',quality:80},{role:'card',widths:[150,400],format:'webp',quality:80},{role:'full',widths:[800,1600],format:'webp',quality:80}], multi_page:false, render_dpi:150, keep_alpha:false },
  TECH_DOC:    { variants: [{role:'icon',widths:[50],format:'webp',quality:80},{role:'page',widths:[800],format:'webp',quality:85},{role:'email',widths:[800],format:'webp',quality:80}], multi_page:true,  render_dpi:150, email_dpi:100, keep_alpha:false },
}

const SIZES = { sm: '150×150', md: '400×400', lg: '800×800' }

export default {
  name: 'ImageProcessorTest',
  components: { ImageCropper },
  data() {
    return {
      categoryCode: '',
      categories: CATEGORIES,
      dims: SIZES,
      cropData: null,
      profileResult: null,
      // PDF
      sessionId: null,
      pdfUploaded: false,
      pdfProcessing: false,
      pdfError: '',
      pdfResult: null,
    }
  },
  computed: {
    profile() {
      return this.categoryCode ? PROFILES[this.categoryCode] || null : null
    },
    isPdfCategory() {
      return this.categoryCode === 'CERTIFICATE' || this.categoryCode === 'TECH_DOC'
    },
  },
  methods: {
    async openImage(ev, dataUri) {
      ev.preventDefault()
      const resp = await fetch(dataUri)
      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank')
    },
    onCropComplete(data) {
      if (data.category) {
        this.cropData = null; this.profileResult = data
      } else {
        this.profileResult = null; this.cropData = data
      }
    },
    async onPdfSelected(e) {
      const file = e.target.files[0]
      if (!file) return
      this.pdfError = ''; this.pdfProcessing = true; this.pdfResult = null
      const form = new FormData(); form.append('file', file)
      const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || ''
      try {
        const r = await fetch('/api/image-processor/upload/', {
          method: 'POST', body: form,
          headers: { 'X-CSRFToken': csrf }, credentials: 'include',
        })
        const data = await r.json()
        if (r.ok && data.session_id) {
          this.sessionId = data.session_id
          this.pdfUploaded = true
          this.pdfError = ''
          // Автозапуск обработки
          this.processPdf()
        } else {
          this.pdfError = data.error || 'Upload failed'
        }
      } catch (err) {
        this.pdfError = err.message || 'Upload error'
        this.pdfProcessing = false
      }
    },
    async processPdf() {
      if (!this.sessionId || !this.categoryCode) return
      this.pdfProcessing = true; this.pdfError = ''; this.pdfResult = null
      try {
        const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || ''
        const r = await fetch('/api/image-processor/crop/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
          body: JSON.stringify({
            session_id: this.sessionId,
            category_code: this.categoryCode,
            crop_x: 0, crop_y: 0, crop_size: 0, // фиктивные, для PDF не используются
          }),
        })
        const data = await r.json()
        if (data.pages) {
          this.pdfResult = data
        } else if (data.error) {
          this.pdfError = data.error
        }
      } catch (err) {
        this.pdfError = err.message || 'Process error'
      }
      this.pdfProcessing = false
    },
    fmtSize(b) {
      if (!b) return '—'
      if (b < 1024) return b + ' B'
      if (b < 1048576) return (b / 1024).toFixed(1) + ' KB'
      return (b / 1048576).toFixed(1) + ' MB'
    },
    pct(small, big) {
      if (!big) return '0'
      return (100 - Math.round((small / big) * 100))
    },
  },
}
</script>

<style scoped>
.page { max-width: 1000px; margin: 0 auto; padding: 24px 16px; font-family: var(--cat-font, system-ui, sans-serif); }
h1 { font-size: 22px; margin-bottom: 20px; }

/* Category selector */
.category-bar { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
.category-bar label { font-size: 14px; color: #555; }
.cat-select { padding: 6px 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 14px; }

/* PDF upload */
.pdf-upload { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.pdf-upload .upload-btn { cursor: pointer; }
.pdf-upload .btn-primary { padding: 8px 20px; background: var(--cat-primary, #3b82f6); color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
.pdf-upload .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.pdf-page { margin-bottom: 24px; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; }
.pdf-page h4 { margin: 0 0 8px; font-size: 15px; color: #374151; }
.pdf-page h5 { font-size: 12px; color: #6b7280; text-transform: uppercase; margin: 8px 0 4px; }
.email-card { background: #fefce8; border: 1px solid #fde68a; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px; }
.email-card h4 { margin: 0 0 4px; font-size: 15px; }
.email-size-info { font-size: 13px; color: #666; margin: 0 0 8px; }
.email-pdf-card { background: #fff; }
.pdf-icon { font-size: 32px; text-align: center; padding: 12px 0 4px; }

/* Profile card */
.profile-card { background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px; font-size: 13px; }
.profile-roles { margin: 6px 0; }
.profile-role { margin: 3px 0; display: flex; align-items: center; gap: 6px; }
.role-name { font-weight: 600; min-width: 40px; color: #0369a1; }
.chip { background: #e0f2fe; color: #0284c7; padding: 1px 8px; border-radius: 10px; font-size: 12px; }
.profile-meta { color: #888; margin-top: 6px; }

/* Results */
.results { margin-top: 28px; }
.results h3 { font-size: 16px; margin-bottom: 12px; }
.results h4 { font-size: 14px; color: #555; margin: 12px 0 6px; text-transform: uppercase; }
.role-group { margin-bottom: 16px; }

.sizes-summary { margin-bottom: 16px; }
.size-row { display: flex; align-items: center; gap: 12px; padding: 6px 0; font-size: 14px; }
.size-row span:first-child { color: #666; min-width: 140px; }
.size-row strong { color: #111; min-width: 70px; }
.saving { color: #16a34a; font-size: 13px; }

.variants-row { display: flex; gap: 12px; flex-wrap: wrap; }
.variant-card {
  border: 1px solid #e5e7eb; border-radius: 8px;
  padding: 10px; text-align: center; width: 180px;
}
.variant-card img { max-width: 100%; max-height: 180px; border-radius: 4px; }
.size-label { font-size: 12px; color: #888; margin-bottom: 4px; }
.file-size { font-size: 13px; color: #111; margin: 4px 0; }
.link { font-size: 12px; color: var(--cat-primary, #3b82f6); display: block; margin-top: 4px; }
</style>