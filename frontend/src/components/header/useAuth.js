// composable для проверки роли текущего пользователя
import { ref } from 'vue'
import api from '@/shared/api'

const user = ref(null)
const roles = ref([])
const sectionPermissions = ref([])
const loaded = ref(false)
let fetching = false

export function useAuth() {
  if (!loaded.value && !fetching) {
    fetching = true
    api.get('/auth/me/').then(r => {
      user.value = r.data
      roles.value = r.data.roles || []
      sectionPermissions.value = r.data.section_permissions || []
    }).catch(() => {
      user.value = null
      roles.value = []
      sectionPermissions.value = []
    }).finally(() => {
      loaded.value = true
      fetching = false
    })
  }
  return { user, roles, sectionPermissions, loaded }
}
