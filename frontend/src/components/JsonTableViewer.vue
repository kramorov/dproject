<template>
  <table class="json-table">
    <thead><tr><th>Key</th><th>Type</th><th>Value</th></tr></thead>
    <tbody>
      <template v-for="(val, key) in data" :key="key">
        <tr>
          <td class="key-cell">{{ prefix }}{{ key }}</td>
          <td class="type-cell">{{ typeOf(val) }}</td>
          <td class="value-cell">
            <template v-if="isPrimitive(val)">{{ val }}</template>
            <template v-else-if="Array.isArray(val)">[{{ val.length }}]</template>
            <template v-else>{{ '{' + Object.keys(val).length + '}' }}</template>
          </td>
        </tr>
        <template v-if="isObject(val)">
          <JsonTableViewer :data="val" :prefix="prefix + key + '.'" />
        </template>
      </template>
    </tbody>
  </table>
</template>

<script setup>
defineProps({ data: { type: Object, default: () => ({}) }, prefix: { type: String, default: '' } })

function typeOf(v) {
  if (v === null) return 'null'
  if (Array.isArray(v)) return `array[${v.length}]`
  return typeof v
}
function isPrimitive(v) { return v === null || typeof v !== 'object' }
function isObject(v) { return v !== null && typeof v === 'object' && !Array.isArray(v) }
</script>

<style scoped>
.json-table { width: 100%; border-collapse: collapse; font-size: 13px; font-family: 'Courier New', monospace; }
.json-table th { text-align: left; padding: 4px 8px; background: #f0f0f0; border-bottom: 2px solid #ddd; color: #666; font-size: 12px; }
.json-table td { padding: 3px 8px; border-bottom: 1px solid #eee; vertical-align: top; }
.key-cell { color: #881391; min-width: 200px; }
.type-cell { color: #999; font-style: italic; width: 100px; }
.value-cell { color: #1a1aa6; word-break: break-all; }
</style>
