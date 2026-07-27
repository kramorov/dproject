<template>
  <div>
    <div class="tree-node" :class="'level-' + level">
      <span class="node-icon">{{ icon }}</span>
      <span class="node-label">{{ nodeLabel }}</span>
      <span class="node-status">{{ statusText }}</span>
      <span class="node-qty" v-if="node.quantity !== 1">×{{ node.quantity }} {{ node.quantity_unit }}</span>
      <span class="node-actions">
        <button v-if="canExtract" @click="$emit('extract', node.id)" :disabled="extracting">
          {{ extracting ? '...' : '📝 Извлечь' }}
        </button>
        <button v-if="canFilter" @click="$emit('filter', node.id)" :disabled="filtering">
          {{ filtering ? '...' : '🔍 Подобрать' }}
        </button>
        <button v-if="canCompare" @click="$emit('compare', node.id)">
          📊 Сравнить
        </button>
      </span>
    </div>

        <!-- Extracted params -->
    <div v-if="extractData && !extractData.error" class="extract-params">
      <div v-for="(val, key) in extractData" :key="key" class="param-row">
        <span class="param-key">{{ key }}</span>
        <span class="param-val">{{ Array.isArray(val) ? val.join(', ') : val }}</span>
      </div>
    </div>
    <div v-if="extractData && extractData.error" class="extract-params error">⚠️ Extract failed</div>

    <!-- Options display -->
    <div v-if="showOptions && options.length" class="options-panel">
      <div v-for="opt in options.slice(0, 10)" :key="opt.id || opt.model" class="option-item">
        <span>{{ opt.model || opt.name || opt.label || '#' + (opt.id || '?') }}</span>
        <span v-if="opt.price">💰 {{ opt.price }}</span>
        <button @click="$emit('select', node.id, opt.product_type || opt.type, opt.id)">Выбрать</button>
      </div>
      <div v-if="options.length > 10" class="option-more">... и ещё {{ options.length - 10 }} вариантов</div>
    </div>

    <!-- Children -->
    <div v-if="node.children && node.children.length" class="tree-children">
      <TreeNodeDisplay
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :level="level + 1"
        :options="(selectedChildId === child.id) ? childOptions : []"
        :show-options="selectedChildId === child.id"
        @extract="$emit('extract', $event)"
        @filter="onChildFilter($event)"
        @select="$emit('select', $event)"
        @compare="$emit('compare', $event)"
      />
    </div>
  </div>
</template>

<script>
export default {
  name: 'TreeNodeDisplay',
  props: {
    node: { type: Object, required: true },
    equipNameMap: { type: Object, default: () => ({}) },
    extractedParams: { type: Object, default: () => ({}) },
    level: { type: Number, default: 2 },
    options: { type: Array, default: () => [] },
    showOptions: { type: Boolean, default: false },
  },
  emits: ['extract', 'filter', 'select', 'compare'],
  data() {
    return {
      extracting: false,
      filtering: false,
      childOptions: [],
      selectedChildId: null,
    }
  },
  computed: {
    extractData() { const r = this.extractedParams[this.node.id]; console.log('extractData node.id:', this.node.id, 'found:', !!r); return r && r.extract_output ? r.extract_output : (r || null) },
    icon() {
      const icons = {
        actuator: '🔧', solenoid: '⚡', bkv: '📟',
        cable_gland: '🔌', pneumatic_fitting: '🔩',
        filter_regulator: '💨', manual_override: '🖐',
        mounting_kit: '🔗',
      }
      return icons[this.node.equipment_type] || '📦'
    },
    nodeLabel() {
      const t = this.node.type || this.node.equipment_type
      const name = t ? (this.equipNameMap[t] || t) : t
      return this.node.label || name || 'Компонент'
    },
    statusText() {
      const labels = {
        pending: '⏳', decomposed: '📋', extracted: '✅',
        filtered: '📋', selected: '⭐', compared: '📊',
        needs_info: '⚠️', error: '❌',
      }
      return labels[this.node.status] || this.node.status || ''
    },
    canExtract() {
      return this.node.status === 'decomposed' && this.node.equipment_type
    },
    canFilter() {
      return ['extracted', 'pending'].includes(this.node.status)
    },
    canCompare() {
      return this.node.status === 'selected' || this.node.selected_product_id
    },
  },
  methods: {
    async onChildFilter(nodeId) {
      this.selectedChildId = nodeId
      this.$emit('filter', nodeId)
    },
  },
}
</script>

<style scoped>
.tree-node { display: flex; align-items: center; gap: 8px; padding: 4px 8px; border-radius: 4px; margin: 2px 0; }
.tree-node.level-1 { background: #dbeafe; font-size: 14px; font-weight: 600; }
.tree-node.level-2 { background: #f1f5f9; font-size: 13px; }
.tree-node.level-3 { background: #fff; font-size: 12px; border: 1px solid #e2e8f0; }
.tree-node.level-4 { background: #fff; font-size: 11px; border: 1px dashed #e2e8f0; margin-left: 16px; }
.tree-node.level-5 { background: #fafafa; font-size: 11px; margin-left: 32px; }
.node-icon { font-size: 14px; }
.node-label { flex: 1; }
.node-status { font-size: 11px; color: #64748b; }
.node-qty { font-size: 11px; color: #64748b; }
.node-actions { display: flex; gap: 3px; margin-left: auto; }
.node-actions button { padding: 2px 6px; font-size: 10px; border: 1px solid #cbd5e1; border-radius: 3px; background: #fff; cursor: pointer; white-space: nowrap; }
.node-actions button:hover { background: #f1f5f9; }
.node-actions button:disabled { opacity: 0.5; cursor: default; }
.tree-children { margin-left: 20px; }
.options-panel { margin-top: 4px; margin-left: 20px; padding: 8px; background: #fffbeb; border: 1px solid #fde68a; border-radius: 4px; }
.option-item { display: flex; align-items: center; justify-content: space-between; padding: 3px 0; font-size: 12px; border-bottom: 1px solid #fef3c7; }
.option-item button { padding: 2px 8px; font-size: 11px; background: #2563eb; color: #fff; border: none; border-radius: 3px; cursor: pointer; }
.option-more { font-size: 11px; color: #94a3b8; padding-top: 4px; }
.extract-params { margin-left: 24px; padding: 4px 8px; font-size: 12px; color: #555; }
.param-row { display: flex; gap: 8px; padding: 1px 0; }
.param-key { color: #881391; font-weight: 600; min-width: 140px; }
.param-val { color: #1a1aa6; }
.extract-params.error { color: #e53935; }
</style>
