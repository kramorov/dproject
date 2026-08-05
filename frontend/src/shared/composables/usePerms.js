// shared/composables/usePerms.js
// Single point of permission loading for router (async) and components (reactive).
import { ref } from 'vue'
import api from '@/shared/api'

const objectPerms = ref({})   // { codename: [actions] }
const sectionPerms = ref([])  // [section codes]
const systemGroups = ref([])
const roles = ref([])         // [OrgRole codes]
const loaded = ref(false)
let loadPromise = null

/**
 * Load permissions from /auth/me/. Idempotent — subsequent calls return
 * the same promise while loading, or resolve immediately if already loaded.
 *
 * Usage in router.beforeEach:
 *   await ensurePerms()
 *   const { objectPerms, sectionPerms, systemGroups } = usePerms()
 */
export async function ensurePerms() {
  if (loaded.value) return
  if (loadPromise) return loadPromise

  loadPromise = api.get('/auth/me/')
    .then(r => {
      objectPerms.value = r.data.object_permissions || {}
      sectionPerms.value = r.data.section_permissions || []
      systemGroups.value = r.data.system_groups || []
      roles.value = r.data.roles || []
    })
    .catch(() => {
      objectPerms.value = {}
      sectionPerms.value = []
      systemGroups.value = []
      roles.value = []
    })
    .finally(() => {
      loaded.value = true
      loadPromise = null
    })

  return loadPromise
}

/**
 * Reactive composable for components (v-if, :disabled, :class).
 * Fires ensurePerms() lazily on first call — no need to await in components.
 */
export function usePerms() {
  if (!loaded.value && !loadPromise) {
    ensurePerms()
  }

  return {
    objectPerms,
    sectionPerms,
    systemGroups,
    roles,

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
