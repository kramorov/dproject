<template>
  <div class="register-page">
    <div class="register-card">
      <h1>Регистрация</h1>
      <p class="subtitle">Создайте аккаунт для доступа к каталогу оборудования</p>
      <form @submit.prevent="register" class="reg-form">
        <div class="field">
          <label>Логин</label>
          <input v-model="u" type="text" placeholder="Придумайте логин" autocomplete="username" />
        </div>
        <div class="field">
          <label>Email</label>
          <input v-model="e" type="email" placeholder="your@email.com" autocomplete="email" />
        </div>
        <div class="field">
          <label>Пароль</label>
          <input v-model="p" type="password" placeholder="Минимум 6 символов" autocomplete="new-password" />
        </div>
        <div class="field">
          <label>Подтверждение пароля</label>
          <input v-model="p2" type="password" placeholder="Повторите пароль" autocomplete="new-password" />
        </div>
        <div class="error" v-if="err">{{ err }}</div>
        <div class="success" v-if="success">{{ success }}</div>
        <button class="btn-primary" :disabled="ld">
          <span v-if="ld" class="spinner"></span>
          <span v-else>Зарегистрироваться</span>
        </button>
      </form>
      <p class="link">Уже есть аккаунт? <router-link to="/login">Войти</router-link></p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/shared/api'

const u = ref(''), e = ref(''), p = ref(''), p2 = ref(''), err = ref(''), success = ref(''), ld = ref(false)

async function register() {
  err.value = ''; success.value = ''
  if (!u.value || !e.value || !p.value) { err.value = 'Заполните все поля'; return }
  if (p.value !== p2.value) { err.value = 'Пароли не совпадают'; return }
  if (p.value.length < 6) { err.value = 'Пароль должен быть не менее 6 символов'; return }
  ld.value = true
  try {
    await api.post('/auth/register/', { username: u.value, email: e.value, password: p.value })
    success.value = 'Регистрация успешна! Сейчас вы будете перенаправлены на страницу входа.'
    setTimeout(() => { window.location.href = '/login' }, 2000)
  } catch (e) {
    err.value = e.response?.data?.error || e.response?.data?.detail || Object.values(e.response?.data || {}).flat().join('; ') || 'Ошибка регистрации'
  } finally { ld.value = false }
}
</script>

<style scoped>
.register-page {
  max-width: 440px;
  margin: 40px auto;
  padding: 0 16px;
}
.register-card {
  background: var(--cat-surface);
  border: 1px solid var(--cat-border);
  border-radius: var(--cat-radius-2xl);
  padding: 40px 32px;
  box-shadow: var(--cat-shadow-card);
}
.register-card h1 {
  font-size: var(--cat-text-3xl);
  font-weight: 700;
  color: var(--cat-text);
  margin: 0 0 8px;
}
.subtitle {
  font-size: var(--cat-text-sm);
  color: var(--cat-muted);
  margin: 0 0 28px;
  line-height: 1.5;
}
.reg-form { display: flex; flex-direction: column; gap: 14px }
.field { display: flex; flex-direction: column; gap: 4px }
.field label { font-size: var(--cat-text-sm); color: var(--cat-muted); font-weight: 500 }
.field input {
  padding: 10px 14px;
  font-size: 14px;
  border: 1px solid var(--cat-border);
  border-radius: var(--cat-radius-md);
  outline: none;
  background: var(--cat-surface);
  color: var(--cat-text);
  transition: border-color .15s;
}
.field input:focus { border-color: var(--cat-primary); box-shadow: 0 0 0 3px rgba(37,99,235,.1) }
.btn-primary {
  padding: 12px 24px;
  background: var(--cat-primary);
  color: #fff;
  border: none;
  border-radius: var(--cat-radius-md);
  font-size: var(--cat-text-base);
  font-weight: 600;
  cursor: pointer;
  transition: background .15s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 44px;
}
.btn-primary:hover { background: var(--cat-primary-hover) }
.btn-primary:disabled { opacity: .6; cursor: not-allowed }
.error { color: #dc2626; font-size: var(--cat-text-sm); padding: 8px 12px; background: #fef2f2; border-radius: var(--cat-radius-sm) }
.success { color: #16a34a; font-size: var(--cat-text-sm); padding: 8px 12px; background: #f0fdf4; border-radius: var(--cat-radius-sm) }
.spinner {
  width: 18px; height: 18px;
  border: 2px solid rgba(255,255,255,.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg) } }
.link { font-size: var(--cat-text-sm); color: var(--cat-muted); text-align: center; margin-top: 20px }
.link a { color: var(--cat-primary); text-decoration: none; font-weight: 500 }
.link a:hover { text-decoration: underline }
</style>