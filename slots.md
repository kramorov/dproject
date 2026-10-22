Архитектурный паттерн: «Узлы, Слоты и Универсальные Матрицы»

> **Статус документа.** Разделы 1–5 — первоначальная идея и материал обсуждения,
> **не императив реализации**. Они оставлены как фон и мотивация; ряд формулировок
> в них (GenericFK, координаты, плоский JSON, локальный расчёт в браузере)
> пересмотрен в главах «Предлагаемый паттерн» и «Что изменить для унификации».
> Целевая архитектура — в этих двух главах и в блоке «Решения» в конце
> «Предлагаемого паттерна».

Назначение: Конфигурирование сложного промышленного оборудования с высокой вариативностью параметров, исключающее комбинаторный взрыв в базе данных и хардкод логических правил.

1. Фундаментальный принцип (Золотое правило)

• Физика и Характеристики железа — строго типизируются. Каждая сложная сущность (платы, кабели, счетчики) имеет свою кастомную Django-модель с уникальным набором физических полей.
• Взаимосвязи и Ограничения — универсальны. Логика совместимости, ценообразование и поведение интерфейса управляются 
тремя абстрактными сквозными паттернами через механизм ContentType.

2. Структурный контракт (Как строятся данные)

2.1. Слот (ParameterSlot)

Слот — это абстрактная «розетка» или точка конфигурации в интерфейсе (например, «Напряжение питания», «Основной датчик момента»). Слот не хранит данные, он лишь декларирует:
• Системный уникальный код (code).
• Мультиязычное имя в формате JSON-i18n ({"ru": "...", "en": "..."}).
• Строгий тип данных (DataType: выбор из списка, число, ссылка на модель).

2.2. Опция (Option)
Опция — это вариант заполнения слота. Опция может быть:
• Простой: содержит только текст (мультиязычный JSON) и код-модификатор для артикула (например, значение «Да», «SPDT», «Нормально-замкнутый»).
• Сложной (Объектной): через полиморфную связь (GenericForeignKey) указывает на конкретную физическую Django-модель железа (например, на запись в таблице ControlBoard).

2.3. Узел конфигурации (ConfigurationNode)
Узел отвечает за иерархию, визуальную вложенность и группировку слотов на фронтенде (например, «Привод ➔ Блок управления ➔ Плата входов»). 
Узлы могут бесконечно вкладываться друг в друга (parent_node), формируя дерево шагов конфигуратора. Каждый узел содержит плоский список привязанных к нему слотов с указанием порядка их сортировки.

3. Логический контракт (Три универсальных паттерна)
Вся бизнес-логика настраивается вручную через кастомную фронтенд-админку и оперирует исключительно тремя паттернами, которые одинаково обрабатывают любые типы данных.

Паттерн А: Матрица совместимости (UniversalCompatibilityMatrix)
• Зона ответственности: Логика ограничений каталога. Отвечает на вопрос: «Доступна ли опция Х для выбора, если мы сейчас находимся в точке Y?».
• Принцип работы: На основе заданных координат [Производитель + Модель + Вольтаж] определяет массив разрешенных ContentType-объектов (опций или железок) и указывает, какой из них выставить на фронтенде по умолчанию (is_default).

Паттерн Б: Матрица цен (UniversalPriceMatrix)

• Зона ответственности: Экономика продукта. Отвечает на вопрос: «Какова итоговая стоимость сборки в точке Y?».
• Принцип работы: Использует аддитивную модель наценок. По заданным координатам система ищет все подходящие строки (базовая цена модели, наценка за вольтаж, наценка за конкретную плату) и математически суммирует их модификаторы цены (price_modifier).

Паттерн В: Движок динамических правил (AdvancedRule)

• Зона ответственности: Поведение интерфейса на лету (Event-driven UI). Отвечает на вопрос: «Если пользователь прямо сейчас кликнул на опцию Х, как должна измениться доступность других полей конфигуратора?».
• Принцип работы: Оперирует плоской логикой: Если Слот_А [Оператор проверки] Значение_JSON ➔ Применить к Слоту_Б Действие (Скрыть / Показать / Заблокировать / Сделать обязательным).

4. Контракт транзакций (Результат сборки)

Итоговый сконфигурированный продукт (заказ или карточка готового привода в каталоге) сохраняется в модель ConfiguredProduct по следующим правилам:
1. Базовые неизменяемые параметры «механического железа» (серия, габарит) пишутся в классические ForeignKey поля для обеспечения моментального поиска.
2. Вся конфигурация электроники, сигналов и опций Блока Управления сохраняется в единое плоское поле control_unit_config = models.JSONField() в виде пар {"slot_code": "selected_value_or_id"}.
3. Система гарантирует обратную совместимость: если при изменении линеек оборудования в базу добавляется новый слот, старые инстансы приводов не перегенерируются, а система подставляет для них дефолтное значение («fallback») из справочника слотов.
4. Итоговый артикул (full_sku) автоматически генерируется на бэкенде в методе save() путем склеивания базового артикула и суффиксов (code_modifier) всех выбранных в JSON опций за один проход по базе.

5. Контракт взаимодействия (Бэкенд ➔ Фронтенд)

Бэкенд полностью абстрагирован от физического смысла деталей. При запуске конфигуратора он отдаёт фронтенду строго стандартизированный JSON-пакет:
• Дерево узлов и слотов для отрисовки интерфейса.
• Массив доступных опций (со строгой типизацией данных и мультиязычными текстами).
• Плоский список правил совместимости и интерактивного поведения интерфейса.
Фронтенд, используя этот пакет, производит всю калькуляцию доступности полей и предварительный расчет цены локально в памяти браузера, обеспечивая моментальный отклик интерфейса для пользователя без постоянного подёргивания сервера.
Этот текст можно дополнить готовыми UML-диаграммами связей или шаблонами JSON-ответов для вашего фронтендера. С какого элемента конфигуратора вы планируете начать писать код — создать Django-модели по этой спецификации или зафиксировать формат обмена данными (API)?

---

## Сравнение предлагаемых паттернов и существующих

> Сводка анализа 2026-10-22. Зафиксирована здесь, чтобы не повторять анализ заново.
>
> **Уточнено позже** (см. «Предлагаемый паттерн → Решения»): концепт разделён
> на **две модели** (Требование и Слот), цена — вне scope, калькулятор — на
> бэке. Ниже — исходный срез на дату 2026-10-22.

**Факт из кода:** моделей из этого документа (`ParameterSlot`, `ConfigurationNode`, `UniversalCompatibilityMatrix`, `UniversalPriceMatrix`, `AdvancedRule`, `ConfiguredProduct`) в проекте нет. Это спецификация-предложение. При этом сама идея уже реализована **тремя разными словарями**:

- **ЭП** — `electric_actuators`: `EaSignalSlot` / `EaSlotOption` / `EaSignalMatrixEntry` / `EaWiringDiagramBinding`. (Отдельно: `params.ControlUnitSignalProfile` — физический профиль «роль → датчик», в ЭП-схеме не используется.)
- **Конфигуратор** — `configurator`: `EquipmentTypeParameter` / `ParameterRule` / `ParameterBinding` / `DerivationRule` (+ `assemblies.AssemblyRequirements` / `ComponentRequirement`).
- **AI** — `ai_assistant`: `FilterDefinition` / `CompositionGroup`; классификатор — `core.EquipmentType`.

Сопоставление понятий `slots.md` ↔ существующее:

- **Золотое правило** (физика типизирована, связи универсальны) — **соответствует**. ЭП устроен именно так: типизированные справочники (`EaSignalForm`, `EaControlSignal`, `EaFeedbackSignal`, `EaCommProtocol`, `EaFeedbackDevice`, `ActuatorHeaterSupply`, `ControlUnitInstalledOption`) + универсальные `EaSignalSlot`/`EaSlotOption`/`EaSignalMatrixEntry`. Расхождение в механике: у нас типизированные FK с дискриминатором `EaSlotOption.kind` (`signal`/`heater`/`none`/`pair`), а не голый `GenericForeignKey`/`ContentType`.
- **ParameterSlot** ≈ `EaSignalSlot` ≈ `EquipmentTypeParameter` ≈ `FilterDefinition` — **один концепт под тремя именами**.
- **Option** ≈ `EaSlotOption` + `EquipmentTypeParameter.get_options()` (6 стратегий). «Сложная опция» — типизированный FK (`feedback_signal`/`control_signal`/`protocol`/`heater_supply`/`device`), а не один `GenericFK`.
- **ConfigurationNode** — **отсутствует**. Слоты ЭП плоские (`sorting_order`), иерархия есть только у `EquipmentType.parent` (классификатор) и `CompositionGroup.parent` (состав), но оба вкладывают **типы оборудования**, а не слоты одного изделия.
- **Паттерн А (CompatibilityMatrix)** ≈ `EaSignalMatrixEntry` (+ профиль БУ через бесскоуповые строки). У нас **больше возможностей**: скоуп `brand → model_line → body → model_line_item` с наследованием, координаты `БУ × напряжение × режим`, `availability std/opt/na`, `is_default`, `bundle`, `conflicts`. `ParameterRule` — другая роль: сравнение значения с требованием (фильтр), а не доступность опции.
- **Паттерн Б (PriceMatrix)** ≈ `price.EAPriceConstructor` (аддитивно: base + сумма надбавок). Но ключ — строковое `option_field` + `option_id`, а не `slot`/координаты; сигнальные опции профиля БУ ценой не покрыты; `power_supply` ссылается на legacy `ElectricPowerSupplyOption`.
- **Паттерн В (AdvancedRule)** — **отсутствует как модель**. Логика размазана: `conflicts` (M2M), `bundle`, `clean()`-валидации (`device.emits`, `heater` только `HEATER_*`, `protocol` только `PROTOCOL`) и хардкод резолвера.
- **ConfiguredProduct** ≈ `ElectricActuatorCatalogItem` (+ черновик `ElectricActuatorConstructor`). Но выбор хранится как M2M `matrix_rows` + отдельные FK, а не плоским JSON `{slot_code: value}`.
- **full_sku** ≈ `SKUMixin` + `generated_ext_code` + `ext_encoding`/`encoding`. Результат тот же, механика другая (шаблон + `services/ea_ext_code.py`, а не конкатенация `code_modifier` в `save()`).
- **Backend→Frontend JSON-пакет** ≈ `configurator.generate_json_schema(variant)` + `filter-schema` API. Для ЭП конфигуратор — серверный Django-admin (`/admin/ea-constructor`), локального «калькулятора в браузере» нет.

**Вывод:** `slots.md` — не новый паттерн, а абстрактное переописание существующего. Правильный путь — **унификация словаря** на базе `equipment_type` и достройка только недостающего (дерево узлов, движок правил, обобщённая цена, JSON-снимок результата, фронт-пакет), а не третья параллельная система.

---

## Предлагаемый паттерн

Ключевое решение: паттерн транслируется в схему `equipment_type` и делится на
**два независимых рода листьев** — «требования» и «слоты». Они разные по сути
и наполнению, поэтому это **две модели**.

### Глоссарий (канонические термины)

- **Узел (Node)** — `core.EquipmentType` (тип/подтип) +
  `ai_assistant.CompositionGroup` (состав, `group_type` `required|optional|xor`)
  + узлы-секции (группировка слотов). Отвечает за иерархию и вложенность.
- **Требование (Requirement)** — `configurator.EquipmentTypeParameter`.
  Условие **подбора и сравнения**: `field_path`, `filter_type`,
  `data_source_type`, `parameter_rule`, `is_required`, `required_condition`,
  `inherit_mode`. Используется каталогом (фильтры) и AI (extract). Сюда
  поглощается `FilterDefinition`.
- **Слот (Slot)** — новая модель `ConfigSlot` (обобщает `EaSignalSlot`). Точка
  **выбора внутри конфигурации изделия**: `selection_mode`
  (`single|multi|xor|bundle`), `slot_kind` (`value|object|subtype`), `bundle`,
  `conflicts`. Опции слота — `ConfigSlotOption` (обобщает `EaSlotOption`).
- **Опция (Option)** — значение: для слота — `ConfigSlotOption`; для
  требования — допустимые значения через `options_config`/`enum_values`.
- **Матрица (Matrix)** — доступность опций слота по контексту (Паттерн А).
- **Правило (Rule)** — два рода: `ParameterRule` (сравнение значений, для
  требований/фильтров) и `SlotRule` (динамика UI, для слотов).

Граница ответственности:

- **Требование** → «какое оборудование подходит под условия» (фильтр каталога,
  сравнение, AI-извлечение).
- **Слот** → «какие опции выбраны внутри изделия» (конфигурация, артикул,
  спецификация).

Матрица (А) и правила динамики (В) работают со **слотами**; фильтры и сравнение —
с **требованиями**. Это снимает неоднозначность границы А↔В: оба паттерна
принадлежат домену слотов.

### Детали

- Мост «слот = подтип оборудования»: `slot_kind=subtype` = `options_config.model
  = core.EquipmentType` + фильтр по `parent`. Выбор подтипа — обычный слот со
  списком опций-подтипов.
- Полиморфизм опции — гибридный (см. «Решения» в конце главы): типизированные FK
  + `kind` для целостности, `ContentType`/строковая ссылка — для открытых
  ссылок на модель.

### Три универсальных паттерна (применительно к слотам)

- **Паттерн А — доступность (Матрица).** Обобщить `EaSignalMatrixEntry` до
  `SlotMatrixEntry`: `slot` (FK → `ConfigSlot`) + контекст (типизированные FK
  `brand`/`model_line`/`body`/`model_line_item`/`control_unit`/`power_supply`/
  `mode` + расширяемый `context_extra` JSON) + `option` + `availability
  std/opt/na` + `is_default` + `bundle` + `conflicts`.
- **Паттерн Б — цена.** **Вне scope конфигуратора.** Это пример применимости
  паттерна к другой сущности; для цен будет отдельная сущность по общему
  паттерну. Сейчас `price.EAPriceConstructor` **не трогаем**.
- **Паттерн В — динамика (SlotRule).** Новый `SlotRule`: `when {slot, operator,
  value}` → `then {action: show|hide|block|require|set_default, target_slot}` +
  `priority` + `is_active`. Заменяет хардкод резолвера; `bundle`/`conflicts`
  остаются декларативными в матрице. Операторы/семантика сравнения берутся из
  того же словаря, что и фильтры (`filter_type`/`ParameterRule.match_type`).

Результат и профили:

- **Результат** — `ElectricActuatorCatalogItem` (+ общий `ConfiguredProduct`):
  базовые механические параметры — классические FK; выбор —
  материализованный `config_snapshot = JSONField({slot_code: value})`, где
  `matrix_rows` остаётся источником истины, а JSON — портируемый снимок +
  fallback-дефолты. `full_sku` — из `encoding`/`ext_encoding` опций.
- **Профиль** — набор default-значений слотов для типа БУ (бесскоуповые строки
  матрицы `EaSignalMatrixEntry`). Это механизм «варианты описания БУ», который
  можно менять без хардкода. (`params.ControlUnitSignalProfile` — отдельный
  физический профиль «роль → датчик», в ЭП-схеме не используется.)
- **Вычисление** — на **бэке**: доступность (А), правила (В), цена (когда
  появится). Фронт отрисовывает и отправляет изменения; сервер — источник
  истины и валидатор.

Что **изменить** в существующем и что **добавить**:

1. Развести две модели: **Требование** = `EquipmentTypeParameter` (фильтр/сравнение),
   **Слот** = новый `ConfigSlot` (конфигурация изделия). Не сливать.
2. В `EquipmentTypeParameter` добавить `inherit_mode`/`is_interface`, поглотить
   `FilterDefinition`, свести дубли осей (`field_type`/`param_type`,
   `data_source_type`/`options_source`).
3. Создать `ConfigSlot`/`ConfigSlotOption` (обобщение `EaSignalSlot`/`EaSlotOption`)
   и отобразить ЭП-схему на них.
4. `CompositionGroup` — «узел состава»; `group_type` в `EquipmentType` не переносить.
5. Добавить `SlotRule` (Паттерн В) и перевести на него правила ЭП.
6. Добавить `config_snapshot` на карточку ЭП и на общий `ConfiguredProduct`.

### Решения (Decision Log)

1. **Две модели:** Требование (`EquipmentTypeParameter`) и Слот (`ConfigSlot`).
2. **Фильтры каталога** (`FilterDefinition`) интегрируются в Требование
   (`filter_type` + `data_source_type` + `parameter_rule`).
3. **Цена** — вне scope; отдельная сущность по общему паттерну, обсуждается
   как пример применимости.
4. **GenericFK:** проблема была в описании, не в реализации — полиморфизм уже
   реализован через `product_model = FK(ContentType)` + `product_model_ref` +
   типизированные FK + `kind`. Документ описывает это точно, а не заявляет
   «без GenericFK».
5. **Калькулятор** — на бэке.
6. **Версионирование** — не для моделей конфигуратора (слоты/узлы/правила);
   только для вариантов сборок (уже в `assemblies`).
7. **Изменения описания/опций БУ** — перевод на слоты делает их конфигурацией
   данных, а не кодом.

---

## Предлагаемая реализация паттерна на примере блока управления ЭП

Эталонная реализация паттерна на электроприводе. Дерево опций (графически):

```
ЭЛЕКТРОПРИВОД  (core.EquipmentType: electric-actuator)          [УЗЕЛ-ТИП]
│
├─ КОРПУС / ПРИВОД (механика)                                    [УЗЕЛ-СЕКЦИЯ]
│  ├─ ⬦ power_supply      Напряжение питания       → ElectricPowerSupplyOption / params.PowerSupplies
│  ├─ ⬦ temperature       Температурное исполнение → ElectricTemperatureOption (+ heater_supply)
│  ├─ ⬦ ip                IP-защита                → params.IpOption
│  ├─ ⬦ exd               Взрывозащита             → ElectricExdOption
│  ├─ ⬦ body_coating      Покрытие корпуса         → params.BodyCoatingOption
│  ├─ ⬦ body_color        Цвет                     → params.BodyColor
│  ├─ ⬦ hand_wheel        Ручной дублер            → params.HandWheelInstalledOption
│  ├─ ⬦ turn_angle        Угол поворота            → ElectricTurnAngleOption
│  └─ ⬦ cable_glands      Кабельные вводы          → CableGlandHolesSet
│
└─ БЛОК УПРАВЛЕНИЯ  (подтип equipment_type / слот выбора БУ)     [УЗЕЛ-ТИП]
   ├─ ⬦ control_unit      Тип БУ (БУ / нет / позиционер) → params.ControlUnitInstalledOption (через AllowedControlUnitOption)
   ├─ ⬦ cu_power_supply   Питание БУ                        → params.PowerSupplies (через AllowedControlUnitOption)
   │
   ├─ СИГНАЛЫ УПРАВЛЕНИЯ (входы)                               [УЗЕЛ-СЕКЦИЯ]
   │  ├─ ⬦ LOCAL_CONTROL  Местное управление  → BUTTONS / SELECTOR / NONE
   │  ├─ ⬦ CMD            Команды (multi)     → OPEN / CLOSE / STOP / EMERGENCY / MODE / REMOTE (DISC_AC / DISC_DC)
   │  └─ ⬦ SETPOINT       Уставка 4-20        → AN_4_20_ACTIVE / AN_4_20_PASSIVE / AN_4_20_HART
   │
   ├─ ОБРАТНАЯ СВЯЗЬ (выходы)                                   [УЗЕЛ-СЕКЦИЯ]
   │  ├─ ⬦ LIMIT_SWITCHES   Концевые     → FB_END_OPEN/CLOSE  (SPDT E1 / DPDT E2)  [bundle OPEN+CLOSE]
   │  ├─ ⬦ WAY_SWITCHES     Путевые      → FB_WAY_OPEN/CLOSE  (SPDT W1 / DPDT W2)  [bundle]
   │  ├─ ⬦ TORQUE_SWITCHES  Моментные    → FB_TORQUE_OPEN/CLOSE (SPDT T1 / DPDT T2)[bundle]
   │  ├─ ⬦ POSITION_FEEDBACK Позиционная → 4-20 ACTIVE(TA)/PASSIVE(T)/HART(TH), POT(P), MWG [bundle MWG]
   │  ├─ ⬦ THERMAL_SENSOR   Теплозащита  → NO_SENSOR / FB_OVERHEAT_NC / FB_OVERHEAT_SPDT (+ device)
   │  ├─ ⬦ INDICATOR        Индикация    → LED_SET(D) / BLINKER(B) / DB / LCD(L) / LB
   │  ├─ ⬦ TURN_COUNTER     Счётчик      → NONE / MECH(M) / ELECTRONIC(E) / EM / MF / EMF
   │  └─ ⬦ (сигналы состояния) FB_STOP, FB_LOCAL_REMOTE, FB_READY_NO, FB_ALARM*, FB_PHASE_LOSS, FB_TORQUE_4_20MA, FB_TURN_COUNTER_NO
   │
   ├─ СВЯЗЬ                                                    [УЗЕЛ-СЕКЦИЯ]
   │  └─ ⬦ PROTOCOL        Шина         → PB / PN / MB / MT / FF / HART
   │
   └─ ОБОГРЕВ / ПИТАНИЕ                                        [УЗЕЛ-СЕКЦИЯ]
      └─ ⬦ HEATER_CONTROL_UNIT  Обогрев БУ → NO_HEATER / CU_CIRCUIT(C) / SEPARATE_LINE(S)
```

**Какие существующие модели куда привязываются:**

- Узел «Электропривод» = `core.EquipmentType` с `code='electric-actuator'` (источник шаблонов name/description — уже работает через `TemplateMixin`).
- Узел «Блок управления» = дочерний `EquipmentType` (подтип) **и** слот `control_unit` с опциями-подтипами БУ — это и есть трансляция «слот = подтип».
- Слоты = `configurator.EquipmentTypeParameter`, в которые отображаются существующие `EaSignalSlot` (`LOCAL_CONTROL`, `CMD`, `SETPOINT`, `LIMIT_SWITCHES`, `WAY_SWITCHES`, `TORQUE_SWITCHES`, `POSITION_FEEDBACK`, `PROTOCOL`, `THERMAL_SENSOR`, `HEATER_CONTROL_UNIT`, `INDICATOR`, `TURN_COUNTER` и отдельные сигналы состояния).
- Опции слотов = `EaSlotOption` (каталог, `ext_encoding` = код позиции ext) + типизированные FK на `EaControlSignal`/`EaFeedbackSignal`/`EaCommProtocol`/`EaFeedbackDevice`/`ActuatorHeaterSupply`.
- Доступность = `EaSignalMatrixEntry` (скоуп × БУ × напряжение × режим), бесскоуповые строки = профиль сигналов типа БУ.
- Динамика = новый `SlotRule` вместо хардкода: `conflicts` и `bundle` остаются в матрице, всё остальное — правила.
- Цена = `EAPriceConstructor`, генерализованный до ключа `slot` + `option`.
- Результат = `ElectricActuatorCatalogItem` (M2M `matrix_rows`) + материализованный `config_snapshot` JSON.
- Профиль БУ = бесскоуповые строки матрицы `EaSignalMatrixEntry` (без скоупов); `params.ControlUnitSignalProfile` — отдельный физический профиль (роль → датчик), в ЭП-схеме не используется.

**Возможные связи между ветвями дерева** (кросс-слотовые зависимости):

- **Тип БУ → сигнальные слоты** (профиль): `int-*` открывает `SELECTOR`+`LCD`+`LIMIT_SWITCHES`(int-варианты), базовый БУ — `BUTTONS`+`LED_SET`, `NONE` — скрывает все сигнальные слоты. Это Паттерн А (доступность) + Паттерн В (show/hide).
- **Тип БУ → `PROTOCOL`/`HART`**: HART — отдельный тип БУ, а не опция; шина доступна только интеллектуальным БУ.
- **`SETPOINT` ↔ `POSITION_FEEDBACK` (HART)**: HART привязан к аналоговой петле — одна ext-позиция `{hart}`; выбор HART в одном слоте влияет на другой.
- **`POSITION_FEEDBACK=MWG` ↔ `LIMIT_SWITCHES`/`TORQUE_SWITCHES`**: атомарный пакет через три слота (`bundle`); если хоть одна строка недоступна — пакет недоступен целиком.
- **Внутри слота E1/E2, W1/W2, T1/T2**: взаимоисключение (`selection_mode=single`), а пары `OPEN+CLOSE` атомарны через `bundle`.
- **`THERMAL_SENSOR` ↔ `device`**: опция требует `EaFeedbackDevice`, и `device.emits` должен содержать сигнал — валидация типизированного FK.
- **`HEATER_CONTROL_UNIT` ↔ тип БУ**: слот скрыт для `kind=NONE` (Паттерн В hide).
- **`cu_power_supply` ↔ тип БУ**: `null` = от питания привода; у `int-*` — отдельное питание (через `AllowedControlUnitOption`).
- **Механика `temperature` ↔ обогрев привода**: `heater_supply` — свойство температурной опции (`ElectricTemperatureOption`), а не слот.
- **`EaAccessDeviceOption` ↔ тип БУ**: для не-int БУ доступно только «нет» (Паттерн В block).

Так образцовое решение на бэке — дерево `EquipmentType` + слоты `EquipmentTypeParameter` + матрица + правила + цена + `config_snapshot`, а на фронте — один пакет `{tree, slots, options, rules, price, defaults}` с локальным расчётом доступности и цены. Этот же образец затем применяется к другим моделям (пневмоприводы, пневматические фитинги, соленоидные клапаны и т.д.).

---

## Реализация предлагаемого паттерна для подбора подходящего оборудования

### 1. Применимость (анализ)

Вывод: паттерн применим **напрямую**, и большая часть механизма уже есть в
коде — его надо не строить заново, а **дооформить декларативно и визуально**.

Существующие кирпичи (проверено по коду):

- `ai_assistant.CompositionGroup` — «какое оборудование может входить в
  состав»: `group_type` (`required | optional | xor`), вложенность `children`,
  ссылки `references`, M2M `equipment_types`. Это и есть «схема состава».
  Важно: состав описан в `CompositionGroup`, а не в самом `EquipmentType` —
  `EquipmentType` остаётся классификатором типов.
- `configurator.DerivationRule` — «по схеме заполняем автоматически»:
  `source_type → target_type`, `source_product_field → target_param`,
  `transform`, `condition`, `priority`. Ядро
  `cascade.resolve_derivation_params(...)` — чистая функция, которую
  переиспользуют оба дерева (configurator `cascade_after_select` и ai_assistant
  `TreeProcessor.select_product`).
- `configurator.FittingPattern` / `FittingPatternItem` — динамическое создание
  связанных позиций (фитинги) с подстановкой `parent.<field>`.
- `resolver.resolve_effective_requirements` — приоритет `own > global >
  cascade` + трансляция `param_name → field_path` через
  `EquipmentTypeParameter`.
- `EquipmentTypeParameter` — слот: `field_path`, `data_source_type`,
  `options_config`, `parameter_rule`, `is_required`, `required_condition`.
- Унификация имён параметров уже заведена: `temp_min → LimitSwitchBox.work_temp_min
  / GearBox.work_temp_min / CableGland.work_temp_min`, `exd → …_id`,
  `ip → …_id`, `thread` — один `param_name`, разные `field_path`.

Что это уже покрывает:

- **БКВ → кабельные вводы** — тип/размер резьбы, взрывозащита, температура:
  `DerivationRule` + унификация `param_name`.
- **Соленоидный клапан → КВ + фитинги** — `CompositionGroup` (состав) +
  `DerivationRule` (совместимость) + `FittingPattern`.
- **Сборка пневмопривода (несколько уровней)** — `CompositionGroup`
  (`pa-kit`, вложенность + `references`).

### 2. Как работает механизм (ручной подбор и AI)

В связанную позицию приходят значения двух **разных** родов, и их нельзя
смешивать:

**А. Совместимость (жёсткий интерфейс)** — берётся из факта выбранной модели
родителя:

- БКВ.thread_type → КВ.thread_type (резьба КВ должна совпасть);
- БКВ.thread_size → КВ.thread_size;
- БКВ.exd → КВ.exd (класс взрывозащиты — совместимый);
- ПП.port → соленоид.connection, ПП.mounting_flange → МК.flange.

Реализация: `DerivationRule` (каскад из `selected_product_specs`), приоритет
каскада ниже требований пользователя.

**Б. Требование пользователя (наследуемое окружение)** — берётся из запроса и
применимо ко **всем** позициям сборки:

- `temp_min` / `temp_max`, `ip`, (частично `exd` — требование среды).

Реализация: `global_requirements` (или `own_requirements`) резолвятся на все
компоненты с тем же `param_name` через `field_path`.

**Сценарий БКВ → КВ (ручной конфигуратор):**

1. Пользователь выбирает БКВ.
2. По `CompositionGroup` у БКВ есть опциональный ребёнок «Кабельный ввод».
3. По `DerivationRule` в `cascade_params` КВ проставляются thread_type /
   thread_size / exd (из модели БКВ).
4. По global/own проставляется температура (из требований сборки).
5. Неизвестными остаются **только** тип кабеля, его диаметр, броня/металлорукав
   → конфигуратор запрашивает только их.
6. Фильтр КВ работает по `effective = own > global > cascade`.

**Сценарий AI (наследование требований, пример −30 / −60):**

1. Запрос: «…температура минимум −30…».
2. `extract` кладёт `temp_min = −30` в `global_requirements`.
3. Подобрали БКВ; у модели `work_temp_min = −60` (удовлетворяет, даже лучше).
4. Для КВ требование = **−30** (global), а не −60 (факт модели) — приоритет
   `global > cascade` это гарантирует.
5. Каскад из БКВ несёт только интерфейс (thread/exd), но не температуру.

Ключевое правило, которое надо зафиксировать в модели: **«факт выбранной
модели» ≠ «требование».** Требование наследуется из запроса (global/own),
интерфейс — из модели родителя (cascade). Отсюда — поле `inherit_mode` на слоте
(раздел 3).

### 3. Что изменить/добавить в модели equipment_type

1. **`EquipmentTypeParameter` (+ поля):**
   - `inherit_mode` = `none | parent_model | global_requirement` — откуда слот
     берёт значение, если пользователь не задал его сам;
   - `is_interface` (bool) — параметр является физическим интерфейсом
     (жёсткая совместимость → каскад из модели родителя);
   - `group` (опционально) — группировка слотов в узлы-секции внутри типа.
2. **`DerivationRule` (+ поле `source_kind`)** = `parent_model` (default,
   текущее поведение) | `global_requirement` — чтобы правило могло явно
   пробрасывать и требование, а не только факт модели. (Частично избыточно:
   global и так резолвится по всем типам; поле нужно для наглядности и
   валидации схемы.)
3. **`CompositionGroup`** оставить «узлом состава»; связь с конкретными
   слотами — через `EquipmentTypeParameter` на входящем `EquipmentType`
   (отдельной связи «узел → слот» не требуется).
4. **`ParameterRule` / `ParameterBinding`** применить к КВ и фитингам:
   `thread_compatible`, `exd_compatible` (filter_type'ы уже есть), чтобы
   совместимость считалась семантически (`hierarchy`/`compatible`), а не
   точным равенством.
5. **`FittingPattern`** — подстановку `parent.<field>` расширить на значения,
   пришедшие каскадом (сейчас читает только из `selected_product_specs`).

### 4. Фронтенд: что уже есть (проверено) и что доделать

Уже реализовано:

- `/admin/pipeline-config` — `PipelineConfigPage.vue`: CRUD-таблицы для
  `ParameterRule`, `ParameterBinding`, `DerivationRule`, `FittingPattern`,
  классификатора `EquipmentType`; генерация JSON-схем из ETP.
- `components/admin/EquipmentTypeEditor.vue` (вкладка «Equipment Types»):
  редактирование `EquipmentType` (`SpecTemplateEditor`, `SemanticsEditor`,
  `HintsEditor`, `ListParamsEditor`) **и** таблица слотов
  `EquipmentTypeParameter` — но пока только часть полей (`param_name`,
  `field_path`, `param_type`, `unit`, `compare_*`, `is_required`).
- `/admin/skill-config` — `SkillConfigPage.vue`: визуальное дерево состава —
  компоненты `TreeNode.vue`, `CompositionGroupNode.vue`, `EquipmentTypeNode.vue`,
  `MBOMItemNode.vue` (вкладки «Дерево» / «Конструктор» / «MBOM», dblclick-модалки,
  drag-drop).
- `/configurator/pa-kit` — `ConfiguratorPaKitPage.vue`; `/admin/assemblies` —
  `AssembliesPage.vue`.
- `/admin/configurator-rules` — `ConfiguratorRulesPage.vue`: теперь
  заглушка-редирект в Pipeline Config + генерация JSON-схемы.

Чего не хватает (визуальный редактор):

1. **Единый граф-редактор «узлы + слоты + связи».** Сейчас узлы живут в
   SkillConfigPage (дерево), а связи (DerivationRule/ParameterBinding/
   FittingPattern) — отдельными таблицами в PipelineConfigPage. Нужна страница,
   где узел = `EquipmentType`/`CompositionGroup`, слот = `EquipmentTypeParameter`,
   а рёбра = `DerivationRule` (стрелка source→target с подписью field→param) +
   `ParameterBinding`.
2. **Полный редактор слота** — вывести в EquipmentTypeEditor недостающие поля:
   `data_source_type`, `filter_type`, `options_config`, `parameter_rule` и новые
   `inherit_mode`, `is_interface` (+ `selection_mode`, `slot_kind` из главы
   «Предлагаемый паттерн»).
3. **Визуализация наследования** — показать, какой параметр глобальный
   (пробрасывается во все типы) и какой каскадный (из модели родителя).
4. **Редактор состава и правил в одном графе** — чтобы связь «БКВ → КВ»
   задавалась одним жестом (узел + ребро), а не в двух местах.

### 5. План внедрения

**Фаза 1 — Модели:**
1. Миграция: `EquipmentTypeParameter.inherit_mode` / `is_interface` / `group`;
   `DerivationRule.source_kind`.
2. Привязать `ParameterRule` (`thread_compatible`, `exd_compatible`) к КВ и
   фитингам через `ParameterBinding`.

**Фаза 2 — Сервисы:**
3. `resolve_effective_requirements`: учитывать `inherit_mode` — не перетирать
   каскадом параметр, помеченный `global_requirement`, если значение пришло из
   global/own.
4. `resolve_derivation_params`: поддержать `source_kind = global_requirement`.
5. `TreeProcessor.extract`: окружение (`temp_min`/`temp_max`/`ip`/`exd`)
   класть в `global_requirements`, интерфейсные параметры — в узловые
   требования; промпт extract формировать из ETP с учётом `inherit_mode`.

**Фаза 3 — Данные:**
6. CompositionGroup для БКВ (→ КВ), соленоида (→ КВ + фитинги) — дополнить
   существующие `references`.
7. DerivationRule: БКВ.thread_type → КВ.thread_type, thread_size, exd;
   соленоид → КВ/фитинги (connection/thread).
8. Пометить окружение (`temp_min`/`temp_max`/`ip`) как
   `inherit_mode = global_requirement`.

**Фаза 4 — Фронт:**
9. Граф-редактор (п. 4.1–4.4) на базе существующих
   `TreeNode`/`CompositionGroupNode`/`EquipmentTypeNode` + панель рёбер.
10. Полный редактор слота (п. 4.2).

**Фаза 5 — Проверка:**
11. Ручной сценарий БКВ → КВ (автозаполнение thread/exd/temp, запрос только
    cable type / diameter).
12. AI-сценарий −30 / −60 (температура наследуется −30, интерфейс — из модели).
13. Регрессия `configurator` + `ai_assistant` (+ `assemblies`),
    `python manage.py check`.

---

## Что изменить для унификации (конкретный план)

Сводный план, сводящий три словаря (ЭП, `configurator`, `ai_assistant`) к
единому паттерну. Основан на решениях из «Предлагаемый паттерн → Решения».
**Цена — вне scope** (отдельная сущность по общему паттерну, позже).

**Общее решение.** Два рода листьев — **Требование** и **Слот** — две модели;
узел = `EquipmentType` (тип/подтип) + `CompositionGroup` (состав); сравнение —
`ParameterRule`/`ParameterBinding`; доступность и динамика — для слотов
(`SlotMatrixEntry` + `SlotRule`). ЭП-схема (`EaSignalSlot`/`EaSlotOption`/
`EaSignalMatrixEntry`) — конкретная реализация, не дублируется, а обобщается.

### 1. Требование — `EquipmentTypeParameter`

Файл: [configurator/models/equipment_type_parameter.py](configurator/models/equipment_type_parameter.py).

- Оставить как есть: `field_path`, `filter_type`, `data_source_type`,
  `parameter_rule`, `is_required`, `required_condition`, AI-поля
  (`param_type`/`unit`/`description`/`enum_values`/`ai_extraction_hint`).
- Добавить `inherit_mode` = `none | parent_model | global_requirement` и
  `is_interface` (bool) — разделение «факт модели» vs «требование».
- **Интегрировать `FilterDefinition`**: настройки каталога
  ([core/models/filter_definition.py](core/models/filter_definition.py)) переносятся
  в строки `EquipmentTypeParameter` (`filter_type` + `data_source_type` +
  `parameter_rule`); `FilterDefinition` — временный адаптер до полной миграции,
  затем deprecate.
- Свести дубли осей: `field_type` ↔ `param_type` → одна; `data_source_type` ↔
  `options_source` → одна. Консолидировать `EquipmentType.param_semantics` и
  `compare_direction`/`compare_label` в ETP.

### 2. Слот — новая модель `ConfigSlot`

- Новая общая модель `ConfigSlot` (место: `configurator` или отдельное
  приложение) — обобщает `EaSignalSlot`
  ([electric_actuators/models/ea_signal_slot.py](electric_actuators/models/ea_signal_slot.py)):
  `code`, `name_i18n`, `selection_mode` (`single|multi|xor|bundle`), `slot_kind`
  (`value|object|subtype`), `group` (узел-секция), `sorting_order`.
- `ConfigSlotOption` — обобщает `EaSlotOption`
  ([electric_actuators/models/ea_slot_option.py](electric_actuators/models/ea_slot_option.py)):
  `kind` + типизированные FK + `ext_encoding`.
- Опция-подтип = `slot_kind=subtype` + `options_config.model=EquipmentType` +
  фильтр по `parent`.

### 3. Узел

- `EquipmentType` ([core/models/equipment_type.py](core/models/equipment_type.py)) —
  тип/подтип (`parent`/`level`/`content_type`).
- `CompositionGroup` ([ai_assistant/models/composition_group.py](ai_assistant/models/composition_group.py)) —
  «узел состава». `group_type` в `EquipmentType` не переносить.

### 4. Связи и правила

- `DerivationRule` ([configurator/models/derivation_rule.py](configurator/models/derivation_rule.py)) —
  совместимость/наследование (`source_type → target_type`). Добавить
  `source_kind` = `parent_model | global_requirement`.
- `ParameterRule`/`ParameterBinding`
  ([configurator/models/parameter_rule.py](configurator/models/parameter_rule.py),
  [configurator/models/parameter_binding.py](configurator/models/parameter_binding.py)) —
  сравнение значений (для требований).
- `SlotMatrixEntry` — обобщить `EaSignalMatrixEntry`
  ([electric_actuators/models/ea_signal_matrix.py](electric_actuators/models/ea_signal_matrix.py)):
  `slot` → `ConfigSlot`, контекст + `availability` + `is_default` + `bundle` +
  `conflicts`. Бесскоуповые строки = профиль БУ.
- **Новое `SlotRule`** (Паттерн В) — заменить хардкод в
  [electric_actuators/services/ea_signal_resolver.py](electric_actuators/services/ea_signal_resolver.py).

### 5. Результат

- [electric_actuators/models/ea_catalog_item.py](electric_actuators/models/ea_catalog_item.py) —
  `ElectricActuatorCatalogItem`: добавить `config_snapshot` JSON (M2M
  `matrix_rows` — источник истины).
- [assemblies/models/assembly.py](assemblies/models/assembly.py) +
  [assemblies/models/component.py](assemblies/models/component.py) — сборки
  (варианты) со своим версионированием; модели конфигуратора не версионируются.

### Порядок внедрения

1. Требование: `inherit_mode`/`is_interface`, интеграция `FilterDefinition`,
   сведение дублей осей — не трогая ЭП.
2. Слот: `ConfigSlot`/`ConfigSlotOption`, отобразить `EaSignalSlot`.
3. `SlotRule` + перевод EA-правил.
4. `config_snapshot` на карточке ЭП.
5. Депрекейт `FilterDefinition` — в конце.
6. Цена — отдельно, по общему паттерну, вне этого плана.

---

## Карта файлов и моделей (для продолжения без повторного изучения)

**Документы:**

- [slots.md](slots.md) — паттерн «узлы, слоты, матрицы» (этот файл).
- [configurator.md](configurator.md) — концепция конфигуратора (снапшот 2026-08-11).
- [ai-assistant.md](ai-assistant.md) — AI-пайплайн (снапшот 2026-07-31).
- [ea-models-analysis.md](ea-models-analysis.md) — состояние моделей ЭП (после фаз 7 и 9).
- [ea-signals-options-spec.md](ea-signals-options-spec.md) — справочник сигналов/опций ЭП.
- [ea-legacy-removal-task.md](ea-legacy-removal-task.md) — удаление legacy ЭП.
- [EXECUTION_PLAN.md](EXECUTION_PLAN.md) — план (assemblies/configurator), состояние пунктов.
- [assy.md](assy.md), [ARCHITECTURE_PLAN.md](ARCHITECTURE_PLAN.md).

**Бэкенд — модели:**

- Узел/классификатор: `core/models/equipment_type.py` → `EquipmentType`.
- Слот: `configurator/models/equipment_type_parameter.py` → `EquipmentTypeParameter`.
- Состав: `ai_assistant/models/composition_group.py` → `CompositionGroup`.
- Связи/правила: `configurator/models/derivation_rule.py`, `parameter_rule.py`,
  `parameter_binding.py`, `fitting_pattern.py`.
- Сборка: `assemblies/models/assembly.py` (`AssemblyRequirements`),
  `component.py` (`ComponentRequirement`).
- Фильтр (legacy): `core/models/filter_definition.py` → `FilterDefinition`.
- ЭП-сигналы: `electric_actuators/models/ea_signal_slot.py` (`EaSignalSlot`),
  `ea_slot_option.py` (`EaSlotOption`), `ea_signal_matrix.py`
  (`EaSignalMatrixEntry`, `EaWiringDiagramBinding`), `ea_catalog_item.py`
  (`ElectricActuatorCatalogItem`), `ea_actuator_constructor.py`
  (`ElectricActuatorConstructor`).
- Цена: `price/models/ea_price_constructor.py` → `EAPriceConstructor`.
- Профиль сигналов (физический, роль → датчик): `params/control_unit_signal_profile.py` →
  `ControlUnitSignalProfile`/`ControlUnitSignalProfileEntry`.

**Бэкенд — сервисы:**

- `configurator/services/resolver.py` — `own > global > cascade`.
- `configurator/services/cascade.py` — `resolve_derivation_params` (общее ядро
  каскада для configurator и AI).
- `configurator/services/expander.py` — `CompositionGroup → ComponentRequirement`.
- `configurator/services/filter_engine.py`, `parameter_filter.py`, `registry.py`.
- `ai_assistant/services/tree_processor.py` — decompose/extract/filter/select/
  compare/ebom/mbom.
- `ai_assistant/services/filter_handlers.py` — AI-фильтры по типам.
- `electric_actuators/services/ea_signal_resolver.py` — резолвер матрицы ЭП.
- `electric_actuators/services/ea_configurator_data.py` — пакет сигнальных слотов
  для конструктора.
- `electric_actuators/services/ea_ext_code.py` — ext-код заказа.
- `electric_actuators/management/commands/seed_ea_cu_profiles.py` — заливка
  профилей БУ.

**Фронтенд:**

- `frontend/src/pages/admin/PipelineConfigPage.vue` — CRUD ParameterRule/
  ParameterBinding/DerivationRule/FittingPattern/классификатор + JSON-схемы.
- `frontend/src/pages/admin/SkillConfigPage.vue` — дерево состава
  (`TreeNode`/`CompositionGroupNode`/`EquipmentTypeNode`/`MBOMItemNode`).
- `frontend/src/pages/admin/ConfiguratorRulesPage.vue` — заглушка-редирект.
- `frontend/src/components/admin/EquipmentTypeEditor.vue` — редактор
  `EquipmentType` + частично `EquipmentTypeParameter`.
- `frontend/src/components/bom/*.vue` — дерево BOM.
- `frontend/src/router/index.js` — роуты (`/admin/pipeline-config`,
  `/admin/skill-config`, `/configurator/pa-kit`, `/admin/assemblies` и др.).
