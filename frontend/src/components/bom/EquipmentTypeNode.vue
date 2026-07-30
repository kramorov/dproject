<template>
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
</template>

<script>
export default {
  name: 'EquipmentTypeNode',
  props: { node: Object, depth: Number },
  emits: ['dragstart', 'dblclick'],
  data() { return { expanded: false } },
  computed: {
    hasChildren() { return this.node.children && this.node.children.length > 0 },
  },
}
</script>

<style>
@import './shared.css';
</style>
<style scoped>
.et-node { cursor: grab; }
.et-node:active { cursor: grabbing; }
.node-code { color: #999; font-size: 12px; }
</style>
