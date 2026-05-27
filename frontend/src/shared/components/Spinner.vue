<!-- shared/components/Spinner.vue -->
<template>
  <div class="spinner-wrap">
    <div class="spinner"></div>
    <p class="spinner-text" v-if="text">{{ text }}</p>
  </div>
</template>
<script setup>
defineProps({ text: { type: String, default: '' } })
</script>
<style scoped>
.spinner-wrap { display:flex; flex-direction:column; align-items:center; justify-content:center; padding:60px 20px; gap:12px }
.spinner { width:32px; height:32px; border:3px solid var(--cat-border,#e5e7eb); border-top-color:var(--cat-primary,#2563eb); border-radius:50%; animation:spin .6s linear infinite }
@keyframes spin { to { transform:rotate(360deg) } }
.spinner-text { font-size:var(--cat-text-sm,13px); color:var(--cat-muted-light,#9ca3af); margin:0 }
</style>
