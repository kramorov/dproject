<template>
  <div class="admin-page">
    <h1>Виджеты</h1>
    <WidgetApp :allowed-catalogs="['gearbox','filter_regulator','limit_switch']" />
  </div>
</template>
<script setup>
import WidgetApp from '@/apps/widget/App.vue'
</script>
<style scoped>
.admin-page { max-width: 1440px; margin: 0 auto; }
</style>
