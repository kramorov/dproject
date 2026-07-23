<template>
  <div class="placeholder-page">
    <h1>{{ title }}</h1>
    <p>Раздел в разработке</p>
    <router-link to="/">← На главную</router-link>
  </div>
</template>
<script setup>
defineProps({ title: { type: String, default: 'Страница' } })
</script>
<style scoped>
.placeholder-page{max-width:800px;margin:60px auto;text-align:center;padding:40px}
.placeholder-page h1{font-size:24px;color:#1f2937;margin-bottom:12px}
.placeholder-page p{font-size:16px;color:#6b7280}
</style>
