# limit-switch-catalog — Блоки концевых выключателей

Vue 3 мини-приложение. 4 страницы: серии, список с фильтрами, карточка товара, товары серии.

## Файлы

| Файл | Назначение |
|------|-----------|
| `index.html` | Точка входа Vite |
| `main.js` | Монтирование + импорт темы `default.css` |
| `App.vue` | Роутер страниц (section / list / detail / brand) |
| `api.js` | API-клиент → `/api/pa-controls/` |
| `components/LsbSection.vue` | Сетка серий (группировка по model_line) |
| `components/LsbList.vue` | Список с фильтрами (поиск, серия, сенсор, бренд) |
| `components/LsbDetail.vue` | Карточка через shared `ProductDetail` |
| `components/LsbBrand.vue` | Товары одной серии |

## API

| Метод | URL | Ответ |
|-------|-----|-------|
| `list(params)` | `GET /api/pa-controls/catalog/` | `{data, total, filters_applied}` |
| `getDetail(id)` | `GET /api/pa-controls/catalog/<id>/` | `{sections, template_vars, model_line, ...}` |
| `getFilters()` | `GET /api/pa-controls/filters/` | `{model_line_id: [...], sensor_variety_id: [...], ...}` |
| `getMeta()` | `GET /api/pa-controls/meta/` | `{field_key: {label, group, unit, type}}` |

## Стилизация

Все компоненты используют CSS-переменные `--cat-*` из `shared/themes/default.css`.
Тема подключается в `main.js`: `import '@/shared/themes/default.css'`.

## Сборка

Добавлен в `vite.config.js` → `rollupOptions.input` как `'limit-switch-catalog'`.
Dev: `npm run dev` → `/src/apps/limit-switch-catalog/index.html`.

## Меню

В `TopMenu.vue`: ⚙️ Настройки → 🔌 Блоки концевых выключателей.
В `CatalogIndex.vue`: карточка в виджете.
