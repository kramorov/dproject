// shared/stores/auth.js — единый реактивный auth-store (пользователь + права).
// Один источник истины: один запрос /api/auth/me/. Используется шапкой (Header/TopMenu),
// router-гардом (через usePerms) и страницами входа. Логин/логаут без перезагрузки страницы.

import { ref, computed } from 'vue'
import api from '@/shared/api'

const user = ref(null)
const roles = ref([])
const sectionPerms = ref([])
const systemGroups = ref([])
const objectPerms = ref({})
const loaded = ref(false)
let loadPromise = null

function applyProfile(data) {
  user.value = data
  roles.value = data.roles || []
  sectionPerms.value = data.section_permissions || []
  systemGroups.value = data.system_groups || []
  objectPerms.value = data.object_permissions || {}
}

function resetAuth() {
  user.value = null
  roles.value = []
  sectionPerms.value = []
  systemGroups.value = []
  objectPerms.value = {}
}

/** Идемпотентная загрузка текущего пользователя (включая анонимные права). */
export async function ensureAuth() {
  if (loaded.value) return
  if (loadPromise) return loadPromise

  loadPromise = api.get('/auth/me/')
    .then(r => applyProfile(r.data))
    .catch(() => resetAuth())
    .finally(() => {
      loaded.value = true
      loadPromise = null
    })

  return loadPromise
}

/** Вход: применяем данные ответа сразу, без полной перезагрузки. */
export async function login(credentials) {
  const r = await api.post('/auth/login/', credentials)
  applyProfile(r.data)
  loaded.value = true
  return r.data
}

/** Выход: сбрасываем состояние и перезагружаем анонимные права. */
export async function logout() {
  try { await api.post('/auth/logout/') } catch (e) { /* сессия могла уже истечь */ }
  resetAuth()
  loaded.value = false
  return ensureAuth()
}

export function useAuth() {
  if (!loaded.value && !loadPromise) ensureAuth()

  const isAdmin = computed(() => systemGroups.value.includes('administrators'))

  function can(codename, action = 'view') {
    const allowed = objectPerms.value[codename] || []
    return allowed.includes(action) || allowed.includes('manage')
  }
  function canAny(...pairs) {
    return pairs.some(([codename, action]) => can(codename, action || 'view'))
  }
  function canSeeSection(code) {
    return sectionPerms.value.includes(code)
  }

  return {
    user, roles, sectionPerms, systemGroups, objectPerms, loaded, isAdmin,
    ensureAuth, login, logout, can, canAny, canSeeSection,
  }
}
