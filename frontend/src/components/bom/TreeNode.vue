<template>
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
</template>

<script>
export default {
  name: 'TreeNode',
  props: { node: Object, depth: Number },
  emits: ['dblclick'],
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
</script>

<style>
@import './shared.css';
</style>
