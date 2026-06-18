<!-- pages/PdfToDocxTest.vue -->
<template>
  <div class="page">
    <h1>📄 PDF → Word — экспорт форматированного текста</h1>

    <div class="upload-bar">
      <label class="upload-btn">
        <input type="file" accept=".pdf" @change="onFileSelected" hidden ref="fileInput" />
        <span>{{ file ? '📎 ' + file.name : '📁 Выбрать PDF' }}</span>
      </label>
    </div>

    <div class="status-line" v-if="status">{{ status }}</div>

    <div v-if="file && !converting" class="actions">
      <label class="strip-check"><input type="checkbox" v-model="stripImages" /> Без картинок (для PDF со сканом + OCR)</label>
      <button @click="convert" class="btn-primary">📥 Конвертировать в DOCX</button>
      <button @click="preview" class="btn-secondary">🔍 Превью блоков</button>
    </div>

    <div v-if="downloadUrl" class="download-link">
      <a :href="downloadUrl" :download="downloadName">💾 Скачать {{ downloadName }}</a>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const fileInput = ref(null)
const file = ref(null)
const converting = ref(false)
const status = ref('')
const downloadUrl = ref('')
const downloadName = ref('')
const stripImages = ref(false)

function onFileSelected(e) {
  file.value = e.target.files[0]
  status.value = ''
  downloadUrl.value = ''
}

async function convert() {
  if (!file.value) return
  converting.value = true
  status.value = '⏳ Загрузка...'
  downloadUrl.value = ''

  const form = new FormData()
  form.append('file', file.value)
  const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || ''
  const base = 'http://127.0.0.1:8000/api/svg-converter/to-docx'
  const url = stripImages.value ? base + '/?strip_images=1' : base + '/'

  try {
    // POST — запустить конвертацию
    const r = await fetch(url, {
      method: 'POST', body: form,
      headers: { 'X-CSRFToken': csrf }, credentials: 'include',
    })
    if (!r.ok) {
      const data = await r.json().catch(() => ({}))
      status.value = '❌ ' + (data.error || `Ошибка ${r.status}`)
      converting.value = false
      return
    }
    const { task_id } = await r.json()
    if (!task_id) { status.value = '❌ Нет task_id'; converting.value = false; return }

    // Опрос статуса раз в 10 секунд
    const poll = async () => {
      const sr = await fetch(`${base}/${task_id}/`, { credentials: 'include' })
      const data = await sr.json()
      const ts = new Date().toLocaleTimeString()
      if (data.status === 'done') {
        downloadUrl.value = data.download_url
        downloadName.value = data.filename
        status.value = `✅ Готово — ${data.filename} [${ts}]`
        converting.value = false
      } else if (data.status === 'error') {
        status.value = `❌ ${data.message || 'Ошибка'} [${ts}]`
        converting.value = false
      } else {
        const elapsed = data.elapsed ? ` (${data.elapsed}с)` : ''
        status.value = `🔄 ${data.message || 'Обработка...'}${elapsed} [${ts}]`
        setTimeout(poll, 10000)
      }
    }
    poll()
  } catch (e) {
    status.value = '❌ ' + (e.message || 'Ошибка конвертации')
    converting.value = false
  }
}

async function preview() {
  if (!file.value) return
  status.value = '🔍 Извлечение блоков...'
  const form = new FormData(); form.append('file', file.value)
  const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || ''
  try {
    const r = await fetch('http://127.0.0.1:8000/api/svg-converter/to-docx/?preview=1', {
      method: 'POST', body: form,
      headers: { 'X-CSRFToken': csrf }, credentials: 'include',
    })
    const data = await r.json()
    if (data.pages) {
      const total = data.pages.reduce((n, p) => n + p.blocks.length, 0)
      status.value = `📋 Страниц: ${data.total_pages}, блоков: ${total}`
      console.log('Preview blocks:', data)
    } else {
      status.value = '❌ ' + (data.error || 'Ошибка превью')
    }
  } catch (e) {
    status.value = '❌ ' + e.message
  }
}
</script>

<style scoped>
.page { max-width: 700px; margin: 0 auto; padding: 24px 16px; font-family: system-ui, sans-serif; }
h1 { font-size: 22px; margin-bottom: 16px; }
.upload-bar { margin-bottom: 16px; }
.upload-btn { cursor: pointer; padding: 10px 20px; background: #f3f4f6; border: 1px dashed #999; border-radius: 8px; display: inline-block; font-size: 14px; }
.upload-btn:hover { background: #e5e7eb; }
.actions { margin-top: 12px; margin-bottom: 12px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.strip-check { font-size: 13px; color: #555; cursor: pointer; display: flex; align-items: center; gap: 4px; }
.btn-primary { padding: 10px 24px; background: #2563eb; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
.btn-secondary { padding: 10px 24px; background: #e5e7eb; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; font-size: 14px; }
.status-line {
  margin: 12px 0; padding: 8px 14px;
  background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 6px;
  font-size: 13px; font-family: monospace; color: #0369a1;
  min-height: 20px;
}
.download-link { margin-top: 10px; }
.download-link a { color: #2563eb; font-size: 14px; text-decoration: none; font-weight: 600; }
.download-link a:hover { text-decoration: underline; }
</style>
