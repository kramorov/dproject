<template>
  <div class="debug-page">
    <!-- Левая панель: запросы -->
    <div class="panel queries-panel">
      <h3>Запросы</h3>
      <button class="btn-sm" @click="openQueryModal()">+ Добавить</button>
      <div class="list">
        <div v-for="q in queries" :key="q.id" class="card"
             :class="{ active: selectedQuery && selectedQuery.id === q.id }"
             @click="selectQuery(q)">
          <div class="card-id">#{{ q.id }}</div>
          <div class="card-text">{{ (q.text || '').slice(0, 120) }}{{ (q.text || '').length > 120 ? '…' : '' }}</div>
          <div class="actions">
            <button class="btn-xs" @click.stop="openQueryModal(q)">✎</button>
            <button class="btn-xs" @click.stop="sendToInput(q)">→</button>
            <button class="btn-xs del" @click.stop="deleteQuery(q.id)">✕</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Центр -->
    <div class="center">
      <div class="input-area">
        <textarea v-model="inputText" placeholder="Текст запроса…" :disabled="loading" />
        <button :disabled="loading || !inputText.trim()" @click="runAnalyze">
          {{ loading ? 'Анализ…' : 'Анализировать' }}
        </button>
      </div>

      <ProgressBar :running="loading" :duration-sec="estimatedSec" :segments="10" :text="'Анализ и подбор параметров. Займет примерно ' + estimatedSec + ' сек.'" @completed="onProgressDone" />

      <div v-if="analyzeStatus" class="status-panel" :class="'status-' + analyzeStatus">
        <div v-if="analyzeStatus === 'ready'">
          ✅ Всё понятно. Найдено {{ tasks.length }} задач.
          <div class="task-list">
            <div v-for="t in tasks" :key="t.id" class="task-item">
              <b>#{{ t.id }}</b> {{ t.type }}
              <span v-if="t.depends_on && t.depends_on.length">← зависит от [{{ t.depends_on.join(', ') }}]</span>
              — {{ t.summary }}
            </div>
          </div>
          <button class="btn-execute" @click="runExecute" :disabled="executing">
            {{ executing ? 'Выполняю…' : '▶ Продолжить' }}
          </button>
        </div>
        <div v-else-if="analyzeStatus === 'needs_info'">
          ⚠️ Нужны уточнения:
          <pre class="info-text">{{ analysisText }}</pre>
          <em>Допишите запрос и отправьте снова.</em>
        </div>
        <div v-else-if="analyzeStatus === 'rejected'">
          ❌ Отказ: {{ analysisText }}
        </div>
      </div>

      <div v-if="rawResponse" class="raw-json-panel">
        <h4 @click="showRawJson = !showRawJson" style="cursor:pointer">{{ showRawJson ? '▼' : '▶' }} Raw JSON ответ</h4>
        <pre v-if="showRawJson">{{ rawResponse }}</pre>
      </div>

      <div v-if="treeData && treeData.positions" class="tree-panel">
        <h4>Дерево подбора</h4>
        <div v-for="pos in treeData.positions" :key="pos.id" class="tree-position">
          <div class="tree-node level-1">
            <strong>📦 {{ pos.description || 'Позиция' }}</strong>
            <span class="node-status">{{ pos.status || '' }}</span>
          </div>
          <div v-if="pos.components" class="tree-children">
            <TreeNodeDisplay
              :equipNameMap="equipNameMap"
              :extractedParams="extractedParams"
              v-for="comp in pos.components"
              :key="comp.id"
              :node="comp"
              :level="2"
              @select="onNodeSelect"
              @extract="onNodeExtract"
              @filter="onNodeFilter"
            />
          </div>
        </div>
      </div>

      <!-- Прогресс-лог -->
      <div v-if="progressLog.length" class="progress-panel">
        <h4>Прогресс выполнения</h4>
        <div v-for="(entry, i) in progressLog" :key="i" class="log-line" :class="'log-' + entry.status">
          {{ entry.message }}
        </div>
      </div>
    </div>

        <!-- Правая панель: скиллы — временно скрыта, decompose_v4 используется по умолчанию -->
    <div v-if="false" class="panel skills-panel">
      <h3>Скилл</h3>
      <div class="list">
        <div v-for="s in skills" :key="s.id" class="card"
             :class="{ active: selectedSkill && selectedSkill.id === s.id }">
          <label class="card-label">
            <input type="checkbox"
                   :checked="selectedSkill && selectedSkill.id === s.id"
                   @change="selectSkill(s)" />
            {{ s.code || (s.step + ' / ' + (s.equipment_type_detail ? s.equipment_type_detail.name : '*')) }}
          </label>
          <div class="card-meta">{{ s.prompt_template_detail ? s.prompt_template_detail.code || 'prompt #' + s.prompt_template : 'no prompt' }}</div>
        </div>
      </div>
    </div>

<!-- Статистика -->
    <div v-if="stats.length" class="stats-bar">
      <b>Запрос:</b> {{ lastPromptTokens }}→{{ lastCompletionTokens }} ({{ lastTokens }}) токенов, ${{ lastCost.toFixed(6) }}
      &nbsp;|&nbsp;
      <b>Сессия:</b> {{ stats.length }} запросов, {{ totalTokens }} токенов,
      avg {{ avgTokens }} / запрос, ${{ totalCost.toFixed(4) }} всего
    </div>

    <!-- Модалки (без изменений) -->
    <div v-if="showQueryModal" class="modal-overlay" @click.self="showQueryModal = false">
      <div class="modal">
        <h3>{{ editingQuery.id ? 'Редактировать запрос #' + editingQuery.id : 'Новый запрос' }}</h3>
        <textarea v-model="editingQuery.text" rows="12" class="modal-textarea" placeholder="Текст запроса…" />
        <div class="modal-actions"><button @click="saveQuery">Сохранить</button><button class="cancel" @click="showQueryModal = false">Отмена</button></div>
      </div>
    </div>
    <div v-if="showPromptModal" class="modal-overlay" @click.self="showPromptModal = false">
      <div class="modal">
        <h3>{{ editingPrompt.id ? 'Редактировать промпт #' + editingPrompt.id : 'Новый промпт' }}</h3>
        <div class="modal-row"><input v-model="editingPrompt.name" placeholder="Имя" class="modal-input" /><input v-model="editingPrompt.version" placeholder="Версия" class="modal-input" style="width:100px" /></div>
        <textarea v-model="editingPrompt.template_text" rows="16" class="modal-textarea" placeholder="Текст промпта…" />
        <div class="modal-actions"><button @click="savePrompt">Сохранить</button><button class="cancel" @click="showPromptModal = false">Отмена</button></div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/shared/api'
import TreeNodeDisplay from '@/components/TreeNodeDisplay.vue'
import ProgressBar from '@/components/ProgressBar.vue'

export default {
  name: 'AiDebugPage',
  components: { TreeNodeDisplay, ProgressBar },
  data() {
    return {
      queries: [], selectedQuery: null, showQueryModal: false, editingQuery: { id: null, text: '' },
      skills: [],
      equipmentTypes: [], selectedSkill: null, showPromptModal: false, editingPrompt: { id: null, name: '', version: '1', template_text: '' },
      inputText: '', loading: false, executing: false,
      analyzeStatus: '', analysisText: '', tasks: [], globalReqs: {},
      progressLog: [],
      stats: [],
      treeData: null,
      rawResponse: null,
      showRawJson: false,
      conversationId: null,
      nodeIds: [], extractedParams: {},
      estimatedSec: 5, 
      selectedNodeId: null,
      nodeOptions: [],
      selectingNodeId: null,
    }
  },
  computed: {
    equipNameMap() { const m = {}; this.equipmentTypes.forEach(e => { m[e.code] = e.name }); return m },
    lastTokens() { const s = this.stats.at(-1); return s ? s.tokens : 0 },
    lastCost() { const s = this.stats.at(-1); return s ? s.cost : 0 },
    lastPromptTokens() { const s = this.stats.at(-1); return s ? (s.prompt_tokens || 0) : 0 },
    lastCompletionTokens() { const s = this.stats.at(-1); return s ? (s.completion_tokens || 0) : 0 },
    totalTokens() { return this.stats.reduce((a, s) => a + (s.tokens || 0), 0) },
    totalCost() { return this.stats.reduce((a, s) => a + (s.cost || 0), 0) },
    avgTokens() { return this.stats.length ? Math.round(this.totalTokens / this.stats.length) : 0 },
  },
  async mounted() { await this.loadQueries(); await this.loadSkills(); this.loadEquipmentTypes() },
  methods: {
    onProgressDone() { /* progress finished */ },
    
    async loadQueries() { const r = await api.get('/ai-assistant/samples/'); this.queries = (r.data && r.data.results) || [] },
    async loadEquipmentTypes() { try { const r = await api.get('/ai-assistant/equipment-types/'); this.equipmentTypes = Array.isArray(r.data) ? r.data : (r.data.results || []) } catch { this.equipmentTypes = [] } },
    async loadSkills() {
      try {
        const r = await api.get('/ai-assistant/skills/')
        this.skills = Array.isArray(r.data) ? r.data : (r.data.results || [])
        const d4 = this.skills.find(s => s.code === 'decompose_v4')
        if (d4) { this.selectedSkill = d4; if (d4.avg_latency_ms) this.estimatedSec = Math.round(d4.avg_latency_ms * 1.3 / 1000) || 5 }
      } catch { this.skills = [] }
    },
    selectQuery(q) { this.selectedQuery = q },
    selectSkill(s) { this.selectedSkill = (this.selectedSkill && this.selectedSkill.id === s.id) ? null : s; if (s && s.avg_latency_ms) this.estimatedSec = Math.round(s.avg_latency_ms * 1.3 / 1000) || 5 },
    sendToInput(q) { this.inputText = q.text || '' },

    async runAnalyze() {
      if (!this.inputText.trim()) return
      this.loading = true; this.analyzeStatus = ''; this.tasks = []; this.progressLog = []; this.treeData = null
      try {
        const payload = { text: this.inputText.trim() }
        if (this.selectedSkill && this.selectedSkill.code) payload.skill_code = this.selectedSkill.code
        const { data } = await api.post('/ai-assistant/decompose/', payload)
        this.analyzeStatus = data.status
        this.analysisText = data.tree ? JSON.stringify(data.tree, null, 2) : ''
        this.rawResponse = JSON.stringify(data, null, 2); this.treeData = data.tree
        this.nodeIds = data.node_ids || []; console.log('nodeIds:', this.nodeIds.length, this.nodeIds); this.conversationId = data.conversation_id
        this.extractedParams = data.extracted || {}
        this.tasks = data.tasks || []
        this.stats.push({ tokens: data.tokens || 0, prompt_tokens: data.prompt_tokens || 0, completion_tokens: data.completion_tokens || 0, cost: data.cost || 0, ts: Date.now() })
      } catch (e) {
        this.analyzeStatus = 'rejected'; this.analysisText = e.displayMessage || e.message || 'Ошибка'
      } finally { this.loading = false }
    },

    async runExecute() {
      if (!this.tasks.length) return
      this.executing = true; this.progressLog = []
      try {
        const { data } = await api.post('/ai-assistant/execute/', { tasks: this.tasks, global_requirements: this.globalReqs })
        this.progressLog = data.progress_log || []
      } catch (e) {
        this.progressLog = [{ status: 'error', message: e.displayMessage || e.message || 'Ошибка' }]
      } finally { this.executing = false }
    },

    openQueryModal(q) { this.editingQuery = q ? { id: q.id, text: q.text } : { id: null, text: '' }; this.showQueryModal = true },
    async saveQuery() { const { id, text } = this.editingQuery; if (!text) return; if (id) await api.patch(`/ai-assistant/samples/${id}/`, { text }); else await api.post('/ai-assistant/samples/', { text }); this.showQueryModal = false; await this.loadQueries() },
    async deleteQuery(id) { if (!confirm('Удалить?')) return; await api.delete(`/ai-assistant/samples/${id}/`); await this.loadQueries() },
    openPromptModal(p) { this.editingPrompt = p ? { id: p.id, name: p.name, version: p.version, template_text: p.template_text } : { id: null, name: '', version: '1', template_text: '' }; this.showPromptModal = true },
    async savePrompt() { const { id, name, version, template_text } = this.editingPrompt; if (!name) return; if (id) await api.patch(`/ai-assistant/prompts/${id}/`, { name, version, template_text }); else await api.post('/ai-assistant/prompts/', { name, version, template_text }); this.showPromptModal = false; await this.loadSkills(); this.loadEquipmentTypes() },

    async onNodeExtract(nodeId) {
      try {
        const { data } = await api.post(`/ai-assistant/extract/${nodeId}/`)
        this.loadTree()
      } catch (e) {
        console.error('extract error', e)
      }
    },
    async onNodeFilter(nodeId) {
      this.selectingNodeId = nodeId
      try {
        const { data } = await api.post(`/ai-assistant/filter/${nodeId}/`)
        this.nodeOptions = data.options || []
      } catch (e) {
        console.error('filter error', e)
      }
    },
    async onNodeSelect(nodeId, productType, productId) {
      try {
        await api.post(`/ai-assistant/select/${nodeId}/`, {
          product_type: productType,
          product_id: productId
        })
        this.nodeOptions = []
        this.selectingNodeId = null
        this.loadTree()
      } catch (e) {
        console.error('select error', e)
      }
    },
    async loadTree() {
      if (!this.conversationId) return
      const { data } = await api.get(`/ai-assistant/tree/${this.conversationId}/`)
      this.treeData = { positions: data.tree }
    },
  },
}
</script>

<style scoped>

.debug-page { display: grid; grid-template-columns: 300px 1fr 280px; grid-template-rows: 1fr auto; gap: 10px; height: calc(100vh - 60px); padding: 10px; }
.panel { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; overflow-y: auto; }
.panel h3 { margin: 0 0 8px; font-size: 15px; font-weight: 600; }
.list { display: flex; flex-direction: column; gap: 4px; }
.card { border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 8px; cursor: pointer; background: #fff; display: flex; flex-wrap: wrap; align-items: center; gap: 4px; }
.card:hover { background: #f1f5f9; }
.card.active { background: #dbeafe; border-color: #3b82f6; }
.card-id { font-size: 10px; color: #64748b; font-weight: 600; min-width: 24px; }
.card-text { font-size: 12px; line-height: 1.4; flex: 1; word-break: break-word; }
.card-label { font-size: 12px; display: flex; align-items: center; gap: 4px; flex: 1; cursor: pointer; }
.actions { display: flex; gap: 2px; margin-left: auto; }
.btn-sm { padding: 3px 10px; font-size: 12px; background: #2563eb; color: #fff; border: none; border-radius: 4px; cursor: pointer; margin-bottom: 8px; }
.btn-xs { padding: 1px 5px; font-size: 10px; border: 1px solid #cbd5e1; border-radius: 3px; cursor: pointer; background: #fff; }
.btn-xs.del { color: #dc2626; border-color: #dc2626; }
.center { display: flex; flex-direction: column; gap: 10px; overflow-y: auto; }
.input-area { display: flex; gap: 8px; }
.center textarea { flex: 1; height: 120px; padding: 8px; font-size: 13px; border: 1px solid #ccc; border-radius: 6px; resize: vertical; }
.center button { padding: 8px 16px; background: #2563eb; color: #fff; border: none; border-radius: 6px; white-space: nowrap; cursor: pointer; }
.center button:disabled { background: #94a3b8; cursor: default; }
.status-panel { padding: 12px; border-radius: 8px; font-size: 14px; }
.status-ready { background: #f0fdf4; border: 1px solid #86efac; }
.status-needs_info { background: #fef9c3; border: 1px solid #facc15; }
.status-rejected { background: #fef2f2; border: 1px solid #fca5a5; }
.task-list { margin: 8px 0; }
.task-item { padding: 4px 8px; background: #fff; border-radius: 4px; margin-bottom: 4px; font-size: 13px; }
.btn-execute { margin-top: 8px; padding: 8px 24px; background: #16a34a; color: #fff; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; }
.btn-execute:disabled { background: #86efac; }
.info-text { white-space: pre-wrap; margin: 6px 0; font-size: 13px; }
.progress-panel { background: #1e293b; color: #e2e8f0; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 12px; }
.progress-panel h4 { margin: 0 0 6px; color: #94a3b8; font-size: 12px; }
.log-line { padding: 2px 0; }
.log-running { color: #facc15; }
.log-done { color: #4ade80; }
.log-skipped { color: #94a3b8; }
.log-error { color: #f87171; }
.stats-bar { grid-column: 1 / -1; background: #1e293b; color: #e2e8f0; padding: 8px 14px; border-radius: 6px; font-size: 13px; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: #fff; border-radius: 10px; padding: 20px; width: 700px; max-height: 85vh; overflow-y: auto; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
.modal h3 { margin: 0 0 12px; font-size: 16px; font-weight: 600; }
.modal-textarea { width: 100%; padding: 10px; font-size: 15px; line-height: 1.5; border: 1px solid #cbd5e1; border-radius: 6px; resize: vertical; box-sizing: border-box; font-family: inherit; }
.modal-row { display: flex; gap: 8px; margin-bottom: 8px; }
.modal-input { flex: 1; padding: 6px 8px; font-size: 14px; border: 1px solid #cbd5e1; border-radius: 4px; }
.modal-actions { display: flex; gap: 8px; margin-top: 12px; }
.modal-actions button { padding: 6px 16px; font-size: 14px; border: none; border-radius: 5px; background: #2563eb; color: #fff; cursor: pointer; }
.modal-actions .cancel { background: #94a3b8; }

.tree-panel { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-top: 10px; }
.tree-panel h4 { margin: 0 0 8px; font-size: 14px; }
.tree-position { margin-bottom: 16px; }
.tree-node { display: flex; align-items: center; gap: 6px; padding: 5px 10px; border-radius: 6px; border-left: 3px solid transparent; }
.tree-node.level-1 { background: #dbeafe; font-size: 14px; font-weight: 600; border-left-color: #3b82f6; }
.tree-node.level-2 { background: #f1f5f9; font-size: 13px; }
.tree-node.level-3 { background: #fff; font-size: 12px; border: 1px solid #e2e8f0; }
.tree-children { margin-left: 8px; }
.node-status { font-size: 11px; color: #64748b; }
.node-actions { display: flex; gap: 4px; }
.options-panel { margin-top: 8px; padding: 8px; background: #fff; border: 1px solid #e2e8f0; border-radius: 4px; }
.option-item { display: flex; align-items: center; justify-content: space-between; padding: 4px 0; font-size: 12px; border-bottom: 1px solid #f1f5f9; }
.option-item button { padding: 2px 6px; font-size: 11px; }

</style>
