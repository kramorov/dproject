<!-- pages/TableOcrTool.vue — единая структура: разделы / текст / таблицы (изображения и PDF) -->
<template>
  <div class="ocr">
    <header class="toolbar">
      <label class="upload-btn">
        <input type="file" accept="image/*,.pdf" @change="onFileSelected" hidden />
        <span>{{ file ? '📎 ' + file.name : '📁 Выбрать изображение или PDF' }}</span>
      </label>
      <span class="toolbar-hint">
        Обведите область — фрагмент распознается и встанет на холст. Начало блока — выделение раздела.
        PDF разбивается на страницы.
      </span>
    </header>

    <div class="body">
      <!-- слева: изображение для распознавания -->
      <div class="preview-pane">
        <div v-if="pages.length > 1" class="page-nav">
          <button class="mini" :disabled="pageIndex === 0" @click="goPage(-1)">‹</button>
          <span class="page-nav-label">Страница {{ pageIndex + 1 }} из {{ pages.length }}</span>
          <button class="mini" :disabled="pageIndex >= pages.length - 1" @click="goPage(1)">›</button>
        </div>

        <div v-if="pageBusy" class="placeholder">⏳ Открываю PDF…</div>

        <div v-else-if="currentUrl" class="preview-wrap" @mousemove="onImgHover" @mouseleave="onImgLeave">
          <img :key="pageIndex" ref="previewImg" :src="currentUrl" class="preview-img" alt="preview"
            draggable="false" @dragstart.prevent
            @load="onImgLoad" @mousedown="onImgMouseDown" />

          <div v-for="o in overlays" :key="o.uid" class="node-overlay"
            :class="['ov-' + o.kind, { 'ov-editing': o.uid === editingUid }]" :style="dispStyle(o.region)"></div>

          <div v-for="h in editHandlePositions" :key="h.corner" class="region-handle" :class="'handle-' + h.corner"
            :style="h.style" @mousedown.stop.prevent="onHandleDown(h.corner, $event)"></div>

          <div v-if="drawRect.w > 3 && drawRect.h > 3" class="draw-overlay" :style="drawRectStyle"></div>
        </div>
        <div v-else class="placeholder">Загрузите изображение или PDF</div>

        <div v-if="magnifierOn && hoverPos" class="magnifier" :style="magnifierStyle"><span class="magnifier-cross"></span></div>
      </div>

      <!-- между изображением и холстом: инструменты выделения -->
      <div class="tools-pane">
        <button class="tool" :class="{ 'tool-active': selMode === 'section' }" :disabled="!currentUrl" @click="setSel('section')">＋ Раздел</button>
        <button class="tool" :class="{ 'tool-active': selMode === 'text' }" :disabled="!currentUrl" @click="setSel('text')">＋ Текст</button>
        <button class="tool" :class="{ 'tool-active': selMode === 'fv' }" :disabled="!currentUrl" @click="setSel('fv')">＋ Таблица F-V</button>
        <button class="tool" :class="{ 'tool-active': selMode === 'grid' }" :disabled="!currentUrl" @click="setSel('grid')">＋ Таблица</button>

        <div class="tool-opts">
          <div class="tool-opts-title">Классическая таблица</div>
          <label class="mini-check"><input v-model="useHeader" type="checkbox" /> шапка в 1-й строке</label>
          <label class="mini-check"><input v-model="borderless" type="checkbox" /> без линий</label>
        </div>

        <button class="tool" :class="magnifierOn ? 'tool-active' : ''" @click="magnifierOn = !magnifierOn">🔍 Лупа</button>

        <span v-if="selMode" class="hint">{{ selHint }}</span>
        <span v-else-if="busy" class="hint">⏳ Распознаю…</span>
      </div>

      <!-- справа: холст заданий / структура результата -->
      <aside class="canvas-pane">
        <div v-if="error" class="error">{{ error }}</div>

        <div class="row-actions">
          <button class="btn" @click="copyJSON">📋 JSON</button>
          <button class="btn" @click="downloadJSON">💾 JSON</button>
          <button class="btn" @click="copyTextAll">📋 Текст</button>
          <button class="btn" @click="downloadText">💾 Текст</button>
          <button class="btn" @click="reRecognizeAll" :disabled="!flatList.length || busy || pageBusy">⟳ Распознать всё</button>
          <button class="btn" @click="exportStructure('xlsx')" :disabled="!flatList.length">💾 Excel</button>
          <button class="btn" @click="exportStructure('docx')" :disabled="!flatList.length">💾 Word</button>
        </div>

        <div class="root-zone"
          :class="{ 'drop-root': dragOverRoot }"
          @dragover.prevent="dragOverRoot = true"
          @dragleave="onRootDragLeave"
          @drop.prevent="onRootDrop"
          @click="activeSectionUid = null"
        >
          <div class="root-title" :class="{ 'root-active': !activeSectionUid }" @click="activeSectionUid = null; editingUid = null">▸ Главный раздел</div>

          <div v-if="!flatList.length" class="hint">
            Фрагменты появятся здесь. Новые выделения попадают в активный раздел (подсвечен),
            пока разделов нет — в главный.
          </div>

          <div v-for="f in flatList" :key="f.node.uid"
            class="block"
            :class="{ 'block-active': isActive(f), 'drop-over': dropOverUid === f.node.uid, 'block-editing': f.node.uid === editingUid }"
            :style="{ marginLeft: (f.depth * 18) + 'px' }"
            draggable="true"
            @dragstart="onDragStart(f.node.uid, $event)"
            @dragover.prevent="onBlockDragOver(f)"
            @dragleave="onBlockDragLeave(f)"
            @drop.prevent="onBlockDrop(f)"
            @click.stop="activate(f)"
            @dblclick.stop="openDetail(f)"
          >
            <div class="block-head">
              <div v-if="f.node.region" class="frag-crop" :style="cropStyle(f.node.region)"></div>
              <div class="frag-body">
                <div class="frag-kind">
                  {{ kindLabel(f) }}
                  <span v-if="pages.length > 1" class="page-badge">· стр. {{ f.node.page || 1 }}</span>
                </div>
                <div class="frag-text">{{ fragText(f) }}</div>
              </div>
              <div class="frag-actions">
                <button class="mini" title="Вверх" @click.stop="moveFrag(f, -1)">↑</button>
                <button class="mini" title="Вниз" @click.stop="moveFrag(f, 1)">↓</button>
                <button class="mini" title="Вложить в предыдущий раздел" @click.stop="indentFrag(f)">↳</button>
                <button class="mini" title="Наружу" @click.stop="outdentFrag(f)">↰</button>
                <button class="mini danger" title="Удалить" @click.stop="deleteFrag(f)">✕</button>
              </div>
            </div>

            <div v-if="f.node.uid === editingUid" class="edit-bar">
              <span class="hint" style="margin:0">Тяните углы области на изображении</span>
              <button class="btn" @click.stop="recognizeBlock(f.node)" :disabled="busy">⟳ Распознать</button>
              <button class="btn" @click.stop="acceptEdit">✓ Готово</button>
              <button class="mini danger" @click.stop="cancelEdit">✕</button>
            </div>

            <div v-if="isFv(f) && f.node.rows.length" class="block-detail">
              <table class="mini-grid">
                <tbody>
                  <tr v-for="(r, ri) in f.node.rows" :key="ri"><td class="td-f">{{ r.field }}</td><td>{{ r.value }}</td></tr>
                </tbody>
              </table>
            </div>
            <div v-else-if="isGrid(f) && f.node.rows.length" class="block-detail">
              <table class="mini-grid">
                <thead v-if="f.node.headers.length"><tr><th v-for="(c, ci) in f.node.headers" :key="ci">{{ c }}</th></tr></thead>
                <tbody><tr v-for="(r, ri) in f.node.rows" :key="ri"><td v-for="(c, ci) in r" :key="ci">{{ c ?? '' }}</td></tr></tbody>
              </table>
            </div>
          </div>
        </div>

        <div v-if="flatList.length" class="summary">Блоков: {{ flatList.length }}</div>
      </aside>
    </div>

    <div v-if="detailNode" class="modal-backdrop" @click.self="closeDetail">
      <div class="modal">
        <div class="modal-head">
          <span class="modal-title">{{ detailTitle }}</span>
          <button class="btn" @click="copyDetail">📋 Копировать</button>
          <button class="mini danger" @click="closeDetail">✕</button>
        </div>
        <div class="modal-body">
          <pre v-if="detailNode.kind !== 'table'" class="text-pre">{{ detailNode.kind === 'section' ? detailNode.title : detailNode.text }}</pre>
          <table v-else-if="detailNode.variant !== 'grid'" class="mini-grid">
            <tbody>
              <tr v-for="(r, ri) in detailNode.rows" :key="ri"><td class="td-f">{{ r.field }}</td><td>{{ r.value }}</td></tr>
            </tbody>
          </table>
          <table v-else class="mini-grid">
            <thead v-if="detailNode.headers.length"><tr><th v-for="(c, ci) in detailNode.headers" :key="ci">{{ c }}</th></tr></thead>
            <tbody><tr v-for="(r, ri) in detailNode.rows" :key="ri"><td v-for="(c, ci) in r" :key="ci">{{ c ?? '' }}</td></tr></tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-if="toast" class="toast">{{ toast }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import api from '@/shared/api'
import { API_URL, API_PREFIX } from '@/shared/config'

const SCHEMA_VERSION = 2

// ── состояние ──
const file = ref(null)
const isPdf = ref(false)
const pagesToken = ref('')
const fileSha256 = ref('')
const pages = ref([])       // [{ url, w, h }] — objectURL (изображение) или server-URL (PDF)
const pageIndex = ref(0)
const pageBusy = ref(false)
const busy = ref(false)
const error = ref('')
const toast = ref('')

const useHeader = ref(true)   // классическая таблица: первая строка — заголовки
const borderless = ref(false) // классическая таблица: без линий

// ── дерево структуры (головной раздел всегда пустой и неявный) ──
const tree = ref([])                // корневые узлы
const activeSectionUid = ref(null)  // активный раздел — куда попадают новые фрагменты
const selMode = ref(null)           // 'section'|'text'|'fv'|'grid'
let uidSeq = 0

const selHint = computed(() => ({
  section: 'Обведите название раздела',
  text: 'Обведите фрагмент текста',
  fv: 'Обведите таблицу из двух столбцов (поле → значение)',
  grid: 'Обведите таблицу целиком',
}[selMode.value] || ''))

// ── изображение / страницы ──
const previewImg = ref(null)
const scale = ref(1)

const drawing = ref(false)
const drawStart = ref({ x: 0, y: 0 })
const drawRect = ref({ x: 0, y: 0, w: 0, h: 0 })

const magnifierOn = ref(false)
const hoverPos = ref(null)
const magnifierSize = 220
const magnifierZoom = 3

const currentPage = computed(() => pages.value[pageIndex.value] || null)
const currentUrl = computed(() => currentPage.value?.url || '')

// ── drag & drop ──
let dragUid = null
const dropOverUid = ref(null)
const dragOverRoot = ref(false)

// ── редактирование области / попап содержимого ──
const editingUid = ref(null)     // блок, у которого редактируется область
const handleDrag = ref(null)     // { uid, corner, opp: {x, y} } при перетаскивании угла
const detailNode = ref(null)     // блок, открытый в попапе (двойной клик)

// ── вычисляемые ──
const drawRectStyle = computed(() => ({
  left: drawRect.value.x + 'px', top: drawRect.value.y + 'px',
  width: drawRect.value.w + 'px', height: drawRect.value.h + 'px',
}))

const magnifierStyle = computed(() => {
  if (!hoverPos.value || !currentUrl.value || !scale.value) return { display: 'none' }
  const cp = currentPage.value
  if (!cp || !cp.w) return { display: 'none' }
  const nx = hoverPos.value.x * scale.value
  const ny = hoverPos.value.y * scale.value
  const left = Math.min(window.innerWidth - magnifierSize - 16, hoverPos.value.clientX + 24)
  const top = Math.min(window.innerHeight - magnifierSize - 16, hoverPos.value.clientY + 24)
  return {
    width: magnifierSize + 'px', height: magnifierSize + 'px',
    left: Math.max(8, left) + 'px', top: Math.max(8, top) + 'px',
    backgroundImage: `url("${currentUrl.value}")`,
    backgroundSize: `${cp.w * magnifierZoom}px ${cp.h * magnifierZoom}px`,
    backgroundPosition: `${-(nx * magnifierZoom) + magnifierSize / 2}px ${-(ny * magnifierZoom) + magnifierSize / 2}px`,
  }
})

// плоский список блоков холста (для отрисовки и dnd)
const flatList = computed(() => {
  const out = []
  const walk = (nodes, depth, parentArray, ownerUid) => {
    for (let i = 0; i < nodes.length; i++) {
      const n = nodes[i]
      out.push({ node: n, depth, parentArray, index: i, ownerUid })
      if (n.kind === 'section') walk(n.children, depth + 1, n.children, n.uid)
    }
  }
  walk(tree.value, 0, tree.value, null)
  return out
})

// оверлеи на превью (только для текущей страницы)
const overlays = computed(() => {
  const out = []
  const walk = (nodes) => {
    for (const n of nodes) {
      if (n.region && (n.page || 1) === pageIndex.value + 1) {
        const kind = n.kind === 'table' ? (n.variant === 'grid' ? 'grid' : 'fv') : n.kind
        out.push({ uid: n.uid, kind, region: n.region })
      }
      if (n.kind === 'section') walk(n.children)
    }
  }
  walk(tree.value)
  return out
})

function flash(msg) { toast.value = msg; setTimeout(() => { toast.value = '' }, 2200) }

// редактируемый блок и позиции угловых маркеров (display-координаты)
const editingNode = computed(() =>
  flatList.value.find(x => x.node.uid === editingUid.value)?.node || null
)
const editHandlePositions = computed(() => {
  const n = editingNode.value
  if (!n || !n.region || !scale.value) return []
  if ((n.page || 1) !== pageIndex.value + 1) return []
  const x = n.region.x / scale.value
  const y = n.region.y / scale.value
  const w = n.region.w / scale.value
  const h = n.region.h / scale.value
  const s = 6
  return [
    { corner: 'tl', style: { left: (x - s) + 'px', top: (y - s) + 'px' } },
    { corner: 'tr', style: { left: (x + w - s) + 'px', top: (y - s) + 'px' } },
    { corner: 'bl', style: { left: (x - s) + 'px', top: (y + h - s) + 'px' } },
    { corner: 'br', style: { left: (x + w - s) + 'px', top: (y + h - s) + 'px' } },
  ]
})
const detailTitle = computed(() => {
  const n = detailNode.value
  if (!n) return ''
  if (n.kind === 'section') return 'Раздел: ' + (n.title || '(без названия)')
  if (n.kind === 'text') return 'Текст'
  return n.variant === 'grid' ? 'Таблица' : 'Таблица F-V'
})

// ── файл / страницы ──
async function onFileSelected(e) {
  const f = e.target.files?.[0]
  if (!f) return
  error.value = ''
  tree.value = []
  activeSectionUid.value = null
  selMode.value = null
  pageIndex.value = 0
  pagesToken.value = ''
  fileSha256.value = ''
  for (const p of pages.value) if (p.url && p.url.startsWith('blob:')) URL.revokeObjectURL(p.url)
  pages.value = []
  file.value = f
  computeSha256(f).then(h => { fileSha256.value = h })
  resetImage()

  const type = f.type || ''
  isPdf.value = type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf')
  if (!isPdf.value) {
    if (!type.startsWith('image/')) {
      file.value = null
      error.value = 'Поддерживаются только изображения и PDF.'
      return
    }
    pages.value = [{ url: URL.createObjectURL(f), w: 0, h: 0 }]
    return
  }

  pageBusy.value = true
  try {
    const fd = new FormData()
    fd.append('file', f)
    const { data } = await api.post('/admin/media/ocr/pages/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    pagesToken.value = data.token
    pages.value = (data.pages || []).map((p, i) => ({
      url: `${API_URL}${API_PREFIX}/admin/media/ocr/pages/${data.token}/${i + 1}/`,
      w: p.w, h: p.h,
    }))
  } catch (err) {
    file.value = null
    error.value = err?.displayMessage || err?.message || 'Не удалось открыть PDF'
  } finally {
    pageBusy.value = false
  }
}

async function computeSha256(f) {
  try {
    const buf = await f.arrayBuffer()
    const digest = await crypto.subtle.digest('SHA-256', buf)
    return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, '0')).join('')
  } catch (_) { return '' }
}

function goPage(d) {
  const n = pageIndex.value + d
  if (n < 0 || n >= pages.value.length) return
  pageIndex.value = n
  resetImage()
}

function resetImage() {
  drawRect.value = { x: 0, y: 0, w: 0, h: 0 }
  drawing.value = false
  scale.value = 1
  hoverPos.value = null
}

function onImgLoad() {
  const img = previewImg.value
  const cp = currentPage.value
  if (!img || !cp) return
  cp.w = img.naturalWidth
  cp.h = img.naturalHeight
  if (img.clientWidth > 0) scale.value = img.naturalWidth / img.clientWidth
}

function imagePoint(e) {
  const img = previewImg.value
  if (!img) return null
  const r = img.getBoundingClientRect()
  return { x: Math.min(Math.max(0, e.clientX - r.left), r.width), y: Math.min(Math.max(0, e.clientY - r.top), r.height) }
}

function onImgHover(e) {
  if (!magnifierOn.value) { if (hoverPos.value) hoverPos.value = null; return }
  const p = imagePoint(e)
  if (!p) return
  hoverPos.value = { x: p.x, y: p.y, clientX: e.clientX, clientY: e.clientY }
}
function onImgLeave() { hoverPos.value = null }

function onImgMouseDown(e) {
  if (!selMode.value || !currentUrl.value) { editingUid.value = null; return }
  if (e.ctrlKey) e.preventDefault()
  const p = imagePoint(e)
  if (!p) return
  drawing.value = true
  drawStart.value = { x: p.x, y: p.y }
  drawRect.value = { x: p.x, y: p.y, w: 0, h: 0 }
}

function onImgMouseMove(e) {
  if (handleDrag.value) {
    const p = imagePoint(e)
    const hd = handleDrag.value
    const n = flatList.value.find(x => x.node.uid === hd.uid)?.node
    const cp = currentPage.value
    if (!p || !n || !cp || !cp.w || !cp.h) return
    const nx = clampNum(p.x * scale.value, 0, cp.w)
    const ny = clampNum(p.y * scale.value, 0, cp.h)
    const opp = hd.opp
    const w = Math.abs(nx - opp.x)
    const h = Math.abs(ny - opp.y)
    if (w < 5 || h < 5) return
    n.region = {
      x: Math.round(Math.min(nx, opp.x)),
      y: Math.round(Math.min(ny, opp.y)),
      w: Math.round(w), h: Math.round(h),
    }
    return
  }
  if (!drawing.value) return
  const p = imagePoint(e)
  if (!p) return
  const sx = drawStart.value.x, sy = drawStart.value.y
  drawRect.value = { x: Math.min(sx, p.x), y: Math.min(sy, p.y), w: Math.abs(p.x - sx), h: Math.abs(p.y - sy) }
}

function onImgMouseUp() {
  if (handleDrag.value) { handleDrag.value = null; return }
  if (!drawing.value) return
  drawing.value = false
  const r = drawRect.value
  drawRect.value = { x: 0, y: 0, w: 0, h: 0 }
  if (r.w < 5 || r.h < 5) return
  const nat = {
    x: Math.round(r.x * scale.value), y: Math.round(r.y * scale.value),
    w: Math.round(r.w * scale.value), h: Math.round(r.h * scale.value),
  }
  processSelection(nat)
}

// ── инструменты и распознавание фрагмента ──
function setSel(m) { selMode.value = selMode.value === m ? null : m }

async function processSelection(nat) {
  const m = selMode.value
  selMode.value = null
  editingUid.value = null
  busy.value = true
  error.value = ''
  try {
    const blob = await pageBlob()
    if (m === 'section') addSection(await ocrTextBlob(blob, nat), nat)
    else if (m === 'text') addText(await ocrTextBlob(blob, nat), nat)
    else if (m === 'fv') addFvTable(await fvTableBlob(blob, nat), nat)
    else if (m === 'grid') addGridTable(await gridTableBlob(blob, nat), nat)
  } catch (e) {
    error.value = e?.displayMessage || e?.message || 'Ошибка распознавания фрагмента'
  } finally {
    busy.value = false
  }
}

async function pageBlob() {
  if (!isPdf.value) return file.value
  const resp = await fetch(pageServerUrl(pageIndex.value + 1), { credentials: 'include' })
  if (!resp.ok) throw new Error('Не удалось получить страницу PDF')
  return await resp.blob()
}
function pageServerUrl(n) {
  return `${API_URL}${API_PREFIX}/admin/media/ocr/pages/${pagesToken.value}/${n}/`
}

function regionFdFor(blob, nat, kind) {
  const fd = new FormData()
  fd.append('file', blob, file.value?.name || 'image')
  fd.append('kind', kind)
  fd.append('x', nat.x); fd.append('y', nat.y); fd.append('w', nat.w); fd.append('h', nat.h)
  return fd
}
async function ocrTextBlob(blob, nat) {
  const { data } = await api.post('/admin/media/ocr/region/', regionFdFor(blob, nat, 'text'), { headers: { 'Content-Type': 'multipart/form-data' } })
  return data.text || ''
}
async function fvTableBlob(blob, nat) {
  const { data } = await api.post('/admin/media/ocr/region/', regionFdFor(blob, nat, 'fvtable'), { headers: { 'Content-Type': 'multipart/form-data' } })
  return data.rows || []
}
async function gridTableBlob(blob, nat) {
  const fd = new FormData()
  fd.append('file', blob, file.value?.name || 'image')
  fd.append('use_first_row_as_header', useHeader.value ? 'true' : 'false')
  fd.append('borderless_tables', borderless.value ? 'true' : 'false')
  fd.append('region_x', nat.x); fd.append('region_y', nat.y)
  fd.append('region_w', nat.w); fd.append('region_h', nat.h)
  const { data } = await api.post('/admin/media/ocr/recognize/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  const t = data?.pages?.[0]?.tables?.[0]
  if (!t) throw new Error('Таблица в области не найдена.')
  return {
    headers: (t.columns || []).map(c => c == null ? '' : String(c)),
    rows: (t.rows || []).map(r => (r || []).map(c => c == null ? '' : String(c))),
  }
}

// ── редактирование области фрагмента ──
function clampNum(v, lo, hi) { return Math.min(Math.max(v, lo), hi) }

function onHandleDown(corner) {
  const n = editingNode.value
  if (!n || !n.region) return
  const r = n.region
  const opp = {
    tl: { x: r.x + r.w, y: r.y + r.h },
    tr: { x: r.x, y: r.y + r.h },
    bl: { x: r.x + r.w, y: r.y },
    br: { x: r.x, y: r.y },
  }[corner]
  handleDrag.value = { uid: n.uid, corner, opp }
}

function acceptEdit() { editingUid.value = null; flash('Область обновлена') }
function cancelEdit() { editingUid.value = null }

async function recognizeBlock(n) {
  if (!n.region || busy.value) return
  busy.value = true
  error.value = ''
  try {
    const page = n.page || 1
    const blob = isPdf.value ? await fetchPageBlob(page) : file.value
    if (n.kind === 'section' || n.kind === 'text') {
      const text = await ocrTextBlob(blob, n.region)
      if (n.kind === 'section') n.title = text
      else n.text = text
    } else if (n.kind === 'table') {
      if (n.variant === 'grid') {
        const t = await gridTableBlob(blob, n.region)
        n.headers = t.headers
        n.rows = t.rows
      } else {
        const rows = await fvTableBlob(blob, n.region)
        n.rows = rows.map(r => ({ field: r.field || '', value: r.value || '' }))
      }
    }
    editingUid.value = null
    flash('Фрагмент перераспознан')
  } catch (e) {
    error.value = e?.displayMessage || e?.message || 'Ошибка перераспознавания фрагмента'
  } finally {
    busy.value = false
  }
}

// ── операции с деревом ──
function makeUid() { return ++uidSeq }

function findSection(nodes, uid) {
  for (const n of nodes) {
    if (n.kind === 'section') {
      if (n.uid === uid) return n
      const r = findSection(n.children, uid)
      if (r) return r
    }
  }
  return null
}

function activeContainer() {
  if (activeSectionUid.value) {
    const s = findSection(tree.value, activeSectionUid.value)
    if (s) return s.children
  }
  return tree.value
}

function addSection(title, region) {
  const node = { uid: makeUid(), kind: 'section', title, region, page: pageIndex.value + 1, children: [] }
  activeContainer().push(node)
  activeSectionUid.value = node.uid
  flash('Раздел добавлен — следующие фрагменты попадут в него')
}
function addText(text, region) {
  const node = { uid: makeUid(), kind: 'text', text, region, page: pageIndex.value + 1 }
  activeContainer().push(node)
  flash('Текст добавлен')
}
function addFvTable(rows, region) {
  const node = {
    uid: makeUid(), kind: 'table', variant: 'fv', region, page: pageIndex.value + 1,
    rows: (rows || []).map(r => ({ field: r.field || '', value: r.value || '' })),
  }
  activeContainer().push(node)
  flash('Таблица F-V добавлена')
}
function addGridTable(tbl, region) {
  const node = { uid: makeUid(), kind: 'table', variant: 'grid', region, page: pageIndex.value + 1, headers: tbl.headers, rows: tbl.rows }
  activeContainer().push(node)
  flash('Таблица добавлена')
}

// ── холст: отображение ──
function kindLabel(f) {
  const n = f.node
  if (n.kind === 'section') return 'раздел'
  if (n.kind === 'text') return 'текст'
  if (n.kind === 'table') return n.variant === 'grid' ? 'таблица' : 'таблица F-V'
  return ''
}
function isFv(f) { return f.node.kind === 'table' && f.node.variant !== 'grid' }
function isGrid(f) { return f.node.kind === 'table' && f.node.variant === 'grid' }
function fragText(f) {
  const n = f.node
  if (n.kind === 'section') return n.title || '(без названия)'
  if (n.kind === 'text') return (n.text || '').split('\n')[0] || '(пусто)'
  if (n.kind === 'table') {
    if (n.variant === 'grid') {
      const head = (n.headers || []).join(' | ')
      const widths = (n.rows || []).map(r => (r || []).length)
      const dims = `${(n.rows || []).length} × ${Math.max(n.headers?.length || 0, ...widths, 0)}`
      return head ? `${head} (${dims})` : dims
    }
    return `${(n.rows || []).length} строк`
  }
  return ''
}
function isActive(f) {
  return f.node.kind === 'section' && f.node.uid === activeSectionUid.value
}
function activate(f) {
  editingUid.value = f.node.uid
  const p = f.node.page || 1
  if (p !== pageIndex.value + 1) {
    pageIndex.value = p - 1
    resetImage()
  }
  if (f.node.kind === 'section') {
    activeSectionUid.value = activeSectionUid.value === f.node.uid ? null : f.node.uid
  }
}

function cropStyle(region) {
  const cp = currentPage.value
  if (!region || !currentUrl.value || !scale.value || !cp || !cp.w) return {}
  const maxW = 150, maxH = 52
  const s = Math.min(maxW / region.w, maxH / region.h)
  return {
    width: Math.round(region.w * s) + 'px', height: Math.round(region.h * s) + 'px',
    backgroundImage: `url("${currentUrl.value}")`,
    backgroundSize: `${Math.round(cp.w * s)}px ${Math.round(cp.h * s)}px`,
    backgroundPosition: `${-Math.round(region.x * s)}px ${-Math.round(region.y * s)}px`,
  }
}
function dispStyle(region) {
  return { left: (region.x / scale.value) + 'px', top: (region.y / scale.value) + 'px', width: (region.w / scale.value) + 'px', height: (region.h / scale.value) + 'px' }
}

// ── холст: кнопки ──
function deleteFrag(f) {
  if (f.node.uid === editingUid.value) editingUid.value = null
  f.parentArray.splice(f.index, 1)
}
function moveFrag(f, dir) {
  const j = f.index + dir
  if (j < 0 || j >= f.parentArray.length) return
  const [node] = f.parentArray.splice(f.index, 1)
  f.parentArray.splice(j, 0, node)
}
function indentFrag(f) {
  const prev = f.parentArray[f.index - 1]
  if (!prev || prev.kind !== 'section') return
  f.parentArray.splice(f.index, 1)
  prev.children.push(f.node)
}
function outdentFrag(f) {
  const owner = flatList.value.find(x => x.node.uid === f.ownerUid)
  if (!owner) return
  f.parentArray.splice(f.index, 1)
  owner.parentArray.splice(owner.index + 1, 0, f.node)
}

// ── холст: drag & drop мышкой ──
function onDragStart(uid, e) {
  dragUid = uid
  e.dataTransfer.effectAllowed = 'move'
  try { e.dataTransfer.setData('text/plain', String(uid)) } catch (_) { /* noop */ }
}
function onBlockDragOver(f) { dropOverUid.value = f.node.uid }
function onBlockDragLeave(f) {
  if (dropOverUid.value === f.node.uid) dropOverUid.value = null
}
function onRootDragLeave(e) {
  if (!e.currentTarget.contains(e.relatedTarget)) dragOverRoot.value = false
}
function onRootDrop() {
  dragOverRoot.value = false
  if (dragUid === null) return
  const src = flatList.value.find(x => x.node.uid === dragUid)
  dragUid = null
  if (!src || src.parentArray === tree.value) return
  src.parentArray.splice(src.index, 1)
  tree.value.push(src.node)
}
function onBlockDrop(f) {
  dropOverUid.value = null
  if (dragUid === null || dragUid === f.node.uid) { dragUid = null; return }
  const src = flatList.value.find(x => x.node.uid === dragUid)
  dragUid = null
  if (!src) return
  const srcNode = src.node
  // раздел нельзя перенести внутрь самого себя / своего потомка
  if (srcNode.kind === 'section' && containsUid(srcNode, f.node.uid)) return
  src.parentArray.splice(src.index, 1)
  if (f.node.kind === 'section') {
    f.node.children.push(srcNode)
  } else {
    const dst = flatList.value.find(x => x.node.uid === f.node.uid)
    if (!dst) { tree.value.push(srcNode); return }
    dst.parentArray.splice(dst.index, 0, srcNode)
  }
}
function containsUid(node, uid) {
  if (node.uid === uid) return true
  for (const c of node.children || []) {
    if (c.kind === 'section' && containsUid(c, uid)) return true
  }
  return false
}

// ── перераспознавание всех блоков (батч-эндпоинт) ──
async function reRecognizeAll() {
  if (!flatList.value.length || busy.value || pageBusy.value) return
  const groups = new Map()
  for (const f of flatList.value) {
    const page = f.node.page || 1
    if (!groups.has(page)) groups.set(page, [])
    groups.get(page).push(f.node)
  }
  busy.value = true
  error.value = ''
  let updated = 0
  try {
    for (const [page, nodes] of groups) {
      const blob = isPdf.value ? await fetchPageBlob(page) : file.value
      const fd = new FormData()
      fd.append('file', blob, isPdf.value ? `page_${page}.png` : (file.value?.name || 'image'))
      fd.append('use_first_row_as_header', useHeader.value ? 'true' : 'false')
      fd.append('borderless_tables', borderless.value ? 'true' : 'false')
      fd.append('regions', JSON.stringify(nodes.filter(n => n.region).map(n => ({
        id: n.uid,
        kind: (n.kind === 'section' || n.kind === 'text') ? 'text' : (n.variant === 'grid' ? 'grid' : 'fvtable'),
        x: n.region.x, y: n.region.y, w: n.region.w, h: n.region.h,
      }))))
      const { data } = await api.post('/admin/media/ocr/regions/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      const byId = new Map((data.results || []).map(r => [r.id, r]))
      for (const n of nodes) {
        const r = byId.get(n.uid)
        if (!r || r.error) continue
        if (n.kind === 'section') {
          n.title = r.text || ''
        } else if (n.kind === 'text') {
          n.text = r.text || ''
        } else if (n.kind === 'table') {
          if (n.variant === 'grid') {
            n.headers = (r.columns || []).map(c => c == null ? '' : String(c))
            n.rows = (r.rows || []).map(row => (row || []).map(c => c == null ? '' : String(c)))
          } else {
            n.rows = (r.rows || []).map(x => ({ field: x.field || '', value: x.value || '' }))
          }
        }
        updated++
      }
    }
    flash(`Перераспознано блоков: ${updated}`)
  } catch (e) {
    error.value = e?.displayMessage || e?.message || 'Ошибка перераспознавания'
  } finally {
    busy.value = false
  }
}
async function fetchPageBlob(page) {
  const resp = await fetch(pageServerUrl(page), { credentials: 'include' })
  if (!resp.ok) throw new Error(`Не удалось получить страницу ${page}`)
  return await resp.blob()
}

// ── попап содержимого (двойной клик по блоку) ──
function openDetail(f) { editingUid.value = null; detailNode.value = f.node }
function closeDetail() { detailNode.value = null }
function copyDetail() {
  const n = detailNode.value
  if (!n) return
  let text = ''
  if (n.kind === 'text') text = n.text || ''
  else if (n.kind === 'section') text = n.title || ''
  else if (n.kind === 'table') {
    const lines = []
    if (n.variant === 'grid') {
      if ((n.headers || []).length) lines.push((n.headers || []).map(c => c ?? '').join('\t'))
      for (const r of n.rows || []) lines.push((r || []).map(c => c ?? '').join('\t'))
    } else {
      for (const r of n.rows || []) lines.push(`${r.field}: ${r.value}`)
    }
    text = lines.join('\n')
  }
  navigator.clipboard.writeText(text).then(() => flash('Скопировано'))
}

// ── результат: JSON / текст / экспорт ──
function toJSON() {
  const clean = (nodes) => nodes.map(n => {
    const region = n.region ? { x: n.region.x, y: n.region.y, w: n.region.w, h: n.region.h } : null
    if (n.kind === 'section') return { kind: 'section', title: n.title, page: n.page || 1, region, children: clean(n.children) }
    if (n.kind === 'text') return { kind: 'text', text: n.text, page: n.page || 1, region }
    if (n.kind === 'table') {
      if (n.variant === 'grid') {
        return { kind: 'table', variant: 'grid', page: n.page || 1, region, headers: (n.headers || []).slice(), rows: (n.rows || []).map(r => r.slice()) }
      }
      return { kind: 'table', variant: 'fv', page: n.page || 1, region, rows: (n.rows || []).map(r => ({ field: r.field, value: r.value })) }
    }
    return n
  })
  return {
    schema_version: SCHEMA_VERSION,
    document: {
      filename: file.value?.name || '',
      sha256: fileSha256.value || null,
      page_count: pages.value.length,
      page_dims: pages.value.map(p => ({ width: p.w || 0, height: p.h || 0 })),
    },
    items: clean(tree.value),
    text: toText(),
  }
}

function toText() {
  const out = []
  const walk = (nodes, level) => {
    for (const n of nodes) {
      if (n.kind === 'section') {
        out.push('#'.repeat(level + 1) + ' ' + (n.title || ''))
        walk(n.children || [], level + 1)
      } else if (n.kind === 'text') {
        const t = (n.text || '').trim()
        if (t) out.push(t)
      } else if (n.kind === 'table') {
        if (n.variant === 'grid') {
          const lines = []
          if ((n.headers || []).length) lines.push((n.headers || []).map(c => c ?? '').join('\t'))
          for (const r of n.rows || []) lines.push((r || []).map(c => c ?? '').join('\t'))
          if (lines.length) out.push(lines.join('\n'))
        } else {
          for (const r of n.rows || []) out.push(`${r.field}: ${r.value}`)
        }
      }
    }
  }
  walk(tree.value, 0)
  return out.join('\n')
}

async function copyJSON() {
  await navigator.clipboard.writeText(JSON.stringify(toJSON(), null, 2))
  flash('JSON скопирован')
}
function downloadJSON() {
  const blob = new Blob([JSON.stringify(toJSON(), null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = 'структура_распознавания.json'; a.click()
  URL.revokeObjectURL(url)
}
async function copyTextAll() {
  await navigator.clipboard.writeText(toText())
  flash('Текст скопирован')
}
function downloadText() {
  const blob = new Blob([toText()], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = 'распознанный_текст.txt'; a.click()
  URL.revokeObjectURL(url)
}
async function exportStructure(fmt) {
  const base = (file.value?.name || 'структура').replace(/\.[^.]+$/, '')
  try {
    const resp = await api.post('/admin/media/ocr/export-structure/', { structure: toJSON(), format: fmt, filename: base }, { responseType: 'blob' })
    const dispo = resp.headers?.['content-disposition'] || ''
    const match = dispo.match(/filename=\"?([^";]+)\"?/)
    const filename = match ? match[1] : `${base}.${fmt}`
    const url = URL.createObjectURL(resp.data)
    const a = document.createElement('a')
    a.href = url; a.download = filename; a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    error.value = e?.displayMessage || e?.message || 'Ошибка экспорта'
  }
}

function onKeyDown(e) {
  if (e.key !== 'Escape') return
  detailNode.value = null
  editingUid.value = null
  handleDrag.value = null
}

onMounted(() => {
  document.addEventListener('mousemove', onImgMouseMove)
  document.addEventListener('mouseup', onImgMouseUp)
  document.addEventListener('keydown', onKeyDown)
})
onBeforeUnmount(() => {
  document.removeEventListener('mousemove', onImgMouseMove)
  document.removeEventListener('mouseup', onImgMouseUp)
  document.removeEventListener('keydown', onKeyDown)
  for (const p of pages.value) if (p.url && p.url.startsWith('blob:')) URL.revokeObjectURL(p.url)
})
</script>

<style scoped>
.ocr { display: flex; flex-direction: column; height: 100vh; font-family: system-ui, sans-serif; background: #fff; }
.toolbar { flex: 0 0 auto; display: flex; align-items: center; gap: 14px; padding: 10px 16px; border-bottom: 1px solid #e5e7eb; background: #f9fafb; flex-wrap: wrap; }
.upload-btn { cursor: pointer; padding: 9px 16px; background: #fff; border: 1px dashed #999; border-radius: 8px; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 260px; }
.upload-btn:hover { background: #eef2ff; }
.toolbar-hint { font-size: 13px; color: #6b7280; }

.body { flex: 1; display: flex; min-height: 0; }

/* ── изображение ── */
.preview-pane { flex: 1.4; position: relative; overflow: auto; padding: 16px; border-right: 1px solid #e5e7eb; background: #f3f4f6; display: flex; flex-direction: column; align-items: center; gap: 10px; }
.page-nav { display: flex; align-items: center; gap: 10px; }
.page-nav-label { font-size: 13px; color: #374151; }
.preview-wrap { position: relative; display: inline-block; }
.preview-img { max-width: 100%; max-height: calc(100vh - 180px); display: block; user-select: none; cursor: crosshair; }
.placeholder { margin: auto; color: #6b7280; font-size: 14px; }

.draw-overlay { position: absolute; border: 2px dashed #3b82f6; background: rgba(59, 130, 246, .12); pointer-events: none; box-sizing: border-box; }
.node-overlay { position: absolute; border: 2px solid; pointer-events: none; box-sizing: border-box; background: rgba(255, 255, 255, .04); }
.ov-section { border-color: #6366f1; }
.ov-text { border-color: #0ea5e9; }
.ov-fv { border-color: #a855f7; }
.ov-grid { border-color: #f59e0b; }
.ov-editing { border-width: 3px; border-color: #3b82f6 !important; }
.region-handle { position: absolute; width: 12px; height: 12px; background: #fff; border: 2px solid #3b82f6; border-radius: 2px; z-index: 5; box-shadow: 0 1px 3px rgba(0,0,0,.35); }
.handle-tl { cursor: nwse-resize; }
.handle-tr { cursor: nesw-resize; }
.handle-bl { cursor: nesw-resize; }
.handle-br { cursor: nwse-resize; }

/* ── инструменты (между изображением и холстом) ── */
.tools-pane { flex: 0 0 176px; display: flex; flex-direction: column; gap: 8px; padding: 16px 12px; border-right: 1px solid #e5e7eb; background: #fff; }
.tool { padding: 9px 12px; border: 1px solid #d1d5db; background: #fff; border-radius: 8px; cursor: pointer; font-size: 13px; color: #111827; text-align: left; }
.tool:hover { background: #f3f4f6; }
.tool:disabled { opacity: .5; cursor: not-allowed; }
.tool-active { background: #3b82f6; border-color: #3b82f6; color: #fff; }
.tool-active:hover { background: #2563eb; }
.tool-opts { display: flex; flex-direction: column; gap: 6px; border-top: 1px dashed #e5e7eb; padding-top: 8px; }
.tool-opts-title { font-size: 11px; color: #6b7280; text-transform: uppercase; letter-spacing: .04em; }
.mini-check { display: flex; align-items: center; gap: 5px; font-size: 12px; color: #374151; cursor: pointer; }

/* ── холст ── */
.canvas-pane { flex: 1.1; min-width: 440px; overflow-y: auto; padding: 16px; background: #fff; }
.row-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
.summary { font-size: 14px; color: #374151; margin-top: 10px; }
.error { color: #dc2626; font-size: 14px; margin-bottom: 10px; background: #fef2f2; padding: 8px 12px; border-radius: 6px; }

.root-zone { border: 1px dashed #d1d5db; border-radius: 10px; padding: 12px; min-height: 240px; background: #fafafa; display: flex; flex-direction: column; gap: 8px; }
.root-zone.drop-root { border-color: #3b82f6; background: #eff6ff; }
.root-title { font-size: 14px; font-weight: 600; color: #111827; padding: 6px 10px; border-radius: 6px; cursor: pointer; user-select: none; }
.root-title:hover { background: #f3f4f6; }
.root-title.root-active { background: #e0e7ff; color: #3730a3; }

.block { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px 10px; cursor: grab; }
.block:hover { border-color: #c7d2fe; }
.block.drop-over { outline: 2px dashed #3b82f6; outline-offset: -2px; }
.block-active { border-color: #6366f1; box-shadow: 0 0 0 1px #6366f1; }
.block-editing { border-color: #3b82f6; box-shadow: 0 0 0 1px #3b82f6; }
.edit-bar { display: flex; align-items: center; gap: 6px; margin-top: 6px; padding-top: 6px; border-top: 1px dashed #e5e7eb; flex-wrap: wrap; }
.block-head { display: flex; align-items: center; gap: 10px; }
.block-detail { margin-top: 8px; border-top: 1px solid #f3f4f6; padding-top: 6px; max-height: 180px; overflow: auto; }

.frag-crop { flex: 0 0 auto; border: 1px solid #e5e7eb; border-radius: 3px; background-repeat: no-repeat; }
.frag-body { flex: 1 1 auto; min-width: 0; }
.frag-kind { font-size: 10px; text-transform: uppercase; color: #9ca3af; letter-spacing: .04em; }
.page-badge { color: #6b7280; text-transform: none; }
.frag-text { font-size: 13px; color: #111827; white-space: pre-wrap; word-break: break-word; }
.frag-actions { flex: 0 0 auto; display: flex; gap: 2px; opacity: .35; }
.block:hover .frag-actions { opacity: 1; }

.mini-grid { border-collapse: collapse; font-size: 12px; width: 100%; }
.mini-grid th, .mini-grid td { border: 1px solid #e5e7eb; padding: 3px 8px; text-align: left; white-space: nowrap; }
.mini-grid th { background: #f3f4f6; }
.td-f { font-weight: 600; background: #fafafa; }

.btn { padding: 7px 13px; background: #fff; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; font-size: 13px; color: #111827; }
.btn:hover { background: #f3f4f6; }
.btn:disabled { opacity: .5; cursor: not-allowed; }
.mini { border: 1px solid #e5e7eb; background: #fff; border-radius: 4px; cursor: pointer; font-size: 11px; width: 20px; height: 20px; padding: 0; line-height: 1; }
.mini.danger { color: #dc2626; }
.hint { color: #6b7280; font-size: 13px; }

.magnifier { position: fixed; z-index: 50; border: 2px solid #111827; border-radius: 50%; box-shadow: 0 4px 16px rgba(0,0,0,.35); background-repeat: no-repeat; pointer-events: none; }
.magnifier-cross { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); width: 10px; height: 10px; }
.magnifier-cross::before, .magnifier-cross::after { content: ''; position: absolute; background: #ef4444; }
.magnifier-cross::before { width: 2px; height: 100%; left: 4px; top: 0; }
.magnifier-cross::after { width: 100%; height: 2px; left: 0; top: 4px; }

.toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); background: #111827; color: #fff; padding: 8px 16px; border-radius: 8px; font-size: 13px; z-index: 100; }

/* ── попап содержимого фрагмента ── */
.modal-backdrop { position: fixed; inset: 0; background: rgba(17,24,39,.45); z-index: 90; display: flex; align-items: center; justify-content: center; }
.modal { background: #fff; border-radius: 10px; padding: 16px; width: min(720px, 92vw); max-height: 82vh; display: flex; flex-direction: column; gap: 10px; box-shadow: 0 10px 40px rgba(0,0,0,.3); }
.modal-head { display: flex; align-items: center; gap: 10px; }
.modal-title { font-weight: 600; font-size: 14px; flex: 1 1 auto; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.modal-body { overflow: auto; }
.text-pre { white-space: pre-wrap; word-break: break-word; font-family: inherit; font-size: 13px; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 10px; margin: 0; }
</style>
