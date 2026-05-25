// widget/router.js
// Клиентский hash-роутер. Без зависимостей, можно использовать в любом проекте.
//
// Схема URL:
//   #/                          — индекс (список каталогов)
//   #/{catalog}                 — страница раздела (model_lines)
//   #/{catalog}/catalog         — подбор по параметрам (список + фильтры)
//   #/{catalog}/detail/{id}     — карточка товара
//   #/{catalog}/brand/{id}      — витрина бренда

/**
 * Распарсить текущий hash в объект маршрута.
 * @returns {{ catalog: string, view: 'index'|'lines'|'list'|'detail'|'brand', id?: string }}
 */
export function parseHash() {
  const raw = window.location.hash.replace(/^#\/?/, '')
  if (!raw) return { view: 'index' }

  const parts = raw.split('/')
  const catalog = parts[0]

  if (!catalog) return { view: 'index' }

  // #/gearbox → страница серий
  if (parts.length === 1) return { catalog, view: 'lines' }

  // #/gearbox/catalog → каталог
  if (parts[1] === 'catalog') return { catalog, view: 'list' }

  // #/gearbox/detail/123 → карточка
  if (parts[1] === 'detail' && parts[2]) return { catalog, view: 'detail', id: parts[2] }

  // #/gearbox/brand/5 → бренд
  if (parts[1] === 'brand' && parts[2]) return { catalog, view: 'brand', id: parts[2] }

  return { catalog, view: 'lines' }
}

/**
 * Собрать hash-строку из параметров.
 * @param {'lines'|'list'|'detail'|'brand'} view
 * @param {string} catalog
 * @param {string|number} [id]
 */
export function makeHash(catalog, view, id) {
  if (view === 'lines') return `#/${catalog}`
  if (view === 'list') return `#/${catalog}/catalog`
  if (view === 'detail') return `#/${catalog}/detail/${id}`
  if (view === 'brand') return `#/${catalog}/brand/${id}`
  return '#/'
}

/**
 * Перейти на новый маршрут (меняет location.hash).
 */
export function navigate(catalog, view, id) {
  window.location.hash = makeHash(catalog, view, id)
}
