<template>
  <div class="bom-config">
    <h1>BOM Configurator</h1>
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
        <thead><tr><th>ID</th><th>Название</th><th>Код</th><th>Описание</th><th>Создан</th><th></th></tr></thead>
        <tbody>
          <tr v-for="m in mboms" :key="m.id">
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
        </tbody>
      </table>
      <div v-else class="empty">Спецификации отсутствуют.</div>
    </section>
  </div>

    <!-- Edit Modal -->
    <div v-if="editingNode" class="modal-overlay">
      <div class="modal">
        <div class="modal-header">
          <h3>Редактирование: {{ editingNode.name || editingNode.code || '#' + editingNode.id }}</h3>
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
        </div>
        <div class="modal-actions">
          <button class="btn-del-lg" @click="deleteEdit">🗑️ Удалить</button>
          <button class="btn-save-lg" @click="saveEdit">💾 Сохранить</button>
        </div>
      </div>
    </div>
</template>

<script>
import api from '@/shared/api'

export default {
  name: 'BomConfigPage',
  components: { TreeNode, EquipmentTypeNode, CompositionGroupNode },
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
      draggedItem: null,
      editingNode: null,
    }
  },
  async mounted() {
    await Promise.all([this.loadTree(), this.loadEquipmentTypes(), this.loadMboms()])
  },
  methods: {
    async loadTree() {
      try {
        const { data } = await api.get('/ai-assistant/composition-tree/')
        this.compositionTree = Array.isArray(data) ? data : []
      } catch { this.compositionTree = [] }
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
          alert('Сначала создайте CompositionGroup (кнопка «+ Корневая группа»)')
          return
        }
        await this.addEquipmentTypeToGroup(targetGroupId, item.id)
      } else if (item.type === 'composition_group' && targetGroupId !== null && item.id !== targetGroupId) {
        await this.moveGroup(item.id, targetGroupId)
      }
    },
    async onDropItem({ item, groupId }) {
      this.draggedItem = item
      await this.onDrop(new Event('drop'), groupId)
    },

    // CompositionGroup CRUD
    async addRootGroup() {
      const code = prompt('Код группы (уникальный):')
      if (!code) return
      const name = prompt('Название группы:') || code
      try {
        const { data } = await api.post('/ai-assistant/composition-groups/', {
          code, name, parent: null, group_type: 'required',
        })
        await this.loadTree()
      } catch (e) { alert('Ошибка: ' + (e.displayMessage || e.message)) }
    },
    async addChildGroup(parentId) {
      const code = prompt('Код дочерней группы (уникальный):')
      if (!code) return
      const name = prompt('Название:') || code
      try {
        const { data } = await api.post('/ai-assistant/composition-groups/', {
          code, name, parent: parentId, group_type: 'required',
        })
        await this.loadTree()
      } catch (e) { alert('Ошибка: ' + (e.displayMessage || e.message)) }
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
      if (!confirm('Удалить группу и все вложенные?')) return
      try {
        await api.delete(`/ai-assistant/composition-groups/${groupId}/`)
        await this.loadTree()
      } catch (e) { alert('Ошибка: ' + (e.displayMessage || e.message)) }
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
      if (!confirm('Удалить спецификацию?')) return
      try {
        await api.delete(`/ai-assistant/mboms/${id}/`)
        await this.loadMboms()
      } catch (e) { alert('Ошибка: ' + (e.displayMessage || e.message)) }
    },

    // Popup editing
    openEditModal(node) {
      if (node.item_type === 'equipment_type') return // ET редактируются в Django admin
      this.editingNode = { ...node }
    },
    closeModal() {
      this.editingNode = null
    },
    async saveEdit() {
      if (!this.editingNode) return
      const n = this.editingNode
      try {
        await api.patch(`/ai-assistant/composition-groups/${n.id}/`, {
          name: n.name, code: n.code, description: n.description,
          group_type: n.group_type, sorting_order: n.sorting_order,
        })
        this.closeModal()
        await this.loadTree()
      } catch (e) { alert('Ошибка: ' + (e.displayMessage || e.message)) }
    },
    async deleteEdit() {
      if (!this.editingNode) return
      if (!confirm('Удалить группу и все вложенные?')) return
      await api.delete(`/ai-assistant/composition-groups/${this.editingNode.id}/`)
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
  },
}

// ── Recursive Tree Node (for Tree tab) ──
const TreeNode = {
  name: 'TreeNode',
  props: { node: Object, depth: Number },
  template: `
    <div class="tree-node" :style="{ paddingLeft: depth * 20 + 'px' }">
      <div class="tree-node-header" @dblclick="$emit('dblclick', node)">
        <span v-if="hasChildren" class="toggle" @click="expanded = !expanded">{{ expanded ? '▼' : '▶' }}</span>
        <span v-else class="toggle-spacer"></span>
        <span class="node-icon">{{ icon }}</span>
        <span class="node-name">{{ node.name }}</span>
        <span class="node-badge" :class="'badge-' + (node.item_type || 'cg')">{{ node.group_type || node.item_type || 'group' }}</span>
      </div>
      <div v-if="expanded && hasChildren" class="tree-node-children">
        <TreeNode v-for="child in node.children" :key="(child.item_type || 'cg') + '-' + child.id" :node="child" :depth="depth + 1" />
      </div>
    </div>
  `,
  data() { return { expanded: true } },
  computed: {
    hasChildren() { return this.node.children && this.node.children.length > 0 },
    icon() {
      if (this.node.item_type === 'equipment_type') return '📦'
      if (this.node.group_type === 'xor') return '🔀'
      if (this.node.group_type === 'optional') return '❓'
      return '📁'
    },
  },
}

// ── EquipmentType Node (for Constructor left panel) ──
const EquipmentTypeNode = {
  name: 'EquipmentTypeNode',
  props: { node: Object, depth: Number },
  emits: ['dragstart'],
  template: `
    <div class="tree-node et-node" draggable="true"
         :style="{ paddingLeft: depth * 16 + 'px' }"
         @dragstart="$emit('dragstart', $event)">
      <div class="tree-node-header" @dblclick="$emit('dblclick', node)">
        <span v-if="hasChildren" class="toggle" @click="expanded = !expanded">{{ expanded ? '▼' : '▶' }}</span>
        <span v-else class="toggle-spacer"></span>
        <span class="node-icon">📦</span>
        <span class="node-name">{{ node.name }}</span>
        <span class="node-code">{{ node.code }}</span>
      </div>
      <div v-if="expanded && hasChildren">
        <EquipmentTypeNode v-for="child in node.children" :key="'et-' + child.id" :node="child" :depth="depth + 1" @dragstart="(e) => $emit('dragstart', e)" />
      </div>
    </div>
  `,
  data() { return { expanded: false } },
  computed: {
    hasChildren() { return this.node.children && this.node.children.length > 0 },
  },
}

// ── CompositionGroup Node (for Constructor right panel) ──
const CompositionGroupNode = {
  name: 'CompositionGroupNode',
  props: { node: Object, depth: Number },
  emits: ['drop-item', 'add-child-group', 'remove-et', 'delete-group', 'dragstart', 'edit-node'],
  template: `
    <div class="tree-node cg-node"
         :style="{ paddingLeft: depth * 16 + 'px' }"
         :class="'cg-type-' + (node.group_type || 'required')"
         @dragover.prevent
         @drop.prevent="onDropLocal">
      <div class="tree-node-header cg-header"
           draggable="true"
           @dragstart="$emit('dragstart', $event, { type: 'composition_group', id: node.id, name: node.name })"
           @dblclick="$emit('edit-node', node)">
        <span v-if="hasChildren" class="toggle" @click="expanded = !expanded">{{ expanded ? '▼' : '▶' }}</span>
        <span v-else class="toggle-spacer"></span>
        <span class="node-icon">{{ groupIcon }}</span>
        <span class="node-name">{{ node.name }}</span>
        <span class="node-badge">{{ node.group_type || 'required' }}</span>
        <button class="btn-xs" @click.stop="$emit('add-child-group', node.id)" title="Добавить дочернюю группу">+Группа</button>
        <button class="btn-xs del" @click.stop="$emit('delete-group', node.id)" title="Удалить группу">✕</button>
      </div>
      <div v-if="expanded" class="tree-node-children">
        <!-- EquipmentTypes in this group -->
        <div v-for="et in node.children.filter(c => c.item_type === 'equipment_type')" :key="'et-' + et.id"
             class="et-item"
             @dblclick="$emit('edit-node', et)"
             :style="{ paddingLeft: (depth + 1) * 16 + 'px' }">
          <span class="node-icon">📦</span>
          <span class="node-name">{{ et.name }}</span>
          <button class="btn-xs del" @click="$emit('remove-et', node.id, et.id)">✕</button>
        </div>
        <!-- Child CompositionGroups -->
        <CompositionGroupNode
          v-for="child in node.children.filter(c => c.item_type === 'composition_group')"
          :key="'cg-' + child.id"
          :node="child"
          :depth="depth + 1"
          @drop-item="(payload) => $emit('drop-item', payload)"
          @add-child-group="(id) => $emit('add-child-group', id)"
          @remove-et="(gid, eid) => $emit('remove-et', gid, eid)"
          @delete-group="(id) => $emit('delete-group', id)"
          @edit-node="(node) => $emit('edit-node', node)"
          @dragstart="(e, item) => $emit('dragstart', e, item)"
        />
      </div>
    </div>
  `,
  data() { return { expanded: true } },
  computed: {
    hasChildren() {
      return this.node.children && this.node.children.length > 0
    },
    groupIcon() {
      if (this.node.group_type === 'xor') return '🔀'
      if (this.node.group_type === 'optional') return '❓'
      return '📁'
    },
  },
  methods: {
    onDropLocal(event) {
      const raw = event.dataTransfer.getData('text/plain')
      if (!raw) return
      let item
      try { item = JSON.parse(raw) } catch { return }
      this.$emit('drop-item', { item, groupId: this.node.id })
    },
  },
}
</script>

<style scoped>
.bom-config { padding: 20px; max-width: 1400px; margin: 0 auto; }
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

/* Tree nodes */
.tree-node { user-select: none; }
.tree-node-header { display: flex; align-items: center; gap: 4px; padding: 4px 8px; border-radius: 4px; cursor: default; }
.tree-node-header:hover { background: #f0f4ff; }
.toggle { cursor: pointer; width: 16px; text-align: center; font-size: 10px; color: #888; flex-shrink: 0; }
.toggle-spacer { width: 16px; flex-shrink: 0; }
.node-icon { font-size: 16px; flex-shrink: 0; }
.node-name { font-weight: 500; flex: 1; }
.node-code { color: #999; font-size: 12px; }
.node-badge { font-size: 10px; padding: 1px 6px; border-radius: 8px; background: #e8e8e8; color: #666; }
.badge-composition_group { background: #dbeafe; color: #1e40af; }
.badge-equipment_type { background: #dcfce7; color: #166534; }

/* ET item in constructor */
.et-item { display: flex; align-items: center; gap: 4px; padding: 2px 8px; margin: 2px 0; background: #f9fafb; border-radius: 4px; }
.et-item:hover { background: #f0f4ff; }

/* CG node styling */
.cg-node { border-left: 3px solid #3b82f6; margin: 4px 0; }
.cg-type-optional { border-left-color: #f59e0b; }
.cg-type-xor { border-left-color: #ef4444; }
.cg-header { background: #eff6ff; border-radius: 4px; }
.cg-type-optional .cg-header { background: #fffbeb; }
.cg-type-xor .cg-header { background: #fef2f2; }

/* ET node draggable */
.et-node { cursor: grab; }
.et-node:active { cursor: grabbing; }

/* Buttons */
.btn-add { padding: 4px 12px; background: #3b82f6; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-add:hover { background: #2563eb; }
.btn-xs { padding: 1px 6px; font-size: 11px; border: 1px solid #ccc; background: #fff; border-radius: 3px; cursor: pointer; }
.btn-xs:hover { background: #f0f0f0; }
.btn-xs.del { color: #ef4444; border-color: #fca5a5; }
.btn-xs.del:hover { background: #fef2f2; }
.btn-save-sm { padding: 2px 8px; font-size: 14px; border: none; background: none; cursor: pointer; }
.btn-del { padding: 2px 8px; font-size: 14px; border: none; background: none; cursor: pointer; color: #ef4444; }
.cell-input { width: 100%; border: 1px solid #ddd; padding: 4px 6px; border-radius: 3px; font-size: 13px; }

/* Table */
table { width: 100%; border-collapse: collapse; margin-top: 12px; }
th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; font-size: 13px; }
th { background: #f9fafb; font-weight: 600; }

.empty { color: #999; padding: 24px; text-align: center; font-style: italic; }

/* Tree container (for Tree tab) */
.tree-container { padding: 8px 0; }
.tree-section .tree-node { margin: 2px 0; }

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
</style>
