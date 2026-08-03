<template>
  <header class="site-header">
    <div class="header-left"><router-link to="/" class="logo">На главную</router-link></div>
    <nav class="header-nav"><TopMenu /></nav>
    <div class="header-right">
      <template v-if="user">
        <span class="user-name">{{ user.username }}</span>
        <button class="logout-btn" @click="doLogout">Выход</button>
      </template>
      <router-link v-else to="/login" class="auth-link">Вход</router-link>
    </div>
  </header>
</template>
<script setup>
import TopMenu from './TopMenu.vue'
import AppButton from '@/shared/components/AppButton.vue'
import { useAuth } from './useAuth.js'
import api from '@/shared/api'
const { user, role } = useAuth()
async function doLogout() {
  try { await api.post('/auth/logout/') } catch(e) {}
  user.value = null
  role.value = 'viewer'
  window.location.href = '/'
}
</script>
<style scoped>
.site-header{display:flex;align-items:center;justify-content:space-between;background:var(--site-header-bg);color:var(--site-header-text);padding:0 20px;height:56px;gap:16px}
.header-left{flex-shrink:0}
.logo{font-size:18px;font-weight:700;color:inherit;text-decoration:none}
.header-nav{flex:1}
.header-right{display:flex;align-items:center;gap:12px;flex-shrink:0}
.user-name{font-size:13px;opacity:.9}
.logout-btn{background:rgba(255,255,255,.15);color:#fff;border:1px solid rgba(255,255,255,.25);padding:5px 14px;border-radius:var(--cat-radius-md,6px);cursor:pointer;font-size:13px}
.logout-btn:hover{background:rgba(255,255,255,.25)}
.auth-link{color:inherit;text-decoration:none;font-size:14px;padding:6px 12px;border-radius:4px;transition:background .15s}
.auth-link:hover{background:rgba(255,255,255,.15)}
</style>