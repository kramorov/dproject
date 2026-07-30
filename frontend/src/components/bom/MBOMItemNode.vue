<template>
  <div class="mbom-item-node" :style="{ paddingLeft: depth * 20 + 'px' }">
    <div class="mbom-item-header">
      <span v-if="hasChildren" class="toggle" @click="expanded = !expanded">{{ expanded ? '▼' : '▶' }}</span>
      <span v-else class="toggle-spacer"></span>
      <span class="item-icon">{{ compositionIcon }}</span>
      <span class="item-type">{{ node.equipment_type_name || '—' }}</span>
      <span class="item-sku" v-if="node.sku_code">{{ node.sku_code }}</span>
      <span class="item-sku empty" v-else>нет SKU</span>
      <span class="item-qty">×{{ node.quantity }} {{ node.quantity_unit || 'шт' }}</span>
      <span class="item-group" v-if="node.composition_group">{{ node.composition_group }}</span>
      <span class="item-notes" v-if="node.notes">{{ node.notes }}</span>
    </div>
    <div v-if="expanded && hasChildren" class="mbom-item-children" :class="{ 'is-root': depth === 0 }">
      <MBOMItemNode
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :depth="depth + 1"
      />
    </div>
  </div>
</template>

<script>
export default {
  name: 'MBOMItemNode',
  props: { node: Object, depth: Number },
  data() { return { expanded: true } },
  computed: {
    hasChildren() {
      return this.node.children && this.node.children.length > 0
    },
    compositionIcon() {
      return this.node.composition_group ? '📁' : '📦'
    },
  },
}
</script>

<style scoped>
.mbom-item-node { user-select: none; margin: 2px 0; }
.mbom-item-header { display: flex; align-items: center; gap: 6px; padding: 3px 8px; border-radius: 4px; cursor: default; }
.mbom-item-header:hover { background: #f0f4ff; }
.toggle { cursor: pointer; width: 16px; text-align: center; font-size: 10px; color: #888; flex-shrink: 0; }
.toggle-spacer { width: 16px; flex-shrink: 0; }
.item-icon { font-size: 16px; flex-shrink: 0; }
.item-type { font-weight: 500; color: #1e40af; }
.item-sku { font-size: 13px; color: #333; font-family: monospace; background: #f3f4f6; padding: 1px 6px; border-radius: 3px; }
.item-sku.empty { color: #999; font-style: italic; background: none; }
.item-qty { font-size: 12px; color: #666; }
.item-group { font-size: 10px; padding: 1px 6px; border-radius: 8px; background: #e8e8e8; color: #666; }
.item-notes { font-size: 11px; color: #999; }

/* Nested children indent */
.mbom-item-children {
  margin-left: 4px;
  padding-left: 12px;
  border-left: 2px solid #e5e7eb;
}
.mbom-item-children.is-root {
  border-left-color: #3b82f6;
}
</style>
