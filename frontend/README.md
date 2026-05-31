# Frontend — структура проекта

Vue 3 + Vite. Мини-приложения в `src/apps/`, переиспользуемое в `src/shared/`.

## `src/shared/` — общие модули

| Путь | Назначение |
|------|-----------|
| `shared/config.js` | API_URL, API_PREFIX |
| `shared/api.js` | Axios-инстанс (CSRF, withCredentials, перехватчик ошибок) |
| `shared/endpoints.js` | Единый источник URL API для каталогов |
| `shared/components/AppButton.vue` | Кнопка (primary/secondary/ghost/danger, disabled) |
| `shared/components/ProductCard.vue` | Карточка товара с картинкой и ценой |
| `shared/components/ProductGallery.vue` | Галерея изображений с лайтбоксом |
| `shared/components/ProductDetail.vue` | Детальная карточка (секции specs/docs/certs) |
| `shared/components/FilterSidebar.vue` | Боковая панель фильтров + чекбокс «Показывать совместимые» |
| `shared/components/Breadcrumbs.vue` | Хлебные крошки |
| `shared/components/Spinner.vue` | Индикатор загрузки |
| `shared/components/PageTitle.vue` | Заголовок страницы (title + context-чип) |
| `shared/components/catalog/CatalogActions.vue` | Кнопки «Инженерный/Быстрый подбор» |
| `shared/components/MediaViewer.vue` | Просмотрщик медиафайлов (изображения/PDF) |
| `shared/components/ImageCropper.vue` | Интерактивная обрезка: drag/зум, фон/rembg, профили |
| `shared/components/M2MDualList.vue` | M2M-селектор filter_horizontal (две панели + поиск) |
| `shared/components/JsonFieldsEditor.vue` | Редактор JSON extra_params (таблица + raw JSON) |
| `shared/components/MediaUploadModal.vue` | Модалка загрузки файла в медиатеку |
| `shared/components/BasePicker.vue` | Модальный подбор (fetchFn, filterDefs, columns) |
| `shared/components/ChipList.vue` | Таблица code+name с чекбоксами и batch-удалением |
| `shared/components/FkSelect.vue` | Выбор ForeignKey с поиском |
| `shared/components/M2MSelect.vue` | Выбор ManyToMany с чипсами |
| `shared/components/catalog/CatalogSection.vue` | Сетка серий + CatalogActions |
| `shared/components/catalog/CatalogList.vue` | Инженерный подбор (фильтры + поиск + exact/compatible секции) |
| `shared/components/catalog/CatalogModelLine.vue` | Товары серии (fixedParams + context + exact/compatible секции) |
| `shared/components/catalog/CatalogDetail.vue` | Карточка товара |
| `shared/components/catalog/QuickSelect.vue` | Быстрый подбор (чипсы → карточка) |
| `shared/composables/useCatalog.js` | Логика каталогов: fetchData, пагинация, фильтры, exact/compatible split |
| `shared/composables/useCatalogRouter.js` | Навигация App.vue каталогов |

### `useCatalog.js` — поля и методы

```javascript
const {
  // State
  items,                // точные совпадения (или все, если split выключен)
  compatibleData,       // совместимые (только при showCompatible=true)
  total,                // общее количество до пагинации
  exactTotal,           // exact_count на текущей странице
  compatibleTotal,      // compatible_count на текущей странице
  splitFilter,          // по какому фильтру разделение
  loading, limit, offset,

  // Filters
  filterData,           // reactive: { param_name: { label, order, options } }
  filtersLoaded,
  showCompatibleAvailable,  // true если бэкенд поддерживает split
  showCompatible,       // состояние чекбокса
  activeFilters,        // { param_name: selectedValue }
  search,

  // Actions
  loadFilters(),        // GET /filters/?scope=...
  fetchData(),          // GET /catalog/ с фильтрами
  onFilterChange(key, value),
  toggleCompatible(val), // включить/выключить split
  resetFilters(),
  onSearchInput(),
  goPage(n),
} = useCatalog(api, {
  fixedParams,          // { model_line_id: 10 }
  filterScope: 'model_line',  // ?scope=model_line для страницы серии
  withSearch: true,
})
```

### FilterSidebar — «Показывать совместимые»

Чекбокс виден когда `showCompatibleAvailable=true` (бэкенд вернул `show_compatible: true` в ответе `/filters/`).
При включении отправляет `show_compatible=true` → бэкенд разделяет ответ на `data` (exact) и `compatible_data`.

### ⚠️ api.js: getFilters ДОЛЖЕН принимать params

```javascript
// Правильно:
getFilters(params) { return api.get(E.filters, { params }) }

// Неправильно (params игнорируются → scope не доходит до бэкенда):
getFilters() { return api.get(E.filters) }
```

## `src/apps/` — мини-приложения

### Каталоги (для виджета)
| Приложение | API |
|-----------|-----|
| `gearbox-catalog/` | /api/gearbox/ |
| `filter-regulator-catalog/` | /api/filter-regulator/ |
| `limit-switch-catalog/` | /api/pa-controls/ |

Все каталоги используют Generic-компоненты из shared/components/catalog/.
App.vue параметризуется через `labels` + `api`.

### Админка
| Приложение | API | Страница SPA |
|-----------|-----|-------------|
| `media-library/` | /api/media/, /api/core/ | /admin/media |
| `cert-docs/` | /api/admin/certs/ | /admin/cert-docs |
| `price-catalog/` | /api/admin/prices/ | /admin/price |
| `sku-admin/` | /api/admin/sku/ | /admin/sku |
| `limit-switch-admin/` | /api/core/ + /api/pa-controls/ | /admin/limit-switch |

### Виджет
| Приложение | Назначение |
|-----------|-----------|
| `widget/` | Клиентский hash-роутер для встраивания на сайты партнёров |

## `src/pages/` — страницы SPA

| Путь | Маршрут | Назначение |
|------|---------|-----------|
| `pages/HomePage.vue` | / | Главная |
| `pages/catalog/GearboxPage.vue` | /catalog/gearbox | Ручные дублёры |
| `pages/catalog/FilterRegulatorPage.vue` | /catalog/filter-regulator | Фильтр-регуляторы |
| `pages/catalog/LimitSwitchPage.vue` | /catalog/limit-switch | Блоки концевых выключателей |
| `pages/auth/LoginMainPage.vue` | /login | Вход |
| `pages/auth/RegisterMainPage.vue` | /register | Регистрация (заглушка) |
| `pages/admin/MediaPage.vue` | /admin/media | Медиабиблиотека |
| `pages/admin/CertDocsPage.vue` | /admin/cert-docs | Сертификаты |
| `pages/admin/PriceCatalogPage.vue` | /admin/price | Цены |
| `pages/admin/SkuAdminPage.vue` | /admin/sku | Номенклатура |
| `pages/admin/WidgetsPage.vue` | /widgets | Виджеты |
| `pages/ImageProcessorTest.vue` | /tools/image-processor | Тест обработки изображений и PDF (профили) |

## `src/components/` — общие компоненты SPA

| Путь | Назначение |
|------|-----------|
| `components/header/Header.vue` | Шапка (лого, меню, пользователь) |
| `components/header/TopMenu.vue` | Верхнее меню (ролевая модель: admin/user) |
| `components/header/useAuth.js` | Composable: /auth/me/, роль, загрузка |

## `src/router/index.js`

Все маршруты. Роли: `meta.role = 'admin'` для страниц администрирования.
`beforeEach` — проверка роли через `/api/auth/me/`.

## `src/services/`

| Путь | Назначение |
|------|-----------|
| `services/api.js` | Axios-инстанс + доменные API |
| `services/axios.js` | Плагин axios для Options API |

## Медиафайлы — как работает

Все изображения/PDF проходят через Django API:
- `<img src="/api/media/{id}/view/">` → Django MediaPreviewView
- `MEDIA_SERVE_MODE = 'redirect'` → 302 на presigned URL Cloud.ru
- Presigned URL содержит tenant_id в `X-Amz-Credential` (SigV4)
- Браузер качает напрямую с Cloud.ru, минуя Django

Подробнее о проблемах Cloud.ru и опробованных решениях — в `media_library/README.md`.
