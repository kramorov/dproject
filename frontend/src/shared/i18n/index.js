// shared/i18n/index.js — лёгкая мультиязычность (без внешних зависимостей).
// Реактивная локаль + словари ru/en/zh. Локаль хранится в localStorage и
// отражается в URL-префиксе (/en/..., /zh/...), который разбирает router.

import { ref } from 'vue'
import { messages } from './locales'

export const LOCALES = ['ru', 'en', 'zh']
export const DEFAULT_LOCALE = 'ru'

function detectInitialLocale() {
  try {
    const saved = localStorage.getItem('locale')
    if (saved && LOCALES.includes(saved)) return saved
    const nav = (navigator.language || '').toLowerCase()
    if (nav.startsWith('zh')) return 'zh'
    if (nav.startsWith('en')) return 'en'
  } catch (e) { /* SSR/инкогнито */ }
  return DEFAULT_LOCALE
}

const locale = ref(detectInitialLocale())

export function setLocale(l) {
  if (!LOCALES.includes(l)) return
  locale.value = l
  try { localStorage.setItem('locale', l) } catch (e) { /* ignore */ }
  if (typeof document !== 'undefined') {
    document.documentElement.lang = l === 'zh' ? 'zh-CN' : l
  }
}

export function getLocale() {
  return locale.value
}

/**
 * Переводит ключ (или возвращает строку как есть, если ключа нет в словарях —
 * это позволяет прогрессивно переводить UI без отдельной миграции строк).
 */
export function t(key, params) {
  const dict = messages[locale.value] || messages[DEFAULT_LOCALE]
  const msg = dict[key] ?? messages[DEFAULT_LOCALE][key] ?? key
  if (typeof msg === 'string' && params) {
    return msg.replace(/\{(\w+)\}/g, (_, k) => (params[k] ?? ''))
  }
  return msg
}

export function useI18n() {
  return { locale, t, setLocale, getLocale, LOCALES, DEFAULT_LOCALE }
}

// '/en/catalog/gearbox' → '/catalog/gearbox'; '/en' → '/'; без префикса → как есть.
export function stripLocalePrefix(path) {
  const p = path || '/'
  for (const l of ['en', 'zh']) {
    if (p === `/${l}`) return '/'
    if (p.startsWith(`/${l}/`)) return p.slice(l.length + 1)
  }
  return p
}

// localizedPath('/catalog/x', 'en') → '/en/catalog/x'; для 'ru' — без префикса.
export function localizedPath(path, l) {
  if (!l || l === DEFAULT_LOCALE) return stripLocalePrefix(path)
  const p = stripLocalePrefix(path)
  return p === '/' ? `/${l}` : `/${l}${p}`
}
