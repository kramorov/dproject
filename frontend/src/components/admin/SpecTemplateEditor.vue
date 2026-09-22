<!-- components/admin/SpecTemplateEditor.vue — конструктор spec_template -->
<template>
  <div class="ste-wrap">
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
      <datalist :id="datalistId">
        <option v-for="f in fields" :key="f.key" :value="f.key">{{ optionLabel(f) }}</option>
      </datalist>

      <div v-for="(g, gi) in groups" :key="gi" class="ste-group">
        <div class="ste-group-head">
          <input v-model="g.title" class="ste-inp ste-title" placeholder="Название группы" />
          <button class="ste-del" @click="removeGroup(gi)" title="Удалить группу">✕</button>
        </div>
        <div v-for="(r, ri) in g.rows" :key="ri" class="ste-row">
          <input v-model="r.label" class="ste-inp ste-label" placeholder="Подпись" />
          <input v-model="r.key" class="ste-inp ste-key" placeholder="Ключ поля" :list="datalistId" />
          <button class="ste-del" @click="removeRow(gi, ri)" title="Удалить поле">×</button>
        </div>
        <button class="ste-add" @click="addRow(gi)">+ Поле</button>
      </div>
      <button class="ste-add" @click="addGroup">+ Группа</button>
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

const datalistId = 'spec-template-field-keys'

function toGroups(obj) {
  const res = []
  for (const [title, fields] of Object.entries(obj || {})) {
    const rows = Object.entries(fields || {}).map(([label, key]) => ({ label, key }))
    res.push({ title, rows })
  }
  if (!res.length) res.push({ title: '', rows: [{ label: '', key: '' }] })
  return res
}

function toObject() {
  const obj = {}
  const used = new Set()
  let emptyCounter = 0
  for (const g of groups.value) {
    const fields = {}
    for (const r of g.rows) {
      const key = (r.key || '').trim()
      if (!key) continue
      fields[(r.label || '').trim() || key] = key
    }
    if (!Object.keys(fields).length) continue
    let title = (g.title || '').trim()
    if (!title) {
      emptyCounter += 1
      title = emptyCounter === 1 ? 'Основные' : `Группа ${emptyCounter}`
    }
    // Гарантируем уникальность заголовка (пустой или дублирующийся).
    let finalTitle = title
    let n = 2
    while (used.has(finalTitle)) {
      finalTitle = `${title} ${n++}`
    }
    used.add(finalTitle)
    obj[finalTitle] = fields
  }
  return obj
}

const groups = ref(toGroups(props.modelValue))

watch(groups, () => emit('update:modelValue', toObject()), { deep: true })

const { rawMode, rawText, rawError, toggle, onRawInput, formatRaw } = useJsonTextMode({
  getValue: () => toObject(),
  applyValue: (v) => { groups.value = toGroups(v) },
  isArray: false,
})

function optionLabel(f) {
  const parts = [f.key]
  if (f.label) parts.push(f.label)
  if (f.placeholder) parts.push(f.placeholder)
  if (f.unit) parts.push(`[${f.unit}]`)
  return parts.join(' · ')
}

function addGroup() {
  groups.value.push({ title: '', rows: [{ label: '', key: '' }] })
}
function removeGroup(i) { groups.value.splice(i, 1) }
function addRow(gi) { groups.value[gi].rows.push({ label: '', key: '' }) }
function removeRow(gi, ri) { groups.value[gi].rows.splice(ri, 1) }
</script>

<style scoped>
.ste-wrap { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.ste-group { border: 1px solid #e5e7eb; border-radius: 6px; padding: 8px; background: #fafafa; }
.ste-group-head { display: flex; gap: 6px; align-items: center; margin-bottom: 6px; }
.ste-row { display: flex; gap: 6px; align-items: center; margin: 4px 0; }
.ste-inp { padding: 5px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px; box-sizing: border-box; }
.ste-inp:focus { outline: none; border-color: #2563eb; }
.ste-title { flex: 1; font-weight: 500; }
.ste-label { width: 38%; }
.ste-key { width: 46%; font-family: monospace; }
.ste-del { background: none; border: none; color: #dc2626; cursor: pointer; font-size: 15px; line-height: 1; padding: 2px 6px; }
.ste-del:hover { color: #991b1b; }
.ste-add { padding: 5px 12px; border: 1px dashed #2563eb; border-radius: 5px; background: #fff; color: #2563eb; cursor: pointer; font-size: 12px; align-self: flex-start; }
.ste-add:hover { background: #eff6ff; }

.raw-toolbar { display: flex; gap: 6px; }
.raw-btn { padding: 3px 10px; border: 1px solid #d1d5db; border-radius: 4px; background: #fff; cursor: pointer; font-size: 12px; color: #374151; }
.raw-btn:hover { background: #f3f4f6; }
.raw-text { width: 100%; padding: 6px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 11px; font-family: monospace; resize: vertical; box-sizing: border-box; }
.raw-text.invalid { border-color: #dc2626; background: #fff8f8; }
.raw-error { color: #dc2626; font-size: 11px; }
</style>
