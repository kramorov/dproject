<template>
  <div class="tree-node cg-node"
       :style="{ paddingLeft: depth * 24 + 'px' }"
       :class="['cg-type-' + (node.group_type || 'required'), { 'is-reference': isReference, 'drag-over': dragOver }]"
       @dragover.prevent="onDragOver"
       @dragleave="onDragLeave"
       @drop.prevent="onDropLocal">
    <div class="tree-node-header cg-header"
         :draggable="!isReference"
         @dragstart="$emit('dragstart', $event, { type: 'composition_group', id: node.id, name: node.name })"
         @dblclick="$emit(node.item_type === 'reference' ? 'edit-reference' : 'edit-node', node)">
      <span v-if="hasChildren" class="toggle" @click="expanded = !expanded">{{ expanded ? '▼' : '▶' }}</span>
      <span v-else class="toggle-spacer"></span>
      <span class="node-icon">{{ isReference ? '🔗' : groupIcon }}</span>
      <span class="node-name">{{ node.name }}</span>
      <span class="node-badge">{{ node.item_type === 'reference' ? 'ссылка' : isReference ? 'вложение' : (node.group_type || 'required') }}</span>
      <button v-if="!isReference" class="btn-xs" @click.stop="$emit('add-child-group', node.id)" title="Добавить дочернюю группу">+Группа</button>
      <button v-if="node.item_type === 'reference'" class="btn-xs del" @click.stop="$emit('remove-reference', node.id)" title="Убрать ссылку">✕</button>
      <button v-else-if="isReference" class="btn-xs del" @click.stop="$emit('delete-group', node.id)" title="Удалить вложение">✕</button>
      <button v-else class="btn-xs del" @click.stop="$emit('delete-group', node.id)" title="Удалить группу">✕</button>
    </div>
    <div v-if="expanded" class="tree-node-children">
      <div v-for="et in node.children.filter(c => c.item_type === 'equipment_type')" :key="'et-' + et.id"
           class="et-item"
           @dblclick="$emit('edit-node', et)"
           :style="{ paddingLeft: (depth + 1) * 24 + 'px' }">
        <span class="node-icon">📦</span>
        <span class="node-name">{{ et.name }}</span>
        <button v-if="!isReference" class="btn-xs del" @click="$emit('remove-et', node.id, et.id)">✕</button>
      </div>
      <CompositionGroupNode
        v-for="child in node.children.filter(c => c.item_type === 'composition_group' || c.item_type === 'reference')"
        :key="(child.item_type || 'cg') + '-' + child.id"
        :node="child"
        :depth="depth + 1"
        @drop-item="(payload) => $emit('drop-item', payload)"
        @add-child-group="(id) => $emit('add-child-group', id)"
        @remove-et="(gid, eid) => $emit('remove-et', gid, eid)"
        @delete-group="(id) => $emit('delete-group', id)"
        @edit-node="(node) => $emit('edit-node', node)"
        @edit-reference="(refNode) => $emit('edit-reference', refNode, node.id)"
        @dragstart="(e, item) => $emit('dragstart', e, item)"
        @remove-reference="(...args) => $emit('remove-reference', node.id, args[args.length - 1])"
      />
    </div>
  </div>
</template>

<script>
export default {
  name: 'CompositionGroupNode',
  props: { node: Object, depth: Number, isReference: { type: Boolean, default: false } },
  emits: ['drop-item', 'add-child-group', 'remove-et', 'delete-group', 'dragstart', 'edit-node', 'edit-reference', 'remove-reference'],
  data() { return { expanded: true, dragOver: false } },
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
    onDragOver(event) {
      if (this.isReference) return
      this.dragOver = true
    },
    onDragLeave(event) {
      this.dragOver = false
    },
    onDropLocal(event) {
      this.dragOver = false
      if (this.isReference) return
      event.stopPropagation()
      const raw = event.dataTransfer.getData('text/plain')
      if (!raw) return
      let item
      try { item = JSON.parse(raw) } catch { return }
      this.$emit('drop-item', { item, groupId: this.node.id })
    },
  },
}
</script>

<style>
@import './shared.css';
</style>
<style scoped>
.cg-node { border-left: 3px solid #3b82f6; margin: 4px 0; }
.cg-node.is-reference { border-left-color: #9ca3af; opacity: 0.85; }
.cg-type-optional { border-left-color: #f59e0b; }
.cg-type-xor { border-left-color: #ef4444; }
.cg-header { background: #eff6ff; border-radius: 4px; }
.cg-node.is-reference .cg-header { background: #f3f4f6; }
.cg-type-optional .cg-header { background: #fffbeb; }
.cg-type-xor .cg-header { background: #fef2f2; }
.et-item { display: flex; align-items: center; gap: 4px; padding: 2px 8px; margin: 2px 0; background: #f9fafb; border-radius: 4px; }
.et-item:hover { background: #f0f4ff; }
.btn-xs { padding: 1px 6px; font-size: 11px; border: 1px solid #ccc; background: #fff; border-radius: 3px; cursor: pointer; }
.btn-xs:hover { background: #f0f0f0; }
.btn-xs.del { color: #ef4444; border-color: #fca5a5; }
.btn-xs.del:hover { background: #fef2f2; }
.cg-node.drag-over { outline: 3px dashed #3b82f6; outline-offset: 2px; background: #dbeafe; border-radius: 6px; }
.cg-node.drag-over .cg-header { background: #bfdbfe; }
</style>
