<template>
  <div class="site">
    <Header />
    <main class="main">
      <Breadcrumbs :items="breadcrumbs" />
      <router-view />
    </main>
  </div>
</template>
<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Header from './components/header/Header.vue'
import Breadcrumbs from '@/shared/components/Breadcrumbs.vue'
const route = useRoute()
const breadcrumbs = computed(() => {
  const parts = [{ name: 'Главная', to: '/' }]
  if (route.meta.title) parts.push({ name: route.meta.title })
  return parts
})
</script>
<style>
:root {
  --site-header-bg: var(--cat-primary, #2563eb);
  --site-header-text: #fff;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--cat-font,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto);background:var(--cat-bg-page,#f5f5f5);color:var(--cat-text,#1f2937)}
.site{min-height:100vh;display:flex;flex-direction:column}
.main{flex:1;max-width:1440px;width:100%;margin:0 auto;padding:16px}
</style>
