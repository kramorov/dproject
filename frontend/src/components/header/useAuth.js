// composable для проверки роли текущего пользователя
import { ref } from 'vue'
import api from '@/shared/api'

const user = ref(null)
const role = ref('viewer')
const loaded = ref(false)
let fetching = false

export function useAuth() {
  if (!loaded.value && !fetching) {
    fetching = true
    api.get('/auth/me/').then(r => {
      user.value = r.data
      role.value = r.data.role || 'viewer'
    }).catch(() => {
      user.value = null
      role.value = 'viewer'
    }).finally(() => {
      loaded.value = true
      fetching = false
    })
  }
  return { user, role, loaded }
}
