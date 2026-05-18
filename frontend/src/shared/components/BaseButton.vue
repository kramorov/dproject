<template>
  <button class="base-btn" :class="variant" :disabled="disabled || loading" @click="$emit('click')">
    <span v-if="loading" class="spinner" />
    <slot />
  </button>
</template>

<script setup>
defineProps({
  variant: { type: String, default: 'primary' },
  disabled: Boolean,
  loading: Boolean,
})
defineEmits(['click'])
</script>

<style scoped>
.base-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 16px; border: 1px solid #d1d5db; border-radius: 6px;
  background: #fff; color: #374151; font-size: 14px; cursor: pointer;
}
.base-btn.primary { background: #2563eb; color: #fff; border-color: #2563eb; }
.base-btn.danger  { background: #dc2626; color: #fff; border-color: #dc2626; }
.base-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.spinner {
  width: 14px; height: 14px; border: 2px solid #fff; border-top-color: transparent;
  border-radius: 50%; animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
