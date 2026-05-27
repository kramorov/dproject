<template>
  <div class="login-page">
    <h1>Вход</h1>
    <form @submit.prevent="login" class="login-form">
      <div class="field"><label>Логин</label><input v-model="u" placeholder="Введите логин" /></div>
      <div class="field"><label>Пароль</label><input v-model="p" type="password" placeholder="Введите пароль" /></div>
      <div class="error" v-if="err">{{ err }}</div>
      <AppButton variant="primary" :disabled="ld">Войти</AppButton>
      <p class="link">Нет аккаунта? <router-link to="/register">Регистрация</router-link></p>
    </form>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import AppButton from '@/shared/components/AppButton.vue'
import api from '@/shared/api'
const u=ref(''), p=ref(''), err=ref(''), ld=ref(false)
async function login(){
  if(!u.value||!p.value){err.value='Заполните все поля';return}
  ld.value=true;err.value=''
  await api.get('/auth/login/')
  try{await api.post('/auth/login/',{username:u.value,password:p.value});window.location.href='/'}
  catch(e){err.value=e.response?.data?.error||e.displayMessage||'Ошибка входа'}
  finally{ld.value=false}
}
</script>
<style scoped>
.login-page{max-width:400px;margin:60px auto;padding:32px;background:var(--cat-surface,#fff);border:1px solid var(--cat-border,#e5e7eb);border-radius:var(--cat-radius-lg,12px)}
h1{font-size:var(--cat-text-3xl,24px);margin-bottom:24px;color:var(--cat-text,#1f2937)}
.login-form{display:flex;flex-direction:column;gap:16px}
.field{display:flex;flex-direction:column;gap:4px}
.field label{font-size:var(--cat-text-sm,13px);color:var(--cat-muted,#6b7280)}
.field input{padding:10px 14px;font-size:14px;border:1px solid var(--cat-border,#d1d5db);border-radius:var(--cat-radius-md,6px);outline:none;background:var(--cat-surface,#fff);color:var(--cat-text,#1f2937)}
.field input:focus{border-color:var(--cat-primary,#2563eb)}
.error{color:var(--cat-price-color,#dc2626);font-size:13px}
.link{font-size:13px;color:var(--cat-muted,#6b7280);text-align:center}
.link a{color:var(--cat-primary,#2563eb)}
</style>