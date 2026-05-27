<template>
  <div class="admin-page">
    <h1>Медиабиблиотека</h1>
    <MediaLibraryApp />
  </div>
</template>
<script setup>
import MediaLibraryApp from '@/apps/media-library/App.vue'
</script>
<style scoped>
.admin-page { max-width: 1440px; margin: 0 auto; }
</style>
