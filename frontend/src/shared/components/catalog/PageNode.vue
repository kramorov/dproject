<template>
  <div class="pn-node" :class="{ 'pn-entry': data.isEntry }">
    <Handle type="target" :position="Position.Top" />
    <div class="pn-header">
      <span class="pn-name">{{ data.name || id }}</span>
    </div>
    <div v-if="data.isEntry" class="pn-entry-badge">▸ ВХОД</div>
    <div class="pn-body">
      <div v-if="data.description" class="pn-desc">{{ data.description }}</div>
      <div v-for="p in data.params" :key="p.order || p.param_name" class="pn-param">
        <span class="pn-order">{{ p.order }}</span>
        <span class="pn-title">{{ p.title || p.param_name }}</span>
        <span class="pn-param-name">{{ p.param_name }}</span>
      </div>
      <div v-if="!data.params || data.params.length === 0" class="pn-empty">Нет вопросов</div>
    </div>
    <Handle type="source" :position="Position.Bottom" />
  </div>
</template>

<script setup>
import { Handle, Position } from '@vue-flow/core'
defineProps({ id: String, data: Object })
</script>

<style scoped>
.pn-node { background: #fff; border: 2px solid #93c5fd; border-radius: 10px; min-width: 200px; max-width: 300px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.pn-node.pn-entry { border-color: #2563eb; }
.pn-header { display: flex; align-items: center; gap: 6px; padding: 7px 10px; background: #eff6ff; border-bottom: 1px solid #dbeafe; border-radius: 8px 8px 0 0; }
.pn-name { font-size: 13px; font-weight: 600; color: #1e40af; flex: 1; }
.pn-entry-badge { background: #dbeafe; color: #1d4ed8; padding: 2px 10px; font-size: 10px; font-weight: 600; text-align: center; border-top: 1px solid #bfdbfe; }
.pn-body { padding: 6px 8px; display: flex; flex-direction: column; gap: 3px; }
.pn-param { display: flex; align-items: center; gap: 6px; padding: 3px 6px; background: #f8fafc; border-radius: 4px; }
.pn-order { font-size: 10px; color: #94a3b8; font-weight: 600; min-width: 16px; }
.pn-title { font-size: 12px; color: #334155; flex: 1; }
.pn-desc { font-size: 11px; color: #64748b; padding: 2px 4px 4px; line-height: 1.3; }
.pn-param-name { font-size: 10px; color: #0369a1; font-family: monospace; background: #f0f9ff; padding: 1px 4px; border-radius: 3px; }
.pn-empty { font-size: 11px; color: #94a3b8; padding: 4px; }
</style>
