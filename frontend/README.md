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
| `shared/components/FilterSidebar.vue` | Боковая панель фильтров |
| `shared/components/Breadcrumbs.vue` | Хлебные крошки |
| `shared/components/Spinner.vue` | Индикатор загрузки |
| `shared/components/MediaViewer.vue` | Просмотрщик медиафайлов (изображения/PDF) |
| `shared/components/M2MDualList.vue` | M2M-селектор filter_horizontal (две панели + поиск) |
| `shared/components/JsonFieldsEditor.vue` | Редактор JSON extra_params (таблица + raw JSON) |
| `shared/components/MediaUploadModal.vue` | Модалка загрузки файла в медиатеку |
| `shared/components/BasePicker.vue` | Модальный подбор (fetchFn, filterDefs, columns) |
| `shared/components/ChipList.vue` | Таблица code+name с чекбоксами и batch-удалением |
| `shared/components/FkSelect.vue` | Выбор ForeignKey с поиском |
| `shared/components/M2MSelect.vue` | Выбор ManyToMany с чипсами |
| `shared/components/catalog/CatalogSection.vue` | Страница серий (grid карточек) |
| `shared/components/catalog/CatalogList.vue` | Каталог с фильтрами и пагинацией |
| `shared/components/catalog/CatalogBrand.vue` | Витрина бренда |
| `shared/components/catalog/CatalogDetail.vue` | Карточка товара |
| `shared/components/catalog/QuickSelect.vue` | Быстрый подбор (чипсы → карточка) |
| `shared/composables/useCatalog.js` | Логика каталогов (fetchData, пагинация, фильтры) |
| `shared/composables/useCatalogRouter.js` | Навигация App.vue каталогов |
| `shared/themes/default.css` | CSS Custom Properties (тема по умолчанию) |

## `src/apps/` — мини-приложения

### Каталоги (для виджета)
| Приложение | API |
|-----------|-----|
| `gearbox-catalog/` | /api/gearbox/ |
| `filter-regulator-catalog/` | /api/filter-regulator/ |
| `limit-switch-catalog/` | /api/pa-controls/ |

Все каталоги используют Generic-компоненты из shared/components/catalog/.
App.vue параметризуется через `labels` + `api`. 13 старых компонентов удалены.

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
