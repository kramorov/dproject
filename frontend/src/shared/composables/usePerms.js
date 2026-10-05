// shared/composables/usePerms.js
// Переиспользует единый auth-store (src/shared/stores/auth.js).
// Имена ensurePerms/usePerms сохранены для совместимости с router/index.js.
export { ensureAuth as ensurePerms, useAuth as usePerms } from '@/shared/stores/auth'
