# Exd-опция (взрывозащита): доменная модель, контракт и целевая архитектура

> Статус: единый паттерн внедрён во всех каталоговых моделях (задача 1) и
> фильтры переведены на M2M-семантику (задача 2) — 2026-09-16. Все шаги
> плана «Идеальная архитектура» выполнены (§6.2/6.3 помечены).

---

## 1. Доменная модель

### 1.1. Понятия

| Понятие | Класс / файл | Роль |
|---|---|---|
| **Вид взрывозащиты** (разновидность) | `params.ExdOption` — `params/exd_models.py` | Справочная запись полной маркировки: «Ex db IIC T6 Gb X», «Ex ia IIB T4 Ga», «Общепромышленное». Один вид = одна строка справочника. |
| **Опция с кодировкой** (through-строка) | подклассы `BaseM2MExdThroughOption` | Единица ВЫБОРА в каталоге: кодировка (`encoding`) для артикула + M2M видов Exd, которые она «притягивает». Привязана к серии (`model_line`) или модели в серии. |
| **Артикул / модель в серии** (потребитель) | каталоговые модели, см. §2 | Выбирает опцию из списка привязанных к серии → получает кодировку и весь набор видов. |
| Метод / тип / уровень / группа / температура | `ExplosionProtectionMethod`, `ExplosionProtectionType`, `ExplosionProtectionLevel`, `HazardousGroup`, `TemperatureClass` — `params/exd_models.py` | Справочники-компоненты маркировки и правила совместимости. |

### 1.2. Правило выбора и «притягивания» видов

```
Серия (model_line)
 └── Through-строка (опция): encoding='Ex'  ──M2M──► ExdOption «Ex db IIC T6 Gb X»
      │                                        └──► ExdOption «Ex ia IIC T6 Ga X»
      └── Артикул выбирает опцию (FK) → получает encoding='Ex' + оба вида сразу
```

- Одна кодировка = одна строка; виды добавляются в существующую строку (валидация `validate_unique_encoding`).
- «Общепром» — строка с пустым M2M (или видом без кода) и собственной кодировкой.
- Для `model_line_item`/артикула выбор хранится либо как **FK на строку** (`exd_option`), либо как **денормализованный M2M видов** (копия из строки — паттерн `ExdOptionsConsumerMixin`).

### 1.3. Правила совместимости видов («не хуже чем»)

1. **Тип**: лестница уровней `общепром < Ex ia < Ex ib < Ex e < Ex d < Ex d IIC` (`ParameterRule 'exd'`, `configurator/management/commands/seed_configurator_rules.py`). Вид уровня N подходит для требования уровня ≤ N. Внутри метода подтипы равнозначны «не хуже» (db → подходят и db, и da).
2. **Группа**: та же среда (GAS/DUST) и `rating >=` требуемого (IIC ≥ IIB ≥ IIA).
3. **Температура**: газ — `strictness_rating >=` требуемого (T6 ≥ T5 ≥ …); пыль — по `dust_temperature`.
4. **Соглашение (утверждено пользователем)**: если у вида в полном коде НЕ указан температурный класс — он подходит под ЛЮБОЙ запрос по температуре. Это покрывает кабельные вводы (у их видов температурный класс не указывается) — отдельный фильтр не нужен.
5. **Модель совместима с запросом, если хотя бы ОДИН вид из её списка совместим с запрошенным** (EXISTS-семантика). EXACT — запрошенный вид присутствует в списке модели.

---

## 2. Инвентаризация по видам оборудования

### 2.1. Единый паттерн (through-строка с кодировкой + M2M видов)

| Оборудование | Through-модель | Привязана к (FK) | Потребитель (артикул/модель) | Поле выбора у потребителя |
|---|---|---|---|---|
| Кабельные вводы | `CableGlandExdOption` (`cable_glands/models/cg_exd_option.py`) | `CableGlandModelLine` (`related_name='exd_options'`) | `CableGland` (`cable_glands/models/cg_actual.py`) | `exd_option` FK → `CableGlandExdOption` |
| Позиционеры | `PosiExdOption` (`pa_controls/models/posi_model_line.py:370`) | `PosiModelLine` | `PosiModelLineItem` (денорм. M2M `exd_options` через `ExdOptionsConsumerMixin`); `PosiConstructor` | `selected_exd_row` FK → `PosiExdOption` **и** `selected_exd` FK → `params.ExdOption` (выбранный вид из M2M строки, синхронизируется в `save()` через `_resolve_exd_variant` — двухполевой вариант, см. §4.4) |
| БКВ | `LimitSwitchExdOption` (`pa_controls/models/lsb_model_line.py:86`) | `LimitSwitchModelLine` | `LimitSwitchBox` (денорм. M2M `exd` через `ExdOptionsConsumerMixin`) | M2M `exd` (`exd_m2m_field='exd'`) |
| Соленоидные клапаны | `DirectionValveExdOption` (`solenoid_valves/models/dv_exd_option.py`) | `DirectionalValveModelLine` | `DirectionValve` (`solenoid_valves/models/dv_model_line_item.py`) | `exd_option` FK → `DirectionValveExdOption` |
| Электроприводы | `ElectricExdOption` (`electric_actuators/models/ea_options.py`) | `ElectricActuatorModelLine` | `ElectricActuatorConstructor`, `ElectricActuatorSelected` | `selected_exd` FK → `ElectricExdOption` |
| Пневмоприводы | `PneumaticExdOption` (`pneumatic_actuators/models/pa_options.py`) | `PneumaticActuatorModelLine` | `PneumaticActuatorItem`, `PneumaticActuatorConstructor`, `PneumaticActuatorSelected` | `selected_exd` FK → `PneumaticExdOption` |

Все шесть through-моделей — тонкие подклассы `BaseM2MExdThroughOption`: объявляют FK на свою серию + `Meta` + `_get_parent_field_name()`. У `CableGland` и `DirectionValve` выбор/отображение/валидация реализованы общим миксином `ChosenExdRowMixin` (§3.7).

### 2.2. Исключения (осознанные)

| Место | Что | Решение |
|---|---|---|
| `GearboxInterlock.interlock_exd` (`gearbox/models/interlock.py:42`) | Плоский M2M → `ExdOption` без кодировки и серии | Интерлок — самостоятельная модель без `model_line`. Оставлен как есть; перевести при появлении серии/кодировки. |
| `EttElectricOptionsCombination.exd_choice` (`ett/models.py:291`) | FK → `ExdOption` | Справочник кодировок ЕТТ, не каталог. Не трогать. |
| `AbstractActuatorMixin.exd` (`djangoProject1/common_models/abstract_models.py`) | FK (legacy) | **Удалено 2026-09-16** (наследников не было, миграция не нужна). |

---

## 3. Базовые классы (контракт) — `options/exd.py` (реэкспорт из `options/models.py`)

### 3.1. `BaseThroughOptionNoDefault` (общая база всех through-опций)
Поля: `encoding` (код для артикула), `description`, `sorting_order`, `is_active`.
Служебные методы:
- `_get_parent_object()` — родитель (серия/модель);
- `_get_parent_field_name()` — имя FK на родителя (авто-определение первого FK, переопределяется в подклассе);
- `get_option_info()` — словарь `{id, encoding, description, display_name, is_default, is_active, sorting_order, has_encoding}` для API;
- `options_list` — все активные опции родителя;
- `is_option_allowed(option)` — проверка принадлежности опции родителю (для валидации выбора).

### 3.2. `BaseThroughOption(BaseThroughOptionNoDefault)`
Добавляет `is_default`.
- `ensure_default_exists(parent)` — гарантирует дефолтную опцию серии (создаёт `_create_basic_default_option` — строка `encoding='STD'`, пустой M2M, если подкласс не определил своё);
- `get_or_create_default(parent)` — вернуть/создать дефолт;
- `get_default_or_any_allowed(parent)` — дефолт или первая активная;
- `default_option` — property, дефолтная опция родителя;
- `validate_unique_default()` — заглушка (проверка после сохранения).

### 3.3. `BaseM2MExdThroughOption(BaseThroughOption, ExdFormattingMixin)` — **целевая база опции**
```python
exd_options = models.ManyToManyField('params.ExdOption', blank=True,
                                     related_name='%(class)s_exd_rows')
```
- `validate_unique_encoding()` — одна кодировка на серию (работает и при создании, и при правке; пустые кодировки пропускает);
- `get_display_name()` / `__str__()` — «Серия → encoding: виды» (безопасно для несохранённых строк);
- `get_description_data()` — словарь для рендера спецификаций: `{'exd_option': {display_name, value}, 'is_default': {display_name, value}}` (формат совместим с `electric_actuators/utils/universal_renderer.py`, который читает `exd_data.exd_option.value`);
- `get_effective_row(parent=None, parent_id=None)` — эффективная строка серии: активная `is_default=True`, иначе первая активная (без лишнего запроса к родителю).

### 3.4. `ExdFormattingMixin` (поведение форматирования, без полей)
- `exd_m2m_field` (default `'exd_options'`) — имя M2M-поля с видами на объекте;
- `EXD_RELATED` — кортеж справочников для `select_related` (не порождать N+1);
- `get_exd_options()` — список видов с подгруженными справочниками;
- `has_exd()` — True, если среди видов есть вид с непустым `code`;
- `get_exd_list` (property) — полный текст: группировка одинаковых степеней с разными температурами «Ex db IIB T5/T6»;
- `get_exd_short_list` (property) — короткий уникальный список степеней «Ex db / Ex ia».

### 3.5. `ExdOptionsConsumerMixin(ExdFormattingMixin)` (потребитель-артикул с денормализованным M2M)
- `exd_through_model` (`'pa_controls.PosiExdOption'` по умолчанию; у БКВ — `'pa_controls.LimitSwitchExdOption'`) — ленивый `apps.get_model`;
- `exd_parent_field` (`'model_line'`); `exd_m2m_field` (у БКВ `'exd'`);
- `get_exd_options()` — приоритет источников: (1) `_selected_exd_row` (строка, переданная конструктором/превью) → (2) собственный M2M → (3) дефолтная строка серии;
- `_sync_exd_options_from_model_line()` — при создании item копирует виды из эффективной строки серии в M2M item;
- `exd_encoding` (property) — кодировка: из `_selected_exd_row`, иначе поиск строки серии по набору видов (есть Ex-виды → строка с непустым M2M, нет → строка с пустым);
- `exd_display` (property) — `get_exd_list` или «Нет» (для шаблонов и админки).

### 3.6. `ChosenExdRowMixin(ExdFormattingMixin)` — потребитель с FK на строку
Живёт в `options/exd.py`; на нём — `CableGland` и `DirectionValve`. Настройки:
`exd_row_field` (default `'exd_option'`), `exd_through_model` (обязателен, `'app.Model'`),
`exd_parent_field` (default `'model_line'`). Предоставляет: `_get_effective_exd_row`,
`get_exd_options` (из эффективной строки), `get_exd_display`, `get_exd_short_list`,
`exd_encoding` и `clean()` (валидация «опция ↔ серия», с вызовом `super().clean()`).

### 3.7. `BaseExdThroughOption` — legacy FK-вариант
Одна строка = один вид (`exd_option` FK). **Удалён 2026-09-16** (подклассов не осталось).

---

## 4. Каталог служебных свойств, методов и функций

### 4.1. Справочник `ExdOption` (`params/exd_models.py`)

| Метод/свойство | Описание | Связан с |
|---|---|---|
| `get_formatted_ex_code(option)` | Формирует маркировку: `'name'` — «Ex db IIC T5 Gb X», `'code'` — «db-iic-t5-gb-x» | автозаполнение `name`/`code` в `save()` |
| `save()` | Автозаполняет `name`, `code`, `temperature_rating` (из `TemperatureClass.strictness_rating` или `dust_temperature`) | денормализация для быстрой фильтрации |
| `get_compatible_ids()` | ID всех активных видов, совместимых с ТЕКУЩИМ видом: тот же метод, группа `rating>=` (та же среда), температура `rating>=` (газ) / `dust <=` (пыль) | PA-селектор `_match_exd_for_model_lines`, иерархический резолвер (как семантика одной ветки) |
| `resolve_compatible(method_id, type_id, group_id, temp_id) -> (ids, exact_id)` | Один SQL-запрос: виды «не хуже» выбранных компонентов каскада + точный вид (если единственный). `type_id` → все типы метода; группа — среда + `rating>=`; температура — газ `rating>=`, пыль не фильтруется | `ExdCompatibleView` (`core/views.py:962`), фронт `ExdFilter.vue` |
| `get_compatible_ids_by_components(...)` | Обёртка над `resolve_compatible` (обратная совместимость) | — |
| `get_structured_choices()` | Иерархия для каскада: методы с типами, газ/пыль группы, температурные классы, уровни защиты | `ExdStructureView` (`core/views.py:885`) |

### 4.2. Справочники-компоненты
- `HazardousGroup.is_compatible(required_code)` — сравнение по `rating` в одной среде;
- `TemperatureClass.save()` — автозаполнение `strictness_rating` по карте T1..T6;
- `ExplosionProtectionType` — FK на `ExplosionProtectionMethod`, `category` (GAS/DUST), `get_text_description()`.

### 4.3. Через-строка (опция) — см. §3.2–3.3
`get_effective_row`, `validate_unique_encoding`, `get_display_name`, `get_description_data`, `get_option_info`, `ensure_default_exists`, `get_or_create_default`, `options_list`, `is_option_allowed`.

### 4.4. Потребитель (артикул/item)

| Свойство/метод | Где | Описание |
|---|---|---|
| `exd_option` FK | `CableGland`, `DirectionValve` | Выбранная опция серии; пусто → дефолт серии |
| `selected_exd` / `selected_exd_row` FK | конструкторы/selected EA-PA, `PosiConstructor` | То же для конструкторского выбора. **Особый случай PosiConstructor**: хранит И строку (`selected_exd_row` → `PosiExdOption`), И выбранный вид (`selected_exd` → `params.ExdOption`), который резолвится в `save()` через `_resolve_exd_variant` (`posi_constructor.py:448,529,531`) — спецификация позиционера требует конкретный вид, а артикул — кодировку строки |
| `_get_effective_exd_row()` / `get_exd_display` / `get_exd_short_list` / `exd_encoding` / `clean()` | **`ChosenExdRowMixin`** (`options/exd.py`) — `CableGland`, `DirectionValve` | Эффективная строка (выбранная → дефолт серии), полный/короткий списки видов, кодировка, валидация принадлежности серии |
| `get_exd_options()` / `_sync_exd_options_from_model_line()` / `exd_display` | `ExdOptionsConsumerMixin` (Posi, БКВ) | Денормализованный M2M и его синхронизация |
| `exd_display` (property) | `ElectricActuatorModelLine`, `PneumaticActuatorModelLine`, конструкторы EA/PA | Отображение стандартной/выбранной опции: `get_exd_short_list` строки |
| `_get_option_encoding('selected_exd')` | конструкторы EA/PA (`ea_actuator_constructor.py:762`, PA аналог) | Кодировка выбранной строки для подстановки `{exd}` в артикул |

### 4.5. Шаблоны (`{exd}` / `{exd_short}`) — реестры `*_item_fields.py`

| Модель | Файл | `{exd}` path | `{exd_short}` path | `code_path` |
|---|---|---|---|---|
| `CableGland` | `cable_glands/models/cg_item_fields.py` | `get_exd_display` | `get_exd_short_list` | `exd_encoding` |
| `DirectionValve` | `solenoid_valves/models/dv_item_fields.py` | `get_exd_display` | `get_exd_short_list` | `exd_encoding` |
| `PosiModelLineItem` | `pa_controls/models/posi_item_fields.py` | `get_exd_list` | `get_exd_short_list` | `exd_encoding` |
| `LimitSwitchBox` | `pa_controls/models/lsb_item_fields.py` | `exd_display` | `get_exd_short_list` | — |
| `PneumaticActuatorItem` | `pneumatic_actuators/models/pa_item_fields.py` | `selected_exd__get_exd_list` | `selected_exd__get_exd_short_list` | `exd_encoding` |

Ключи `exd`/`exd_short` включены в `NAME_FIELD_KEYS`/`VARS_FIELD_KEYS` у всех потребителей.

### 4.6. Админки (through-строки редактируются инлайном на серии)

| Инлайн | Файл | Регистрация строки отдельно |
|---|---|---|
| `CableGlandExdOptionInline` | `cable_glands/admin/cg_model_line_admin.py:21` | — |
| `PosiExdOptionInline` | `pa_controls/admin/positioner_admin.py:238` | — |
| `LimitSwitchExdOptionInline` | `pa_controls/admin/limit_switch_admin.py:161` | — |
| `DirectionValveExdOptionInline` | `solenoid_valves/admin/dv_model_line_admin.py` | — |
| `ElectricExdOptionInline` | `electric_actuators/admin/ea_model_line_admin.py:416` | `ElectricExdOptionAdmin` (`ea_body_admin.py:98`) |
| `PneumaticExdOptionInline` | `pneumatic_actuators/admin/pa_model_line_admin.py:43` | — |

Все инлайны — подклассы общего `BaseExdOptionInline` (`options/admin.py`):
`fields = [exd_options, encoding, is_default, sorting_order, is_active]` +
`filter_horizontal = [exd_options]`; подклассы задают только `model` (+ `ordering`/verbose-имена).

### 4.7. Фильтры и подбор

| Компонент | Файл | Роль |
|---|---|---|
| `FilterDefinition fd_exd` (EXD_COMPATIBLE + `parameter_rule_code='exd'`) | `cable_glands/catalog/filter_defs.py` (`model_field='exd_option__exd_options'`), `solenoid_valves/catalog/filter_defs.py` (то же), `pa_controls/catalog/filter_defs.py` (`model_field='exd'`) | Декларативный фильтр каталога |
| `ParameterRule 'exd'` (hierarchy) | `configurator/management/commands/seed_configurator_rules.py` | Лестница уровней для бэкенд-подбора |
| `_resolve_hierarchy_compatible_ids` + `_build_q_from_binding`/`_build_q_from_parameter_rule` | `configurator/services/parameter_filter.py` | Иерархия одним OR-запросом (2 запроса вместо ~50) + кэш LocMem (300 с); инвалидация — сигналы `params/exd_signals.py` (версия `exd_compat_version`, подключение в `params/apps.py.ready`) |
| `classify_match(obj, value, exact_value)` | `core/models/filter_definition.py:610` | M2M-aware split exact/compatible: `_get_m2m_ids`/`_walk_m2m` (пути `exd`, `exd_option__exd_options`, reverse-менеджеры; prefetch-aware), `_parse_id_list`; FK-путь сохранён для THREAD/FUNCTION/IP_RANK |
| `apply_filters_and_split` | `core/models/smart_catalog_mixin.py:206` | Проброс `exact_value`; режим `{param}_match=exact` + `{param}_exact` (например `exd_id_match=exact&exd_id_exact=4`) |
| `ExdStructureView`, `ExdParseView`, `ExdCompatibleView` | `core/views.py:885-985` | `/api/core/exd/structure|parse|compatible` (compatible возвращает `ids` + `exact_id` через `resolve_compatible`) |
| `ExdStringParser` | `core/models/exd_parser.py` | Разбор строки «Ex db IIC T6 Gb X» в компоненты каскада |
| `ExdFilter.vue` | `frontend/src/shared/components/ExdFilter.vue` | Каскад метод→тип→группа→температура + ввод строки; шлёт `exd_id` (csv совместимых видов, sentinel `_none_`/`_empty_`) и `exactId` (точный вид из `resolve_compatible`) |
| `FilterSidebar.vue`, `EngineerFilterBar.vue` | `frontend/src/shared/components/...` | Приём `exd_id` + `exd_id_exact` и отправка в каталог. **Мастер (`WizardSelection`) — НЕ шлёт** `exd_id_exact` (split'а у мастера нет; параметр был убран как инертный) |
| `filter_handlers._apply_filters` (AI) | `ai_assistant/services/filter_handlers.py` | exd_compatible → прямое `Q(field=value)`; LSB-ветка — `apply_parameter_rules` → иерархия через M2M `exd__in` |
| PA-селектор | `pneumatic_actuators/actuator_selector_handler.py::_match_exd_for_model_lines` | Hard-фильтр серий «∃ совместимый вид» по M2M строк `PneumaticExdOption` (один запрос на вызов); аннотирует `exd_option_id`/`exd_encoding`/`exd_short`/`exd_variety_ids`; `filter_engine._filter_pa_selector` несёт их в кандидатах |
| `_serialize_candidate` / `_json_safe` | `configurator/services/filter_engine.py` | Сериализация кандидатов (lazy-переводы → str; чинит сохранение `filter_results` в JSONField) |
| `actuator_selector_helper.py` | `pneumatic_actuators/` | **Закомментирован целиком** — вероятно мёртвый код (никем не импортируется, несовместим с моделями); пояснение в шапке файла |

### 4.8. Прочее
- `cart/models/cart_item.py` — сводка корзины: пробует `get_exd_display` → `get_exd_list` → `get_exd_short_list`, фолбэк на M2M-атрибут `exd`;
- `electric_actuators/utils/universal_renderer.py:353-363` — рендер `exd_data.exd_option.value` / `exd_data.is_default.value` в docx;
- `pneumatic_actuators/services/sku_service.py` — маппинг `'exd' → 'selected_exd'` для кодировки артикула;
- `core/management/commands/regenerate_catalog_descriptions.py` — `EXD_PREFETCH_MAP` (анти-N+1 при массовой перегенерации).

---

## 5. Семантика фильтров (реализовано 2026-09-16)

1. **«Не хуже чем»**: фильтр принимает уровень («Ex d»), частичную («Ex db IIC») или полную маркировку; резолвер вычисляет набор совместимых видов (лестница + группа + температура, соглашение «нет класса = любой»); модель проходит, если **∃ вид из её списка** в наборе. Реализовано: `_resolve_hierarchy_compatible_ids` — один SQL-запрос с OR-ветками + кэш LocMem с инвалидацией по сигналам справочников (`params/exd_signals.py`).
2. **EXACT**: модель проходит, если запрошенный вид **есть** в её списке; в выдаче «Точно подходят» отделяется от «Совместимых» (`classify_match`, M2M-aware; фронт передаёт `exd_id_exact`; режим `exd_id_match=exact` — строгий фильтр).
3. Справочный резолвер един: `ExdOption.resolve_compatible` + иерархическая надстройка — и для каскада, и для AI-подбора; PA-селектор — через `_match_exd_for_model_lines` (пересечение видов строки с совместимым набором).

---

## 6. Идеальная архитектура (как должно быть)

### 6.1. Ответ на вопрос «одна абстрактная модель?»
**Да — но не одна таблица.** Единая КОНКРЕТНАЯ модель невозможна: у каждой опции свой FK-родитель (шесть разных серий), а GenericForeignKey/мультитаблица — антипаттерн (теряются FK-целостность, индексы, related_name-ы, админки). Правильная унификация — **комплект из трёх абстракций**, который уже существует и покрывает все шесть видов оборудования:

```
BaseM2MExdThroughOption   (опция: кодировка + M2M видов + валидации + get_effective_row)
ExdFormattingMixin        (форматирование: get_exd_list / get_exd_short_list / has_exd)
ExdOptionsConsumerMixin   (потребитель: денормализованный M2M + sync + exd_encoding/exd_display)
```

### 6.2. Выполнено 2026-09-16 (бывший список «что осталось дожать»)

- [x] 1. **Дубли у потребителей убраны**: `ChosenExdRowMixin` реализован в `options/exd.py`
  (атрибуты `exd_row_field`/`exd_through_model`/`exd_parent_field`; методы
  `_get_effective_exd_row`, `get_exd_options`, `get_exd_display`, `get_exd_short_list`,
  `exd_encoding`, `clean()` с `super().clean()`); `CableGland` и `DirectionValve` на нём.
- [x] 2. **Гигиена модуля**: exd-классы вынесены в `options/exd.py`; `options.models`
  реэкспортирует (обратная совместимость).
- [x] 3. **Общий инлайн**: `BaseExdOptionInline` (`options/admin.py`); все шесть инлайнов — подклассы.
- [x] 4. **Единый резолвер**: иерархия — один OR-запрос + кэш LocMem; инвалидация
  сигналами в `params/exd_signals.py`.
- [x] 5. **`classify_match` M2M-aware** + `exd_id_exact` во фронте (FilterSidebar/EngineerFilterBar;
  мастер — намеренно без exact, split'а нет).
- [x] 6. **Исключения зафиксированы** в §2.2 (`GearboxInterlock`, ETT).
- [x] 7. **Legacy вычищено**: `BaseExdThroughOption` удалён, `AbstractActuatorMixin.exd` удалён,
  колонки `default_exd`/`allowed_exd` EA/PA удалены миграциями (0022/0042/0038 — reversable,
  проверены round-trip на реальной базе).

### 6.3. Остаточные хвосты (не блокеры)
- `GearboxInterlock` — при появлении серии/кодировки перевести на паттерн (пока плоский M2M, §2.2).
- Мастер подбора (Wizard) — без exact-режима; включить split при необходимости.
- Внешние потребители `ExdFilter` (`ConfiguratorPaKitPage`, `PaSelectionPage`, `RequirementForm`)
  не слушают `exactId`.
- `pneumatic_actuators/actuator_selector_helper.py` — закомментирован как вероятно мёртвый код;
  удалить при подтверждении.
- cart-дрейф колонок `price_*` (не exd, но блокирует чистый `makemigrations --check`).
