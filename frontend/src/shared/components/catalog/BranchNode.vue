<template>
  <div class="bn-node">
    <Handle type="target" :position="Position.Top" />
    <div class="bn-body">
      <div class="bn-name">{{ data.name || 'Ветвление' }}</div>
      <div class="bn-label">{{ data.param_name }}</div>
      <div class="bn-conds" v-if="data.conditions">
        <span v-for="(target, val) in data.conditions" :key="val" class="bn-cond">{{ val }}</span>
      </div>
    </div>
    <Handle type="source" :position="Position.Bottom" />
  </div>
</template>

<script setup>
import { Handle, Position } from '@vue-flow/core'
defineProps({ id: String, data: Object })
</script>

<style scoped>
.bn-node {
  background: #faf5ff; border: 2px solid #c084fc; border-radius: 8px;
  min-width: 120px; max-width: 220px;
  transform: rotate(0deg);
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.bn-body { padding: 8px 12px; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.bn-name { font-size: 12px; font-weight: 600; color: #5b21b6; text-align: center; }
.bn-label { font-size: 10px; color: #7c3aed; font-family: monospace; text-align: center; }
.bn-conds { display: flex; flex-wrap: wrap; gap: 3px; justify-content: center; }
.bn-cond { font-size: 10px; background: #ede9fe; color: #5b21b6; padding: 1px 5px; border-radius: 3px; font-family: monospace; }
</style>
