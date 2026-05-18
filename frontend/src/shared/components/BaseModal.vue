<template>
  <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-window" :style="{ maxWidth: width }">
      <div class="modal-header">
        <h3>{{ title }}</h3>
        <button class="modal-close" @click="$emit('close')">&times;</button>
      </div>
      <div class="modal-body"><slot /></div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: Boolean,
  title: { type: String, default: '' },
  width: { type: String, default: '500px' },
})
defineEmits(['close'])
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal-window {
  background: #fff; border-radius: 8px; width: 90%;
  box-shadow: 0 4px 24px rgba(0,0,0,0.15);
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid #e5e7eb;
}
.modal-header h3 { margin: 0; font-size: 16px; }
.modal-close { background: none; border: none; font-size: 22px; cursor: pointer; color: #6b7280; }
.modal-body { padding: 20px; }
</style>
