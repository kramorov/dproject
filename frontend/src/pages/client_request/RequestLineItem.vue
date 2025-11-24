<template>
  <li
    class="w3-bar w3-card-2 w3-padding"
    :class="{ 'w3-hover-light-gray': hoverable }"
    @click="emitClick"
  >
    <div>
      <slot name="prefix"></slot>
      <span class="line-id">->{{ line.id }}</span>
      <span class="item-no">№ {{ line.item_no }}</span>
      <span class="request-number">Номер строки в запросе: {{ line.request_line_number }}</span>
      <span class="ol-number">ОЛ: {{ line.request_line_ol }}</span>
      <slot name="suffix"></slot>
    </div>
  </li>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  line: {
    type: Object,
    required: true,
    validator: (value) => {
      return [
        'id',
        'item_no',
        'request_line_number',
        'request_line_ol'
      ].every(prop => prop in value)
    }
  },
  hoverable: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['click'])

const emitClick = () => {
  emit('click', props.line)
}
</script>

<style scoped>
.w3-bar {
  cursor: pointer;
  transition: background-color 0.3s;
}

.line-id {
  font-weight: bold;
  margin-right: 8px;
}

.item-no {
  color: #2196F3;
  margin-right: 12px;
}

.request-number {
  margin-right: 12px;
}

.ol-number {
  font-style: italic;
}
</style>