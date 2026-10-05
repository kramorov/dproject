<template>
  <div class="auth-page">
    <div class="auth-container">
      <!-- Левая панель: Вход -->
      <div class="auth-panel auth-panel-login">
        <div class="auth-panel-inner">
          <h1>{{ t('auth.title.login') }}</h1>
          <p class="auth-subtitle">{{ t('auth.subtitle.login') }}</p>
          <form @submit.prevent="login" class="auth-form">
            <div class="field">
              <label>{{ t('auth.username') }}</label>
              <input v-model="u" name="username" type="text" placeholder="Введите логин" autocomplete="username" />
            </div>
            <div class="field">
              <label>{{ t('auth.password') }}</label>
              <input v-model="p" name="password" type="password" placeholder="Введите пароль" autocomplete="current-password" />
            </div>
            <div class="error" v-if="err">{{ err }}</div>
            <button class="btn-primary" :disabled="ld">
              <span v-if="ld" class="spinner"></span>
              <span v-else>{{ t('auth.signIn') }}</span>
            </button>
          </form>
        </div>
      </div>

      <!-- Правая панель: Регистрация -->
      <div class="auth-panel auth-panel-register">
        <div class="auth-panel-inner">
          <h1>{{ t('auth.title.register') }}</h1>
          <p class="auth-subtitle">{{ t('auth.subtitle.register') }}</p>
          <form @submit.prevent="register" class="auth-form">
            <div class="field">
              <label>{{ t('auth.username') }}</label>
              <input v-model="ru" name="username" type="text" placeholder="Придумайте логин" autocomplete="username" />
            </div>
            <div class="field">
              <label>{{ t('auth.email') }}</label>
              <input v-model="re" name="email" type="email" placeholder="your@email.com" autocomplete="email" />
            </div>
            <div class="field">
              <label>{{ t('auth.password') }}</label>
              <input v-model="rp" name="new-password" type="password" placeholder="Минимум 6 символов" autocomplete="new-password" />
            </div>
            <div class="field">
              <label>{{ t('auth.passwordConfirm') }}</label>
              <input v-model="rp2" name="new-password-confirm" type="password" placeholder="Повторите пароль" autocomplete="new-password" />
            </div>
            <div class="error" v-if="rerr">{{ rerr }}</div>
            <div class="success" v-if="rsuccess">{{ rsuccess }}</div>
            <button class="btn-primary btn-primary-outline" :disabled="rld">
              <span v-if="rld" class="spinner"></span>
              <span v-else>{{ t('auth.signUp') }}</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/shared/api'
import { login as doLogin } from '@/shared/stores/auth'
import { useI18n } from '@/shared/i18n'
const { t } = useI18n()

const router = useRouter()
const route = useRoute()

// ── Вход ──
const u = ref(''), p = ref(''), err = ref(''), ld = ref(false)
async function login() {
  if (!u.value || !p.value) { err.value = t('auth.fillAll'); return }
  ld.value = true; err.value = ''
  try {
    await doLogin({ login: u.value, password: p.value })
    const next = typeof route.query.next === 'string' ? route.query.next : '/'
    router.push(next)
  } catch (e) {
    err.value = e.response?.data?.error || e.response?.data?.detail || t('auth.loginError')
  } finally { ld.value = false }
}

// ── Регистрация ──
const ru = ref(''), re = ref(''), rp = ref(''), rp2 = ref(''), rerr = ref(''), rsuccess = ref(''), rld = ref(false)
async function register() {
  rerr.value = ''; rsuccess.value = ''
  if (!ru.value || !re.value || !rp.value) { rerr.value = t('auth.fillAll'); return }
  if (rp.value !== rp2.value) { rerr.value = t('auth.passwordsMismatch'); return }
  if (rp.value.length < 6) { rerr.value = t('auth.passwordMin'); return }
  rld.value = true
  try {
    await api.post('/auth/register/', { username: ru.value, email: re.value, password: rp.value })
    rsuccess.value = t('auth.registerSuccess')
    ru.value = ''; re.value = ''; rp.value = ''; rp2.value = ''
  } catch (e) {
    rerr.value = e.response?.data?.error || e.response?.data?.detail || Object.values(e.response?.data || {}).flat().join('; ') || 'Ошибка регистрации'
  } finally { rld.value = false }
}
</script>

<style scoped>
.auth-page {
  max-width: 900px;
  margin: 40px auto;
  padding: 0 16px;
}
.auth-container {
  display: flex;
  gap: 0;
  background: var(--cat-surface);
  border: 1px solid var(--cat-border);
  border-radius: var(--cat-radius-2xl);
  overflow: hidden;
  box-shadow: var(--cat-shadow-card);
}
.auth-panel {
  flex: 1;
  padding: 40px 32px;
}
.auth-panel-login {
  background: var(--cat-surface);
}
.auth-panel-register {
  background: var(--cat-bg);
  border-left: 1px solid var(--cat-border);
}
.auth-panel-inner {
  max-width: 340px;
  margin: 0 auto;
}
.auth-panel h1 {
  font-size: var(--cat-text-3xl);
  font-weight: 700;
  color: var(--cat-text);
  margin: 0 0 8px;
}
.auth-subtitle {
  font-size: var(--cat-text-sm);
  color: var(--cat-muted);
  margin: 0 0 24px;
  line-height: 1.5;
}
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.field label {
  font-size: var(--cat-text-sm);
  color: var(--cat-muted);
  font-weight: 500;
}
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
.btn-primary-outline {
  background: transparent;
  color: var(--cat-primary);
  border: 1.5px solid var(--cat-primary);
}
.btn-primary-outline:hover { background: var(--cat-primary-light) }
.error {
  color: #dc2626;
  font-size: var(--cat-text-sm);
  padding: 8px 12px;
  background: #fef2f2;
  border-radius: var(--cat-radius-sm);
}
.success {
  color: #16a34a;
  font-size: var(--cat-text-sm);
  padding: 8px 12px;
  background: #f0fdf4;
  border-radius: var(--cat-radius-sm);
}
.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg) } }

@media (max-width: 640px) {
  .auth-container { flex-direction: column }
  .auth-panel-register { border-left: none; border-top: 1px solid var(--cat-border) }
}
</style>