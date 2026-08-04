// composable для проверки прав текущего пользователя
import { ref } from 'vue'
import api from '@/shared/api'

const user = ref(null)
const roles = ref([])
const sectionPermissions = ref([])
const systemGroups = ref([])
const objectPermissions = ref({})
const loaded = ref(false)
let fetching = false

export function useAuth() {
  if (!loaded.value && !fetching) {
    fetching = true
    api.get('/auth/me/').then(r => {
      user.value = r.data
      roles.value = r.data.roles || []
      sectionPermissions.value = r.data.section_permissions || []
      systemGroups.value = r.data.system_groups || []
      objectPermissions.value = r.data.object_permissions || {}
    }).catch(() => {
      user.value = null
      roles.value = []
      sectionPermissions.value = []
      systemGroups.value = []
      objectPermissions.value = {}
    }).finally(() => {
      loaded.value = true
      fetching = false
    })
  }
  return { user, roles, sectionPermissions, systemGroups, objectPermissions, loaded }
}
