# Узлы, Слоты и Матрицы — конфигуратор БУ (ea_control)

Назначение: конфигурирование сложного оборудования без комбинаторного взрыва
в БД и без хардкода логических правил. Текущая реализация отлаживается на
блоке управления электропривода (БУ) в приложении `ea_control`.

---

## 1. Паттерн

### Золотое правило

- **Физика типизируется**: справочники и физические сущности — обычные
  Django-модели с типизированными полями (скаляры + FK/M2M на справочники),
  без композитных данных.
- **Связи и ограничения универсальны**: логика доступности, дефолтов и
  динамики управляется сквозными паттерн-моделями, одинаковыми для любых
  типов данных.

### Роли (словарь)

- **Узел (Node)** — группировка слотов в дерево конфигуратора; вкладывается
  через `parent`.
- **Слот (Slot)** — точка конфигурации («розетка»): `selection_mode`,
  `slot_kind`, `required`. Не хранит выбранное значение.
- **Опция (Option)** — возможное значение слота; несёт типизированную
  полезную нагрузку по `kind`.
- **Матрица (MatrixEntry)** — доступность опции в точке контекста (Паттерн А).
- **Правило (Rule)** — динамика UI по выбранному значению (Паттерн В).
- **Снимок (Snapshot)** — плоский результат `{slot_code: value}`.

Вложенность жёсткая: **узел → слот → опция**. Вложенных слотов нет: слот —
лист узла, опция — лист-значение слота.

### Три паттерна

- **Паттерн А — Матрица.** Доступность опции по контексту (скоуп + координаты):
  `availability` std/opt/na, `is_default`, `bundle`, `conflicts`.
- **Паттерн Б — Цена.** Вне scope конфигуратора; отдельная сущность по общему
  паттерну, не реализована в `ea_control`.
- **Паттерн В — Правило.** `when {slot, operator, value}` → `then {action,
  target_slot}`: show/hide/block/require/set_default.

### Граница «узел дерева vs опция изделия»

БУ — **не узел дерева**, а опция слота `control_unit` (kind=`object`).
Доступность и дефолты для конкретного БУ задаются строками матрицы со скоупом
`control_unit`, а не отдельным деревом на каждый БУ.

---

## 2. Текущие модели — приложение `ea_control`

### Абстракции (`models/abstract.py`)

Общие поля и логика; связные поля (FK/M2M) объявляет наследник.

- `AbstractConfigNode` — узел: `code`, `name`, `parent` (self-FK), `description`,
  `sorting_order`, `is_active`.
- `AbstractConfigSlot` — слот: `code`, `name`, `selection_mode`
  (single/multi/xor/bundle), `slot_kind` (value/object/subtype), `required`,
  `description`, `sorting_order`, `is_active`.
- `AbstractSlotOption` — опция: `code`, `kind`, `name`, `encoding`/`ext_encoding`,
  `description`, `sorting_order`, `is_active`.
- `AbstractSlotMatrixEntry` — строка матрицы: `availability` (std/opt/na),
  `is_default`, `bundle`, `conflicts` (M2M self), `encoding`/`ext_encoding`,
  `name`, `description`, `sorting_order`; `save()` ставит std → is_default.
- `AbstractSlotRule` — правило: `when_operator`, `when_value` (JSON), `action`
  (show/hide/block/require/set_default), `action_value` (JSON), `priority`,
  `is_active`.
- `AbstractConfigSnapshot` — снимок: `config_snapshot` (JSON) + методы
  `set_option`/`get_option`/`apply_defaults`/`full_code`.

Словари: `ConfigSelectionMode`, `ConfigSlotKind`, `ConfigAvailability`,
`ConfigRuleAction`, `ConfigRuleOperator`.

### Конкретные модели (`models/cu_config.py`)

- `CuSectionNode(AbstractConfigNode)` — узел-секция БУ.
- `CuSlot(AbstractConfigSlot)` — слот БУ, + `section` (FK → CuSectionNode).
- `CuSlotOption(AbstractSlotOption)` — опция БУ, + `slot` (FK → CuSlot) и
  типизированные нагрузки по `kind`:
  - `signal` → ровно одно из `control_signal`/`feedback_signal`/`protocol`;
  - `heater` → `heater_supply`; `power` → `signal_power`; `logic` →
    `control_logic`; `signal_type` → `signal_type`; `unit` → `control_unit`
    (только слот `control_unit`); `none`/`pair` → только `name`;
  - `device` — датчик по умолчанию.
- `CuMatrixEntry(AbstractSlotMatrixEntry)` — доступность: `slot`/`option` FK,
  скоуп (`brand`/`model_line`/`body`/`model_line_item` — ровно один),
  контекст (`control_unit`/`power_supply`/`mode`), полезные нагрузки
  (`control_signal`/`feedback_signal`/`protocol`/`device`/`heater_supply`).
  CheckConstraints «один скоуп» и «одна нагрузка»; строки с пустым скоупом —
  профиль (дефолты) типа БУ.
- `CuSlotRule(AbstractSlotRule)` — `when_slot`/`target_slot` FK + `evaluate()`.

### Физическая модель БУ (`models/control_unit.py`)

- `ControlUnit` — тип БУ: `brand`, `code` (уникален в рамках бренда),
  `name_i18n`, `kind` (NONE/BASIC/INTEGRATED/POSITIONER), `location`,
  `control_voltage`, `signal_power`, M2M `accepts`/`emits`/`protocols`/
  `capabilities`, шаблоны `name_template`/`description_template`/`spec_template`
  (+ `_i18n`), `legacy_cu` (1:1 маппинг на legacy справочник).

### Справочники физики

- `models/dictionaries.py` — копии справочников ЭП (изоляция от
  `electric_actuators`): `CuSignalForm`, `CuControlSignal`, `CuFeedbackSignal`,
  `CuCommProtocol`, `CuFeedbackDevice`, `CuHeaterSupply`, `CuLocationOption`,
  `CuCapability`.
- `models/cu_power.py` — схемотехника: `CuSignalPowerSource`, `CuSignalPower`,
  `CuControlLogic`, `CuSignalType` (напряжение — FK `params.PowerSupplies`).

### Сервисы (`services/`)

- `cu_matrix.py` — резолвер доступности: наследование скоупов, na-запреты,
  `resolve_control_units`, profile-дефолты, `validate_selection`
  (bundle/conflicts).
- `cu_rules.py` — движок правил (show/hide/block/require/set_default).
- `cu_package.py` — пакет конфигуратора для фронта
  `{unit, slots, options, defaults, rules, matrix}`.

### API (`api.py`, `/api/ea-control/`)

DRF CRUD всех моделей (IsAdminUser) + особые эндпоинты: `units/`, `meta/`,
`series-units/`, `package/`.

### Данные

`seed_cu_demo` (идемпотентно): 4 типа БУ, 4 узла, 16 слотов, 47 опций,
69 строк матрицы, 6 правил.

---

## 3. Фронтенд

Страница `/admin/ea-control` (`pages/admin/EaControlAdminPage.vue`) — четыре
раздела верхнего уровня:

1. **Конфигуратор опций** — редактор структуры
   (`EaControlStructurePage.vue`): дерево узел → слоты → опции. Редактирование
   в локальном черновике, единая кнопка «Сохранить» коммитит топологически
   (узел → слоты → опции; новые POST, изменённые PUT, помеченные DELETE).
   Удаление двухшаговое (пометка → «Сохранить»). Форма опции kind-driven.
   Слот можно перемещать между узлами селектором «Родитель».
2. **Редактор БУ** — `Блоки управления` (ControlUnit) / `Матрица` / `Правила`.
3. **Справочники** — 12 типизированных справочников.
4. **Превью БУ** — `EaControlConfiguratorPage.vue`: серия → напряжение → БУ →
   пакет, снимок и собранный артикул (применение матрицы и правил).

Вспомогательное: `components/EditorActions.vue` — переиспользуемый блок
«Сохранить»/«Удалить». Пункт «Блоки управления ЭП» добавлен в ТопМеню
(Администрирование).

---

## 4. Ближайшие действия

1. Прогнать `cd frontend; npm run build`; поправить, если упадёт.
2. Ручная проверка разделов: структура (создать узел/слот/опцию, переместить
   слот, «Сохранить»), редактор БУ (матрица/правила), справочники, превью.
3. Прогнать тесты: скопировать `db.sqlite3` → `test_db.sqlite3`,
   `python manage.py test ea_control --keepdb`.
4. Полировка: переименовать `EaControlStructurePage.vue` /
   `EaControlConfiguratorPage.vue` (убрать суффикс «Page», т.к. это компоненты);
   починить локаль превью (`route.meta.locale` → глобальная локаль из i18n).

---

## 5. Дальнейшие действия

1. Перенос абстракций из `ea_control/models/abstract.py` в `core`
   (`ConfigSlot`/`SlotOption`/`SlotMatrixEntry`/`SlotRule`/`ConfigSnapshot`).
2. Migrate-команды из legacy: `migrate_cu_from_params`,
   `migrate_cu_series_links`, `migrate_cu_profiles` (маппинг по кодам).
3. Интеграция в ЭП (фаза 4): переключение `/admin/ea-constructor` на
   `ControlUnit`/`CuMatrixEntry` по критерию готовности (данные перенесены +
   паритет AOX AR01E/AR11E/AR21E/CLFZE).
4. `config_snapshot` на `ElectricActuatorCatalogItem` (+ общий
   `ConfiguredProduct`).
5. Судьба справочников-копий vs ЭП-оригиналов (слияние/замена).
6. Промоушн БУ в узел `EquipmentType` — триггер: собственный каталог или
   состав из позиций.
7. Цена — вне scope; отдельная сущность по общему паттерну.

---

## 6. Связанные документы

- `configurator.md` — концепция конфигуратора (снапшот).
- `ai-assistant.md` — AI-пайплайн (снапшот).
- `ea-models-analysis.md` — состояние моделей ЭП.
- `EXECUTION_PLAN.md` — план assemblies/configurator.
