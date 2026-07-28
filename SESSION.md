# SESSION.md — 2026-07-28

## Где остановились

Фазы decompose + extract пайплайна работают. Конфигуратор пайплайна готов. Классификатор — 9 интентов. Хлебные крошки добавлены во все каталоги. Исправлены баги шаблонов фильтр-регуляторов. Поле `description` добавлено в API model_line всех каталогов.

## Ключевые изменения за сессию

- **Хлебные крошки** — добавлены во все 5 каталогов (БКВ, редукторы, фильтр-регуляторы, клапаны, фитинги) по единому образцу
- **CatalogModelLine** — заголовок «Серия {code}: {description}» вместо «Серия» + контекстный чип
- **EquipmentType.title_template** — добавлен в админку (секция «Шаблоны отображения»)
- **API model_line** — поле `description` добавлено во все `_get_model_line_summary()` и `SectionView`
- **FilterRegulator** — исправлены пути в `_get_data_dict()`: `pressure_min/max` → `model_line__*`, `body/bowl/protection_material` → `model_line__*`
- **Docker** — `.dockerignore` исправлен (BOM, root node_modules, tsconfig.json), `DOCKER_BUILDKIT=0` в `build-demo.ps1`
- **Management command** — `regenerate_filter_regulator_descriptions` для перегенерации описаний

---

## Концепция: каталог пневмоприводов

### Проблема

Сейчас пневмоприводы живут в двух изолированных инструментах:
- **Selector** (`/selector/pa`) — подбор по моменту, текстовый результат без карточек
- **Constructor** (`/admin/pa-constructor`) — сборка конфигурации из опций, отдельная таблица `PneumaticActuatorConstructor`

Ни один не интегрирован с каталогом. Карточек оборудования нет. SKU нет. Пользователь не может «открыть» результат подбора.

### Идея

Сделать каталог пневмоприводов по общему шаблону (как БКВ, редукторы, etc.), но карточка товара — с возможностью выбора опций (пружины, температура, IP, ExD и т.д.).

**Модель-основа** каталога — `PneumaticActuatorModelLineItem`:
- Уже имеет FK на `model_line`, `body`, `variety` (DA/SR)
- Уже связан с опциями через through-модели (`pa_options`)
- Не имеет SKU, не наследует `SKUMixin` ← нужно добавить

**Базовые конфигурации** (то, что идёт в каталог как «товар»):
- DA — двойного действия (без пружин)
- DA.LT — двойного действия, низкотемпературный
- SR с 12 пружинами — самая востребованная конфигурация

Остальные комбинации (8 пружин, 10 пружин, разные температуры) — только через опции на карточке. Отдельные SKU не создаются.

### Архитектура

```
PneumaticActuatorModelLine (серия)          ← как FilterRegulatorModelLine
  ├── name, code, description
  ├── equipment_type → «Пневмопривод»
  └── image_gallery, tech_docs, cert_docs

PneumaticActuatorModelLineItem (модель)     ← добавить SKUMixin + CatalogDictMixin
  ├── name, code, description
  ├── model_line, body, variety (DA/SR)
  ├── sku → синхронизируется при save()
  └── to_dict() → sections, template_vars, model_line, images

Опции (через through-модели — уже есть):
  ├── springs_qty (8, 10, 12, 14)
  ├── temperature (−40..+80, −60..+120)
  ├── safety_position (NC, NO)
  ├── ip (IP65, IP67)
  ├── exd (Exd IIC T6, ...)
  ├── body_coating
  └── hand_wheel
```

### Карточка товара (фронтенд)

```
┌─────────────────────────────────────────────┐
│ [хлебные крошки]                             │
├─────────────────────────────────────────────┤
│ [фото]   APM-SR-20                          │
│          Пневмопривод SR, четвертьоборотный  │
│          Момент: 200 Нм при 6 бар            │
│                                             │
│  Характеристики:                             │
│    Серия: APM-SR                            │
│    Бренд: Archimedes                        │
│    Тип: SR, пружинный возврат               │
│    Макс. момент: 200 Нм                     │
│                                             │
│  ── Опции ──                                │
│    Пружины: [8] [10] [12▾] [14]             │
│    Температура: [−40..+80 ▾]                │
│    Положение безопасности: [NC ▾] [NO]      │
│    IP: [IP65] [IP67 ▾]                     │
│    ExD: [Exd IIC T6 ▾]                     │
│    Покрытие: [стандарт ▾]                   │
│    Штурвал: [нет ▾]                         │
│                                             │
│  Код: APM-SR-20-12-NC-IP67                  │
│  SKU: PA-SR-20-12-NC-IP67                   │
│  Цена: по запросу                           │
└─────────────────────────────────────────────┘
```

При изменении опций — код и SKU пересчитываются на лету. Базовая конфигурация имеет фиксированный SKU в БД.

### Selector → каталог

Результаты селектора становятся ссылками на карточки каталога:
```
Результаты подбора:
  APM-SR-20  → /catalog/pa-actuators/APM-SR-20/
  APM-SR-30  → /catalog/pa-actuators/APM-SR-30/
```

Selector остаётся как инструмент подбора, но вместо текстового вывода — сетка карточек с кнопкой «Открыть».

### Constructor → каталог

Constructor остаётся для административного создания конфигураций. При сохранении:
- Создаётся/обновляется `PneumaticActuatorModelLineItem`
- `sync_sku()` создаёт SKU для базовой конфигурации
- Карточка сразу доступна в каталоге

---

## План действий

### Фаза 1: Бэкенд — SKU + CatalogMixin

- [ ] Добавить `SKUMixin` в `PneumaticActuatorModelLineItem`
  - `get_equipment_type_for_sku()` → `self.model_line.equipment_type`
  - `get_brand_for_sku()` → `self.model_line.brand`
- [ ] Добавить `CatalogDictMixin` (или `SmartCatalogMixin`) для `to_dict()`
- [ ] Реализовать `to_dict()` / `to_values_dict()` — sections, template_vars
- [ ] `_get_data_dict()` — плейсхолдеры для шаблонов
- [ ] Миграция: `sync_sku()` для существующих model_line_item
- [ ] `EquipmentType` «Пневмопривод» — `title_template`

### Фаза 2: Бэкенд — CatalogConfig + API

- [ ] `pneumatic_actuators/catalog/config.py` — `PA_CONFIG = CatalogConfig(...)`
- [ ] `pneumatic_actuators/catalog/filter_defs.py` — фильтры (момент, DA/SR, температура, ...)
- [ ] `pneumatic_actuators/catalog/views_list.py` — `PaCatalogView`
- [ ] `pneumatic_actuators/catalog/views_detail.py` — `PaDetailView`
- [ ] `pneumatic_actuators/catalog/views_filters.py` — `PaFilterOptionsView`
- [ ] `pneumatic_actuators/urls.py` — роуты `/pa-actuators/catalog/`, `/filters/`, etc.

### Фаза 3: Фронтенд — каталог

- [ ] `frontend/src/apps/pa-catalog/` — мини-приложение по шаблону
  - `index.html`, `main.js`, `App.vue`, `api.js`
- [ ] `frontend/src/shared/endpoints.js` — блок `paActuator`
- [ ] Компонент `PaProductCard` с селекторами опций
- [ ] Интеграция с `ProductDetail` или отдельный `PaDetail`
- [ ] `frontend/src/pages/catalog/PaActuatorPage.vue` — страница SPA
- [ ] Роут в `router/index.js`

### Фаза 4: Selector → каталог

- [ ] Выдача селектора — ссылки на карточки вместо текста
- [ ] Фронтенд: результат подбора как сетка ProductCard

### Фаза 5: Constructor → каталог

- [ ] `ConstructorViewSet.create()` — после сохранения возвращать URL карточки
- [ ] При сохранении конфигурации — создавать/обновлять model_line_item

---

## Что работает (из предыдущей сессии)

- Decompose + Extract пайплайна
- Pipeline Configurator (5 вкладок, CRUD)
- Классификатор (9 интентов)
- Прогресс-бар, логирование, маршрутизация
- 45 тестов, 15 миграций

## Что ещё не доделано

- [ ] Фазы 3-5 пайплайна (filter → select → compare)
- [ ] Decompose — анти-галлюцинационные правила
- [ ] Extract промпты — тестирование на реальных данных
- [ ] `mounting-kit` EquipmentType
- [ ] 8 AIQuerySample — разметка для регрессии
- [ ] Конфигураторы сборок арматуры + приводов
- [ ] Заявки клиентов (client_requests)
- [ ] Каталог пневмоприводов ← **в работе**
