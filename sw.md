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

### 2.1 `QuestionGraph` (`core/models/question_graph.py`)

**`graph_json`** — граф с двумя типами узлов:

```json
{"entry_node":"page_variety","nodes":{"page_variety":{"type":"page","name":"Выбор типа","params":[{"title":"Тип","param_name":"fitting_variety_id","order":1}],"next_node":"branch_variety"},"branch_variety":{"type":"branch","name":"По типу","param_name":"fitting_variety_id","match_values":["1","2"],"match_target":"page_pipe","else_target":"page_thread"}},"edges":[{"from":"page_variety","to":"branch_variety"}]}
```

- **page-узел**: `name`, `params` (список {title, param_name, order}), `next_node`
- **branch-узел**: `name`, `param_name`, `match_values`, `match_target`, `else_target`
- **`_get_next_node_id`**: branch проверяет match_values; page: next_node → edges

### 2.2 `SelectionWizard` — устарел

## 3. Бэкенд API

### 3.1 Файлы

| Файл | Назначение |
|------|-----------|
| `core/models/question_graph.py` | Модель `QuestionGraph` |
| `core/question_graph_views.py` | API: config, advance, results |
| `core/wizard_filter_registry.py` | Реестр FilterDefinition |
| `core/management/commands/load_question_graph.py` | Загрузка графов |

### 3.2 Endpoint'ы

| Метод | Путь | Назначение |
|-------|------|-----------|
| `GET` | `/api/core/question-graph/<code>/` | Конфигурация: entry_node + опции |
| `POST` | `.../<code>/advance/` | Переход к следующему узлу |
| `POST` | `.../<code>/results/` | Результаты подбора |
| `GET/POST/PUT/DELETE` | `.../admin/...` | CRUD графов |

### 3.3 Логика advance

1. Для page-узла: сохраняет ответы в `accumulated`
2. Для branch-узла: `branch_val = accumulated[param_name]`
3. `graph._get_next_node_id(node_id, branch_val)`
4. Нет следующего → `terminal: true`
5. Иначе → опции через `_get_options_for_page_node`

### 3.4 Cross-FK

`_resolve_cross_fk_field` ищет `model_field` с `__` (например `body__thread`) через `FilterDefinition` или wizard-реестр.

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

## 7. Как добавить мастер

1. Модель должна иметь `FILTER_DEFINITIONS` или запись в реестре
2. Создать граф через `/admin/wizard-config` или `load_question_graph.py`
3. В `App.vue`: `graph-code="'<code>'"` + `goToWizard()`

## 8. От профилей к графу

Старый `SelectionWizard` с `steps_json` был плоским. QuestionGraph заменил шаги и профили:

- **page-узлы** — аналоги шагов: список параметров
- **branch-узлы** — ветвление: `match_values` → `match_target` (ДА), иначе → `else_target`
- Vue Flow — визуальный редактор вместо номеров шагов

## 9. QuestionGraph — граф вопросов-ответов (2026-08-05)

> Альтернатива `FilterProfile`. Вместо плоских шагов с условной видимостью —
> граф, где узлы = вопросы, рёбра = переходы, `branches` = ветвление по ответу.

### 9.1 Модель

```python
# core/models/question_graph.py
class QuestionGraph(BaseAbstractModel):
    equipment_type = FK(EquipmentType)
    code = CharField(unique=True)
    name = CharField()
    graph_json = JSONField(default=dict)
    # {
    #   "entry_node": "fitting_variety",
    #   "nodes": {
    #     "fitting_variety": {
    #       "question": "Тип фитинга",
    #       "param_name": "fitting_variety_id",
    #       "branches": {"1": "pipe_params", "3": "thread_params", ...}
    #     },
    #     "pipe_params": {
    #       "question": "Трубка",
    #       "param_names": ["pipe_diameter", "pipe_material_id"]
    #     },
    #     "thread_params": {
    #       "question": "Резьба",
    #       "pages": [
    #         {"title": "Тип резьбы", "param_names": ["thread_type_id"]},
    #         {"title": "Размер резьбы", "param_names": ["thread_id"]},
    #         {"title": "Нар/внут", "param_names": ["thread_inner_outer_id"]}
    #       ]
    #     }
    #   },
    #   "edges": [
    #     {"from": "pipe_params", "to": "thread_params"},
    #     {"from": "thread_params", "to": "material_params"}
    #   ]
    # }
```

### 9.2 API

| Метод | Путь | Назначение |
|---|---|---|
| `GET` | `/api/core/question-graph/<code>/` | Граф + опции entry-узла |
| `POST` | `.../<code>/advance/` | Ответ → следующий узел/подстраница |
| `POST` | `.../<code>/results/` | Поиск моделей по накопленным фильтрам |
| `POST` | `.../<code>/to-wizard/` | Конвертер: граф → SelectionWizard |
| `GET/POST` | `/api/core/question-graph/admin/` | CRUD графов |
| `GET/PUT/DELETE` | `.../admin/<id>/` | CRUD одного графа |

### 9.3 Frontend

- `QuestionGraphWizard.vue` — компонент для страниц каталога (radio-кнопки, подстраницы, back-навигация, `filterLabels`, авто-выбор)
- `useCatalogWizard.js` — фронтенд-адаптер (`type: 'graph'|'flat'`)
- `QuestionGraphDemo.vue` — отладочная страница `/demo/question-graph`
- `QuestionGraphAdmin.vue` — админка `/admin/question-graph` (JSON-редактор + превью)
- `WizardAdminPage.vue` — вкладка «📊 Граф» (CRUD графов, конвертер в wizard)

### 9.4 Интеграция в каталоги

Единый endpoint `CatalogWizardAdapterView` (`GET /api/core/catalog-wizard/<code>/`):
приоритет граф → fallback плоский wizard. Все 5 каталогов используют `useCatalogWizard`
в `App.vue`. При появлении графа для любого каталога — автоматическое переключение.

### 9.5 Скоупинг

Опции фильтров скоупятся через `FilterDefinition.build_filter_lookup()`
(включая `THREAD_COMPATIBLE`). Cross-FK поля (`thread_type_id`) маппятся
через `_FIELD_LOOKUP`.

### 9.6 `default_value` и авто-выбор

Узлы/подстраницы поддерживают `"default_value": {"param_name": value}`.
`QuestionGraphWizard` авто-применяет defaults и авто-выбирает единственную опцию.

### 9.7 Графы

| Код | Каталог | Узлы | Branching |
|---|---|---|---|
| `pneumatic_fittings` | Пневмофитинги | fitting_variety → pipe_params/thread_params → material_params | по типу фитинга |
| `lsb` | БКВ | sensor_variety → common_params → protection_params | по типу датчика |

### 9.8 TODO

- Совмещённый фильтр по резьбе (тип + размер в одном визуальном блоке)
- Графы для остальных каталогов при необходимости branching'а## 5. Фронтенд

### 5.1 Компоненты

| Компонент | Назначение |
|-----------|-----------|
| `QuestionGraphWizard.vue` | Мастер подбора: radio-кнопки, авто-переход branch |
| `QuestionGraphAdmin.vue` | Админка: список + редактор |
| `QuestionGraphFlow.vue` | Визуальный редактор (Vue Flow) |
| `PageNode.vue` / `BranchNode.vue` | Карточки узлов на холсте |
| `PageNodeForm.vue` / `BranchNodeForm.vue` | Попапы редактирования |

### 5.2 Архитектура QuestionGraphFlow

- **`liveJson`** — реактивная копия `graphJson`, единственный источник
- **`renderFlow()`** — `liveJson` → Vue Flow nodes/edges
- **`watch(liveJson, renderFlow, {deep:true, immediate:true})`** — авто-перерисовка
- Попапы читают/пишут напрямую в `liveJson`
- «Записать в БД» → `emit('save', liveJson)` → API
- Позиции: `_x`/`_y` в JSON

### 5.3 Каталоги (единообразный `goToWizard()`)

`pneumatic-fittings`, `limit-switch`, `solenoid-valves`, `filter-regulator`, `gearbox`


