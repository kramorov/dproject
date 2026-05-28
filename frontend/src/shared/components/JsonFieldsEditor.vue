<!-- shared/components/JsonFieldsEditor.vue — редактор плоского JSON extra_params -->
<template>
  <div class="jfe-wrap">
    <label class="jfe-label">{{ label }}</label>
    <table class="jfe-table" v-if="rows.length">
      <thead>
        <tr>
          <th class="jfe-th-order">№</th>
          <th>Ключ</th>
          <th>Название</th>
          <th>Значение</th>
          <th class="jfe-th-act"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, i) in rows" :key="i">
          <td class="jfe-td-order">
            <button class="jfe-arr" :disabled="i === 0" @click="moveUp(i)" title="Выше">▲</button>
            <button class="jfe-arr" :disabled="i === rows.length - 1" @click="moveDown(i)" title="Ниже">▼</button>
          </td>
          <td><input v-model="row.key" class="jfe-inp" placeholder="ключ" /></td>
          <td><input v-model="row.label" class="jfe-inp" placeholder="название" /></td>
          <td><input v-model="row.value" class="jfe-inp" placeholder="значение" /></td>
          <td class="jfe-td-del"><button class="jfe-del" @click="remove(i)" title="Удалить">×</button></td>
        </tr>
      </tbody>
    </table>
    <div v-else class="jfe-empty">Нет полей</div>
    <button class="jfe-add" @click="add">+ Добавить поле</button>

    <!-- Raw JSON -->
    <div class="jfe-raw">
      <div class="jfe-raw-btns">
        <button class="jfe-raw-btn" @click="tableToJson" title="Таблица → JSON">▼</button>
        <button class="jfe-raw-btn" @click="jsonToTable" title="JSON → Таблица">▲</button>
      </div>
      <textarea v-model="rawJson" class="jfe-raw-text" rows="4"
        placeholder='[{"key":"...","label":"...","value":"..."}]'></textarea>
      <div v-if="rawError" class="jfe-raw-error">{{ rawError }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  label: { type: String, default: 'Доп. параметры' },
})

const emit = defineEmits(['update:modelValue'])

const rawJson = ref('')
const rawError = ref('')

const rows = computed({
  get: () => {
    if (!Array.isArray(props.modelValue)) return []
    return [...props.modelValue]
      .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
      .map(r => ({ key: r.key || '', label: r.label || '', value: r.value || '', order: r.order ?? 0 }))
  },
  set: (val) => emit('update:modelValue', val),
})

function add() {
  const maxOrder = rows.value.reduce((m, r) => Math.max(m, r.order), 0)
  const updated = [...rows.value, { key: '', label: '', value: '', order: maxOrder + 1 }]
  emit('update:modelValue', updated)
}

function remove(i) {
  const updated = rows.value.filter((_, idx) => idx !== i)
  emit('update:modelValue', updated)
}

function moveUp(i) {
  if (i === 0) return
  const updated = [...rows.value]
  ;[updated[i - 1], updated[i]] = [updated[i], updated[i - 1]]
  // swap orders
  const tmp = updated[i - 1].order
  updated[i - 1].order = updated[i].order
  updated[i].order = tmp
  emit('update:modelValue', updated)
}

function moveDown(i) {
  if (i === rows.length - 1) return
  const updated = [...rows.value]
  ;[updated[i], updated[i + 1]] = [updated[i + 1], updated[i]]
  const tmp = updated[i].order
  updated[i].order = updated[i + 1].order
  updated[i + 1].order = tmp
  emit('update:modelValue', updated)
}

function tableToJson() {
  const items = rows.value.map(r => ({ key: r.key, label: r.label, value: r.value, order: r.order }))
  rawJson.value = JSON.stringify(items, null, 2)
  rawError.value = ''
}

function jsonToTable() {
  rawError.value = ''
  if (!rawJson.value.trim()) return
  let parsed
  try {
    parsed = JSON.parse(rawJson.value)
  } catch {
    rawError.value = 'Невалидный JSON'
    return
  }
  if (!Array.isArray(parsed)) {
    rawError.value = 'Ожидается массив [{key, label, value, order}]'
    return
  }
  for (let i = 0; i < parsed.length; i++) {
    const item = parsed[i]
    if (!item || typeof item !== 'object') {
      rawError.value = `Элемент ${i}: не объект`
      return
    }
    if (!('key' in item) || !('label' in item) || !('value' in item)) {
      rawError.value = `Элемент ${i}: обязательны поля key, label, value`
      return
    }
  }
  const items = parsed.map((r, i) => ({
    key: r.key || '', label: r.label || '', value: r.value || '',
    order: r.order ?? i + 1,
  }))
  emit('update:modelValue', items)
}
</script>

<style scoped>
.jfe-wrap { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.jfe-label { font-size: 13px; color: #374151; }
.jfe-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.jfe-table th { text-align: left; padding: 4px 6px; background: #f9fafb; border-bottom: 2px solid #e5e7eb; color: #6b7280; font-weight: 500; }
.jfe-table td { padding: 3px 6px; border-bottom: 1px solid #f3f4f6; }
.jfe-th-order { width: 50px; }
.jfe-th-act { width: 30px; }
.jfe-td-order { white-space: nowrap; text-align: center; }
.jfe-td-del { text-align: center; }
.jfe-inp { padding: 4px 6px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px; width: 100%; box-sizing: border-box; }
.jfe-inp:focus { outline: none; border-color: #2563eb; }
.jfe-arr {
  padding: 0 4px; border: none; background: none; cursor: pointer; font-size: 10px; color: #6b7280;
  line-height: 1;
}
.jfe-arr:disabled { opacity: .3; cursor: default; }
.jfe-arr:not(:disabled):hover { color: #2563eb; }
.jfe-del {
  padding: 0 6px; border: none; background: none; cursor: pointer; font-size: 16px; color: #dc2626;
  line-height: 1;
}
.jfe-del:hover { color: #991b1b; }
.jfe-empty { padding: 12px; text-align: center; color: #9ca3af; font-size: 12px; border: 1px dashed #d1d5db; border-radius: 6px; }
.jfe-add {
  padding: 6px 14px; border: 1px solid #2563eb; border-radius: 5px;
  background: #fff; color: #2563eb; cursor: pointer; font-size: 12px; align-self: flex-start;
}
.jfe-add:hover { background: #eff6ff; }
.jfe-raw { display: flex; flex-direction: column; gap: 4px; margin-top: 8px; }
.jfe-raw-btns { display: flex; gap: 4px; }
.jfe-raw-btn {
  padding: 3px 10px; border: 1px solid #d1d5db; border-radius: 4px;
  background: #fff; cursor: pointer; font-size: 12px; color: #374151;
}
.jfe-raw-btn:hover { background: #f3f4f6; }
.jfe-raw-text {
  padding: 6px 8px; border: 1px solid #d1d5db; border-radius: 4px;
  font-size: 11px; font-family: monospace; resize: vertical;
}
.jfe-raw-error { color: #dc2626; font-size: 11px; }
</style>
