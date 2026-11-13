<template>
  <div class="cu-slots">
    <div v-for="section in sectionTree" :key="section.code" class="cu-section">
      <h4 class="cu-section-title">{{ section.name }}</h4>
      <template v-for="slot in slotsOf(section)" :key="slot.code">
        <div v-if="slotState(slot.code).visible && availableOptions(slot).length"
             class="cu-slot" :class="{ blocked: slotState(slot.code).blocked }">
          <div class="cu-slot-head">
            <strong>{{ slot.name }}</strong>
            <span v-if="slot.required || slotState(slot.code).required" class="req">обязателен</span>
          </div>
          <!-- один std и нет opt-опций: выбора нет — read-only -->
          <div v-if="slotReadonly(slot)" class="cu-opts readonly">
            <span class="avail">std</span>
            <span class="name">{{ availableOptions(slot)[0].name }}</span>
          </div>
          <div v-else class="cu-opts">
            <label v-for="o in slot.options" :key="o.code"
                   :class="['cu-opt', { na: o.availability === null, std: o.availability === 'std' }]">
              <input v-if="slot.selection_mode === 'multi'" type="checkbox"
                     :disabled="o.availability === null || slotState(slot.code).blocked"
                     :checked="(selection[slot.code] || []).includes(o.code)"
                     @change="toggleOption(slot, o)" />
              <input v-else type="radio" :name="slot.code"
                     :disabled="o.availability === null || slotState(slot.code).blocked"
                     :checked="selection[slot.code] === o.code"
                     @change="selectOption(slot, o)" />
              <span class="name">{{ o.name }}</span>
              <span v-if="o.availability" class="avail">{{ o.availability }}</span>
            </label>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
/**
 * Универсальный рендерер слотов БУ (пакет ea_control.services.cu_package).
 *
 * Принимает ``pkg`` (unit/sections/slots/defaults/rules) и ``modelValue``
 * (снимок {slot_code: option_code}); эмитит обновлённый снимок. Значение
 * слота control_unit (код опции выбора БУ) держится внутренне для оценки
 * правил и в снимок НЕ попадает — БУ выбирается снаружи (привязка).
 *
 * Переиспользуется конфигуратором ЭП и Превью БУ (при необходимости).
 */
import { computed, reactive, watch } from 'vue'

const props = defineProps({
  pkg: { type: Object, default: null },
  modelValue: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:modelValue'])

const selection = reactive({})

const sectionTree = computed(() => {
  if (!props.pkg) return []
  const byCode = {}
  for (const s of props.pkg.sections) byCode[s.code] = { ...s, children: [] }
  const roots = []
  for (const node of Object.values(byCode)) {
    if (node.parent_code && byCode[node.parent_code]) {
      byCode[node.parent_code].children.push(node)
    } else {
      roots.push(node)
    }
  }
  return roots
})

function slotsOf(section) {
  return (props.pkg?.slots || []).filter(s => s.section_code === section.code)
}

function availableOptions(slot) {
  return (slot.options || []).filter(o => o.availability !== null)
}

function slotReadonly(slot) {
  const avail = availableOptions(slot)
  return avail.length === 1 && avail[0].availability === 'std'
}

function slotState(slotCode) {
  if (!props.pkg) return { visible: true, blocked: false, required: false, default: null }
  const value = selection['control_unit']
  const rules = (props.pkg.rules || []).filter(r => r.target_slot === slotCode)
  const state = { visible: true, blocked: false, required: false, default: null }
  for (const r of [...rules].sort((a, b) => (a.priority - b.priority) || (a.id - b.id))) {
    const current = r.when_slot === 'control_unit' ? value : selection[r.when_slot]
    if (!evaluate(r.operator, r.when_value, current)) continue
    if (r.action === 'show') state.visible = true
    else if (r.action === 'hide') state.visible = false
    else if (r.action === 'block') state.blocked = true
    else if (r.action === 'require') state.required = true
    else if (r.action === 'set_default') state.default = r.action_value
  }
  return state
}

function evaluate(op, expected, current) {
  if (op === 'is_set') return current !== null && current !== undefined && current !== ''
  if (op === 'not_exact') return current !== expected
  if (op === 'icontains') return String(current || '').includes(String(expected || ''))
  if (op === 'gte') return Number(current) >= Number(expected)
  if (op === 'lte') return Number(current) <= Number(expected)
  if (op === 'in') return Array.isArray(expected) && expected.includes(current)
  if (op === 'not_in') return Array.isArray(expected) && !expected.includes(current)
  return current === expected
}

function selectOption(slot, o) {
  selection[slot.code] = o.code
  applySetDefaults()
  emitSnapshot()
}

function toggleOption(slot, o) {
  const arr = selection[slot.code] ? [...selection[slot.code]] : []
  const i = arr.indexOf(o.code)
  if (i >= 0) arr.splice(i, 1)
  else arr.push(o.code)
  selection[slot.code] = arr
  applySetDefaults()
  emitSnapshot()
}

function applySetDefaults() {
  if (!props.pkg) return
  for (const slot of props.pkg.slots) {
    const state = slotState(slot.code)
    if (state.default !== null && selection[slot.code] === undefined) {
      selection[slot.code] = state.default
    }
  }
}

function applyDefaults() {
  if (!props.pkg) return
  for (const [slotCode, optionCode] of Object.entries(props.pkg.defaults || {})) {
    if (selection[slotCode] === undefined) selection[slotCode] = optionCode
  }
  for (const slot of props.pkg.slots) {
    if (selection[slot.code] === undefined) {
      const def = slot.options.find(o => o.is_default && o.availability !== null)
      if (def) selection[slot.code] = def.code
    }
  }
}

function buildSelection() {
  for (const k of Object.keys(selection)) delete selection[k]
  Object.assign(selection, props.modelValue || {})
  if (props.pkg?.unit?.option_code) {
    selection['control_unit'] = props.pkg.unit.option_code
  }
  applyDefaults()
  emitSnapshot()
}

function emitSnapshot() {
  const out = {}
  for (const [k, v] of Object.entries(selection)) {
    if (k === 'control_unit') continue
    if (v !== undefined && v !== null) out[k] = v
  }
  emit('update:modelValue', out)
}

watch(() => props.pkg, (v) => { if (v) buildSelection() }, { immediate: true })
</script>

<style scoped>
.cu-slots { display: flex; flex-direction: column; gap: 10px; }
.cu-section { border: 1px solid #e0e0e0; border-radius: 6px; padding: 10px; }
.cu-section-title { margin: 0 0 8px; font-size: 14px; color: #2c6fb0; }
.cu-slot { margin-bottom: 10px; }
.cu-slot.blocked { opacity: .55; }
.cu-slot-head { display: flex; gap: 8px; align-items: baseline; margin-bottom: 4px; }
.cu-slot-head .req { color: #b60; font-size: 12px; }
.cu-opts { display: flex; flex-wrap: wrap; gap: 8px; }
.cu-opts.readonly { opacity: .85; }
.cu-opts.readonly .name { font-weight: 500; }
.cu-opt { display: flex; gap: 6px; align-items: center; border: 1px solid #ddd; border-radius: 4px; padding: 4px 8px; font-size: 13px; }
.cu-opt.na { opacity: .4; }
.cu-opt.std { border-color: #7ab07a; background: #f2faf2; }
.cu-opt .avail { color: #999; font-size: 11px; }
</style>
