<!-- shared/components/AppButton.vue -->
<template>
  <button class="app-btn" :class="variant" :disabled="disabled" @click="$emit('click')">
    <slot />
  </button>
</template>
<script setup>
defineProps({
  variant: { type: String, default: 'primary' },
  disabled: { type: Boolean, default: false },
})
defineEmits(['click'])
</script>
<style scoped>
.app-btn {
  padding: 8px 20px; font-size: 14px; font-weight: 500;
  border: 1px solid transparent; border-radius: var(--cat-radius-md, 6px);
  cursor: pointer; transition: all .15s; white-space: nowrap;
  display: inline-flex; align-items: center; gap: 6px;
}
.app-btn.primary  { background: var(--cat-primary, #2563eb); color: #fff; border-color: var(--cat-primary, #2563eb); }
.app-btn.primary:hover:not(:disabled) { background: var(--cat-primary-hover, #1d4ed8); }
.app-btn.danger   { background: var(--cat-price-color, #dc2626); color: #fff; }
.app-btn.danger:hover:not(:disabled) { background: #b91c1c; }
.app-btn.cancel   { background: var(--cat-surface, #fff); color: var(--cat-text, #1f2937); border-color: var(--cat-border, #d1d5db); }
.app-btn.cancel:hover:not(:disabled) { border-color: var(--cat-primary, #2563eb); color: var(--cat-primary, #2563eb); }
.app-btn.ghost    { background: transparent; color: var(--cat-primary, #2563eb); border-color: transparent; }
.app-btn.ghost:hover:not(:disabled) { background: rgba(37,99,235,.08); }
.app-btn:disabled { opacity: .4; cursor: default; }
</style>
