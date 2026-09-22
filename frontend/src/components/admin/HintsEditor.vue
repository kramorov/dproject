<!-- components/admin/HintsEditor.vue — конструктор ai_hints (список строк) -->
<template>
  <div class="he-wrap">
    <div class="raw-toolbar">
      <button type="button" class="raw-btn" @click="toggle">{{ rawMode ? '✓ Применить' : 'JSON' }}</button>
      <button v-if="rawMode" type="button" class="raw-btn" @click="formatRaw">Форматировать</button>
    </div>

    <template v-if="rawMode">
      <textarea v-model="rawText" rows="6" class="raw-text" :class="{ invalid: rawError }"
                @input="onRawInput" spellcheck="false"></textarea>
      <div v-if="rawError" class="raw-error">{{ rawError }}</div>
    </template>

    <template v-else>
      <div v-for="(item, i) in items" :key="i" class="he-row">
        <input v-model="items[i]" class="he-inp" placeholder="Подсказка" />
        <button class="he-del" @click="remove(i)" title="Удалить">×</button>
      </div>
      <button class="he-add" @click="add">+ Подсказка</button>
    </template>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useJsonTextMode } from './useJsonTextMode'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

function toArray() {
  return items.value.map(s => (s || '').trim()).filter(Boolean)
}

const items = ref(Array.isArray(props.modelValue) ? [...props.modelValue] : [])
if (!items.value.length) items.value.push('')

watch(items, () => emit('update:modelValue', toArray()), { deep: true })

const { rawMode, rawText, rawError, toggle, onRawInput, formatRaw } = useJsonTextMode({
  getValue: () => toArray(),
  applyValue: (v) => { items.value = v.length ? [...v] : [''] },
  isArray: true,
})

function add() { items.value.push('') }
function remove(i) { items.value.splice(i, 1) }
</script>

<style scoped>
.he-wrap { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.he-row { display: flex; gap: 6px; align-items: center; }
.he-inp { flex: 1; padding: 5px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px; }
.he-inp:focus { outline: none; border-color: #2563eb; }
.he-del { background: none; border: none; color: #dc2626; cursor: pointer; font-size: 15px; line-height: 1; padding: 2px 6px; }
.he-del:hover { color: #991b1b; }
.he-add { padding: 5px 12px; border: 1px dashed #2563eb; border-radius: 5px; background: #fff; color: #2563eb; cursor: pointer; font-size: 12px; align-self: flex-start; }
.he-add:hover { background: #eff6ff; }

.raw-toolbar { display: flex; gap: 6px; }
.raw-btn { padding: 3px 10px; border: 1px solid #d1d5db; border-radius: 4px; background: #fff; cursor: pointer; font-size: 12px; color: #374151; }
.raw-btn:hover { background: #f3f4f6; }
.raw-text { width: 100%; padding: 6px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 11px; font-family: monospace; resize: vertical; box-sizing: border-box; }
.raw-text.invalid { border-color: #dc2626; background: #fff8f8; }
.raw-error { color: #dc2626; font-size: 11px; }
</style>
