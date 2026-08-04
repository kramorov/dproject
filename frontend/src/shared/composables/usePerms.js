// shared/composables/usePerms.js
// Единая точка проверки прав на фронтенде.
// Используется роутером (beforeEach) и компонентами (v-if, :disabled, :class).
import { ref } from 'vue'
import api from '@/shared/api'

const objectPerms = ref({})   // { codename: [actions] }
const sectionPerms = ref([])  // [section codes]
const systemGroups = ref([])
const loaded = ref(false)
let fetching = false

export function usePerms() {
  if (!loaded.value && !fetching) {
    fetching = true
    api.get('/auth/me/').then(r => {
      objectPerms.value = r.data.object_permissions || {}
      sectionPerms.value = r.data.section_permissions || []
      systemGroups.value = r.data.system_groups || []
    }).catch(() => {
      // Not authenticated — empty permissions
      objectPerms.value = {}
      sectionPerms.value = []
      systemGroups.value = []
    }).finally(() => {
      loaded.value = true
      fetching = false
    })
  }

  return {
    objectPerms,
    sectionPerms,
    systemGroups,

    /** Check system permission: can('admin.media', 'edit') */
    can(codename, action = 'view') {
      const allowed = objectPerms.value[codename] || []
      return allowed.includes(action) || allowed.includes('manage')
    },

    /** Check any of multiple permissions: canAny(['admin.media','edit'], ['ai.debug','view']) */
    canAny(...pairs) {
      return pairs.some(([codename, action]) => this.can(codename, action || 'view'))
    },

    /** Check org section access */
    canSeeSection(code) {
      return sectionPerms.value.includes(code)
    },

    /** Is current user an admin? */
    get isAdmin() {
      return systemGroups.value.includes('administrators')
    },

    loaded,
  }
}
