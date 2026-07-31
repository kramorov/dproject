<template>
  <div class="skill-config">
    <h1>Skill Configurator</h1>
    <nav class="tabs">
      <button v-for="t in tabs" :key="t.id" :class="{ active: activeTab === t.id }" @click="activeTab = t.id">{{ t.label }}</button>
    </nav>

    <!-- 🌳 Tree Tab -->
    <section v-show="activeTab === 'tree'" class="section tree-section">
      <h2>Дерево CompositionGroup + EquipmentType</h2>
      <div class="tree-container">
        <TreeNode v-for="node in compositionTree" :key="nodeKey(node)" :node="node" :depth="0" @dblclick="openEditModal(node)" />
        <div v-if="!compositionTree.length" class="empty">Нет данных. Создайте CompositionGroup во вкладке «Конструктор».</div>
      </div>
    </section>

    <!-- 🏗️ Constructor Tab -->
    <section v-show="activeTab === 'constructor'" class="section constructor-section">
      <div class="constructor-layout">
        <!-- Left: EquipmentType tree -->
        <div class="panel left-panel">
          <h3>EquipmentType</h3>
          <div class="panel-tree">
            <EquipmentTypeNode
              v-for="et in equipmentTypeTree"
              :key="'et-' + et.id"
              :node="et"
              :depth="0"
              @dragstart="onDragStart($event, { type: 'equipment_type', id: et.id, name: et.name })"
            />
          </div>
        </div>

        <!-- Right: CompositionGroup editor -->
        <div class="panel right-panel">
          <div class="right-header">
            <h3>CompositionGroup</h3>
            <button class="btn-add" @click="addRootGroup">+ Корневая группа</button>
          </div>
          <div
            class="drop-zone"
            @dragover.prevent
            @drop.prevent="onDrop($event, null)"
          >
            <CompositionGroupNode
              v-for="cg in compositionTree"
              :key="'cg-' + cg.id"
              :node="cg"
              :depth="0"
              @drop-item="onDropItem"
              @add-child-group="addChildGroup"
              @remove-et="removeEquipmentType"
              @delete-group="deleteGroup"
              @edit-node="openEditModal"
              @dragstart="onDragStart"
              @remove-reference="(...args) => removeReferenceFromGroup(...args)"
              @edit-reference="openReferenceEdit"
            />
            <div v-if="!compositionTree.length" class="empty">
              Перетащите EquipmentType сюда или создайте группу.
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 📋 MBOM Tab -->
    <section v-show="activeTab === 'mbom'" class="section">
      <h2>MBOM (Спецификации) <button class="btn-add" @click="addMbom">+ Создать</button></h2>
      <table v-if="mboms.length">
        <thead><tr><th></th><th>ID</th><th>Название</th><th>Код</th><th>Описание</th><th>Создан</th><th></th></tr></thead>
        <tbody>
          <tr v-for="m in mboms" :key="m.id">
            <td><span class="toggle" @click="toggleMbom(m.id)">{{ expandedMboms.has(m.id) ? '▼' : '▶' }}</span></td>
            <td>{{ m.id }}</td>
            <td><input v-model="m.name" class="cell-input" /></td>
            <td><input v-model="m.code" class="cell-input" /></td>
            <td><input v-model="m.description" class="cell-input" /></td>
            <td>{{ formatDate(m.created_at) }}</td>
            <td>
              <button class="btn-save-sm" @click="saveMbom(m)">💾</button>
              <button class="btn-del" @click="deleteMbom(m.id)">✕</button>
            </td>
          </tr>
          <tr v-if="expandedMboms.has(m.id) && m.items && m.items.length" class="mbom-items-row">
            <td colspan="8">
              <div class="mbom-items-tree">
                <MBOMItemNode v-for="item in m.items" :key="item.id" :node="item" :depth="0" />
              </div>
            </td>
          </tr>
          <tr v-else-if="expandedMboms.has(m.id)" class="mbom-items-row">
            <td colspan="8"><div class="empty">Нет элементов в спецификации.</div></td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">Спецификации отсутствуют.</div>
    </section>
  </div>

    <!-- Edit Modal -->
    <div v-if="editingNode" class="modal-overlay">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingNode.id ? 'Редактирование: ' + (editingNode.name || editingNode.code || '#' + editingNode.id) : 'Новая группа' }}</h3>
          <button class="modal-close" @click="closeModal">✕</button>
        </div>
        <div class="modal-body">
          <label>Название</label>
          <input v-model="editingNode.name" class="modal-input" />
          <label>Код</label>
          <input v-model="editingNode.code" class="modal-input" />
          <label>Описание</label>
          <textarea v-model="editingNode.description" class="modal-textarea" rows="3" />
          <label>Тип группы</label>
          <select v-model="editingNode.group_type" class="modal-input">
            <option value="required">Обязательный</option>
            <option value="optional">Опциональный</option>
            <option value="xor">XOR — ровно один из</option>
          </select>
          <label>Порядок сортировки</label>
          <input v-model.number="editingNode.sorting_order" type="number" class="modal-input" />
          <label v-if="editingNode.id">Родитель</label>
          <select v-if="editingNode.id" v-model="editingNode.parent_id" class="modal-input">
            <option :value="null">— Корневая (без родителя) —</option>
            <option v-for="g in parentOptions" :key="g.id" :value="g.id">{{ g.name }} ({{ g.code }})</option>
          </select>
          <label>JSON Schema</label>
          <select v-model="editingNode.output_schema" class="modal-input">
            <option :value="null">— Без схемы —</option>
            <option v-for="s in schemas" :key="s.id" :value="s.id">{{ s.name }} v{{ s.version }}</option>
          </select>
          <label>Prompt Template</label>
          <select v-model="editingNode.prompt_template" class="modal-input">
            <option :value="null">— Без промпта —</option>
            <option v-for="p in prompts" :key="p.id" :value="p.id">{{ p.code || p.name }} v{{ p.version }}</option>
          </select>
        </div>
        <div class="modal-actions">
          <button v-if="editingNode.id" class="btn-del-lg" @click="deleteEdit">🗑️ Удалить</button>
          
          <div class="modal-actions-right">
            <button class="btn-cancel-lg" @click="closeModal">Отмена</button>
            <button class="btn-save-lg" @click="saveEdit">💾 Сохранить</button>
          </div>
        </div>
      </div>
    </div>

    <!-- EquipmentType Edit Modal -->
    <div v-if="editingET" class="modal-overlay">
      <div class="modal">
        <div class="modal-header">
          <h3>Редактирование: {{ editingET.name || editingET.code }}</h3>
          <button class="modal-close" @click="closeETEdit">✕</button>
        </div>
        <div class="modal-body">
          <label>Название</label>
          <input v-model="editingET.name" class="modal-input" />
          <label>Код</label>
          <input v-model="editingET.code" class="modal-input" />
          <label>Родитель</label>
          <select v-model="editingET.parent_id" class="modal-input">
            <option :value="null">— Корневой —</option>
            <option v-for="et in allETsFlat" :key="et.id" :value="et.id">{{ et.name }} ({{ et.code }})</option>
          </select>
          <label>Уровень</label>
          <input v-model.number="editingET.level" type="number" class="modal-input" />
          <label>Иконка</label>
          <input v-model="editingET.icon" class="modal-input" placeholder="📦" />
          <label>JSON Schema <button type="button" class="btn-xs" @click="openSchemaEditor(editingET.output_schema)" title="Редактировать схему">✏️</button></label>
          <div style="display:flex;gap:4px">
            <select v-model="editingET.output_schema" class="modal-input" style="flex:1">
              <option :value="null">— Без схемы —</option>
              <option v-for="s in schemas" :key="s.id" :value="s.id">{{ s.name }} v{{ s.version }}</option>
            </select>
            <button type="button" class="btn-xs" @click="generateSchemaFromModel" title="Взять схему из модели">🔄</button>
          </div>
          <label>Prompt Template</label>
          <select v-model="editingET.prompt_template" class="modal-input">
            <option :value="null">— Без промпта —</option>
            <option v-for="p in prompts" :key="p.id" :value="p.id">{{ p.code || p.name }} v{{ p.version }}</option>
          </select>
        </div>
        <div class="modal-actions">
          <div></div>
          <div class="modal-actions-right">
            <button class="btn-cancel-lg" @click="closeETEdit">Отмена</button>
            <button class="btn-save-lg" @click="saveETEdit">💾 Сохранить</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Schema Editor Modal -->
    <div v-if="editingSchema" class="modal-overlay">
      <div class="modal modal-wide">
        <div class="modal-header">
          <h3>Редактор схемы: {{ editingSchema._name || 'Новая' }}</h3>
          <button class="modal-close" @click="closeSchemaEditor">✕</button>
        </div>
        <div class="modal-body">
          <div style="display:flex;gap:8px;margin-bottom:12px">
            <input v-model="editingSchema._name" class="modal-input" placeholder="Имя схемы" style="flex:1" />
            <input v-model="editingSchema._version" class="modal-input" placeholder="Версия" style="width:80px" />
            <button class="btn-add" @click="saveSchema">💾 Сохранить</button>
          </div>
          <div v-if="editingSchema._fields && editingSchema._fields.length" style="max-height:300px;overflow-y:auto;margin-bottom:12px">
            <table style="width:100%">
              <thead><tr><th>Параметр</th><th>Тип</th><th>Обязательность</th></tr></thead>
              <tbody>
                <tr v-for="(f, i) in editingSchema._fields" :key="i">
                  <td><strong>{{ f.param_name }}</strong><br><small style="color:#888">{{ f.label }}</small></td>
                  <td>{{ f.type }}</td>
                  <td>
                    <select v-model="f.required" class="cell-input" style="width:120px">
                      <option :value="false">Опция</option>
                      <option :value="true">Обязательно</option>
                    </select>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="editingSchema._fields && !editingSchema._fields.length" class="empty">Нет полей. Нажмите «Взять из модели» в карточке EquipmentType.</div>
          <label>JSON Schema (preview)</label>
          <textarea :value="schemaPreview" rows="16" class="modal-textarea" readonly style="font-family:monospace;font-size:12px"></textarea>
        </div>
      </div>
    </div>

    <!-- Reference Edit Modal -->
    <div v-if="referenceEdit" class="modal-overlay">
      <div class="modal">
        <div class="modal-header">
          <h3>Редактирование ссылки: {{ referenceEdit.node.name }}</h3>
          <button class="modal-close" @click="closeReferenceEdit">✕</button>
        </div>
        <div class="modal-body">
          <label>Код</label>
          <input :value="referenceEdit.node.code" disabled class="modal-input" />
          <label>Родитель</label>
          <select v-model="referenceEdit.newParentId" class="modal-input">
            <option v-for="g in allGroups" :key="g.id" :value="g.id">{{ g.name }} ({{ g.code }})</option>
          </select>
        </div>
        <div class="modal-actions">
          <div></div>
          <div class="modal-actions-right">
            <button class="btn-cancel-lg" @click="closeReferenceEdit">Отмена</button>
            <button class="btn-save-lg" @click="saveReferenceEdit">💾 Сохранить</button>
          </div>
        </div>
      </div>
    </div>

</template>

<script>
import api from '@/shared/api'
import TreeNode from '@/components/bom/TreeNode.vue'
import EquipmentTypeNode from '@/components/bom/EquipmentTypeNode.vue'
import CompositionGroupNode from '@/components/bom/CompositionGroupNode.vue'
import MBOMItemNode from '@/components/bom/MBOMItemNode.vue'

export default {
  name: 'SkillConfigPage',
  components: { TreeNode, EquipmentTypeNode, CompositionGroupNode, MBOMItemNode },
  data() {
    return {
      activeTab: 'constructor',
      tabs: [
        { id: 'tree', label: '🌳 Дерево' },
        { id: 'constructor', label: '🏗️ Конструктор' },
        { id: 'mbom', label: '📋 MBOM' },
      ],
      compositionTree: [],
      equipmentTypeTree: [],
      mboms: [],
      expandedMboms: new Set(),
      draggedItem: null,
      editingNode: null,
      editingET: null,
      editingSchema: null,
      allETsFlat: [],
      referenceEdit: null,
      allGroups: [],
      schemas: [],
      prompts: [],
      creatingParentId: null,
    }
  },


  async mounted() {
    await Promise.all([this.loadTree(), this.loadAllGroups(), this.loadEquipmentTypes(), this.loadMboms(), this.loadSchemas(), this.loadPrompts(), this.loadETsFlat()])
  },
  methods: {
    async loadTree() {
      try {
        const { data } = await api.get('/ai-assistant/composition-tree/')
        this.compositionTree = Array.isArray(data) ? data : []
      } catch { this.compositionTree = [] }
    },
    async loadAllGroups() {
      try { const { data } = await api.get('/ai-assistant/composition-groups/'); this.allGroups = Array.isArray(data) ? data : [] } catch { this.allGroups = [] }
    },
    async loadEquipmentTypes() {
      try {
        const { data } = await api.get('/ai-assistant/equipment-type-tree/')
        this.equipmentTypeTree = Array.isArray(data) ? data : []
      } catch { this.equipmentTypeTree = [] }
    },
    async loadMboms() {
      try {
        const { data } = await api.get('/ai-assistant/mboms/')
        this.mboms = Array.isArray(data) ? data : (data.results || [])
      } catch { this.mboms = [] }
    },
    async loadSchemas() {
      try { const { data } = await api.get('/ai-assistant/schemas/'); this.schemas = Array.isArray(data) ? data : [] } catch { this.schemas = [] }
    },
    async loadPrompts() {
      try { const { data } = await api.get('/ai-assistant/prompts/'); this.prompts = Array.isArray(data) ? data : [] } catch { this.prompts = [] }
    },
    async loadETsFlat() {
      try { const { data } = await api.get('/core/', { params: { model: 'core.EquipmentType' } }); this.allETsFlat = Array.isArray(data) ? data : [] } catch { this.allETsFlat = [] }
    },

    // Drag & Drop
    onDragStart(event, item) {
      this.draggedItem = item
      event.dataTransfer.effectAllowed = 'move'
      event.dataTransfer.setData('text/plain', JSON.stringify(item))
    },
    async onDrop(event, targetGroupId) {
      const item = this.draggedItem
      if (!item) return
      this.draggedItem = null

      if (item.type === 'equipment_type') {
        if (targetGroupId === null) {
          this.showConfirm({ title: "Внимание", message: "Сначала создайте CompositionGroup (кнопка «+ Корневая группа»)", cancelText: "" })
          return
        }
        await this.addEquipmentTypeToGroup(targetGroupId, item.id)
      } else if (item.type === 'composition_group' && targetGroupId !== null && item.id !== targetGroupId) {
        if (confirm("Перенести группу?\nOK - перенести (изменит подчинённость)\nОтмена - сделать ссылку")) {
          await this.moveGroup(item.id, targetGroupId)
        } else {
          await this.addReferenceToGroup(targetGroupId, item.id)
          await this.loadTree()
        }
      } else if (item.type === 'composition_group' && targetGroupId === null) {
        if (confirm("Переместить '" + item.name + "' в корень?")) {
          await this.moveGroup(item.id, null)
        }
      }
    },
    async onDropItem({ item, groupId }) {
      this.draggedItem = item
      await this.onDrop(new Event('drop'), groupId)
    },

    // CompositionGroup CRUD
    addRootGroup() {
      this.creatingParentId = null
      this.editingNode = {
        name: '',
        code: '',
        description: '',
        group_type: 'required',
        sorting_order: 0,
      }
    },
    addChildGroup(parentId) {
      this.creatingParentId = parentId
      this.editingNode = {
        name: '',
        code: '',
        description: '',
        group_type: 'required',
        sorting_order: 0,
      }
    },
    async addEquipmentTypeToGroup(groupId, etId) {
      try {
        const { data: group } = await api.get(`/ai-assistant/composition-groups/${groupId}/`)
        const current = group.equipment_types || []
        if (current.includes(etId)) return // already there
        await api.patch(`/ai-assistant/composition-groups/${groupId}/`, {
          equipment_types: [...current, etId],
        })
        await this.loadTree()
      } catch (e) { alert('Ошибка: ' + (e.displayMessage || e.message)) }
    },
    async removeEquipmentType(groupId, etId) {
      try {
        const { data: group } = await api.get(`/ai-assistant/composition-groups/${groupId}/`)
        const updated = (group.equipment_types || []).filter(id => id !== etId)
        await api.patch(`/ai-assistant/composition-groups/${groupId}/`, { equipment_types: updated })
        await this.loadTree()
      } catch (e) { alert('Ошибка: ' + (e.displayMessage || e.message)) }
    },
    async moveGroup(groupId, newParentId) {
      try {
        await api.patch(`/ai-assistant/composition-groups/${groupId}/`, { parent: newParentId })
        await this.loadTree()
      } catch (e) { alert('Ошибка: ' + (e.displayMessage || e.message)) }
    },
    async deleteGroup(groupId) {
      if (!confirm("Удалить группу и все вложенные?")) return
      try {
        await api.delete(`/ai-assistant/composition-groups/${groupId}/`)
        await this.loadTree()
      } catch (e) { alert('Ошибка: ' + (e.displayMessage || e.message)) }
    },





    async addReferenceToGroup(groupId, refGroupId) {
      try {
        await api.post(`/ai-assistant/composition-groups/${groupId}/add_reference/`, { reference_id: refGroupId })
      } catch (e) { alert('Ошибка: ' + (e.displayMessage || e.message)) }
    },
    async removeReferenceFromGroup(groupId, refGroupId) {
      if (!confirm("Убрать ссылку?")) return
      try {
        await api.post(`/ai-assistant/composition-groups/${groupId}/remove_reference/`, { reference_id: refGroupId })
        await this.loadTree()
      } catch (e) { alert('Ошибка: ' + (e.displayMessage || e.message)) }
    },

    // MBOM tree
    toggleMbom(id) {
      if (this.expandedMboms.has(id)) this.expandedMboms.delete(id)
      else this.expandedMboms.add(id)
      this.expandedMboms = new Set(this.expandedMboms)
    },

    // MBOM CRUD
    async addMbom() {
      const name = prompt('Название спецификации:')
      if (!name) return
      try {
        await api.post('/ai-assistant/mboms/', { name })
        await this.loadMboms()
      } catch (e) { alert('Ошибка: ' + (e.displayMessage || e.message)) }
    },
    async saveMbom(m) {
      try {
        await api.patch(`/ai-assistant/mboms/${m.id}/`, {
          name: m.name, code: m.code, description: m.description,
        })
      } catch (e) { alert('Ошибка: ' + (e.displayMessage || e.message)) }
    },
    async deleteMbom(id) {
      if (!await this.showConfirm({ title: "Удаление", message: "Удалить спецификацию?", confirmText: "Удалить" })) return
      try {
        await api.delete(`/ai-assistant/mboms/${id}/`)
        await this.loadMboms()
      } catch (e) { alert('Ошибка: ' + (e.displayMessage || e.message)) }
    },

    // Popup editing
    async openEditModal(node) {
      if (node.item_type === 'equipment_type') { await this.openETEdit(node); return }
      await this.loadAllGroups()
      this.editingNode = { ...node }
      this.editingNode.parent_id = this.findParentId(node.id)
      this.creatingParentId = null
    },
    closeModal() {
      this.editingNode = null
      this.allGroups = []
      this.creatingParentId = null
    },
    async saveEdit() {
      if (!this.editingNode) return
      const n = this.editingNode
      try {
        if (n.id) {
          await api.patch(`/ai-assistant/composition-groups/${n.id}/`, {
            name: n.name, code: n.code, description: n.description,
            group_type: n.group_type, sorting_order: n.sorting_order,
            parent: n.parent_id ?? null,
            output_schema: n.output_schema ?? null,
            prompt_template: n.prompt_template ?? null,
          })
        } else {
          await api.post('/ai-assistant/composition-groups/', {
            name: n.name, code: n.code, description: n.description,
            group_type: n.group_type, sorting_order: n.sorting_order,
            parent: this.creatingParentId,
          })
        }
        this.closeModal()
        await this.loadTree()
      } catch (e) { alert('Ошибка: ' + (e.displayMessage || e.message)) }
    },
    async deleteEdit() {
      if (!this.editingNode) return
      if (!await this.showConfirm({ title: "Удаление", message: "Удалить группу и все вложенные?", confirmText: "Удалить" })) return
      try {
        await api.delete(`/ai-assistant/composition-groups/${this.editingNode.id}/`)
      } catch (e) { alert('Ошибка: ' + (e.displayMessage || e.message)); return }
      this.closeModal()
      await this.loadTree()
    },

    // Helpers
    nodeKey(node) {
      return (node.item_type || 'cg') + '-' + node.id
    },
    formatDate(s) {
      if (!s) return '—'
      return new Date(s).toLocaleDateString('ru-RU')
    },

    // EquipmentType editing
    async openETEdit(node) {
      await this.loadETsFlat()
      this.editingET = { ...node }
      this.editingET.parent_id = node.parent_id || (node.parent ? node.parent.id : null)
    },
    closeETEdit() {
      this.editingET = null
    },
    async saveETEdit() {
      const et = this.editingET
      if (!et) return
      try {
        await api.put('/core/', {
          model: 'core.EquipmentType',
          id: et.id,
          name: et.name,
          code: et.code,
          parent: et.parent_id ?? null,
          level: et.level,
          icon: et.icon,
          output_schema: et.output_schema ?? null,
          prompt_template: et.prompt_template ?? null,
        })
        this.closeETEdit()
        await this.loadEquipmentTypes()
        await this.loadTree()
      } catch (e) { alert('Ошибка: ' + (e.displayMessage || e.message)) }
    },

    // Schema editing
    openSchemaEditor(schemaId) {
      if (schemaId) {
        const s = this.schemas.find(x => x.id === schemaId)
        if (s) {
          this.editingSchema = {
            ...s,
            _name: s.name,
            _version: s.version,
            _fields: this.parseSchemaFields(s.schema_json),
          }
          return
        }
      }
      this.editingSchema = { _name: '', _version: '1', _fields: [], schema_json: {} }
    },
    closeSchemaEditor() { this.editingSchema = null },
    parseSchemaFields(schemaJson) {
      if (!schemaJson || !schemaJson.properties) return []
      const required = schemaJson.required || []
      return Object.entries(schemaJson.properties).map(([key, val]) => ({
        param_name: key,
        label: val.description || key,
        type: val.type || 'string',
        required: required.includes(key),
      }))
    },
    async saveSchema() {
      const s = this.editingSchema
      if (!s || !s._name) return
      const required = (s._fields || []).filter(f => f.required).map(f => f.param_name)
      const properties = {}
      ;(s._fields || []).forEach(f => { properties[f.param_name] = { type: f.type, description: f.label } })
      const schemaJson = { type: 'object', properties, required }
      try {
        if (s.id) {
          await api.patch(`/ai-assistant/schemas/${s.id}/`, {
            name: s._name, version: s._version,
            schema_json: schemaJson, is_active: s.is_active !== false,
          })
        } else {
          const { data } = await api.post('/ai-assistant/schemas/', {
            name: s._name, version: s._version,
            schema_json: schemaJson, is_active: true,
          })
          s.id = data.id
        }
        await this.loadSchemas()
        this.closeSchemaEditor()
      } catch (e) { alert('Ошибка: ' + (e.displayMessage || e.message)) }
    },
    async generateSchemaFromModel() {
      const et = this.editingET
      if (!et || !et.id) return
      try {
        const { data } = await api.post('/ai-assistant/schemas/generate-from-model/', { equipment_type_id: et.id })
        this.editingSchema = {
          _name: (et.code || 'schema') + '_v1',
          _version: '1',
          _fields: data.fields || [],
          schema_json: data.schema_json,
          _generatedFrom: et.id,
        }
      } catch (e) { alert('Ошибка: ' + (e.displayMessage || e.message)) }
    },

    // Reference editing
    async openReferenceEdit(refNode, oldParentId) {
      await this.loadAllGroups()
      this.referenceEdit = { node: refNode, oldParentId, newParentId: oldParentId }
    },
    closeReferenceEdit() {
      this.referenceEdit = null
    },
    async saveReferenceEdit() {
      const ref = this.referenceEdit
      if (!ref) return
      try {
        if (ref.newParentId !== ref.oldParentId) {
          await api.post(`/ai-assistant/composition-groups/${ref.oldParentId}/remove_reference/`, { reference_id: ref.node.id })
          await api.post(`/ai-assistant/composition-groups/${ref.newParentId}/add_reference/`, { reference_id: ref.node.id })
        }
        this.closeReferenceEdit()
        await this.loadTree()
      } catch (e) { alert('Ошибка: ' + (e.displayMessage || e.message)) }
    },

    // Helpers for parent selection
    findParentId(nodeId) {
      const found = this.allGroups.find(g => {
        return g.children && g.children.some(c => c.id === nodeId)
      })
      return found ? found.id : null
    },
    collectDescendantIds(node) {
      const ids = [node.id]
      if (node.children) {
        node.children.filter(c => c.item_type === 'composition_group').forEach(c => {
          ids.push(...this.collectDescendantIds(c))
        })
      }
      return ids
    },
  },
  computed: {
    schemaPreview() {
      if (!this.editingSchema || !this.editingSchema._fields) return ''
      const required = (this.editingSchema._fields || []).filter(f => f.required).map(f => f.param_name)
      const properties = {}
      ;(this.editingSchema._fields || []).forEach(f => { properties[f.param_name] = { type: f.type, description: f.label } })
      return JSON.stringify({ type: 'object', properties, required }, null, 2)
    },
    parentOptions() {
      if (!this.editingNode || !this.editingNode.id) return []
      const excludeIds = this.collectDescendantIds(this.editingNode)
      return this.allGroups.filter(g => !excludeIds.includes(g.id))
    },
  },
}

</script>

<style scoped>
.skill-config { padding: 20px; max-width: 1400px; margin: 0 auto; }
.tabs { display: flex; gap: 4px; margin-bottom: 16px; }
.tabs button { padding: 8px 16px; border: 1px solid #ccc; background: #f5f5f5; cursor: pointer; border-radius: 4px 4px 0 0; }
.tabs button.active { background: #fff; border-bottom-color: #fff; font-weight: bold; }

.section { background: #fff; border: 1px solid #ddd; border-radius: 0 8px 8px 8px; padding: 16px; min-height: 400px; }
h2 { margin-top: 0; }
h3 { margin: 0 0 8px 0; }

/* Constructor Layout */
.constructor-layout { display: flex; gap: 12px; height: calc(100vh - 200px); }
.left-panel { flex: 1; overflow-y: auto; border: 1px solid #eee; border-radius: 6px; padding: 12px; background: #fafafa; }
.right-panel { flex: 2; overflow-y: auto; border: 1px solid #eee; border-radius: 6px; padding: 12px; }
.right-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.panel-tree { min-height: 100px; }

/* Drop zone */
.drop-zone { min-height: 200px; border: 2px dashed transparent; border-radius: 6px; transition: border-color 0.2s; }

/* Buttons */
.btn-add { padding: 4px 12px; background: #3b82f6; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-add:hover { background: #2563eb; }
.btn-save-sm { padding: 2px 8px; font-size: 14px; border: none; background: none; cursor: pointer; }
.btn-del { padding: 2px 8px; font-size: 14px; border: none; background: none; cursor: pointer; color: #ef4444; }
.cell-input { width: 100%; border: 1px solid #ddd; padding: 4px 6px; border-radius: 3px; font-size: 13px; }

/* Table */
table { width: 100%; border-collapse: collapse; margin-top: 12px; }
th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; font-size: 13px; }
th { background: #f9fafb; font-weight: 600; }

.empty { color: #999; padding: 24px; text-align: center; font-style: italic; }
/* MBOM items tree */
.mbom-items-row td { padding: 0; }
.mbom-items-tree { padding: 8px 16px 12px 32px; background: #fafbfc; border-top: 1px solid #eee; }

/* Modal */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: #fff; border-radius: 8px; width: 480px; max-height: 80vh; overflow-y: auto; box-shadow: 0 8px 32px rgba(0,0,0,.2); }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #eee; }
.modal-header h3 { margin: 0; font-size: 16px; }
.modal-close { background: none; border: none; font-size: 18px; cursor: pointer; color: #999; padding: 4px 8px; }
.modal-close:hover { color: #333; }
.modal-body { padding: 20px; display: flex; flex-direction: column; gap: 8px; }
.modal-body label { font-size: 12px; font-weight: 600; color: #666; text-transform: uppercase; }
.modal-input { width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; box-sizing: border-box; }
.modal-textarea { width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; box-sizing: border-box; resize: vertical; }
.modal-actions { display: flex; justify-content: space-between; padding: 16px 20px; border-top: 1px solid #eee; }
.btn-save-lg { padding: 8px 24px; background: #3b82f6; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
.btn-save-lg:hover { background: #2563eb; }
.btn-del-lg { padding: 8px 24px; background: #fff; color: #ef4444; border: 1px solid #fca5a5; border-radius: 4px; cursor: pointer; font-size: 14px; }
.btn-del-lg:hover { background: #fef2f2; }
.modal-actions-right { display: flex; gap: 8px; margin-left: auto; }
.btn-cancel-lg { padding: 8px 24px; background: #fff; color: #666; border: 1px solid #ccc; border-radius: 4px; cursor: pointer; font-size: 14px; }
.btn-cancel-lg:hover { background: #f5f5f5; }
</style>
