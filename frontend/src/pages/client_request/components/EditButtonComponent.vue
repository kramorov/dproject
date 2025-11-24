<template>
  <button
    @click="$emit('edit', item)"
    class="w3-button w3-small w3-teal"
    :disabled="disabled"
  >
    <i class="fa fa-edit"></i> {{ label }}
  </button>
</template>

<script setup>
const props = defineProps({
  // Объект, который нужно редактировать
  item: {
    type: Object,
    required: true
  },
  // Текст кнопки
  label: {
    type: String,
    default: 'Редактировать'
  },
  // Флаг неактивного состояния
  disabled: {
    type: Boolean,
    default: false
  }
});

defineEmits(['edit']);
</script>

<style scoped>
/* Можно добавить дополнительные стили при необходимости */
</style>