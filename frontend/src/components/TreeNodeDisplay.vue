<template>
  <div>
    <div class="tree-node" :class="'level-' + level" :style="{ marginLeft: (level - 1) * 20 + 'px' }">
      <span class="node-icon">{{ icon }}</span>
      <span class="node-label" :title="nodeLabel">{{ nodeLabel }}</span>
      <span class="node-status">{{ statusText }}</span>
      <span class="node-qty" v-if="node.quantity !== 1 && node.quantity">×{{ node.quantity }} {{ node.quantity_unit || '' }}</span>
      <span class="node-actions">
        <button v-if="canExtract" class="btn-ai btn-extract" @click="$emit('extract', node.id)" :disabled="extracting">
          {{ extracting ? '...' : '📝' }}
        </button>
        <button v-if="canFilter" class="btn-ai btn-filter" @click="$emit('filter', node.id)" :disabled="filtering">
          {{ filtering ? '...' : '🔍' }}
        </button>
        <button v-if="canCompare" class="btn-ai btn-compare" @click="$emit('compare', node.id)">
          📊
        </button>
      </span>
    </div>

        <!-- Extracted params -->
    <div v-if="showExtractParams" class="extract-params">
      <div v-for="(val, key) in extractData" :key="key" class="param-row">
        <span class="param-key">{{ fieldLabel(key) }}</span>
        <span class="param-val">{{ formatValue(key, val) }}</span>
      </div>
    </div>
    <div v-if="extractData && extractData.error" class="extract-params error">⚠️ Ошибка извлечения</div>

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
    _rawData() { const r = this.extractedParams[this.node.id]; return r && r.extract_output ? r.extract_output : (r || null) },
    _fieldLabels() { const d = this._rawData; return (d && d._field_labels) || {} },
    _valueLabels() { const d = this._rawData; const l = (d && d._labels) || {}; const c = { ...l }; delete c._field_labels; return c },
    extractData() {
      const d = this._rawData
      if (!d) return null
      const clean = { ...d }
      delete clean._field_labels
      delete clean._labels
      return clean
    },
    showExtractParams() {
      return this.extractData && !this.extractData.error && Object.keys(this.extractData).length > 0
    },
    fieldLabelMap() {
      return this._fieldLabels
    },
    valueLabelMap() {
      return this._valueLabels
    },
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
    fieldLabel(key) {
      return this.fieldLabelMap[key] || key.replace(/_id$/, '').replace(/_/g, ' ')
    },
    formatValue(key, val) {
      const label = this.valueLabelMap[key]
      if (label) return label
      if (Array.isArray(val)) return val.join(', ')
      // Strip leading numeric ID from values like "1 DA" → "DA"
      if (typeof val === 'string' && /^\d+\s+\S/.test(val)) return val.replace(/^\d+\s+/, '')
      return val
    },
    async onChildFilter(nodeId) {
      this.selectedChildId = nodeId
      this.$emit('filter', nodeId)
    },
  },
}
</script>

<style scoped>
.tree-node {
  display: flex; align-items: center; gap: 6px;
  padding: 5px 10px; margin: 1px 0; border-radius: 6px; border-left: 3px solid transparent; transition: background 0.2s;
}
.tree-node.level-1 { background: #dbeafe; font-size: 14px; font-weight: 600; border-left-color: #3b82f6; }
.tree-node.level-2 { background: #f1f5f9; font-size: 13px; border-left-color: #94a3b8; }
.tree-node.level-3 { background: #fff; font-size: 12px; border: 1px solid #e2e8f0; border-left-color: #cbd5e1; }
.tree-node.level-4,.tree-node.level-5 { background: #fff; font-size: 11px; border: 1px dashed #e2e8f0; border-left-color: #e2e8f0; }
.node-icon { font-size: 15px; flex-shrink: 0; }
.node-label { flex: 1; }
.node-status { font-size: 10px; color: #64748b; white-space: nowrap; }
.node-qty { font-size: 11px; color: #64748b; }
.node-actions { display: flex; gap: 2px; flex-shrink: 0; }
.btn-ai {
  padding: 2px 6px; font-size: 12px; border: 1px solid #cbd5e1; border-radius: 4px; background: #fff; cursor: pointer; transition: all 0.15s;
}
.btn-ai:hover { transform: scale(1.1); }
.btn-extract:hover { border-color: #8b5cf6; background: #f5f3ff; }
.btn-filter:hover { border-color: #3b82f6; background: #eff6ff; }
.btn-compare:hover { border-color: #10b981; background: #ecfdf5; }
.node-actions button:disabled { opacity: 0.5; cursor: default; }
.tree-children { margin-left: 0; border-left: 1px dotted #cbd5e1; padding-left: 8px; }
.options-panel { margin-top: 4px; margin-left: 20px; padding: 8px; background: #fffbeb; border: 1px solid #fde68a; border-radius: 4px; }
.option-item { display: flex; align-items: center; justify-content: space-between; padding: 3px 0; font-size: 12px; border-bottom: 1px solid #fef3c7; }
.option-item button { padding: 2px 8px; font-size: 11px; background: #2563eb; color: #fff; border: none; border-radius: 3px; cursor: pointer; }
.option-more { font-size: 11px; color: #94a3b8; padding-top: 4px; }
.extract-params {
  margin: 4px 0 4px 28px; padding: 8px 12px;
  background: #faf5ff; border: 1px solid #e9d5ff; border-radius: 6px;
  font-size: 12px;
}
.param-row { display: flex; gap: 6px; padding: 3px 0; border-bottom: 1px solid #f3e8ff; }
.param-row:last-child { border-bottom: none; }
.param-key {
  color: #6b21a8; font-weight: 600; min-width: 160px; text-transform: capitalize;
}
.param-val {
  color: #1e40af; font-weight: 500;
}
.extract-params.error { color: #e53935; background: #fef2f2; border-color: #fca5a5; }
</style>
