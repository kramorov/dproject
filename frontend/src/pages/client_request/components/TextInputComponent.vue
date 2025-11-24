<template>
  <div class="text-input-container">
    <div class="w3-row w3-margin-bottom">
      <div class="w3-col" style="width:120px">
        <label class="w3-padding-small" v-if="label">{{label}}</label>
      </div>
      <div class="w3-rest">
                <textarea
                    v-model="textInputString"
                    class="w3-input w3-border"
                    :rows="rows"
                    @input="onChange"
                ></textarea>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch} from 'vue';

const props = defineProps({
  modelValue: {
    type: [Number, String],
    default: null
  },
  rows: {
    type: [Number],
    default: 1
  },
  label: {
    type: String,
    default: ''
  }
});
const textInputString = ref(props.modelValue);
const emit = defineEmits(['update:modelValue']);

// Отслеживаем изменения внешнего modelValue
watch(() => props.modelValue, (newVal) => {
  textInputString.value = newVal;
});

// Отправляем изменения наружу
const onChange = () => {
  emit('update:modelValue', textInputString.value);
};
</script>

<style scoped>
.select-drop-down-container {
  margin-bottom: 1rem;
}
</style>