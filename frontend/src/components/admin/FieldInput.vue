<script setup>
/**
 * Одно поле формы по дескриптору {name, label, type, choices, source, nullable}.
 * Переиспользуется редакторами справочников (DictEditor) и формами
 * слотов/узлов/опций конфигуратора.
 *
 * modelValue — текущее значение; options — список {id, label} для
 * select/multiselect; события: update:modelValue, toggle-ms (multiselect).
 */
import { computed } from 'vue'

const props = defineProps({
  field: { type: Object, required: true },
  modelValue: { default: null },
  options: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue', 'toggle-ms'])

const isWide = computed(() =>
  ['textarea', 'json', 'multiselect'].includes(props.field.type))

function onText(e) {
  emit('update:modelValue', e.target.value)
}
function onNumber(e) {
  emit('update:modelValue',
       e.target.value === '' ? null : Number(e.target.value))
}
function onBool(e) {
  emit('update:modelValue', e.target.checked)
}
function toggleMs(id) {
  emit('toggle-ms', id)
}
</script>

<template>
  <label class="field-input" :class="{ wide: isWide }">
    <span class="lbl">{{ field.label }}</span>
    <input v-if="field.type === 'text'"
           :value="modelValue ?? ''" @input="onText" />
    <textarea v-else-if="field.type === 'textarea'"
              :value="modelValue ?? ''" @input="onText" rows="2"></textarea>
    <input v-else-if="field.type === 'number'" type="number"
           :value="modelValue ?? ''" @input="onNumber" />
    <input v-else-if="field.type === 'bool'" type="checkbox"
           :checked="!!modelValue" @change="onBool" />
    <select v-else-if="field.type === 'select'"
            :value="modelValue ?? ''" @change="onText">
      <option value="">— не задано —</option>
      <option v-for="o in options" :key="o.id" :value="o.id">{{ o.label }}</option>
    </select>
    <textarea v-else-if="field.type === 'json'"
              :value="modelValue ?? ''" @input="onText" rows="4"
              :placeholder="`{'key': 'value'} или []`"></textarea>
    <div v-else-if="field.type === 'multiselect'" class="ms">
      <label v-for="o in options" :key="o.id" class="ms-item">
        <input type="checkbox" :value="o.id"
               :checked="(modelValue || []).includes(o.id)"
               @change="toggleMs(o.id)" />
        {{ o.label }}
      </label>
    </div>
  </label>
</template>

<style scoped>
.field-input { display: flex; align-items: center; gap: 8px; min-width: 0; }
.field-input > .lbl { flex: 0 0 110px; text-align: right; color: #444; font-size: 13px; }
.field-input > input, .field-input > select, .field-input > textarea {
  flex: 1; min-width: 0; padding: 4px 6px; border: 1px solid #ccc;
  border-radius: 3px; box-sizing: border-box;
}
.field-input > input[type='checkbox'] { flex: 0 0 auto; }
.field-input.wide { grid-column: 1 / -1; }
.ms { display: flex; flex-wrap: wrap; gap: 6px; max-height: 120px; overflow: auto;
      border: 1px solid #eee; padding: 4px; }
.ms-item { display: flex; gap: 4px; align-items: center; font-size: 13px; }
</style>
