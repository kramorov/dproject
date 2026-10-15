<!-- components/admin/ListParamsEditor.vue — конструктор list_params
     (параметры быстрого просмотра). Формат: объект «Подпись» → «ключ поля»,
     локализуется через list_params_i18n (RU — основное поле). Режим полей и JSON. -->
<template>
  <div class="lpe-wrap">
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
      <datalist :id="datalistId">
        <option v-for="f in fields" :key="f.key" :value="f.key">{{ optionLabel(f) }}</option>
      </datalist>

      <div v-for="(r, i) in rows" :key="i" class="lpe-row">
        <span class="lpe-index">{{ i + 1 }}</span>
        <input v-model="r.label" class="lpe-label" placeholder="Подпись параметра" />
        <input v-model="r.key" class="lpe-key" placeholder="Ключ поля" :list="datalistId" />
        <button type="button" class="lpe-del" @click="removeRow(i)" title="Удалить параметр">×</button>
      </div>
      <button type="button" class="lpe-add" @click="addRow">+ Параметр</button>
      <div class="lpe-hint">Подписи локализуются: RU — основное поле, EN/CN — list_params_i18n.</div>
    </template>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useJsonTextMode } from './useJsonTextMode'

const props = defineProps({
  modelValue: { type: Object, default: () => ({}) },
  fields: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

const datalistId = 'list-params-field-keys'

function toRows(obj) {
  const res = Object.entries(obj || {}).map(([label, key]) => ({ label, key }))
  if (!res.length) res.push({ label: '', key: '' })
  return res
}

function toObject() {
  const obj = {}
  for (const r of rows.value) {
    const key = (r.key || '').trim()
    if (!key) continue
    obj[(r.label || '').trim() || key] = key
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

function optionLabel(f) {
  const parts = [f.key]
  if (f.label) parts.push(f.label)
  if (f.placeholder) parts.push(f.placeholder)
  if (f.unit) parts.push(`[${f.unit}]`)
  return parts.join(' · ')
}

function addRow() { rows.value.push({ label: '', key: '' }) }
function removeRow(i) { rows.value.splice(i, 1) }
</script>

<style scoped>
.lpe-wrap { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.lpe-row { display: flex; gap: 6px; align-items: center; margin: 4px 0; }
.lpe-index { color: #999; font-size: 12px; width: 18px; text-align: right; flex-shrink: 0; }
.lpe-label { width: 38%; padding: 5px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px; box-sizing: border-box; }
.lpe-key { width: 46%; padding: 5px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px; font-family: monospace; box-sizing: border-box; }
.lpe-label:focus, .lpe-key:focus { outline: none; border-color: #2563eb; }
.lpe-del { background: none; border: none; color: #dc2626; cursor: pointer; font-size: 15px; line-height: 1; padding: 2px 6px; }
.lpe-del:hover { color: #991b1b; }
.lpe-add { padding: 5px 12px; border: 1px dashed #2563eb; border-radius: 5px; background: #fff; color: #2563eb; cursor: pointer; font-size: 12px; align-self: flex-start; }
.lpe-add:hover { background: #eff6ff; }
.lpe-hint { font-size: 11px; color: #999; }

.raw-toolbar { display: flex; gap: 6px; }
.raw-btn { padding: 3px 10px; border: 1px solid #d1d5db; border-radius: 4px; background: #fff; cursor: pointer; font-size: 12px; color: #374151; }
.raw-btn:hover { background: #f3f4f6; }
.raw-text { width: 100%; padding: 6px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 11px; font-family: monospace; resize: vertical; box-sizing: border-box; }
.raw-text.invalid { border-color: #dc2626; background: #fff8f8; }
.raw-error { color: #dc2626; font-size: 11px; }
</style>
