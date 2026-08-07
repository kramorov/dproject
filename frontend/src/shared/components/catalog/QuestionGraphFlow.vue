<template>
  <div class="qgf-editor">
    <div class="qgf-toolbar">
      <span class="qgf-title">Редактор графа</span>
      <div class="qgf-actions">
        <button class="qgf-btn qgf-btn-accent" @click="autoLayout">📐 Авто-расстановка</button>
        <button class="qgf-btn qgf-btn-outline" @click="addPageNode">+ Страница</button>
        <button class="qgf-btn qgf-btn-outline" @click="addBranchNode">+ Ветвление</button>
        <button class="qgf-btn qgf-btn-primary" @click="saveToApi">💾 Записать в БД</button>
        <button class="qgf-btn qgf-btn-outline" @click="$emit('close')">✕ Закрыть</button>
      </div>
    </div>

    <div class="qgf-main">
      <VueFlow
        v-model:nodes="flowNodes"
        v-model:edges="flowEdges"
        :node-types="nodeTypes"
        :default-viewport="{ zoom: 1, x: 20, y: 20 }"
        :min-zoom="0.2" :max-zoom="2"
        fit-view-on-init
        @node-click="onNodeClick"
        @edge-double-click="onEdgeDblClick"
        @connect="onConnect"
        delete-key-code="Delete"
      >
        <Background :gap="20" />
        <Controls position="bottom-right" />
        <MiniMap position="bottom-left" />
      </VueFlow>
    </div>

    <!-- Page Node Popup -->
    <PageNodeForm v-if="editingPage"
      :node="editingPage"
      :all-nodes="allNodesForSelect"
      :is-entry="liveJson.entry_node === editingPage.id"
      @save="onPageSave"
      @cancel="editingPage = null"
    />

    <!-- Branch Node Popup -->
    <BranchNodeForm v-if="editingBranch"
      :node="editingBranch"
      :all-nodes="allNodesForSelect"
      :graph-code="graphCode"
      @save="onBranchSave"
      @cancel="editingBranch = null"
    />

    <!-- Edge edit modal -->
    <div class="qgf-modal-overlay" v-if="edgeEdit" @click.self="edgeEdit = null">
      <div class="qgf-modal">
        <h4>{{ edgeEdit.source }} → {{ edgeEdit.target }}</h4>
        <div class="qgf-field"><label>Метка</label><input v-model="edgeEdit.label" class="qgf-input" @keyup.enter="saveEdgeEdit" /></div>
        <div class="qgf-actions">
          <button class="qgf-btn qgf-btn-primary" @click="saveEdgeEdit">OK</button>
          <button class="qgf-btn qgf-btn-outline" @click="edgeEdit = null">Отмена</button>
          <button class="qgf-btn qgf-btn-danger" @click="deleteEdge">Удалить</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, markRaw, nextTick } from 'vue'
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import PageNode from './PageNode.vue'
import BranchNode from './BranchNode.vue'
import PageNodeForm from './PageNodeForm.vue'
import BranchNodeForm from './BranchNodeForm.vue'
import api from '@/shared/api'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'

const props = defineProps({
  graphJson: { type: Object, default: () => ({ nodes: {}, edges: [], entry_node: '' }) },
  graphCode: { type: String, default: '' },
})
const emit = defineEmits(['update:graphJson', 'save', 'close'])

// ── Single source of truth: reactive deep copy of graphJson ──
const liveJson = ref({ entry_node: '', nodes: {}, edges: [] })

watch(() => props.graphJson, (gj) => {
  if (!gj) return
  liveJson.value = JSON.parse(JSON.stringify(gj))
}, { immediate: true, deep: true })

// ── Vue Flow state (derived from liveJson) ──
const flowNodes = ref([])
const flowEdges = ref([])
const nodeTypes = { page: markRaw(PageNode), branch: markRaw(BranchNode) }

const editingPage = ref(null)
const editingBranch = ref(null)
const edgeEdit = ref(null)
const allNodesForSelect = computed(() => {
  // Build select options from liveJson
  return Object.entries(liveJson.value.nodes || {}).map(([id, nd]) => ({
    id, type: nd.type || 'page',
    data: { name: nd.name || id },
  }))
})

function renderFlow() {
  const gj = liveJson.value
  const ns = [], es = []
  const ids = Object.keys(gj.nodes || {})

  ids.forEach(id => {
    const node = gj.nodes[id]
    const savedPos = (node._x != null && node._y != null) ? { x: node._x, y: node._y } : null
    const pos = savedPos || { x: ids.indexOf(id) * 320 + 160, y: 60 }

    ns.push({
      id, type: node.type || 'page', position: pos,
      data: {
        isEntry: id === gj.entry_node,
        name: node.name || id,
        next_node: node.next_node || (gj.edges || []).find(e => e.from === id)?.to || '',
        params: (node.params || []).map((p, i) => ({ ...p, order: p.order ?? i + 1 })),
        param_name: node.param_name || '',
        match_values: [...(node.match_values || [])],
        match_target: node.match_target || '',
        else_target: node.else_target || '',
      },
    })
  })

  ;(gj.edges || []).forEach((e, i) => {
    es.push({ id: `e-${e.from}-${e.to}-${i}`, source: e.from, target: e.to, label: e.label || '' })
  })

  // Branch edges
  ids.forEach(id => {
    const node = gj.nodes[id]
    if (node.type === 'branch') {
      if (node.match_target) {
        const eid = `br-yes-${id}-${node.match_target}`
        if (!es.some(e => e.id === eid)) es.push({ id: eid, source: id, target: node.match_target, label: 'Да' })
      }
      if (node.else_target) {
        const eid = `br-no-${id}-${node.else_target}`
        if (!es.some(e => e.id === eid)) es.push({ id: eid, source: id, target: node.else_target, label: 'Нет' })
      }
    }
  })

  flowNodes.value = ns
  flowEdges.value = es
}

// Re-render whenever liveJson changes
watch(() => liveJson.value, renderFlow, { deep: true, immediate: true })

// ── Node click → populate popup props from liveJson ──
function onNodeClick({ node }) {
  const gjNode = liveJson.value.nodes[node.id]
  if (!gjNode) return
  if (node.type === 'page') {
    editingPage.value = { ...node, data: { ...node.data, next_node: gjNode.next_node || '' } }
  } else {
    editingBranch.value = { ...node, data: { ...node.data } }
  }
}

// ── Page save → write to liveJson → re-render ──
function onPageSave(data) {
  liveJson.value.nodes[data.id] = {
    ...liveJson.value.nodes[data.id],
    type: 'page',
    name: data.name,
    next_node: data.next_node,
    params: data.params,
    _x: liveJson.value.nodes[data.id]?._x,
    _y: liveJson.value.nodes[data.id]?._y,
  }

  // Sync edges: remove old outgoing, add new
  const oldEdges = liveJson.value.edges || []
  liveJson.value.edges = oldEdges.filter(e => e.from !== data.id)
  if (data.next_node) {
    liveJson.value.edges.push({ from: data.id, to: data.next_node, label: '' })
  }

  // Entry node
  if (data.isEntry) liveJson.value.entry_node = data.id
  else if (liveJson.value.entry_node === data.id) liveJson.value.entry_node = ''

  editingPage.value = null
}

// ── Branch save → write to liveJson → re-render ──
function onBranchSave(data) {
  liveJson.value.nodes[data.id] = {
    ...liveJson.value.nodes[data.id],
    type: 'branch',
    name: data.name,
    param_name: data.param_name,
    match_values: data.match_values,
    match_target: data.match_target,
    else_target: data.else_target,
    _x: liveJson.value.nodes[data.id]?._x,
    _y: liveJson.value.nodes[data.id]?._y,
  }
  editingBranch.value = null
}

// ── Add nodes → write to liveJson ──
function addPageNode() {
  const id = `page_${Date.now()}`
  if (!liveJson.value.entry_node) liveJson.value.entry_node = id
  liveJson.value.nodes[id] = {
    type: 'page', name: 'Новая страница', next_node: '', params: [],
    _x: Object.keys(liveJson.value.nodes).length * 320 + 80, _y: 60,
  }
}
function addBranchNode() {
  const id = `branch_${Date.now()}`
  liveJson.value.nodes[id] = {
    type: 'branch', name: '', param_name: '', match_values: [],
    match_target: '', else_target: '',
    _x: Object.keys(liveJson.value.nodes).length * 320 + 80, _y: 60,
  }
}

// ── Edge editing (directly on flowEdges, sync to liveJson) ──
function onEdgeDblClick({ edge }) { edgeEdit.value = { ...edge } }
function saveEdgeEdit() {
  if (!edgeEdit.value) return
  // Sync label to liveJson
  const ge = liveJson.value.edges || []
  const matchEdge = ge.find(e => e.from === edgeEdit.value.source && e.to === edgeEdit.value.target)
  if (matchEdge) matchEdge.label = edgeEdit.value.label
  const feIdx = flowEdges.value.findIndex(e => e.id === edgeEdit.value.id)
  if (feIdx >= 0) flowEdges.value[feIdx].label = edgeEdit.value.label
  edgeEdit.value = null
}
function deleteEdge() {
  liveJson.value.edges = (liveJson.value.edges || []).filter(
    e => !(e.from === edgeEdit.value.source && e.to === edgeEdit.value.target)
  )
  flowEdges.value = flowEdges.value.filter(e => e.id !== edgeEdit.value.id)
  edgeEdit.value = null
}
function onConnect(conn) {
  if (conn.source === conn.target) return
  liveJson.value.edges = liveJson.value.edges || []
  liveJson.value.edges.push({ from: conn.source, to: conn.target, label: '' })
}

// ── Auto-layout (writes _x/_y to liveJson) ──
function autoLayout() {
  const gj = liveJson.value
  const depth = {}, visited = new Set()
  function dfs(id, d) { if (visited.has(id) || !id) return; visited.add(id); depth[id] = Math.max(depth[id]||0, d); (gj.edges||[]).forEach(e => { if (e.from===id) dfs(e.to, d+1) }) }
  if (gj.entry_node) dfs(gj.entry_node, 0)
  Object.keys(gj.nodes).forEach(id => { if (!visited.has(id)) dfs(id, 0) })
  const byD = {}; Object.entries(depth).forEach(([id,d]) => { (byD[d]=byD[d]||[]).push(id) })
  const sx=320, sy=180, ox=80, oy=60
  Object.entries(gj.nodes).forEach(([id, nd]) => {
    const d = depth[id] || 0, sibs = byD[d] || [id]
    const w = sibs.length * sx, off = -w/2 + sx/2, idx = sibs.indexOf(id)
    nd._x = idx*sx + off + ox; nd._y = d*sy + oy
  })
}

// ── Save to API ──
function saveToApi() {
  const gj = JSON.parse(JSON.stringify(liveJson.value))
  emit('update:graphJson', gj)
  emit('save', gj)
}
</script>

<style scoped>
.qgf-editor { display: flex; flex-direction: column; height: 100%; min-height: 600px; }
.qgf-toolbar { display: flex; align-items: center; gap: 16px; padding: 8px 16px; background: #1e293b; color: #fff; }
.qgf-title { font-weight: 600; font-size: 15px; }
.qgf-actions { display: flex; gap: 8px; margin-left: auto; }
.qgf-btn { padding: 6px 14px; border-radius: 6px; font-size: 13px; cursor: pointer; border: 1px solid transparent; font-weight: 500; }
.qgf-btn-primary { background: #2563eb; color: #fff; }
.qgf-btn-accent { background: #7c3aed; color: #fff; }
.qgf-btn-outline { background: transparent; border-color: #cbd5e1; color: #e2e8f0; }
.qgf-btn-danger { background: #dc2626; color: #fff; }
.qgf-main { flex: 1; min-height: 0; }
.qgf-modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 200; }
.qgf-modal { background: #fff; border-radius: 10px; padding: 24px; min-width: 320px; max-width: 420px; }
.qgf-modal h4 { margin: 0 0 16px; font-size: 15px; }
.qgf-field { display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px; }
.qgf-field label { font-size: 12px; font-weight: 600; color: #475569; }
.qgf-input { padding: 7px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; }
.qgf-input:focus { border-color: #3b82f6; outline: none; }
.qgf-actions { display: flex; gap: 8px; margin-top: 12px; }
</style>
