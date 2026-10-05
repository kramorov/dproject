// shared/composables/useCatalogRoute.js
// Проецирует конечный автомат каталога (section/list/brand/detail/quickselect/wizard/graph/ai)
// на URL, чтобы работали браузерные «назад/вперёд», глубокие ссылки и бредкрамбы из маршрута.
// SPA — через vue-router (query-параметры); standalone/embed — через location.hash.

import { ref, computed, watch, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const MODE_TO_PAGE = {
  section: 'section',
  engineer: 'list',
  quickselect: 'quickselect',
  wizard: 'wizard',
  graph: 'graph',
  ai: 'ai',
}

/**
 * @param {Object} [opts]
 * @param {string} [opts.modeParam='mode']   query-параметр режима (section|engineer|quickselect|wizard|graph|ai)
 * @param {string} [opts.mlParam='ml']       query-параметр id серии (model line)
 * @param {string} [opts.itemParam='item']   query-параметр id товара
 * @param {string} [opts.fromParam='from']   query-параметр родительского режима (для бредкрамбов на detail)
 */
export function useCatalogRoute(opts = {}) {
  const {
    modeParam = 'mode',
    mlParam = 'ml',
    itemParam = 'item',
    fromParam = 'from',
  } = opts

  let router = null
  let route = null
  try {
    router = useRouter()
    route = useRoute()
  } catch (e) {
    // standalone/embed: vue-router не установлен → используем location.hash
  }
  const isSpa = !!(router && typeof router.push === 'function')

  function read() {
    if (isSpa) {
      const q = route.query || {}
      return {
        mode: q[modeParam] || 'section',
        ml: q[mlParam] || null,
        item: q[itemParam] || null,
        from: q[fromParam] || null,
      }
    }
    const raw = typeof window !== 'undefined' ? (window.location.hash || '').replace(/^#/, '') : ''
    const p = new URLSearchParams(raw)
    return {
      mode: p.get(modeParam) || 'section',
      ml: p.get(mlParam) || null,
      item: p.get(itemParam) || null,
      from: p.get(fromParam) || null,
    }
  }

  const state = ref(read())

  function write(patch) {
    if (isSpa) {
      const query = { ...(route.query || {}) }
      for (const [k, v] of Object.entries(patch)) {
        if (v === null || v === undefined || v === '') delete query[k]
        else query[k] = v
      }
      router.push({ path: route.path, query }).catch(() => { /* дублирующая навигация (тот же таб) — игнорируем */ })
    } else if (typeof window !== 'undefined') {
      const p = new URLSearchParams((window.location.hash || '').replace(/^#/, ''))
      for (const [k, v] of Object.entries(patch)) {
        if (v === null || v === undefined || v === '') p.delete(k)
        else p.set(k, v)
      }
      window.location.hash = p.toString()
    }
  }

  if (isSpa) {
    watch(() => route.fullPath, () => { state.value = read() })
  } else if (typeof window !== 'undefined') {
    const onHash = () => { state.value = read() }
    window.addEventListener('hashchange', onHash)
    onUnmounted(() => window.removeEventListener('hashchange', onHash))
  }

  const page = computed(() => {
    const { item, ml, mode } = state.value
    if (item) return 'detail'
    if (ml) return 'brand'
    return MODE_TO_PAGE[mode] || 'section'
  })
  const selectedId = computed(() => state.value.item)
  const idValue = computed(() => state.value.ml)
  const fromPage = computed(() => state.value.from || 'section')

  function setMode(mode) {
    write({ [modeParam]: mode, [mlParam]: null, [itemParam]: null, [fromParam]: null })
  }
  function goToSection() { setMode('section') }
  function goToEngineer() { setMode('engineer') }
  function goToList() { goToEngineer() }
  function goToQuickSelect() { setMode('quickselect') }
  function goToWizard() { setMode('wizard') }
  function goToGraph() { setMode('graph') }
  function goToAi() { setMode('ai') }
  function goToBrand(id) {
    write({ [modeParam]: 'section', [mlParam]: id, [itemParam]: null, [fromParam]: null })
  }
  function onSelectItem(id, from) {
    write({ [itemParam]: id, [fromParam]: from || 'section' })
  }
  function closeDetail() {
    write({ [itemParam]: null, [fromParam]: null })
  }

  return {
    page, selectedId, idValue, fromPage, isSpa, router,
    goToSection, goToList, goToEngineer, goToBrand, goToQuickSelect, goToWizard, goToGraph, goToAi,
    onSelectItem, closeDetail,
  }
}
