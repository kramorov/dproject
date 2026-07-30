<template>
  <div v-if="show" class="modal-overlay">
    <div class="modal" :style="{ width: width || '380px' }">
      <div class="modal-header">
        <h3>{{ title }}</h3>
        <button class="modal-close" @click="$emit('cancel')">✕</button>
      </div>
      <div class="modal-body" :style="{ textAlign: 'center', padding: '24px' }">
        <p class="confirm-message">{{ message }}</p>
        <p v-if="subMessage" class="confirm-sub">{{ subMessage }}</p>
        <slot />
      </div>
      <div class="modal-actions" style="justify-content: center; gap: 8px">
        <button v-if="cancelText" class="btn-cancel-lg" @click="$emit('cancel')">{{ cancelText }}</button>
        <button class="btn-save-lg" @click="$emit('confirm')">{{ confirmText }}</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ConfirmDialog',
  props: {
    show: { type: Boolean, default: false },
    title: { type: String, default: 'Подтверждение' },
    message: { type: String, default: '' },
    subMessage: { type: String, default: '' },
    confirmText: { type: String, default: 'OK' },
    cancelText: { type: String, default: '' },
    width: { type: String, default: '380px' },
  },
  emits: ['confirm', 'cancel'],
}
</script>

<style scoped>
.confirm-message { margin: 0 0 4px; font-weight: 600; }
.confirm-sub { margin: 0; color: #666; }

.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: #fff; border-radius: 8px; max-height: 80vh; overflow-y: auto; box-shadow: 0 8px 32px rgba(0,0,0,.2); }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #eee; }
.modal-header h3 { margin: 0; font-size: 16px; }
.modal-close { background: none; border: none; font-size: 18px; cursor: pointer; color: #999; padding: 4px 8px; }
.modal-close:hover { color: #333; }
.modal-body { padding: 20px; display: flex; flex-direction: column; gap: 8px; }
.modal-actions { display: flex; padding: 16px 20px; border-top: 1px solid #eee; }
.btn-save-lg { padding: 8px 24px; background: #3b82f6; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
.btn-save-lg:hover { background: #2563eb; }
.btn-cancel-lg { padding: 8px 24px; background: #fff; color: #666; border: 1px solid #ccc; border-radius: 4px; cursor: pointer; font-size: 14px; }
.btn-cancel-lg:hover { background: #f5f5f5; }
</style>
