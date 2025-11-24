<template>
  <div class="select-drop-down-container">
    <label v-if="label">{{ label }}</label>
    <select
      v-model="selectedValue"
      class="w3-select w3-border w3-small w3-teal"
      :required="required"
      @change="onChange"
    >
      <option
        v-for="item in options"
        :key="item.id"
        :value="item.id"
      >
        {{ item.text_description || item.symbolic_code || item.title || item.id }}
      </option>
    </select>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  modelValue: {
    type: [Number, String, Object],
    default: null
  },
  options: {
    type: Array,
    required: true,
    default: () => []
  },
  label: {
    type: String,
    default: ''
  },
  required: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:modelValue']);

const selectedValue = ref(props.modelValue);

// Отслеживаем изменения внешнего modelValue
watch(() => props.modelValue, (newVal) => {
  selectedValue.value = newVal;
});

// Отправляем изменения наружу
const onChange = () => {
  emit('update:modelValue', selectedValue.value);
};
</script>

<style scoped>
.select-drop-down-container {
  margin-bottom: 1rem;
}
</style>