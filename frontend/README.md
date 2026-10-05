# Frontend — структура проекта

Vue 3 + Vite. Мини-приложения в `src/apps/`, переиспользуемое в `src/shared/`.

> **Актуальный план миграции к полноценному сайту** (роутинг, auth, i18n RU/EN/ZH) —
> [`docs/migration-plan.md`](docs/migration-plan.md). Этот README описывает структуру кода.

## `src/shared/` — общие модули

| Путь | Назначение |
|------|-----------|
| `shared/config.js` | API_URL, API_PREFIX, флаг `debug` (теги компонентов) |
| `shared/api.js` | Axios-инстанс (CSRF, withCredentials, перехватчик ошибок) |
| `shared/endpoints.js` | Единый источник URL API для каталогов |
| `shared/components/AppButton.vue` | Кнопка (primary/secondary/ghost/danger, disabled) |
| `shared/components/Breadcrumbs.vue` | Хлебные крошки (to/router.push + emit navigate) |
| `shared/components/PageTitle.vue` | Заголовок страницы (title + subtitle + context-чип) |
| `shared/components/ProductCard.vue` | Карточка товара с картинкой и ценой |
| `shared/components/ProductGallery.vue` | Галерея изображений с лайтбоксом |
| `shared/components/ProductDetail.vue` | Детальная карточка (JsonLd + Gallery + Header + Tabs) |
| `shared/components/FilterSidebar.vue` | Сайдбар фильтров (select / ExdFilter / ClimateFilter / совместимые). temp_min/max скрыты если есть ClimateFilter |

## `src/shared/components/catalog/` — компоненты каталогов

| Компонент | Назначение |
|-----------|-----------|
| `CatalogActions.vue` | Табы-переключатели режимов: Просмотр по сериям / Инженерный / Быстрый / Мастер / AI. Пропс `active` |
| `CatalogSection.vue` | Сетка серий (карточки: «Серия ИМЯ» + описание). Только `selectSeries`, `navigate` |
| `CatalogModelLine.vue` | Товары серии. Заголовок: «Серия {code}: {description}». Пропс `parentMode` |
| `CatalogDetail.vue` | Карточка товара через `ProductDetail`. Пропс `parentMode` |
| `CatalogList.vue` | Инженерный подбор с `FilterSidebar` + `ProductCard` |
| `EngineerSelection.vue` | Инженерный подбор с `EngineerFilterBar` + `EngineerProductCard` |
| `QuickSelect.vue` | Быстрый подбор (чипсы → карточка). Defaults и labels из API (`data.defaults`, `data.filter_labels`). Стратегии: `first`, `min`, `max` |
| `WizardPlaceholder.vue` | Заглушка «Мастер подбора» (Breadcrumbs + PageTitle + текст) |
| `AiPlaceholder.vue` | Заглушка «AI подбор» |
| `CatalogBrand.vue` | Товары бренда (не используется в новых каталогах) |
| `EngineerFilterBar.vue` | Горизонтальная панель фильтров для `EngineerSelection` |
| `EngineerProductCard.vue` | Горизонтальная карточка товара для `EngineerSelection` |
| `PaQuickSelect.vue` | Конфигуратор пневмоприводов: серия→DA/SR→модель (чипсы) + опции (дропдауны) → `PaProductCard` |
| `PaProductCard.vue` | Карточка пневмопривода: `ProductDetail` + [Добавить в корзину] [Просмотр спецификации] |

### Архитектура каталога (2026-07-28)

Каждый каталог — SPA внутри `App.vue`. Управляется через `useCatalogRouter`:

```
App.vue
├── <Breadcrumbs />          ← всегда видно, computed из page + parentMode
├── <CatalogActions />       ← всегда видно, табы режимов
├── <CatalogSection />       ← v-if="page === 'section'"
├── <EngineerSelection />    ← v-else-if="page === 'list'"
├── <CatalogModelLine />     ← v-else-if="page === 'brand'"
├── <CatalogDetail />        ← v-else-if="page === 'detail'"
├── <QuickSelect />          ← v-else-if="page === 'quickselect'"
├── <WizardPlaceholder />    ← v-else-if="page === 'wizard'"
└── <AiPlaceholder />        ← v-else-if="page === 'ai'"
```

7 состояний страницы. `parentModeName` отслеживает текущий/предыдущий режим.

### Хлебные крошки

Вынесены в `App.vue` (единый `<Breadcrumbs>` над табами). Формат:

| Страница | Крошки |
|----------|--------|
| Просмотр по сериям | `🏠 Каталог` → `Оборудование` → `Просмотр по сериям` |
| Инженерный подбор | `🏠 Каталог` → `Оборудование` → `Инженерный подбор` |
| Серия УРАЛ | `🏠 Каталог` → `Оборудование` → `Просмотр по сериям` → `УРАЛ` |
| Карточка товара | `🏠 Каталог` → `Оборудование` → `{режим}` → `товар` |

`🏠` = `{ to: '/' }` → router.push. Средние крошки → `emit('navigate')` → `goToSection()`.

### Ширина страниц

Все страницы каталога: `max-width: 1200px; margin: 0 auto` (единообразно, без дёрганья при переключении).

### Debug-теги

`<span class="debug-tag">ComponentName</span>` — видны только при `debug=true` в `shared/config.js`. Флаг выставляется в корневом `App.vue` через `setDebug(import.meta.env.DEV)`. Мини-аппы не импортируют `App.vue` → `debug=false` → теги скрыты.

### `parentMode`

Пропс в `CatalogModelLine` и `CatalogDetail` — имя родительского режима для хлебных крошек. По умолчанию `'Просмотр по сериям'`.

## `src/apps/` — мини-приложения (каталоги)

Каталоги:
- `gearbox-catalog` — редукторы (ручные дублёры)
- `filter-regulator-catalog` — фильтр-регуляторы
- `solenoid-valves-catalog` — соленоидные клапаны
- `pneumatic-fittings-catalog` — фитинги (резьба-трубка)
- `pneumatic-plugs-catalog` — заглушки пневматические
- `pneumatic-silencers-catalog` — глушители пневматические
- `limit-switch-catalog` — блоки концевых выключателей (БКВ)
- `cable-gland-catalog` — кабельные вводы
- `pa-catalog` — пневмоприводы

Конструкторы:
- `pa-constructor` (+ легаси `pa-constructor-legacy`) — пневмоприводы
- `ea-constructor` — электроприводы
- `cg-constructor` — кабельные вводы
- `posi-constructor` — позиционеры

Сервисы и админки:
- `price-catalog` — цены и документы
- `media-library` — медиабиблиотека
- `cert-docs` — сертификаты
- `sku-admin` — SKU
- `limit-switch-admin` — админка БКВ
- `ea-admin`, `ea-model-admin`, `ea-wiring-admin`, `ea-switches-admin` — админки электроприводов
- `requests` — заявки клиентов
- `assemblies` — сборки арматуры с приводом

Портал/партнёры:
- `widget` — виджет для партнёров

Standalone-сборка (`vite.config.js → rollupOptions.input`, свой `index.html`): 17 приложений.
SPA-only (обёртки `src/pages/catalog/*`, без собственного входа в сборке):
`pneumatic-fittings/plugs/silencers-catalog`, `requests`, `assemblies`, `ea-model/wiring/switches-admin`.

Структура каждого каталога:
```
apps/xxx-catalog/
├── index.html    ← точка входа Vite
├── main.js       ← createApp + import default.css
├── App.vue       ← роутер страниц + Breadcrumbs + CatalogActions
└── api.js        ← API-клиент → shared/endpoints.js
```

---

## `src/pages/` — страницы SPA (роутер)

### Каталоги

| Файл | Маршрут |
|------|---------|
| `pages/catalog/LimitSwitchPage.vue` | `/catalog/limit-switch` |
| `pages/catalog/GearboxPage.vue` | `/catalog/gearbox` |
| `pages/catalog/FilterRegulatorPage.vue` | `/catalog/filter-regulator` |
| `pages/catalog/SolenoidValvesPage.vue` | `/catalog/solenoid-valves` |
| `pages/catalog/PneumaticFittingsPage.vue` | `/catalog/pneumatic-fittings` |

Каждая — тонкая обёртка над мини-приложением: `<LimitSwitchCatalogApp />`.

## Shared-компоненты UI (общие)

- `PageTitle` — заголовок страницы (title + subtitle + context-чип)
- `Breadcrumbs` — все непоследние крошки кликабельны (to/router.push или emit navigate)
- `FilterSidebar` — сайдбар фильтров + чекбокс «Показывать совместимые», 1 опция → `<span>`
- `ProductCard` — карточка товара
- `ProductDetail` — оркестратор карточки (JsonLd + Gallery + Header + Tabs)
- `ProductGallery` — галерея с лайтбоксом
- `ExdFilter` — каскадный фильтр взрывозащиты
- `ClimateFilter` — каскадный фильтр климатического исполнения

### ClimateFilter — каскадный фильтр климатического исполнения

- Селекты: климатическая зона (У, ХЛ, УХЛ…) + категория размещения (1–5)
- Ручной ввод температуры с debounce 400ms (не шлёт запрос на каждом символе)
- Незаполненные поля не эмитятся (было `Number(null) = 0`)
- Текстовое поле парсинга: `УХЛ4` → автозаполнение через `POST /api/core/climate/parse/`
- Если `fd_climate` (climate_cascade) есть в FilterSet → temp_min/temp_max-селекты скрыты

## `src/components/` — общие компоненты SPA

| Путь | Назначение |
|------|-----------|
| `components/header/Header.vue` | Шапка (лого, меню, пользователь) |
| `components/header/TopMenu.vue` | Верхнее меню (ролевая модель: admin/user) |
| `components/header/useAuth.js` | Composable: /auth/me/, роль, загрузка |

## AI Assistant (`src/pages/`)

| Файл | Назначение |
|------|-----------|
| `pages/AiDebugPage.vue` | Отладка decompose |
| `pages/AiAssistantPage.vue` | Пользовательский интерфейс AI-подбора |
| `pages/admin/PipelineConfigPage.vue` | Конфигуратор pipeline: 5 вкладок, CRUD |

Роуты: `/ai-assistant`, `/ai-debug`, `/admin/pipeline-config`.

## `src/router/index.js`

Все маршруты. `meta.role = 'admin'` для администрирования. `beforeEach` — проверка `/api/auth/me/`.

## Конструктор пневмоприводов (`src/apps/pa-constructor/`)

Пошаговый wizard (`App.vue`; легаси-версия — `App_legacy.vue`, вход `index_legacy.html`).

## Медиафайлы

Все изображения/PDF через Django API → presigned URL Cloud.ru (SigV4). Подробнее: `media_library/README.md`.
