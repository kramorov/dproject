<!-- pages/TableOcrTool.vue -->
<template>
  <div class="ocr">
    <header class="toolbar">
      <label class="upload-btn">
        <input type="file" accept="image/*,.pdf" @change="onFileSelected" hidden />
        <span>{{ file ? '📎 ' + file.name : '📁 Выбрать файл' }}</span>
      </label>

      <div class="tabs">
        <button v-for="m in modes" :key="m.value" class="tab"
          :class="{ active: mode === m.value }" @click="setMode(m.value)">{{ m.label }}</button>
      </div>

      <template v-if="mode === 'table'">
        <label class="mini-check"><input v-model="borderless" type="checkbox" /> без линий</label>
        <label class="mini-check"><input v-model="useHeader" type="checkbox" /> шапка</label>
      </template>

      <button v-if="mode !== 'form'" class="btn-primary" :disabled="!file || recognizing" @click="recognize">
        {{ recognizing ? '⏳ …' : '🔎 Распознать' }}
      </button>
      <span v-else class="toolbar-hint">Разметка ОЛ: выберите действие и обведите область на превью</span>
    </header>

    <div class="body">
      <div class="preview-pane">
        <div v-if="mode !== 'form' && srcUrl && isImage" class="sel-toolbar">
          <button class="btn" :class="regionSelMode ? 'btn-active' : 'btn-secondary'" @click="toggleRegionSel">
            {{ regionSelMode ? 'Готово' : '＋ Добавить выделение' }}
          </button>
          <span v-if="regionSelMode" class="hint">Зажмите левую кнопку мыши и растяните рамку до нижнего правого угла</span>
        </div>

        <div v-if="mode === 'form'" class="sel-toolbar">
          <button class="btn" :class="{ 'btn-active': selMode === 'section' }" @click="setSel('section')">＋ Раздел</button>
          <button class="btn" :class="{ 'btn-active': selMode === 'field' }" @click="setSel('field')">＋ Поле</button>
          <button class="btn" :class="{ 'btn-active': selMode === 'table' }" @click="setSel('table')">＋ Таблица F-V</button>
          <button class="btn" :class="{ 'btn-active': selMode === 'value' }" :disabled="!activeFieldUid" @click="setSel('value')">＋ Значение</button>
          <button class="btn" :class="magnifierOn ? 'btn-active' : 'btn-secondary'" @click="magnifierOn = !magnifierOn">🔍 Лупа</button>
          <span v-if="selMode" class="hint">{{ selHint }}</span>
        </div>

        <div v-if="srcUrl && isImage" class="preview-wrap" @mousemove="onImgHover" @mouseleave="onImgLeave">
          <img ref="previewImg" :src="srcUrl" class="preview-img" alt="preview"
            draggable="false"
            @dragstart.prevent
            @load="onImgLoad" @mousedown="onImgMouseDown" />

          <div v-if="(mode === 'table' || mode === 'text') && regionActive" class="region-overlay" :style="regionStyle"></div>

          <template v-if="mode === 'form'">
            <div v-for="o in overlays" :key="o.uid" class="node-overlay" :class="'ov-' + o.kind" :style="dispStyle(o.region)"></div>
          </template>

          <div v-if="drawRect.w > 3 && drawRect.h > 3" class="draw-overlay" :style="drawRectStyle"></div>
        </div>

        <div v-if="(mode === 'text' || mode === 'table') && regionActive" class="region-bar">
          <span class="hint" style="margin:0">Область выделена</span>
          <button class="btn btn-secondary" @click="clearRegion">✕ Сбросить область</button>
        </div>

        <div v-else-if="srcUrl" class="hint center">PDF: предпросмотр недоступен. Разметка — только для изображений.</div>
        <div v-else class="placeholder">Загрузите изображение</div>

        <div v-if="magnifierOn && hoverPos" class="magnifier" :style="magnifierStyle"><span class="magnifier-cross"></span></div>
      </div>

      <aside class="results-pane">
        <div v-if="error" class="error">{{ error }}</div>

        <!-- ТЕКСТ -->
        <template v-if="mode === 'text'">
          <template v-if="result">
            <div class="summary">Страниц: {{ result.page_count }} · OCR: {{ result.ocr_backend }}</div>
            <div class="row-actions"><button class="btn" @click="copyText">📋 Копировать текст</button></div>
            <pre class="text-pre">{{ result.text || 'Текст не распознан.' }}</pre>
          </template>
          <div v-else class="hint">Выберите файл, при необходимости обведите фрагмент, нажмите «Распознать»</div>
        </template>

        <!-- ТАБЛИЦА -->
        <template v-else-if="mode === 'table'">
          <template v-if="result">
            <div class="summary">Таблиц: {{ result.count }}</div>
            <div class="row-actions" v-if="result.count">
              <button class="btn" @click="copyTables">📋 Копировать</button>
              <button class="btn" @click="download('xlsx')">💾 Excel</button>
            </div>
            <div v-for="page in result.pages" :key="page.n" class="page-block">
              <div v-for="t in page.tables" :key="t.index" class="table-block">
                <div class="table-title">Таблица {{ t.index + 1 }}</div>
                <div class="table-scroll">
                  <table class="grid">
                    <thead><tr><th v-for="(c, ci) in t.columns" :key="ci">{{ c }}</th></tr></thead>
                    <tbody><tr v-for="(row, ri) in t.rows" :key="ri"><td v-for="(cell, ci) in row" :key="ci">{{ cell ?? '' }}</td></tr></tbody>
                  </table>
                </div>
              </div>
            </div>
            <div v-if="!result.count" class="hint">Таблицы не найдены.</div>
          </template>
          <div v-else class="hint">Выберите файл, при необходимости обведите таблицу, нажмите «Распознать»</div>
        </template>

        <!-- ОЛ / РАЗМЕТКА -->
        <template v-else>
          <div v-if="!file || !isImage" class="hint">Загрузите изображение для разметки.</div>
          <template v-else>
            <div class="row-actions">
              <button class="btn" @click="copyJSON">📋 JSON</button>
              <button class="btn" @click="downloadJSON">💾 JSON</button>
              <button class="btn" @click="exportStructure('xlsx')" :disabled="!flatList.length">💾 Excel</button>
              <button class="btn" @click="exportStructure('docx')" :disabled="!flatList.length">💾 Word</button>
            </div>

            <div class="ribbon">
              <div v-if="!flatList.length" class="hint">Отметьте фрагменты: разделы, поля, таблицы, значения.</div>
              <div
                v-for="(f, i) in flatList"
                :key="f.node.uid"
                class="frag"
                :class="{ 'frag-active': isActive(f) }"
                :style="{ paddingLeft: (f.depth * 16 + 8) + 'px' }"
                draggable="true"
                @dragstart="onDragStart(i, $event)"
                @dragover.prevent
                @drop="onDrop(i)"
                @click="activate(f)"
              >
                <div v-if="f.node.region" class="frag-crop" :style="cropStyle(f.node.region)"></div>
                <div class="frag-body">
                  <div class="frag-kind">{{ kindLabel(f) }}</div>
                  <div class="frag-text">{{ fragText(f) }}</div>
                  <div v-if="isCheckboxValue(f)" class="frag-opts">
                    <span v-for="(o, oi) in f.node.options" :key="oi" class="chip" :class="o.checked ? 'chip-on' : 'chip-off'">{{ o.checked ? '☑' : '☐' }} {{ o.label }}</span>
                  </div>
                </div>
                <div class="frag-actions">
                  <button class="mini" title="Вверх" @click.stop="moveFrag(i, -1)">↑</button>
                  <button class="mini" title="Вниз" @click.stop="moveFrag(i, 1)">↓</button>
                  <button class="mini" title="Вложить" @click.stop="indentFrag(i)">↳</button>
                  <button class="mini" title="Наружу" @click.stop="outdentFrag(i)">↰</button>
                  <button class="mini danger" title="Удалить" @click.stop="deleteFrag(i)">✕</button>
                </div>
              </div>
            </div>

            <div v-if="flatList.length" class="summary" style="margin-top:12px">
              Разделов/полей/значений: {{ flatList.length }}
            </div>
          </template>
        </template>
      </aside>
    </div>

    <div v-if="toast" class="toast">{{ toast }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import api from '@/shared/api'

const modes = [
  { value: 'text', label: 'Текст' },
  { value: 'table', label: 'Таблица' },
  { value: 'form', label: 'ОЛ (разметка)' },
]

const mode = ref('form')
const file = ref(null)
const isImage = ref(true)
const srcUrl = ref('')

const recognizing = ref(false)
const error = ref('')
const result = ref(null)
const resultId = ref('')
const toast = ref('')

const borderless = ref(false)
const useHeader = ref(true)

// ── дерево разметки ──
const tree = ref([])              // корневые узлы
const activeFieldUid = ref(null)  // куда добавлять значения
const activeSectionUid = ref(null) // куда добавлять разделы/поля/таблицы
const selMode = ref(null)         // 'section'|'field'|'value'|'table'
let uidSeq = 0

const selHint = computed(() => ({
  section: 'Обведите название раздела',
  field: 'Обведите название поля',
  value: 'Обведите значение для выбранного поля',
  table: 'Обведите таблицу из двух столбцов',
}[selMode.value] || ''))

// ── изображение ──
const previewImg = ref(null)
const imgNaturalW = ref(0)
const imgNaturalH = ref(0)
const imgDisplayW = ref(0)
const imgDisplayH = ref(0)
const scale = ref(1)

const regionActive = ref(false)
const regionSelMode = ref(false)
const region = ref({ x: 0, y: 0, w: 0, h: 0 })
const drawing = ref(false)
const drawStart = ref({ x: 0, y: 0 })
const drawRect = ref({ x: 0, y: 0, w: 0, h: 0 })

const magnifierOn = ref(false)
const hoverPos = ref(null)
const magnifierSize = 220
const magnifierZoom = 3

let dragIndex = null

// ── вычисляемые ──
const regionStyle = computed(() => ({
  left: region.value.x + 'px', top: region.value.y + 'px',
  width: region.value.w + 'px', height: region.value.h + 'px',
}))
const drawRectStyle = computed(() => ({
  left: drawRect.value.x + 'px', top: drawRect.value.y + 'px',
  width: drawRect.value.w + 'px', height: drawRect.value.h + 'px',
}))
const magnifierStyle = computed(() => {
  if (!hoverPos.value || !srcUrl.value || !scale.value) return { display: 'none' }
  const nx = hoverPos.value.x * scale.value
  const ny = hoverPos.value.y * scale.value
  const left = Math.min(window.innerWidth - magnifierSize - 16, hoverPos.value.clientX + 24)
  const top = Math.min(window.innerHeight - magnifierSize - 16, hoverPos.value.clientY + 24)
  return {
    width: magnifierSize + 'px', height: magnifierSize + 'px',
    left: Math.max(8, left) + 'px', top: Math.max(8, top) + 'px',
    backgroundImage: `url("${srcUrl.value}")`,
    backgroundSize: `${imgNaturalW.value * magnifierZoom}px ${imgNaturalH.value * magnifierZoom}px`,
    backgroundPosition: `${-(nx * magnifierZoom) + magnifierSize / 2}px ${-(ny * magnifierZoom) + magnifierSize / 2}px`,
  }
})

// плоский список для ленты
const flatList = computed(() => {
  const out = []
  const walk = (nodes, depth, parentArray, ownerUid) => {
    for (let i = 0; i < nodes.length; i++) {
      const n = nodes[i]
      out.push({ node: n, depth, parentArray, index: i, ownerUid })
      if (n.kind === 'section') walk(n.children, depth + 1, n.children, n.uid)
      if (n.kind === 'field') {
        n.values.forEach((v, vi) => out.push({ node: v, depth: depth + 1, parentArray: n.values, index: vi, ownerUid: n.uid, isValue: true }))
      }
    }
  }
  walk(tree.value, 0, tree.value, null)
  return out
})

// оверлеи на превью
const overlays = computed(() => {
  const out = []
  const walk = (nodes) => {
    for (const n of nodes) {
      if (n.region) out.push({ uid: n.uid, kind: n.kind, region: n.region })
      if (n.kind === 'section') walk(n.children)
      if (n.kind === 'field') {
        for (const v of n.values) if (v.region) out.push({ uid: v.uid, kind: 'value', region: v.region })
      }
    }
  }
  walk(tree.value)
  return out
})

function setMode(m) {
  mode.value = m
  selMode.value = null
  regionSelMode.value = false
  drawRect.value = { x: 0, y: 0, w: 0, h: 0 }
}

function flash(msg) { toast.value = msg; setTimeout(() => { toast.value = '' }, 1600) }

// ── файл ──
function onFileSelected(e) {
  const f = e.target.files?.[0]
  if (!f) return
  file.value = f
  error.value = ''
  result.value = null
  resultId.value = ''
  tree.value = []
  activeFieldUid.value = null
  activeSectionUid.value = null
  selMode.value = null
  isImage.value = (f.type || '').startsWith('image/')
  if (srcUrl.value) URL.revokeObjectURL(srcUrl.value)
  srcUrl.value = isImage.value ? URL.createObjectURL(f) : ''
  resetRegion()
}

function resetRegion() {
  regionActive.value = false
  region.value = { x: 0, y: 0, w: 0, h: 0 }
  drawRect.value = { x: 0, y: 0, w: 0, h: 0 }
  drawing.value = false
  imgNaturalW.value = 0; imgNaturalH.value = 0
  imgDisplayW.value = 0; imgDisplayH.value = 0
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

function clearRegion() {
  regionActive.value = false
  region.value = { x: 0, y: 0, w: 0, h: 0 }
}

function toggleRegionSel() {
  regionSelMode.value = !regionSelMode.value
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
  const canDraw = (mode.value === 'table' || mode.value === 'text') || (mode.value === 'form' && selMode.value)
  if (!canDraw) return
  if (e.ctrlKey) e.preventDefault()
  const p = imagePoint(e)
  if (!p) return
  drawing.value = true
  drawStart.value = { x: p.x, y: p.y }
  drawRect.value = { x: p.x, y: p.y, w: 0, h: 0 }
}

function onImgMouseMove(e) {
  if (!drawing.value) return
  const p = imagePoint(e)
  if (!p) return
  const sx = drawStart.value.x, sy = drawStart.value.y
  drawRect.value = { x: Math.min(sx, p.x), y: Math.min(sy, p.y), w: Math.abs(p.x - sx), h: Math.abs(p.y - sy) }
}

function onImgMouseUp() {
  if (!drawing.value) return
  drawing.value = false
  const r = drawRect.value
  drawRect.value = { x: 0, y: 0, w: 0, h: 0 }
  if (r.w < 5 || r.h < 5) return
  if (mode.value === 'table' || mode.value === 'text') {
    region.value = { ...r }
    regionActive.value = true
    regionSelMode.value = false
    return
  }
  if (mode.value === 'form' && selMode.value) {
    const nat = { x: Math.round(r.x * scale.value), y: Math.round(r.y * scale.value), w: Math.round(r.w * scale.value), h: Math.round(r.h * scale.value) }
    processSelection(nat)
  }
}

// ── разметка: обработка выделения ──
function setSel(m) { selMode.value = selMode.value === m ? null : m }

async function processSelection(nat) {
  const m = selMode.value
  selMode.value = null
  try {
    if (m === 'section') {
      const text = await ocrText(nat)
      addSection(text, nat)
    } else if (m === 'field') {
      const text = await ocrText(nat)
      addField(text, nat)
    } else if (m === 'value') {
      const a = await analyze(nat)
      addValue(a, nat)
    } else if (m === 'table') {
      const rows = await fvTable(nat)
      addTable(rows, nat)
    }
  } catch (e) {
    error.value = e?.displayMessage || e?.message || 'Ошибка разметки'
  }
}

async function ocrText(nat) {
  const fd = regionFd(nat, 'text')
  const { data } = await api.post('/admin/media/ocr/region/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  return data.text || ''
}
async function analyze(nat) {
  const fd = regionFd(nat, 'value')
  const { data } = await api.post('/admin/media/ocr/region/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  return data
}
async function fvTable(nat) {
  const fd = regionFd(nat, 'fvtable')
  const { data } = await api.post('/admin/media/ocr/region/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  return data.rows || []
}
function regionFd(nat, kind) {
  const fd = new FormData()
  fd.append('file', file.value)
  fd.append('kind', kind)
  fd.append('x', nat.x); fd.append('y', nat.y); fd.append('w', nat.w); fd.append('h', nat.h)
  return fd
}

// ── операции с деревом ──
function makeUid() { return ++uidSeq }

function activeContainer() {
  if (activeSectionUid.value) {
    const s = findNode(tree.value, activeSectionUid.value)
    if (s && s.kind === 'section') return s.children
  }
  return tree.value
}

function findNode(nodes, uid) {
  for (const n of nodes) {
    if (n.uid === uid) return n
    if (n.kind === 'section') { const r = findNode(n.children, uid); if (r) return r }
    if (n.kind === 'field') { const v = n.values.find(x => x.uid === uid); if (v) return v }
  }
  return null
}

function addSection(title, region) {
  const node = { uid: makeUid(), kind: 'section', title, region, children: [] }
  activeContainer().push(node)
  activeSectionUid.value = node.uid
  activeFieldUid.value = null
  flash('Раздел добавлен')
}
function addField(field, region) {
  const node = { uid: makeUid(), kind: 'field', field, region, values: [] }
  activeContainer().push(node)
  activeFieldUid.value = node.uid
  flash('Поле добавлено. Теперь «＋ Значение»')
}
function addValue(a, region) {
  const f = findNode(tree.value, activeFieldUid.value)
  if (!f || f.kind !== 'field') { error.value = 'Сначала выберите поле'; return }
  const v = { uid: makeUid(), region, type: a.type || 'text', text: a.text || '', checkboxes: a.checkboxes || [], selected: a.selected || [], options: a.checkboxes ? a.checkboxes.map(c => ({ label: c.label, checked: c.checked })) : [] }
  f.values.push(v)
  flash('Значение добавлено')
}
function addTable(rows, region) {
  const node = { uid: makeUid(), kind: 'table', region, rows: (rows || []).map(r => ({ uid: makeUid(), field: r.field || '', value: r.value || '' })) }
  activeContainer().push(node)
  flash('Таблица добавлена')
}

// ── лента: отображение ──
function kindLabel(f) {
  if (f.isValue) return 'значение'
  return { section: 'раздел', field: 'поле', table: 'таблица' }[f.node.kind] || ''
}
function isCheckboxValue(f) { return f.isValue && f.node.type === 'checkboxes' }
function fragText(f) {
  const n = f.node
  if (n.kind === 'section') return n.title || '(раздел)'
  if (n.kind === 'field') return n.field || '(поле)'
  if (n.kind === 'table') return `таблица: ${(n.rows || []).length} строк`
  if (f.isValue) {
    if (n.type === 'checkboxes') return (n.selected || []).join(', ') || '(нет отметок)'
    return (n.text || '').replace(/\n/g, ' ')
  }
  return ''
}
function isActive(f) {
  if (f.isValue) return false
  if (f.node.kind === 'field') return f.node.uid === activeFieldUid.value
  if (f.node.kind === 'section') return f.node.uid === activeSectionUid.value
  return false
}
function activate(f) {
  if (f.isValue) return
  if (f.node.kind === 'field') { activeFieldUid.value = f.node.uid; return }
  if (f.node.kind === 'section') { activeSectionUid.value = f.node.uid; activeFieldUid.value = null; return }
}

function cropStyle(region) {
  if (!region || !srcUrl.value || !scale.value) return {}
  const maxW = 150, maxH = 52
  const s = Math.min(maxW / region.w, maxH / region.h)
  return {
    width: Math.round(region.w * s) + 'px', height: Math.round(region.h * s) + 'px',
    backgroundImage: `url("${srcUrl.value}")`,
    backgroundSize: `${Math.round(imgNaturalW.value * s)}px ${Math.round(imgNaturalH.value * s)}px`,
    backgroundPosition: `${-Math.round(region.x * s)}px ${-Math.round(region.y * s)}px`,
  }
}
function dispStyle(region) {
  return { left: (region.x / scale.value) + 'px', top: (region.y / scale.value) + 'px', width: (region.w / scale.value) + 'px', height: (region.h / scale.value) + 'px' }
}

// ── лента: правки ──
function deleteFrag(i) {
  const f = flatList.value[i]
  f.parentArray.splice(f.index, 1)
}
function moveFrag(i, dir) {
  const f = flatList.value[i]
  const j = f.index + dir
  if (j < 0 || j >= f.parentArray.length) return
  const arr = f.parentArray
  const [node] = arr.splice(f.index, 1)
  arr.splice(j, 0, node)
}
function indentFrag(i) {
  const f = flatList.value[i]
  const prev = f.parentArray[f.index - 1]
  if (!prev || prev.kind !== 'section') return
  f.parentArray.splice(f.index, 1)
  prev.children.push(f.node)
}
function outdentFrag(i) {
  const f = flatList.value[i]
  const ownerItem = flatList.value.find(x => x.node.uid === f.ownerUid)
  if (!ownerItem) return
  f.parentArray.splice(f.index, 1)
  ownerItem.parentArray.splice(ownerItem.index + 1, 0, f.node)
}
function onDragStart(i, e) { dragIndex = i; e.dataTransfer.effectAllowed = 'move' }
function onDrop(i) {
  if (dragIndex === null || dragIndex === i) { dragIndex = null; return }
  const src = flatList.value[dragIndex]
  const dst = flatList.value[i]
  if (src.parentArray !== dst.parentArray) { dragIndex = null; return }
  const [node] = src.parentArray.splice(src.index, 1)
  dst.parentArray.splice(dst.index, 0, node)
  dragIndex = null
}

// ── JSON / экспорт ──
function valueToJSON(v) {
  return { type: v.type || 'text', text: v.text || '', selected: v.selected || [], options: v.options || [], checkboxes: v.checkboxes || [] }
}
function toJSON() {
  const clean = (nodes) => nodes.map(n => {
    if (n.kind === 'section') return { kind: 'section', title: n.title, children: clean(n.children) }
    if (n.kind === 'field') return { kind: 'field', field: n.field, values: (n.values || []).map(valueToJSON) }
    if (n.kind === 'table') return { kind: 'table', rows: (n.rows || []).map(r => ({ field: r.field, value: r.value })) }
    return n
  })
  return { items: clean(tree.value) }
}
async function copyJSON() {
  await navigator.clipboard.writeText(JSON.stringify(toJSON(), null, 2))
  flash('JSON скопирован')
}
function downloadJSON() {
  const blob = new Blob([JSON.stringify(toJSON(), null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = 'опросный_лист.json'; a.click()
  URL.revokeObjectURL(url)
}
async function exportStructure(fmt) {
  try {
    const resp = await api.post('/admin/media/ocr/export-structure/', { structure: toJSON(), format: fmt }, { responseType: 'blob' })
    const dispo = resp.headers?.['content-disposition'] || ''
    const match = dispo.match(/filename="?([^";]+)"?/)
    const filename = match ? match[1] : `опросный_лист.${fmt}`
    const url = URL.createObjectURL(resp.data)
    const a = document.createElement('a')
    a.href = url; a.download = filename; a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    error.value = e?.displayMessage || e?.message || 'Ошибка экспорта'
  }
}

// ── text/table режимы ──
async function recognize() {
  if (!file.value) return
  recognizing.value = true
  error.value = ''
  result.value = null
  resultId.value = ''
  const fd = new FormData()
  fd.append('file', file.value)
  fd.append('use_first_row_as_header', useHeader.value ? 'true' : 'false')
  fd.append('borderless_tables', borderless.value ? 'true' : 'false')
  if ((mode.value === 'table' || mode.value === 'text') && regionActive.value) {
    fd.append('region_x', Math.round(region.value.x * scale.value))
    fd.append('region_y', Math.round(region.value.y * scale.value))
    fd.append('region_w', Math.round(region.value.w * scale.value))
    fd.append('region_h', Math.round(region.value.h * scale.value))
  }
  try {
    const { data } = await api.post('/admin/media/ocr/recognize/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    result.value = data
    resultId.value = data.result_id
  } catch (e) {
    error.value = e?.displayMessage || e?.message || 'Ошибка распознавания'
  } finally {
    recognizing.value = false
  }
}

async function copyText() { await navigator.clipboard.writeText(result.value?.text || ''); flash('Скопировано') }
function tablesToTsv() {
  const rows = []
  for (const page of result.value?.pages || []) for (const t of page.tables || []) {
    rows.push((t.columns || []).join('\t'))
    for (const r of t.rows || []) rows.push((r || []).map(c => c ?? '').join('\t'))
  }
  return rows.join('\n')
}
async function copyTables() { await navigator.clipboard.writeText(tablesToTsv()); flash('Скопировано (TSV)') }

async function download(fmt) {
  if (!resultId.value) return
  try {
    const resp = await api.post('/admin/media/ocr/export/', { result_id: resultId.value, format: fmt }, { responseType: 'blob' })
    const dispo = resp.headers?.['content-disposition'] || ''
    const match = dispo.match(/filename="?([^";]+)"?/)
    const base = (file.value?.name || 'ocr').replace(/\.[^.]+$/, '')
    const filename = match ? match[1] : `${base}.${fmt}`
    const url = URL.createObjectURL(resp.data)
    const a = document.createElement('a'); a.href = url; a.download = filename; a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    error.value = e?.displayMessage || e?.message || 'Ошибка при скачивании'
  }
}

onMounted(() => {
  document.addEventListener('mousemove', onImgMouseMove)
  document.addEventListener('mouseup', onImgMouseUp)
})
onBeforeUnmount(() => {
  document.removeEventListener('mousemove', onImgMouseMove)
  document.removeEventListener('mouseup', onImgMouseUp)
  if (srcUrl.value) URL.revokeObjectURL(srcUrl.value)
})
</script>

<style scoped>
.ocr { display: flex; flex-direction: column; height: 100vh; font-family: system-ui, sans-serif; background: #fff; }
.toolbar { flex: 0 0 auto; display: flex; align-items: center; gap: 14px; padding: 10px 16px; border-bottom: 1px solid #e5e7eb; background: #f9fafb; flex-wrap: wrap; }
.upload-btn { cursor: pointer; padding: 9px 16px; background: #fff; border: 1px dashed #999; border-radius: 8px; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 240px; }
.upload-btn:hover { background: #eef2ff; }
.tabs { display: flex; gap: 4px; background: #e5e7eb; padding: 3px; border-radius: 8px; }
.tab { border: none; background: transparent; padding: 7px 15px; border-radius: 6px; cursor: pointer; font-size: 14px; color: #374151; }
.tab.active { background: #fff; color: #111827; font-weight: 600; box-shadow: 0 1px 2px rgba(0,0,0,.1); }
.mini-check { display: flex; align-items: center; gap: 5px; font-size: 12px; color: #374151; cursor: pointer; }
.toolbar-hint { font-size: 13px; color: #6b7280; }
.btn-primary { padding: 9px 18px; background: #3b82f6; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; margin-left: auto; }
.btn-primary:disabled { opacity: .5; cursor: not-allowed; }

.body { flex: 1 1 auto; display: flex; min-height: 0; }
.preview-pane { flex: 1 1 auto; position: relative; overflow: auto; padding: 12px 16px; background: #f3f4f6; display: flex; flex-direction: column; align-items: center; }
.sel-toolbar { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-bottom: 10px; }
.preview-wrap { position: relative; display: inline-block; line-height: 0; }
.preview-img { max-width: 100%; max-height: calc(100vh - 200px); border: 1px solid #d1d5db; border-radius: 6px; display: block; cursor: crosshair; user-select: none; -webkit-user-drag: none; user-drag: none; }
.placeholder { color: #9ca3af; font-size: 15px; margin-top: 40px; }

.region-overlay { position: absolute; border: 2px dashed #3b82f6; background: rgba(59,130,246,.10); pointer-events: none; }
.region-bar { display: flex; align-items: center; gap: 10px; margin-top: 10px; }
.draw-overlay { position: absolute; border: 2px dashed #3b82f6; background: rgba(59,130,246,.14); pointer-events: none; }
.node-overlay { position: absolute; border: 2px solid; pointer-events: none; box-sizing: border-box; }
.ov-section { border-color: #6366f1; }
.ov-field { border-color: #16a34a; }
.ov-value { border-color: #f59e0b; }
.ov-table { border-color: #a855f7; }

.magnifier { position: fixed; z-index: 50; border: 2px solid #111827; border-radius: 50%; box-shadow: 0 4px 16px rgba(0,0,0,.35); background-repeat: no-repeat; pointer-events: none; }
.magnifier-cross { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); width: 10px; height: 10px; }
.magnifier-cross::before, .magnifier-cross::after { content: ''; position: absolute; background: #ef4444; }
.magnifier-cross::before { width: 2px; height: 100%; left: 4px; top: 0; }
.magnifier-cross::after { width: 100%; height: 2px; left: 0; top: 4px; }

.results-pane { flex: 0 0 440px; overflow-y: auto; border-left: 1px solid #e5e7eb; padding: 16px; background: #fff; }
.summary { font-size: 14px; color: #374151; margin-bottom: 10px; }
.row-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
.btn { padding: 7px 13px; background: #fff; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; font-size: 13px; color: #111827; }
.btn:hover { background: #f3f4f6; }
.btn:disabled { opacity: .5; cursor: not-allowed; }
.btn-secondary { background: #e5e7eb; }
.btn-active { background: #3b82f6; border-color: #3b82f6; color: #fff; }
.btn-link { border: none; background: none; color: #2563eb; cursor: pointer; font-size: 12px; }
.btn-link.danger { color: #dc2626; }
.hint { color: #6b7280; font-size: 13px; margin: 8px 0; }
.hint.center { text-align: center; margin-top: 40px; }
.error { color: #dc2626; font-size: 14px; margin-bottom: 10px; background: #fef2f2; padding: 8px 12px; border-radius: 6px; }

.text-pre { white-space: pre-wrap; word-break: break-word; font-family: inherit; font-size: 13px; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 10px; max-height: 60vh; overflow: auto; }
.page-block { margin-bottom: 16px; }
.table-block { margin-bottom: 20px; }
.table-title { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
.table-scroll { overflow: auto; max-height: 50vh; border: 1px solid #e5e7eb; border-radius: 6px; }
.grid { border-collapse: collapse; font-size: 13px; min-width: 100%; }
.grid th, .grid td { border: 1px solid #e5e7eb; padding: 6px 10px; white-space: nowrap; text-align: left; }
.grid th { background: #f3f4f6; position: sticky; top: 0; }
.grid tbody tr:nth-child(even) { background: #fafafa; }

.ribbon { display: flex; flex-direction: column; gap: 6px; }
.frag { display: flex; align-items: center; gap: 10px; padding: 6px 8px; border: 1px solid #e5e7eb; border-radius: 6px; cursor: grab; background: #fff; }
.frag-active { outline: 2px solid #3b82f6; }
.frag-crop { flex: 0 0 auto; border: 1px solid #e5e7eb; border-radius: 3px; background-repeat: no-repeat; }
.frag-body { flex: 1 1 auto; min-width: 0; }
.frag-kind { font-size: 10px; text-transform: uppercase; color: #9ca3af; letter-spacing: .04em; }
.frag-text { font-size: 13px; color: #111827; white-space: pre-wrap; word-break: break-word; }
.frag-opts { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
.chip { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 12px; border: 1px solid #e5e7eb; }
.chip-on { background: #dcfce7; border-color: #86efac; color: #166534; }
.chip-off { color: #6b7280; }
.frag-actions { flex: 0 0 auto; display: flex; gap: 2px; opacity: .35; }
.frag:hover .frag-actions { opacity: 1; }
.mini { border: 1px solid #e5e7eb; background: #fff; border-radius: 4px; cursor: pointer; font-size: 11px; width: 20px; height: 20px; padding: 0; line-height: 1; }
.mini.danger { color: #dc2626; }

.toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); background: #111827; color: #fff; padding: 8px 16px; border-radius: 8px; font-size: 13px; z-index: 100; }
</style>
