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

Слот принадлежит ровно одному узлу (инвариант 1:1): позиция слота в дереве —
презентация; значение живёт в снимке, доступность — в матрице, динамика — в
правилах. Если слот нужно показать в двух местах — вводим ссылочные узлы
(read-only отображение чужих слотов), а не M2M-владение. Несколько слотов
могут ссылаться на один справочник — это штатный способ «горизонтальной
гибкости»: два слота = две независимые точки со своими строками матрицы и
правилами.

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

- `AbstractConfigNode` — узел: `code`, `key` (стабильный UUID для синхронизации, read-only),
  `name`, `parent` (self-FK), `description`,
  `sorting_order`, `is_active`.
- `AbstractConfigSlot` — слот: `code`, `key` (стабильный UUID), `name`, `selection_mode`
  (single/multi/xor/bundle), `slot_kind` (value/object/subtype), `required`,
  `description`, `sorting_order`, `is_active`.
- `AbstractSlotOption` — опция: `code`, `key` (стабильный UUID), `kind`, `name`,
  `encoding`/`ext_encoding`,
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
    `control_logic`; `unit` → `control_unit`
    (только слот `control_unit`); `location` → `location_option`
    (слот `CU_LOCATION`); `cable_gland` → `cable_gland_set` (общая модель
    ЭП `electric_actuators.CableGlandHolesSet`); `none`/`pair` → только `name`;
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
  `name_i18n`, `kind` (FK → справочник `ControlUnitKind`: NONE/BASIC/
  INTEGRATED/POSITIONER), неизменяемый `key` (короткий UUID
  `uuid.uuid4().hex[:16]`, генерится в `save()`, read-only в API), M2M
  `accepts`/`emits`/`protocols`/`capabilities`, шаблоны
  `name_template`/`description_template`/`spec_template` (+ `_i18n`),
  `legacy_cu` (1:1 маппинг на legacy справочник; сид идентифицирует БУ по
  `legacy_cu`, а не по `code`/`key`). Поля `location`/`control_voltage`/
  `signal_power` из модели убраны (2026-10-29): БУ описывает сигналы и
  датчики — описание подходит к разным моделям и напряжениям серии.
  Размещение — слот `CU_LOCATION` (опции kind=`location` →
  `CuLocationOption`); напряжение/схема цепей — слот `CMD_WIRING`.
  Привязка БУ к model_line_item — отдельная задача (§4.2, опция со своей
  кодировкой через through-модели).

### Справочники физики (`models/dictionaries.py`)

Копии справочников ЭП (изоляция от `electric_actuators`): `CuControlSignalForm`
(формы ВХОДНЫХ сигналов: сухой контакт с внутренним опросом / потенциал AC/DC
/ петля 4–20 мА) и `CuFeedbackSignalForm` (формы ВЫХОДНЫХ: сухой контакт реле
/ петля / потенциометр), `CuControlSignal`, `CuFeedbackSignal`,
`CuCommProtocol`, `CuFeedbackDevice`, `CuHeaterSupply`, `CuLocationOption`,
`CuCapability`, `CuLocalControlType`, `CuDisplayType`, `CuUnitPowerSource`.

Классифицирующие поля переведены с TextChoices на **общие справочники ЭП**
(прецедент — `CableGlandHolesSet`/`EaFeedbackDeviceKind`):

- категория формы: `CuControlSignalForm.category` и
  `CuFeedbackSignalForm.category` → `EaSignalFormCategory` (одна общая:
  объединение категорий ЭП `contact/analog/discrete/resistance` и БУ
  `dry_input/voltage_ac/voltage_dc/current_4_20/dry_output`);
- роль: `CuControlSignal.role` → `EaControlSignalRole`; `CuFeedbackSignal.role`
  → `EaFeedbackSignalRole`;
- норма контакта: `CuFeedbackSignal.contact_normal` → `EaContactNormal`;
- транспорт: `CuCommProtocol.transport` → `EaProtocolTransport` (канон —
  нижний регистр: `rs485`/`ethernet`/`current_loop`/`h1`/`other`);
- устройство ОС: `CuFeedbackDevice.kind`/`technology` →
  `EaFeedbackDeviceKind`/`EaFeedbackTechnology`.

Единые наборы значений — константы в `electric_actuators.models`
(`FEEDBACK_DEVICE_KINDS`, `FEEDBACK_TECHNOLOGIES`, `SIGNAL_FORM_CATEGORIES`,
`CONTROL_SIGNAL_ROLES`, `FEEDBACK_SIGNAL_ROLES`, `CONTACT_NORMALS`,
`PROTOCOL_TRANSPORTS`) и `POLARITIES` в `ea_control.models.cu_power`.
`clean()`/валидация работают по `.code`. Собственная классификация
`CuControlSignal.category` (discrete/analog) и `CuFeedbackSignal.category`
(contact/analog) осталась CharField — это внутренняя ось сигнала, не общий
справочник. Миграции применены (ea_control 0016–0019, electric_actuators
0078–0081), бэкфилл без NULL; `makemigrations` — «No changes».

Дискретные командные сигналы из `EaControlSignal` намеренно не переносятся в
`CuControlSignal` (он только аналоговый) — команды выражены слотами CMD_* +
логикой + схемой цепей.

### Схемотехника цепей управления (`models/cu_power.py`)

- `CuSignalPowerSource` (INTERNAL/EXTERNAL + флаг ``internal`` — встроенный
  источник выдаёт опорное напряжение);
- `CuSignalPower` (схема цепей: источник × напряжение × форма входа ×
  полярность; unique_together + условный UniqueConstraint для пар без формы
  входа — SQLite с NULL в индексе не защищает);
- `CuPolarity` (PNP/NPN/двунаправленный/не применимо — с подробным
  объяснением терминов в help_text) — `CuSignalPower.polarity` → FK;
  callable-дефолты FK возвращают **pk (int)**, а не инстанс (иначе
  SQLite-миграция падает на `_remake_table`);
- `CuControlLogic` (импульсная/потенциальная/настраиваемая). Напряжение — FK
  `params.PowerSupplies`.

### Питание БУ и кабельные вводы

- Слот `CU_POWER_SUPPLY` «Питание БУ» → справочник `CuUnitPowerSource`
  (SHARED_CABLE «От цепей питания привода (общий кабель)» / SEPARATE_CABLE
  «Отдельный кабель питания БУ»). Дефолт кодируется профильными строками
  матрицы типа БУ (встроенный — общий std / отдельный na; навесной —
  отдельный std / общий opt); встроенным слот скрыт правилом.
- Слот `CU_CABLE_GLANDS` «Кабельные вводы БУ» → **общая модель ЭП**
  `electric_actuators.CableGlandHolesSet` (набор отверстий `cg1..cg4` →
  `params.ThreadSize`; свои записи БУ: 3xM20x1.5 / 3xM25x1.5 / 3xPG16 /
  1×1½" NPT + 2×¾" NPT). Для встроенного БУ слот скрыт правилом (вводы —
  у привода).
- **«Чьи отверстия для подбора КВ» — производное, не слот**: `PU_SHARED`
  (общий кабель) → отверстия корпуса привода, вводы БУ не используются
  (правило hide `CU_CABLE_GLANDS`); `PU_SEPARATE` → отверстия БУ (show).
  Отдельный справочник «Используются КВ» не вводим (вторая точка правды
  разошлась бы с выбором питания). Исключение: навесному БУ (`CU_INT_O`)
  вводы БУ показываются всегда (show с priority 1 перебивает PU_SHARED-hide)
  — сигналы заходят в БУ и при общем кабеле питания. «Корпус+Блок» —
  агрегация при подборе КВ (у привода корпусные вводы есть всегда),
  считается кодом сборки, не хранится.

### Структура «Дистанционное управление»

Узел `CONTROL_SIGNALS` → подузел `CMD_INPUTS` «Дистанционное управление»:

- `CMD_WIRING` (single, required) — «Схема цепей управления»: **опция =
  пара источник × напряжение × форма × полярность** (`CuSignalPower`,
  kind=power). Активность (сухой контакт/потенциал) и полярность — атрибуты
  пары, не отдельные слоты. Пара вместо каскада слотов: недопустимые
  сочетания невыразимы в принципе, описание БУ — одна матрица слота вместо
  трёх + связок. К каскаду вернуться, если оси размножатся комбинаторно.
- `CMD_OPEN` / `CMD_CLOSE` / `CMD_STOP` / `CMD_ESD` (single) — сигналы
  дистанционного управления. **Опция слота = логика работы сигнала**
  (дискретный = импульс с самоподхватом / продолжительный = потенциал /
  настраиваемый — `CuControlLogic`, kind=logic) + явная опция
  **«Отсутствие сигнала»** (kind=none, в основном для СТОП, доступна в
  каждом слоте). Состав сигналов — профильные строки конкретного БУ.
- **Набор сигналов — опции схемы**: координата `signal_power` у
  `CuMatrixEntry` — строки с конкретной схемой перекрывают профильные
  («у позиционера дискретные команды только при внешней схеме 24 В DC»).
  Резолвер: без выбранной схемы строки с координатой не применяются.
- ESD — одна команда; направление (аварийно открыть/закрыть) настраивается
  в меню БУ, в конфигураторе не выбирается.
- Удалены: слоты `CMD` (multi), `SIGNAL_POWER_SOURCE`, `CONTROL_LOGIC`,
  `SIGNAL_TYPE`, справочник `CuSignalType`; `CuControlSignal` больше не
  хранит `voltage`/дискретные формы (остались аналоговые уставки).

### Узел «Общие параметры»

Узел `GENERAL` «Общие параметры»: слот `CU_LOCATION` (single, required)
«Размещение БУ» — **опция = справочник `CuLocationOption`** (kind=`location`:
встроенный/навесной). Доступность — профильные строки матрицы типа БУ.
Поля `location`/`control_voltage`/`signal_power` из модели `ControlUnit`
убраны: БУ описывает сигналы и датчики без привязки к модели и напряжению
привода; привязка к model_line_item — отдельная задача (§4.2).

### Сервисы (`services/`)

- `cu_matrix.py` — резолвер доступности: наследование скоупов, na-запреты,
  координаты power_supply/signal_power (схема цепей: без выбранной схемы
  строки с координатой не применяются), `resolve_control_units`,
  profile-дефолты, `validate_selection` (bundle/conflicts).
- `cu_rules.py` — движок правил (show/hide/block/require/set_default).
- `cu_package.py` — пакет конфигуратора для фронта
  `{unit, slots, options, defaults, rules, matrix}`; принимает выбранную
  схему цепей (`signal_power`) и перерезолвивает набор сигналов;
  имена опций — из типизированной нагрузки (`CuSlotOption.localized_name`
  раскрывает power/logic/heater/signal).
- `cu_report.py` — описание БУ для производителя: ВСЕ секции дерева
  (выключенные — с пометкой ``is_active=False``, фронт показывает «раздел
  выключен»), опции с доступностью std/opt/na.
- `cu_unit_matrix.py` — редактируемая матрица профиля БУ (вкладка
  «Настройки»): строки с координатой `signal_power` в редактор не входят
  (это переопределения схем, задаются сидом/отдельным инструментом).

### API (`api.py`, `/api/ea-control/`)

DRF CRUD всех моделей (IsAdminUser) + особые эндпоинты: `units/`, `meta/`,
`series-units/`, `describe/`, `package/`, `unit-matrix/`,
`unit-matrix/save/`. `ControlUnit.key` и `key` сущностей схемы — read-only.

Удаление сущностей схемы (`sections/`, `slots/`, `slot-options/`) и
справочников физики (`control-signal-forms/`, `feedback-signal-forms/`,
`control-signals/`, `feedback-signals/`, `comm-protocols/`,
`feedback-devices/`, `signal-power-sources/`, `signal-powers/`) не
блокируется защитой FK: DELETE без параметра при наличии зависимостей
возвращает 409 с перечнем использования (`usage`: строки матрицы, опции,
правила, слоты всей ветки секции, схемы цепей); DELETE с `?cascade=1`
удаляет зависимые строки вместе с объектом.

### Данные

`seed_cu_demo` (идемпотентно): 5 типов БУ, 43 слота, 133 опции,
331 строка матрицы, 27 правил.

### Правила (Паттерн В) — назначение и примеры

Правила управляют **динамикой UI конфигуратора** в ответ на выбранное
значение (матрица, напротив, — статичная доступность по контексту). Форма:
`when {слот-условие, оператор, значение} → then {действие, слот-цель}`.

Действия и их отображение в конфигураторе:

- `show` — слот отображается (обычно, чтобы «перебить» `hide` с меньшим
  приоритетом);
- `hide` — слот не отображается (убирается из раздела);
- `block` — слот виден, но опции выбрать нельзя (inputs disabled);
- `require` — у слота появляется метка «обязателен»;
- `set_default` — подставляет опцию по умолчанию при выполнении условия
  (динамический дефолт; матричный `std` — статический дефолт профиля).

Примеры:

- `hide PROTOCOL when control_unit = CU_BASIC` — базовому БУ не показываем шину;
- `set_default POSITION_FEEDBACK = POS_HART when SETPOINT = SETPOINT_HART` —
  выбор HART-уставки тянет позиционную ОС HART;
- `hide CU_POWER_SUPPLY when control_unit in [CU_BASIC, CU_INT, CU_INT_MB,
  CU_POSI]` — встроенным БУ не показываем «Питание БУ» (вводы — у привода);
- `hide MOTOR_STARTER when control_unit = CU_BASIC` — у базового БУ стартера
  нет;
- `PU_SHARED → hide CU_CABLE_GLANDS` / `PU_SEPARATE → show CU_CABLE_GLANDS` —
  универсальные правила (when_slot = CU_POWER_SUPPLY): «чьи отверстия для
  подбора КВ» — производное от выбора питания.

В «Редакторе БУ» → «Редактор доступных опций» профильные правила типа БУ
редактируются через `when_slot=control_unit` с операторами exact/in/not_in.
Универсальные правила с `when_slot` ≠ `control_unit` в профильном редакторе
не показываются — они общие для всех БУ и задаются сидом.

---

## 3. Фронтенд

Страница `/admin/ea-control` (`pages/admin/EaControlAdminPage.vue`) — пять
разделов верхнего уровня:

1. **Конфигуратор опций** — редактор структуры
   (`EaControlStructurePage.vue`): дерево узел → слоты → опции. Редактирование
   в локальном черновике, единая кнопка «Сохранить» коммитит топологически
   (узел → слоты → опции; новые POST, изменённые PUT, помеченные DELETE).
   Удаление двухшаговое (пометка → «Сохранить»). Форма опции kind-driven.
   Слот перемещается между узлами селектором «Раздел» — собственный
   dropdown (`.section-picker`: кнопка + меню, пункты с отступом по
   вложенности) вместо нативного `<select>`: нативный popup в Chrome
   периодически закрывается, не закоммитив выбор (change приходит со
   старым значением, PUT сохраняет прежний раздел). У узла — свой
   «Родитель» для вложенности дерева (подписи разведены). В редакторе слота
   свои кнопки: «Сохранить» (только выбранный слот и его опции), «Копировать»
   (клон слота + опций с суффиксом `_Copy` в кодах — глобальная уникальность),
   «Удалить слот». Если удаляемый узел/слот/опция используются (матрица,
   правила, опции), сервер возвращает 409 с перечнем — фронт спрашивает
   «данные используются в …, действительно удалить?» и по подтверждению
   удаляет вместе с зависимыми записями (`?cascade=1`).
   Успех виден зелёным баннером «Сохранено»/«Слот сохранён».
2. **Редактор БУ** — `Блоки управления` (ControlUnit) / `Матрица` / `Правила`.
3. **Справочники** — типизированные формы (входные/выходные отдельно),
   сигналы, схемы цепей (источник × напряжение × форма × полярность),
   протоколы, устройства и т.д. Гэп текущей версии: поля новых FK (категории
   форм, роли, норма контакта, транспорт, полярность) пока редактируются
   хардкод-`choices` — перевод на `source`-селекты в плане (§4.1).
4. **Превью БУ** — `EaControlConfiguratorPage.vue`: серия → напряжение → БУ →
   пакет; выбор опции слота `CMD_WIRING` перезапрашивает пакет с выбранной
   схемой цепей (сервер перерезолвивает набор сигналов, выбор сохраняется);
   снимок и собранный артикул (применение матрицы и правил).
5. **Описание БУ** — `EaControlDescription.vue`: все секции и слоты с
   доступностью std/opt/na, пометка «раздел выключен», кнопка
   «Копировать текст».

Вспомогательное: `components/EditorActions.vue` — переиспользуемый блок
«Сохранить»/«Удалить». Пункт «Блоки управления ЭП» добавлен в ТопМеню
(Администрирование).

---

## 4. Ближайшие действия

1. **Привязка БУ к model_line_item (опция со своей кодировкой).** После
   удаления `control_voltage`/`signal_power`/`location` из ControlUnit БУ стал
   чисто «описанием сигналов и датчиков», пригодным для разных моделей и
   напряжений серии. Привязку делаем отдельно: БУ доступен для конкретной
   модели привода (model_line_item) как опция со своей кодировкой.
   Направление (обсудить): оставляем схему с through-моделями и кодировками
   (как у valve_data/EaSignalMatrixEntry), привязка — к новой модели БУ
   (ControlUnit), а не к legacy-справочнику. Требует выработки: сущность
   привязки, кодировка (вклад в артикул), приоритет строк, обратная
   совместимость с `series-units` (серия × напряжение → набор БУ).
2. Вывести nullable-числовые поля физики в редактор справочников
   (`control-signals`/`feedback-signals`): формы намеренно не показывают
   `current` (CuControlSignal) и `max_voltage`/`max_current`/
   `resistance_kohm`/`max_power_w`/`turns`/`wires` (CuFeedbackSignal) —
   generic-сохранение (`save()` в `EaControlAdminPage.vue`) превращает пустое
   число в `0` и портит `null`. Нужна аккуратная обработка пустого значения:
   для nullable-числовых полей отправлять `null`, а не `0`.
3. Проверить визуально: /admin/ea-control → Конфигуратор опций (слоты CMD_*),
   Редактор БУ (матрица с CMD_WIRING/сигнальными слотами), Справочники
   (формы, полярность), Превью БУ (выбор схемы цепей → перерезолв набора
   сигналов), Описание БУ.
4. Прогнать `cd frontend; npm run build`.
5. Полировка: переименовать `EaControlStructurePage.vue` /
   `EaControlConfiguratorPage.vue` (убрать суффикс «Page», т.к. это
   компоненты); починить локаль превью (`route.meta.locale` → глобальная
   локаль из i18n).
6. Описать остальные БУ по `bu_template.md` в новой структуре сигналов;
   уточнить количества отверстий демо-наборов M20/M25/PG16 (сейчас
   placeholder — 3 шт.).

Выполнено 2026-10-31: рефакторинг «TextChoices → справочники» доведён до
конца — тесты на FK-объектах (ea_control и electric_actuators: 108/108),
`CuPolarity` зарегистрирован в админке, новые справочники привязаны в
`admin_site.py` к блоку 'ea_control', фронт переведён на `source`-селекты
(справочники выдаются generic CRUD).

---

## 5. Дальнейшие действия

1. Перенос абстракций из `ea_control/models/abstract.py` в `core`
   (`ConfigSlot`/`SlotOption`/`SlotMatrixEntry`/`SlotRule`/`ConfigSnapshot`).
2. Migrate-команды из legacy: `migrate_cu_from_params`,
   `migrate_cu_series_links`, `migrate_cu_profiles` (маппинг по кодам).
3. Интеграция в ЭП (фаза 4): переключение `/admin/ea-constructor` на
   `ControlUnit`/`CuMatrixEntry` по критерию готовности (данные перенесены +
   паритет AOX AR01E/AR11E/AR21E/CLFZE). Сюда же — агрегация «Корпус+Блок»
   для подбора КВ (код сборки, не хранение) и скрытие/замена вводов корпуса
   у навесного БУ.
4. `config_snapshot` на `ElectricActuatorCatalogItem` (+ общий
   `ConfiguredProduct`).
5. Судьба справочников-копий vs ЭП-оригиналов (слияние/замена).
   Классифицирующие поля уже общие с ЭП (см. §2); в копиях осталась физика,
   специфичная для БУ. `CuFeedbackSignal` обогащён из `EaFeedbackSignal`
   (`enrich_cu_feedback_signals`); `CuControlSignal` намеренно остаётся только
   аналоговым — дискретные команды выражены слотами CMD_*.
6. Привязка БУ к model_line_item — реализация решения из §4.2.
7. Промоушн БУ в узел `EquipmentType` — триггер: собственный каталог или
   состав из позиций.
8. Цена — вне scope; отдельная сущность по общему паттерну.
9. **Правила: перейти от «одно правило на слот» к списку правил с
   приоритетом** (в «Редакторе БУ» → «Редактор доступных опций»). Сейчас на
   слот хранится одно правило (exact > in > not_in); несколько правил разного
   действия/приоритета на одном слоте невыразимы. Кандидат после проверки
   пользователем — возможно, сложность не понадобится.
10. **Починка свежей цепочки миграций (fresh-установка).** Частично сделано
    2026-10-31: `electric_actuators/0030` (снятие FK перед удалением id
    через-модели), `electric_actuators/0031` (возврат FK на parent-link PK),
    `options/0002` (дубль CreateModel убран). Дальше падает
    `pa_controls/0050_posi_feedback_seed` — data-миграция ищет словари
    (ContactForm/ContactState/SignalType/LimitSwitchSensorVariety) через
    `.first()`, на свежей БД их ещё нет — нужно get_or_create внутри
    миграции. После — прогнать полный `migrate` на scratch-БД до конца и
    фиксить следующие сломанные звенья (тест `electric_actuators` на свежей
    БД — контрольная точка).
