# Selection Wizard (Мастер подбора) — концепция и архитектура

> Создано 2026-07-30.  
> Описывает бэкенд и фронтенд мастера пошагового подбора оборудования.

---

## 1. Концепция

Мастер подбора — пошаговый wizard на странице каталога. Пользователь проходит
последовательность шагов (страниц), на каждом выбирает значения фильтров
(radio-группы «один из нескольких»), и на последнем шаге получает
пагинированный список подходящих моделей оборудования.

Отличие от инженерного подбора (`EngineerSelection`):
- Инженерный подбор: выпадающие списки, коды/названия опций.
- Мастер подбора: radio-кнопки, **название + описание** каждой опции.

Отличие от конструктора (`actuator_constructor_pattern.md`):
- Конструктор: сборка новой конфигурации (SKU) из ограниченного набора through-опций.
- Мастер: фильтрация существующих моделей из каталога.

---

## 2. Модели данных

### 2.1 `SelectionWizard` (`core/models/selection_wizard.py`)

```python
class SelectionWizard(BaseAbstractModel):
    equipment_type = FK(EquipmentType, CASCADE, related_name='selection_wizards')
    steps_json = JSONField(default=dict)
```

**`steps_json`** — JSON из двух секций:

```json
{
  "pages": [
    {"step_number": 1, "title": "Заголовок шага", "description": "Описание"},
    {"step_number": 2, ...}
  ],
  "filters": [
    {
      "param_name": "sensor_variety_id",
      "page": 1,
      "order": 1,
      "label": "Тип сенсора",
      "default_value": null
    },
    ...
  ]
}
```

- **`pages`** — шаги мастера: номер, заголовок, описание.
- **`filters`** — фильтры: ссылка на `param_name` из `FILTER_DEFINITIONS` модели,
  номер шага (`page`), порядок (`order`), заголовок для UI (`label`),
  значение по умолчанию (`default_value`).

Метод `get_steps()` группирует фильтры по `page`, сортирует внутри по `order`,
и возвращает список шагов в формате, готовом для фронтенда:
```python
[
  {
    "step_number": 1,
    "title": "...",
    "description": "...",
    "filters": [{"param_name": "...", "label": "...", ...}, ...]
  },
  ...
]
```

### 2.2 `EquipmentType.active_selection_wizard`

```python
class EquipmentType(BaseAbstractModel):
    active_selection_wizard = FK(SelectionWizard, SET_NULL, null=True,
                                 related_name='equipment_types')
```

Один EquipmentType может иметь один активный мастер. Связь через
`active_selection_wizard` — именно её проверяет API при запросе конфигурации.

### 2.3 `FilterDefinition` (`core/models/filter_definition.py`)

Декларативное описание одного фильтра. Существует в двух местах:
1. **На классе модели** — `LimitSwitchBox.FILTER_DEFINITIONS = [...]`
2. **В catalog/filter_defs.py** — `GEARBOX_FILTER_DEFINITIONS = [...]`

Мастеру нужен `param_name` для поиска FilterDefinition и вызова
`fd.get_options(model_class)`, `fd.build_filter_lookup(value)`.

### 2.4 `wizard_filter_registry.py` — реестр для моделей без FILTER_DEFINITIONS

Некоторые модели (GearBox, DirectionValve, FilterRegulator) хранят
`FilterDefinition` только в `catalog/filter_defs.py`, а не как атрибут класса.
Реестр связывает `content_type_id` с путём импорта:

```python
WIZARD_FILTER_REGISTRY = {
    275: ('gearbox.catalog.filter_defs', 'GEARBOX_FILTER_DEFINITIONS'),   # GearBox
    227: ('solenoid_valves.catalog.filter_defs', 'SOLENOID_VALVES_FILTER_DEFINITIONS'),  # DirectionValve
    270: ('filter_regulator.catalog.filter_defs', 'FILTER_REGULATOR_FILTER_DEFINITIONS'), # FilterRegulator
}
```

Функция `get_filter_definitions_for_ct(content_type_id)` делает ленивый
`importlib.import_module` и возвращает список `FilterDefinition`.
Не модифицирует существующие модели — только читает их `catalog/filter_defs.py`.

---

## 3. Бэкенд API

### 3.1 Структура файлов

| Файл | Назначение |
|------|-----------|
| `core/models/selection_wizard.py` | Модель `SelectionWizard` |
| `core/models/equipment_type.py` | Поле `active_selection_wizard` |
| `core/wizard_views.py` | Все API views (публичные + админские) |
| `core/wizard_filter_registry.py` | Реестр фильтров для моделей без `FILTER_DEFINITIONS` |
| `core/urls.py` | Маршруты `/api/core/wizard/...` |
| `core/admin.py` | Django Admin регистрация `SelectionWizard` |
| `core/migrations/0007_selectionwizard_and_more.py` | Миграция |

### 3.2 Список endpoint'ов

#### Публичные (permission = `catalog_permission_classes()` → `AllowAny`)

| # | Метод | Путь | Назначение |
|---|-------|------|-----------|
| 1 | `GET` | `/api/core/wizard/<equipment_type_id>/` | Конфигурация мастера (шаги + фильтры) |
| 2 | `POST` | `.../<equipment_type_id>/filter-options/` | Опции фильтра с полем `description` |
| 3 | `POST` | `.../<equipment_type_id>/results/` | Подбор: пагинированный список моделей |
| 4 | `GET` | `/api/core/wizard/model-filters/?content_type_id=X` | FILTER_DEFINITIONS модели (для админки) |

#### Админские (permission = `IsAuthenticated` + `IsAdminOrSuperuser`)

| # | Метод | Путь | Назначение |
|---|-------|------|-----------|
| 5 | `GET` | `/api/core/wizard/admin/` | Список всех мастеров |
| 6 | `POST` | `/api/core/wizard/admin/` | Создать мастера |
| 7 | `GET` | `/api/core/wizard/admin/<id>/` | Получить одного |
| 8 | `PUT` | `/api/core/wizard/admin/<id>/` | Обновить |
| 9 | `DELETE` | `/api/core/wizard/admin/<id>/` | Удалить |
| 10 | `GET` | `/api/core/wizard/model-filters/equipment-types/` | Список EquipmentType (для админки) |
| 11 | `GET` | `.../equipment-types/<id>/` | content_type_id одного EquipmentType |

### 3.3 Ключевые классы в `core/wizard_views.py`

**`WizardModelMixin`** — общие методы:
- `_get_equipment_type(id)` — EquipmentType или None
- `_get_model_class(et)` — класс модели Django через `et.content_type.model_class()`
- `_find_filter_definition(model_class, param_name)` — сначала ищет в `model_class.FILTER_DEFINITIONS`, затем fallback в `wizard_filter_registry`
- `_get_definitions_from_registry(model_class)` — ленивый импорт через `ContentType.objects.get_for_model()`

**`WizardConfigView(WizardModelMixin, APIView)`** — эндпоинт 1:
- Берёт `et.active_selection_wizard`
- Вызывает `wizard.get_steps()` → JSON со сгруппированными шагами

**`WizardFilterOptionsView(WizardModelMixin, APIView)`** — эндпоинт 2:
- Принимает `param_name` и опционально `filters_applied`
- `_get_scoped_options()` — если переданы `filters_applied`, строит scoped queryset
  (применяет уже выбранные фильтры кроме текущего) и вызывает `fd.get_options(model_class, queryset=qs)`
- `_enrich_options()` — добавляет поле `description` к каждой опции:
  - Для FK/GLOBAL_MODEL: загружает связанные объекты, берёт `obj.description`
  - Для FIELD_VALUES/CHOICES: `description = name`

**`WizardResultsView(WizardModelMixin, APIView)`** — эндпоинт 3:
- Принимает `filters_applied`, `page`, `page_size`
- Строит queryset, применяет фильтры через `fd.build_filter_lookup(value)`
- `select_related` из `model.SELECT_RELATED_FIELDS`
- Сериализация: `obj.to_dict()` с fallback на `{id, name, code}`
- Пагинация: offset = (page-1) * page_size

**`WizardModelFiltersView(APIView)`** — эндпоинт 4:
- Берёт `content_type_id`, получает модель
- Ищет `FILTER_DEFINITIONS` на модели или через реестр
- Возвращает список `{param_name, label, filter_type, ...}`

**`WizardAdminListView(APIView)`** — эндпоинты 5, 6:
- GET: список всех `SelectionWizard` с `select_related('equipment_type')`
- POST: создаёт мастера (валидация: name не пустой, `equipment_type_id` существует)

**`WizardAdminDetailView(APIView)`** — эндпоинты 7, 8, 9:
- GET/PUT/DELETE одного мастера
- PUT: обновляет переданные поля, валидация name, обработка `IntegrityError`

**`WizardEquipmentTypesView(APIView)`** — эндпоинты 10, 11:
- GET без ID: список всех активных EquipmentType с `content_type_id`
- GET с ID: `content_type_id` одного EquipmentType

**`IsAdminOrSuperuser(BasePermission)`**:
- Проверяет `user.is_authenticated` и `user.is_superuser or user.is_staff`
- Соответствует тому, как `CurrentUserView` возвращает `roles: ['admin']`

### 3.4 Как фильтры попадают в wizard (важно!)

```
┌─────────────────────────────────────────────────────────────┐
│ Модели с FILTER_DEFINITIONS на классе (LimitSwitchBox,      │
│ PneumaticFitting):                                          │
│   model.FILTER_DEFINITIONS → WizardModelMixin читает напрямую│
├─────────────────────────────────────────────────────────────┤
│ Модели без FILTER_DEFINITIONS (GearBox, DirectionValve,     │
│ FilterRegulator):                                           │
│   wizard_filter_registry.py → ленивый importlib.import_module│
│   → catalog/filter_defs.py → XXX_FILTER_DEFINITIONS         │
└─────────────────────────────────────────────────────────────┘
```

Оба пути возвращают список `FilterDefinition` объектов, которые используются
для `get_options()`, `build_filter_lookup()`, и отображения в админке.

---

## 4. Фронтенд

### 4.1 Структура файлов

| Файл | Назначение |
|------|-----------|
| `src/shared/components/catalog/WizardSelection.vue` | Компонент мастера для страниц каталога |
| `src/shared/components/catalog/SelectionResultGrid.vue` | Сетка результатов подбора (переиспользуемая) |
| `src/shared/components/catalog/WizardPlaceholder.vue` | Старая заглушка (больше не используется в каталогах с мастером) |
| `src/pages/admin/WizardAdminPage.vue` | Админка: создание/редактирование JSON мастеров |
| `src/router/index.js` | Маршрут `/admin/wizard-config` |
| `src/components/header/TopMenu.vue` | Пункт меню «Мастер подбора» |

### 4.2 `WizardSelection.vue` — компонент мастера

**Пропсы:**
- `equipmentTypeId` (Number, required) — ID EquipmentType для API-запроса
- `labels` (Object) — `{ wizardTitle, countLabel }`
- `pageSize` (Number, default 24)

**Events:**
- `select(id)` — пользователь кликнул на карточку товара → открыть DetailView
- `navigate` — для хлебных крошек

**Состояния:**
1. `loadingConfig` — загрузка конфигурации с сервера
2. `error` — ошибка загрузки
3. **Шаги** (`!showResults`):
   - Чипсы-кнопки для навигации по шагам (кликабельные, показывают completed/active)
   - Radio-группы для каждого фильтра: **название + описание**
   - Кнопки «← Назад» / «Дальше →» / «Подобрать» (на последнем шаге)
   - Авто-выбор `default_value` при загрузке опций
4. **Результаты** (`showResults`):
   - `EngineerProductCard` для каждого товара
   - Пагинация (← Назад / Стр. X из Y / Вперёд →)
   - Кнопка «← К шагам» для возврата

**Жизненный цикл:**
```
onMounted
  → GET /api/core/wizard/<equipmentTypeId>/
  → загрузка опций для первого шага
    → POST .../filter-options/ для каждого фильтра шага

Пользователь меняет шаг (чипс/кнопка)
  → loadStepFilters(stepIndex)
    → POST .../filter-options/ для каждого фильтра (если ещё не загружены)

Пользователь нажимает «Подобрать»
  → submitWizard()
    → POST .../results/ (page=1)
    → render результатов

Пользователь листает страницы
  → goResultsPage(p)
    → POST .../results/ (page=p)
```

**Ключевая функция `loadStepFilters`:**
1. Для каждого фильтра шага проверяет `filterOptions[param_name]` — если уже загружено, пропускает
2. Иначе: POST `.../filter-options/` с телом `{param_name, filters_applied}`
3. Сохраняет опции в `filterOptions[param_name]`
4. Если у фильтра есть `default_value` — авто-выбирает подходящую опцию

**Дублирование устранено:** `submitWizard()` и `goResultsPage(p)` вызывают общую `fetchResults(page)`.

### 4.3 `WizardAdminPage.vue` — админка

**Два режима:**
1. **Список:** таблица всех мастеров, кнопки «Ред.» / «Уд.»
2. **Редактор:** форма с полями:
   - Название, код, EquipmentType (select), Активен (checkbox)
   - Кнопка «📋 Заполнить фильтры из модели» — вызывает `GET /api/core/wizard/model-filters/`, заполняет `form.filters`
   - Секция «Страницы»: добавить/удалить шаги, редактировать step_number, title, description
   - Секция «Фильтры»: выбрать param_name из modelFilters, указать страницу, порядок, label, default_value
   - Кнопки «💾 Сохранить» / «Отмена»
   - Ошибки: красная плашка `saveError`

**CRUD через админские endpoint'ы (не через UniversalAPIView):**
- `loadWizards()` → `GET /api/core/wizard/admin/`
- `saveWizard()` → `POST .../admin/` или `PUT .../admin/<id>/`
- `deleteWizard(id)` → `DELETE .../admin/<id>/`
- `loadEquipmentTypes()` → `GET .../model-filters/equipment-types/`
- `loadContentTypeForET(etId)` → `GET .../model-filters/equipment-types/<id>/`
- `fillFromModel()` → `GET .../model-filters/?content_type_id=X`

**После сохранения форма закрывается** (`editing.value = false`).
**После отмены форма закрывается.**
**При ошибке форма остаётся открытой** (пользователь может исправить).

### 4.4 Интеграция в каталоги

Каждый каталог (5 штук) в своём `App.vue`:

```vue
<WizardSelection
  v-else-if="page === 'wizard'"
  :equipment-type-id="equipmentTypeId"
  :labels="labels.wizard"
  @select="id => onSelectItem(id, 'wizard')"
  @navigate="goToSection"
/>
```

Константы `equipmentTypeId`:
| Каталог | ET ID | Модель |
|---------|-------|--------|
| limit-switch-catalog | 8 | LimitSwitchBox |
| pneumatic-fittings-catalog | 9 | PneumaticFitting |
| gearbox-catalog | 10 | GearBox |
| filter-regulator-catalog | 11 | FilterRegulator |
| solenoid-valves-catalog | 7 | DirectionValve |

`CatalogActions` имеет вкладку «Мастер подбора» (`@wizard`), которая вызывает
`goToWizard()` → `page.value = 'wizard'`.

---

## 5. Тестирование

### 5.1 Что протестировано

Smoke-test (`_check.py` — удалён после прогона) через Django `Client` на основной БД:
13/13 passed.

| Endpoint | Ожидаемый статус | Статус |
|----------|-----------------|--------|
| `GET wizard/8` (нет мастера) | 404 | ✅ |
| `GET wizard/8` (мастер активен) | 200 | ✅ |
| `POST filter-options` (нет param_name) | 400 | ✅ |
| `POST filter-options` (валидный param_name) | 200 | ✅ |
| `POST results` | 200 | ✅ |
| `GET model-filters` (с content_type_id) | 200 | ✅ |
| `GET model-filters` (без content_type_id) | 400 | ✅ |
| `GET wizard/999` | 404 | ✅ |
| `GET admin/` (без авторизации) | 403 | ✅ |
| `POST admin/` (без авторизации) | 403 | ✅ |
| `GET admin/<id>/` (без авторизации) | 403 | ✅ |
| `DELETE admin/<id>/` (без авторизации) | 403 | ✅ |
| `GET equipment-types/` (без авторизации) | 403 | ✅ |

### 5.2 Почему `manage.py test` не работает

Миграция `electric_actuators.0030` содержит битый FK:
```
"electric_actuators_electricactuatorselected" REFERENCES "electric_actuators_cableglandholessetbodyoption"
```
Таблица-ссылка не существует на момент миграции → `PRAGMA foreign_key_check` падает.
Проблема не связана с мастером подбора — воспроизводится для любого теста в проекте.

---

## 6. Текущее состояние

### 2026-07-30 — базовая реализация
- ✅ Модель `SelectionWizard` + миграция
- ✅ 11 API endpoint'ов (5 публичных + 6 админских)
- ✅ `wizard_filter_registry.py` — адаптер для моделей без `FILTER_DEFINITIONS`
- ✅ `WizardSelection.vue` — компонент мастера в каталогах
- ✅ `WizardAdminPage.vue` — админка с автозаполнением из модели
- ✅ Интеграция во все 5 каталогов
- ✅ Созданы wizard-записи для всех 5 EquipmentType
- ✅ Роутер `/admin/wizard-config` + меню TopMenu

### 2026-07-31 — доработки
- ✅ **`SelectionResultGrid.vue`** — переиспользуемый компонент сетки результатов.
  Оба режима пагинации: страничный (`page`/`totalPages`) и offset-based
  (`offset`/`limit`). Используется в `WizardSelection` и `EngineerSelection`.
- ✅ **`canProceed`** — все фильтры шага обязательны (`.every()`).
  `exd_id` всегда считается заполненным (по умолчанию «Общепром.»),
  `climate` требует оба `work_temp_min` и `work_temp_max`.
- ✅ **Дизейбл чипсов** — будущие шаги неактивны, пока текущий не заполнен.
- ✅ **`WizardAdminPage.vue` редизайн** — табы шагов, табы фильтров внутри
  шага, карточка фильтра в одну строку (`param_name | шаг | порядок`).
  Валидация: уникальность номеров шагов, битые ссылки фильтр→шаг,
  уникальность `order` в пределах шага. `default_value` — выпадающий
  список с реальными опциями.
- ✅ **Сериализация** — `WizardResultsView` использует `to_values_dict()`
  (как инженерный подбор), а не `to_dict()`. Добавлено обогащение цен
  через `get_bulk_prices`.
- ✅ **Меню админки** — перегруппировано: Номенклатура и цены, Клиенты,
  Оборудование, Настройка системы, Инструменты, AI.
- ✅ `LimitSwitchModelLineAdmin` / `LimitSwitchBodyAdmin` — `search_fields`
- ✅ `frontend/dist` в `STATICFILES_DIRS` — условно (только если папка есть)

### НЕ сделано (потенциальные улучшения)
- `equipmentTypeId` захардкожен в каждом `App.vue` — при изменении ID в БД сломается
- Не добавлен `watch` на смену `equipmentTypeId` в `WizardSelection.vue`
- Нет индикатора загрузки на уровне шага (только индивидуальные `loadingFilter`)

---

## 7. Как добавить мастер для нового каталога

1. Убедиться, что модель каталога имеет `FILTER_DEFINITIONS` (на классе или через реестр)
2. В EquipmentType указать `content_type` на правильную модель
3. Через админку (`/admin/wizard-config`) создать `SelectionWizard`:
   - Выбрать EquipmentType → нажать «Заполнить из модели»
   - Сгруппировать фильтры по шагам
   - Сохранить
4. В `App.vue` каталога:
   - Добавить `const equipmentTypeId = <ID>`
   - Импортировать `WizardSelection`
   - Добавить `<WizardSelection v-else-if="page === 'wizard'" .../>`
   - Добавить `goToWizard()` и `tabKeys`
5. Фронтенд каталога сам загрузит конфигурацию через API
