<template>
  <div class="reg-page"><h1>Регистрация</h1><p class="msg">Регистрация временно недоступна. Обратитесь к администратору.</p><p class="link"><router-link to="/login">← Вход</router-link></p></div>
</template>
<style scoped>
.reg-page{max-width:400px;margin:60px auto;padding:32px;background:var(--cat-surface,#fff);border:1px solid var(--cat-border,#e5e7eb);border-radius:var(--cat-radius-lg,12px);text-align:center}
.reg-page h1{font-size:var(--cat-text-3xl,24px);margin-bottom:16px;color:var(--cat-text,#1f2937)}
.msg{color:var(--cat-muted,#6b7280);font-size:14px;margin-bottom:16px}
.link a{color:var(--cat-primary,#2563eb);font-size:14px}
</style>
