// src/shared/config.js
export const API_URL = ''
export const API_PREFIX = '/api'

// Debug tags ("CatalogSection", etc.) — only visible in dev mode via main App.vue.
// Mini-apps (standalone builds) don't import App.vue, so this stays false for partners.
export let debug = false
export function setDebug(v) { debug = v }
