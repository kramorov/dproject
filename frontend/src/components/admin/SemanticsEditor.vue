<!-- components/admin/SemanticsEditor.vue — конструктор param_semantics -->
<template>
  <div class="se-wrap">
    <div class="raw-toolbar">
      <button type="button" class="raw-btn" @click="toggle">{{ rawMode ? '✓ Применить' : 'JSON' }}</button>
      <button v-if="rawMode" type="button" class="raw-btn" @click="formatRaw">Форматировать</button>
    </div>

    <template v-if="rawMode">
      <textarea v-model="rawText" rows="8" class="raw-text" :class="{ invalid: rawError }"
                @input="onRawInput" spellcheck="false"></textarea>
      <div v-if="rawError" class="raw-error">{{ rawError }}</div>
    </template>

    <template v-else>
      <div v-for="(r, i) in rows" :key="i" class="se-row">
        <input v-model="r.param" class="se-inp se-param" placeholder="Параметр (ключ поля)" />
        <select v-model="r.direction" class="se-inp se-dir">
          <option value="min">min (не менее)</option>
          <option value="max">max (не более)</option>
          <option value="exact">exact (точно)</option>
        </select>
        <input v-model="r.label" class="se-inp se-label" placeholder="Подпись" />
        <button class="se-del" @click="remove(i)" title="Удалить">×</button>
      </div>
      <button class="se-add" @click="add">+ Параметр</button>
    </template>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useJsonTextMode } from './useJsonTextMode'

const props = defineProps({
  modelValue: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:modelValue'])

function toRows(obj) {
  const res = Object.entries(obj || {}).map(([param, data]) => ({
    param,
    direction: (data && data.direction) || 'min',
    label: (data && data.label) || '',
  }))
  if (!res.length) res.push({ param: '', direction: 'min', label: '' })
  return res
}

function toObject() {
  const obj = {}
  for (const r of rows.value) {
    const param = (r.param || '').trim()
    if (!param) continue
    obj[param] = { direction: r.direction || 'min', label: (r.label || '').trim() }
  }
  return obj
}

const rows = ref(toRows(props.modelValue))

watch(rows, () => emit('update:modelValue', toObject()), { deep: true })

const { rawMode, rawText, rawError, toggle, onRawInput, formatRaw } = useJsonTextMode({
  getValue: () => toObject(),
  applyValue: (v) => { rows.value = toRows(v) },
  isArray: false,
})

function add() { rows.value.push({ param: '', direction: 'min', label: '' }) }
function remove(i) { rows.value.splice(i, 1) }
</script>

<style scoped>
.se-wrap { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.se-row { display: flex; gap: 6px; align-items: center; }
.se-inp { padding: 5px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px; box-sizing: border-box; }
.se-inp:focus { outline: none; border-color: #2563eb; }
.se-param { width: 30%; font-family: monospace; }
.se-dir { width: 150px; }
.se-label { flex: 1; }
.se-del { background: none; border: none; color: #dc2626; cursor: pointer; font-size: 15px; line-height: 1; padding: 2px 6px; }
.se-del:hover { color: #991b1b; }
.se-add { padding: 5px 12px; border: 1px dashed #2563eb; border-radius: 5px; background: #fff; color: #2563eb; cursor: pointer; font-size: 12px; align-self: flex-start; }
.se-add:hover { background: #eff6ff; }

.raw-toolbar { display: flex; gap: 6px; }
.raw-btn { padding: 3px 10px; border: 1px solid #d1d5db; border-radius: 4px; background: #fff; cursor: pointer; font-size: 12px; color: #374151; }
.raw-btn:hover { background: #f3f4f6; }
.raw-text { width: 100%; padding: 6px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 11px; font-family: monospace; resize: vertical; box-sizing: border-box; }
.raw-text.invalid { border-color: #dc2626; background: #fff8f8; }
.raw-error { color: #dc2626; font-size: 11px; }
</style>
