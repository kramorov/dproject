<template>
  <div class="site">
    <Header />
    <main class="main">
      <router-view />
    </main>
  </div>
</template>
<script setup>
import Header from './components/header/Header.vue'
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
.debug-tag{display:inline-block;background:rgba(0,0,0,.75);color:#0f0;font:10px monospace;padding:1px 6px;border-radius:3px;vertical-align:top;margin-right:8px;user-select:all}
</style>
