# План миграции фронта → полноценный сайт

Дата: 2026-10-05. Документ фиксирует согласованные решения и фазы работ.

## Зафиксированные решения

1. **Стратегия локали**: префикс в URL — `/en/...`, `/zh/...` (RU — дефолт без префикса).
2. **GraphQL**: заморожен. Живём на REST (DRF). Схема `djangoProject1/graphql_api/` не подключается
   к `urls.py`, путь в `settings.GRAPHENE['SCHEMA']` не чиним и не используем.
3. **Переводы данных**: да — каталоги переводятся (не только UI). Хранение переводов решаем в Фазе 4.
4. **SSR (Nuxt)**: на паузе. Остаёмся на SPA (Vue 3 + Vite + vue-router), чтобы сайт и портабельные
   мини-приложения работали единообразно. Пустой `nuxt-app/` не развиваем.

## Текущее состояние (факты на 2026-10-05)

Две параллельные точки входа одного и того же каталога:

- **SPA-оболочка**: `src/main.js → App.vue → router/index.js`. Header (TopMenu, GlobalSearch,
  корзина, избранное, вход), ~80 маршрутов (каталоги, конфигураторы, админка, инструменты).
- **Мини-приложения** `src/apps/*` (24+): `gearbox-catalog`, `filter-regulator-catalog`,
  `limit-switch-catalog`, `solenoid-valves-catalog`, `pneumatic-fittings/plugs/silencers-catalog`,
  `cable-gland-catalog`, `pa-catalog`, `price-catalog`, `media-library`, `cert-docs`,
  `pa/ea/cg/posi-constructor`, `ea-admin`, `ea-model-admin`, `ea-wiring-admin`, `ea-switches-admin`,
  `sku-admin`, `requests`, `assemblies`, `widget`.
  Каждый может собираться standalone (`vite.config.js → rollupOptions.input`) для переноса/виджета.
- **Общий слой** `src/shared/`: `api.js` (axios+CSRF+withCredentials), `endpoints.js` (карта REST-URL),
  composables (`useCatalogRouter`, `useCatalogWizard`, `usePerms`, `useCatalogMeta`),
  UI-компоненты (`Breadcrumbs`, `CatalogActions`, `FilterSidebar`, `ProductDetail`, …).

## Диагноз четырёх проблем

1. **Не работают переходы назад + кривые бредкрамбы** — одна причина: каталоги — конечный автомат
   в памяти (`useCatalogRouter.page` = section/list/brand/detail/quickselect/wizard/ai), в `history`
   ничего не пишется. Бредкрамбы считаются из этого состояния и эмитят `navigate` вместо
   `router.push`. Нет глубоких ссылок на товар/серию/режим.
2. **Странный логин + нет сохранения пароля** — вход через axios JSON-POST (XHR) вместо нативного
   submit формы → менеджер паролей не ловит успешный логин; после входа `window.location.href='/`
   (полная перезагрузка), потому что состояние auth — несвязанные модульные синглтоны.
3. **Мультиязычность отсутствует** — нет vue-i18n, все строки захардкожены по-русски.

## Целевая архитектура

- Каталог = настоящий маршрут SPA с параметрами; URL управляет состоянием; бредкрамбы из маршрута.
- Портабельное мини-приложение = тот же `apps/xxx/App.vue`, но слой истории подменяется
  (vue-router в SPA, hash-история в embed). Компоненты/API/i18n общие.
- Единый реактивный auth-store (один `/auth/me/`, логин/логаут без перезагрузки).
- i18n: vue-i18n + пакеты `ru/en/zh`; префикс локали `/en/`, `/zh/`; `Accept-Language` в API.

## Фазы

- **Фаза 0 — гигиена**: починить `services/axios.js` (dummy Authorization), убрать мёртвый `Auth.vue`,
  актуализировать README, зафиксировать заморозку GraphQL.
- **Фаза 1 — фундамент auth**: единый store, нативный логин/регистрация, логаут без reload,
  редирект на `?next=`.
- **Фаза 2 — URL-каталоги**: `useCatalogRoute`, маршрут-контракт, бредкрамбы из маршрута.
  Пилот — один каталог, затем тиражирование.
- **Фаза 3 — i18n UI-хрома**: vue-i18n, пакеты ru/en/zh, переключатель в шапке, стратегия локали,
  `Accept-Language`.
- **Фаза 4 — i18n данных**: хранение переводов + отдача локализованных меток/описаний, наполнение.
- **Фаза 5 — паритет мини-приложений**: standalone-сборки делят компоненты/i18n/роутинг-шим.
- **Фаза 6 — закалка**: SEO, код-сплит, визуальный QA, тесты.

## Открытые вопросы

- Хранение переводов данных (поля-переводы vs таблицы переводов vs внешний слой) — решить в Фазе 4.
- Авто-выбор локали по `Accept-Language` при первом заходе — подтвердить.
