# Финальная схема: сигналы управления/обратной связи электроприводов

Дата фиксации: 2026-10-18. Основание: `ea-aox-signals-report.md` разд. 6–15 и
`ea-signals-open-questions.md` (вопросы 1–20). Код не менялся — это проектирование.
Решения, принятые «по умолчанию», помечены ⚠ — подтвердить до реализации.

---

## 1. Цель

Универсальная схема описания сигналов управления и обратной связи БУ
электроприводов, пригодная для: собственной линейки (AOX), привода AUMA и ROTORK
как товаров в БД, генерации артикулов (ext_encoding) и ответа на запросы
«замени RWG/EWG».

Принципы:
- сигналы — источник истины (что на клеммах), физика датчиков — справочный слой;
- доступность — вычисляется из наследуемой матрицы, а не хранится на каждой модели;
- существующие механизмы приложения (через-опции, ext_encoding_template,
  FilterDefinition) переиспользуются, а не дублируются.

---

## 2. Каталоги (5 моделей)

### 2.1 EaControlSignal — входные команды

```
role        # CMD_OCS, CMD_REMOTE, CMD_LOCK, CMD_MANUAL_OVERRIDE, CMD_4_20MA,
            # CMD_EMERGENCY_OPEN, CMD_EMERGENCY_CLOSE, MODE,
            # INTERLOCK_OPEN, INTERLOCK_CLOSE, DRIVE_ENABLE
category    # discrete | analog
form        FK EaSignalForm (DISC_AC, DISC_DC, AN_4_20_ACTIVE, AN_4_20_PASSIVE)
voltage     # В, для discrete (номинал цепи); null для analog
current     # мА, потребление входа
wires       # число проводов/клемм на канал (данные для генератора схем)
hart        # bool: true только для форм AN_4_20_* (HART поверх петли)
name, code, description, is_active, sorting_order
```

### 2.2 EaFeedbackSignal — выходная ОС

```
role        # END_OPEN, END_CLOSE, WAY_OPEN, WAY_CLOSE, TORQUE_OPEN, TORQUE_CLOSE,
            # POSITION, OVERHEAT, TURN_COUNTER, ALARM, READY, TORQUE_ANALOG
category    # contact | analog
form        FK EaSignalForm (DRY_SPST, DRY_SPDT, DRY_DPDT,
            #                AN_4_20_ACTIVE, AN_4_20_PASSIVE, RES_POTENTIOMETER)
max_voltage # В, коммутируемое — для contact; null иначе
max_current # А, коммутируемый — для contact; null иначе
wires       # число проводов/клемм на канал (данные для генератора схем)
resistance_kohm  # для RES_POTENTIOMETER; null иначе
max_power_w      # для RES_POTENTIOMETER; null иначе
turns            # оборотов (для потенциометра полного хода); null иначе
hart        # bool: true только для форм AN_4_20_*
name, code, description, is_active, sorting_order
```

### 2.3 EaSignalForm — справочник форм (⚠ решение по вопр. №3/№11)

Код/name/category(contact|analog|discrete|resistance)/description/is_active.
Расширяется данными, без миграций. Стартовый набор — выше.

### 2.4 EaCommProtocol — шинные протоколы БУ (двунаправленные)

```
code / name  # HART_REF (не используется — см. 2.1/2.2), MODBUS_RTU, MODBUS_TCP,
             # PROFIBUS_DP, PROFINET, FOUNDATION_FIELDBUS, PAKSCAN,
             # DEVICENET, ETHERNET_IP
transport    # rs485 | ethernet | current_loop | ...
description, is_active
```

⚠ Вопрос №4 решён: HART — атрибут сигнала (`hart=True` на AN_4_20_*), а не
отдельный протокол БУ (у AUMA и Rotork HART не выбирается отдельно от петли).
Вопрос №5: Modbus RTU и TCP — разные записи справочника.

### 2.5 EaFeedbackDevice — справочник устройств ОС (разд. 12)

```
code / name  # RWG_4020, EWG_01_1, MWG, PRECISION_POT, TRANSMITTER_4_20 (свой),
             # POT_RAW (свой)
technology   # POTENTIOMETER | POT_CONVERTER | HALL | MAGNETIC
contactless  # bool
emits        # M2M EaFeedbackSignal (MWG: контакты + аналог)
equivalents  # M2M self: «наш TRANSMITTER_4_20 ≡ RWG_4020»
accuracy, life_cycles, temp_range, description, is_active
```

---

## 3. EaControlUnit — расширение существующего справочника БУ

⚠ Вопрос №8 решён: **не новая модель**, а расширение существующего
`params.ControlUnitInstalledOption` (БУ уже есть в приложении, на него ссылаются
`ElectricControlUnitOption` и `ControlUnitWiring`). Добавляемые поля:

```
kind            # NONE | BASIC | INTEGRATED | POSITIONER
                # (AUMA NORM→NONE, AM→BASIC, AC.2→INTEGRATED; Rotork IQ3→INTEGRATED)
accepts         # M2M EaControlSignal
emits           # M2M EaFeedbackSignal
protocols       # M2M EaCommProtocol
capabilities    # JSONField: local_controls, display, pst, datalogger, bluetooth,
                # esd, pid, interrupter_timer (вопр. №15)
control_voltage # nullable FK params.PowerSupplies — напряжение цепи управления
                # (24 V DC std / 115 V AC opt у AUMA; полосы Rotork — записи
                # PowerSupplies); null = напряжение задаёт форма сигнала (AOX)
encoding        # ext-код варианта БУ (MSP-часть кода AUMA) ⚠ ext_encoding уже есть
```

Вопрос №7: позиционер — запись с kind=POSITIONER (его сигналы — в accepts/emits);
оборудование позиционера остаётся в `pa_controls` (не дублируем).

**Выбор шины (Р1 из ревью — принято 2026-10-18):** базовые записи БУ, шины —
M2M `protocols`; в конфигураторе шина — слот **PROTOCOL** (single-choice,
внутри слотов матрицы); ext-код БУ = композиция «база БУ + код шины»
(MSP поз. 8, «B» в поз. 2). Для AOX слот пуст — поведение не меняется.

---

## 4. EaSignalSlot + EaSignalMatrixEntry — доступность

### EaSignalSlot (Р3 из ревью — принято 2026-10-18)

```
code / name     # POSITION_FEEDBACK, PROTOCOL, HEATER, ...
required        # bool: в слоте должна быть хотя бы одна доступная строка
sorting_order, is_active
```

Слот — модель, а не строка-код: опечатка невозможна, обязательность и порядок
слотов в UI хранятся в схеме.

### EaSignalMatrixEntry — наследуемая матрица доступности

```
scope: brand (FK producers.Brands) / model_line (FK) / model_line_item (FK)
       # заполнен ровно один уровень; специфичнее перекрывает общий
control_unit   FK params.ControlUnitInstalledOption
power_supply   FK params.PowerSupplies          # питание мотора
mode           # on_off | modulating | both     (вопр. №9 — поле, не ось)
slot           # FK EaSignalSlot (вопр. №17/Р3 — single-choice)
bundle         # строка-код пакета, null (вопр. №14: MWG = три строки bundle='MWG')
signal         # три nullable FK: control_signal / feedback_signal / protocol
               # (protocol — только для строк слота PROTOCOL, Р1);
               # заполнен ровно один ЛИБО все три null — явная строка «нет»
               # («Без переключателей» для MWG-позиций 5/6, «Без обогрева»…)
device         # nullable FK EaFeedbackDevice (только feedback-строки);
               # валидация: device.emits содержит signal
heater_supply  # nullable FK params.ActuatorHeaterSupply — только для слотов
               # HEATER_ACTUATOR / HEATER_CONTROL_UNIT (NO_HEATER / SEPARATE_LINE /
               # MOTOR_CIRCUIT); заполнен ЛИБО none-строка («Без обогрева»)
availability   # std | opt | na   ('na' на специфичном уровне ЗАПРЕЩАЕТ строку)
is_default     # предвыбор в слоте
encoding, ext_encoding   # вклад в артикул (ext — через ext_encoding_template)
sorting_order
conflicts      # M2M self: парный запрет одновременного выбора
```

### EaWiringDiagramBinding — привязка схемы подключения (2026-10-18)

Диаграмма подходит не для всех комбинаций опций, а только для части — поэтому
это **отдельная привязка** со своей подписью: она или есть для выбранного
набора, или нет.

```
scope        # model_line / model_line_item (nullable) — где применима
control_unit # FK params.ControlUnitInstalledOption (nullable)
power_supply # FK params.PowerSupplies (nullable)
mode         # on_off | modulating | both | null
signals      # M2M EaSignalMatrixEntry — подпись набора (какие строки выбраны)
match_type   # exact (выбор == подпись) | superset (подпись ⊆ выбор)
diagram      # FK media_library.MediaLibraryItem (категория SCHEMA)
name, sorting_order, is_active
```

Резолвинг: для выбранного набора строк ищется привязка с совпадающим скоупом,
БУ, напряжением, режимом и подписью (по match_type); нет матча — схемы нет
(«есть или нет»). `ControlUnitWiring` после переезда удаляется целиком — его
роли разобраны: схема → привязка, профиль → удаляется, обогрев → слот HEATER.

### Правила резолвинга

1. Для пары (модель → серия → бренд, БУ, напряжение, режим) берутся строки по
   специфичности: model_line_item → model_line → brand; менее специфичные
   перекрываются.
2. Внутри слота выбирается не более одной строки (`is_default` — предвыбор);
   «нет» = в слоте нет доступных строк.
3. Строки `availability='na'` на специфичном уровне запрещают унаследованную
   опцию (напр., бренд: «моментные есть», серия: «na»).
4. Командные сигналы формы DISC_AC/DISC_DC доступны, если voltage сигнала
   совместим с `EaControlUnit.control_voltage` (или совпадает с напряжением
   мотора для AOX-строк без control_voltage).
5. Конфликты: **парные** — `conflicts` M2M (симметричный запрет); **составные**
   (лимит клемм Q/M: «нельзя DPDT + средний + моментный одновременно» — запрет
   не пар, а набора) — `configurator.ParameterRule` (composite/cardinality), в
   фазу 4 плана.
6. Валидация данных: пары (БУ, напряжение) матричных строк должны быть объявлены
   доступными в `AllowedControlUnitOption` (новая связка серия×БУ×напряжение;
   значения перенесены из старой схемы data-миграцией 0058) — при заливке
   проверять и отчитывать несовпадения (иначе два источника истины для оси
   БУ×напряжение).

### Примеры (концептуально; заполнение — отдельный ввод данных)

- AOX Basic 220AC on-off: слот POSITION_FEEDBACK → POT_RAW (opt) и
  AN_4_20_PASSIVE/TRANSMITTER_4_20 (opt); INT ICU: AN_4_20_PASSIVE (std),
  RES_POT (na).
- **Слоты HEATER (обогрев) — их два:** обогрев **привода** (HEATER_ACTUATOR) и
  обогрев **блока управления** (HEATER_CONTROL_UNIT) — обогреватели независимы,
  в схеме могут присутствовать оба. Каждый слот — три опции: «Без обогрева»
  (none-строка, NO_HEATER), «От отдельной линии» (SEPARATE_LINE), «От цепей
  питания устройства» (MOTOR_CIRCUIT) — значения справочника
  `ActuatorHeaterSupply`; строки обоих слотов входят в подпись
  `EaWiringDiagramBinding` наравне с сигналами. Данные AOX: колонки 73–76
  (обогрев привода), 83–88 (обогрев БУ/INT-модуля), 94 (обогрев −60° для
  INT-модуля) таблицы.
- AUMA NORM: PRECISION_POT (opt), RWG_4020 (opt), EWG_01_1 (opt); MWG — только
  с AC-контроллером (строки со scope=brand, control_unit=AC 01.2).
- Rotork IQ3: CPT (std, device=CPT), CTT (opt), S1–S4 — сигналы DRY_SPST.

---

## 5. Пакеты (вопр. №14) — без отдельной модели пресетов

MWG-пакет = **несколько матричных строк с общим `bundle`** (строка-код на строке
матрицы, null): выбор строки с bundle влечёт остальные строки пакета. **Семантика
атомарна:** если хотя бы одна строка пакета недоступна (na на более специфичном
уровне) — пакет целиком недоступен; выбор/снятие выбора пакета — одной операцией.
MWG = три строки с bundle='MWG': моментные «0» (слот TORQUE_SWITCHES, строка
«нет», ext «0»), концевые «0» (слот LIMIT_SWITCHES, строка «нет», ext «0»),
позиция «I» (слот POSITION_FEEDBACK, device=MWG, signal=POSITION, ext «I») —
позиции 5/6/9 TPA заполняются ext-кодами этих строк. Отдельная модель пресетов
не нужна: данные загружаются напрямую из Excel/каталогов;
`ControlUnitSignalProfile` используется только как шаблон при выгрузке старых
данных, затем удаляется (разд. 7).

---

## 6. Кодировка (разд. 14)

- Позиционность кода заказа обеспечивает существующий механизм:
  `model_line.ext_encoding_template` + плейсхолдеры (`core/models/mixins.py`).
- Значения: через-опции (ext_encoding уже есть — migration 0046), поля модели
  через callable, новые матричные опции — их ext_encoding через расширение
  словаря плейсхолдеров (`_get_ext_code_data_dict`).
- AUMA: TPA (14 позиций) — шаблон серии; MSP — сегмент от
  `ElectricControlUnitOption.ext_encoding`.
- Rotork: структура кода — за spec-листами PUB002-039/065 (добыть).

---

## 7. Миграция: полный переезд (решение 2026-10-18)

Электроприводы в отладке — старый путь не сохраняем, костыли не делаем:

- **Выгрузка → заливка.** Скрипт выгружает значения старых моделей (профили
  сигналов, `ControlUnitWiring`, через-опции переключателей, encoding/ext_encoding)
  в промежуточный JSON → сверка → загрузка в матрицу. Исходные данные хранятся в
  выгрузке до завершения сверки.
- **Удаляется после выгрузки:** `AllowedSignalProfileOption`;
  `ControlUnitWiring` **целиком** (схемы переносятся в `EaWiringDiagramBinding`,
  обогрев — в слот HEATER) + поле `ElectricControlUnitOption.control_unit_wiring`;
  `ControlUnitSignalProfile` + `ControlUnitSignalProfileEntry`; через-опции
  переключателей (End/Way/Torque) — их данные переносятся в матричные строки
  (сигналы DRY_SPDT/DPDT в слотах LIMIT_SWITCHES/WAY_SWITCHES/TORQUE_SWITCHES),
  из конструктора и UI они убираются.
- **Перенос схем (21 связка):** после заливки матрицы каждая wiring-строка из
  снапшота становится `EaWiringDiagramBinding`: скоуп/БУ/напряжение/режим из
  wiring, подпись — матричные строки, соответствующие entries её профиля
  (маппинг F6) **+ строка слота HEATER по heater_supply связки**
  (NO_HEATER/SEPARATE_LINE из снапшота); match_type=exact. Схема медиабиблиотеки
  сохраняется (id/code).
- **Остаётся:** справочники `params.SwitchesParameters` (SPDT/DPDT —
  reference-данные строк), `InputSignalSpec`/`SignalRole` (используются
  БКВ/позиционерами — не трогаем), `ActuatorHeaterSupply` (обогрев),
  `ElectricControlUnitOption`/`ElectricPowerSupplyOption` (декларация доступных
  БУ×напряжений для модели — другой слой, не дубль матрицы).

## 8. Локализация (требование 2026-10-18, по lang.md)

Названия на сайте формируются из значений справочников, а не строковых
заглушек:

- Все новые справочники — `LocalizedDictFieldsMixin` (`name`/`description` RU +
  `name_i18n`/`description_i18n` JSON). Коды (`code`, аббревиатуры SPDT/NAMUR/IP,
  бренды) не переводятся — fallback ru.
- Чтение: `localized_name(obj, locale)` / `pick_i18n(...)`; локаль —
  `locale_from_accept_language` (api.js уже шлёт Accept-Language).
- Матричная строка: имя **выводится** из значений сигнала/устройства + суффикс
  «(Стандарт)/(Опция)» по availability (паттерн through-опций, уроки 18–22 lang.md):
  метод `localized_name(locale)`, `sync_name_i18n = False`.
- Селекторы/списки: `get_for_select(active_only=True, locale=None)`.
- Контент en/cn: идемпотентная management-команда (ключ — code/ru-строка),
  после наполнения справочников.
- Проверка: `python manage.py test core.tests.test_localization --keepdb` +
  smoke Accept-Language ru/en/zh-CN.

## 9. Докстринги (требование 2026-10-18)

Каждая новая модель — подробный модульный докстринг: назначение, примеры
значений, связи с другими моделями, правила валидации; поля — с help_text.
Образец: `electric_actuators/models/ea_control_unit_wiring.py`,
`params/control_unit_signal_profile.py`.

---

## 8. Решённые вопросы (сводка)

№1 V/A — nullable, заполнять по паспортам · №2 роли — свои choice на Ea*-моделях ·
№3/№11 формы — справочник EaSignalForm · №4 HART — атрибут hart на AN_4_20_* ·
№5 Modbus RTU/TCP — разные записи · №6 без GenericFK — три nullable FK
(control/feedback/protocol) + явные строки «нет» (signal=None) ·
№7 позиционер — kind=POSITIONER · №8 БУ — расширяем ControlUnitInstalledOption ·
№9 mode — поле строки · №10 S2/стартер — поля модели · №12 параметры по форме —
nullable-набор · №13 control_voltage — на БУ + voltage в форме сигнала ·
№14 пакеты — bundle на строке (без модели пресетов) · №15 capabilities — JSONField ·
№16 роли — полный каталог сразу · №17 слот — FK EaSignalSlot · №18 EaFeedbackDevice —
вводим сразу · №19 кодировка — ext_encoding (закрыто) · №20 словарь терминов —
ai_assistant. · **Обогрев — слот HEATER (ActuatorHeaterSupply: нет/отдельная линия/
от цепей питания) · Р1 шина — слот PROTOCOL + ext-композиция (принято) · Р3 слот —
модель EaSignalSlot (принято)**

---

## 10. План действий (обновлён 2026-10-18)

## 12. Инструмент обмена матрицей (2026-10-18)

Для любой серии ЭП — экспорт/импорт таблицы опций сигналов в Excel (xlsx).
Строка = модель × БУ × напряжение × слот × сигнал (или обогрев) × форма ×
availability (std/opt/na) × is_default × bundle × encoding/ext_encoding.
В файл входят **коды** (control_unit.code, power_supply.code, slot.code,
signal.code, heater_supply.code, form.code, body.code/item.code) — по ним
идёт обратный импорт (upsert строк на уровне корпуса).

Экспорт — **широкий формат (2026-10-18, для проверки AOX)**: листы
`ea_signal_matrix` (строки = модель × напряжение; колонки = БУ × (команды,
ОС, обогрев БУ); значения std/opt/no/пусто), `device` (датчик перегрева
THERMAL_RELAY/PTC_THERMISTOR на модель×напряжение), плюс прежние
`temp_options`/`cu_options`/`turn_counters` (не менялись):
- `temp_options` — температурные опции серии и **питание обогрева привода**
  (STD→NO_HEATER, LT/VLT × SEPARATE_LINE/MOTOR_CIRCUIT) + is_default;
- `cu_options` — пары БУ×напряжение (`AllowedControlUnitOption`) с
  **питанием БУ** (cu_power_supply) и кодировками encoding/ext_encoding;
  колонка item_code — модельные перекрытия серийной пары
  (is_active=False — запрет пары для модели);
- `turn_counters` — разрешённые **счётчики** серии (`AllowedTurnCounterOption`);
  лист создаётся и пустым (заголовок — подсказка для заполнения).

Классификация БУ (2026-10-18): `none` переименован в `basic` (миграция 0062:
Basic — управление подачей напряжения на мотор, kind=BASIC; «нет управления» —
записей нет). Группы БУ выгрузки: basic, pote, tr-4-20, tr10, posi-4-20,
posi10, int-o, int-l, int-n, int-n-hr, int-n-mb, int-n-pb. Командные сигналы —
220VAC (стандарт) и 24VDC (опция) для каждого; уставка 4-20/0-10 В; ОС —
end/way/torque × Откр/Закр × SPDT/DPDT + момент 4-20 + позиция (4-20 A/P/HART,
0-10 В, пот). Обогрев БУ — SEPARATE_LINE/CU_CIRCUIT (basic/pote/tr — 'no').

Оси пар (БУ×напряжение) — per-модель: серийные активные пары +
перекрытия модели (`AllowedControlUnitOption.model_line_item`, миграция 0061;
`resolve_cu_pair` — резолвер с запретами) + пары строк матрицы. Модели без
пар в каркас не попадают. Правило стартера: БУ×380 — только с БУ (при none
встроенного пускателя нет) → пары none×380 запрещены во всех сериях.

Реализация: `services/ea_matrix_io.py` (`export_series_rows`,
`export_extra_sheets`, `write_xlsx`) + management-команды
`export_ea_signal_matrix`/`import_ea_signal_matrix` + админка серии ЭП
(экспорт — кнопка на change_form + admin action; импорт — кастомный view).

*Прогресс: фаза 1 (выгрузка) и фаза 2 (справочники) выполнены — команда
`export_ea_signal_data`, снапшот `ea_signals_export_2026-10-18.json`, модели
`EaSignalForm`/`EaControlSignal`/`EaFeedbackSignal`/`EaCommProtocol`/
`EaFeedbackDevice`/`EaSignalSlot` (миграции 0049–0050, админка, тесты).
Фаза 3 (модель): `ControlUnitInstalledOption` расширен (kind/accepts/emits/
protocols/capabilities/control_voltage) — миграции params 0073–0074, backfill kind
(8 записей: NONE/POSITIONER/INTEGRATED), админка (autocomplete + json-editor).
Фаза 3 (seed): команда `seed_ea_signal_catalog` — 8 форм, 14 команд, 24 ОС, 8
протоколов, 6 устройств (с equivalents), 7 слотов; идемпотентна. Ревью №4
(М1–М3, L1–L2) закрыто.
Фаза 4 (модели + резолвер): `EaSignalMatrixEntry` (скоуп/слот/bundle/3 nullable
FK/нагреватель/device/conflicts/CheckConstraints) + `EaWiringDiagramBinding`
(подпись/match_type/диаграмма) — миграции 0051–0053; скоуп расширен уровнем
«корпус» (FK на `ElectricActuatorBody` — именно на него ссылается item.body,
QUI-варианты общего корпуса наследуют опции и схемы); сервис
`services/ea_signal_resolver.py` (наследование brand→серия→корпус→модель,
na-запреты, слоты, пакеты, режим, конфликты, поиск схемы); админки;
21 тест зелёный. Остаток фазы 4: составные конфликты через ParameterRule.
Фаза 5 (AOX): команда `load_ea_aox_matrix` — матчинг по колонке «Model»
(нормализация точек), строки на уровне корпуса; маркеры ячейки + статусы колонок
(строка 5); bulk_create; идемпотентность delete-first. Залито: 6 моделей с данными
(AR01E003/005, AR11E.005/015, AR21E007.S45/050.S34) → 23 строки; 38 строк таблицы
ПУСТЫЕ (данные не заполнены); AR21E060.S67/080.S67 отсутствуют в БД. Упрощения v1
в docstring команды (пары контактов — строка-представитель, Basic только 220AC,
команды/перегрев/индикатор/S2/позиционер — не залиты). В settings добавлен
SQLite busy_timeout=30 (диагностика зависших транзакций).*

1. **Выгрузка:** скрипт выгружает профили сигналов, `ControlUnitWiring`,
   через-опции переключателей (с encoding/ext_encoding) → JSON-снапшот +
   отчёт расхождений с таблицей AOX. До выгрузки зафиксировать **таблицы
   маппинга**: SignalRole → Ea*-роли (OPEN_LIMIT→END_OPEN, CLOSE_LIMIT→END_CLOSE,
   TORQUE_*→TORQUE_*, POS_4_20MA→POSITION/AN_4_20, ALARM/READY…),
   InputSignalSpec → EaControlSignal (form/voltage/current), SensorComponent →
   EaFeedbackDevice/EaFeedbackSignal (или «нет эквивалента» — в отчёт).
2. **Справочники:** `EaSignalForm`, `EaControlSignal`, `EaFeedbackSignal`,
   `EaCommProtocol`, `EaFeedbackDevice`, `EaSignalSlot` — с локализацией
   (LocalizedDictFieldsMixin) и подробными докстрингами; seed из разд. 10/13
   отчёта.
3. **Расширение** `params.ControlUnitInstalledOption` (kind, accepts, emits,
   protocols, capabilities, control_voltage) + **data-миграция backfill kind**
   для существующих записей (Basic→BASIC, INT ICU/SRCU/LCU→INTEGRATED…).
4. **Матрица:** `EaSignalMatrixEntry` (скоуп, слот, bundle, availability, device,
   conflicts) + `EaWiringDiagramBinding` (привязка схемы с подписью сигналов) +
   сервис резолвинга (наследование + слоты + bundle + конфликты + mode-фильтр +
   поиск схемы) с кэшем; составные конфликты (лимит клемм Q/M) —
   `configurator.ParameterRule`.
5. **Заливка данных:** AOX из `available-options-ea-AOX.xlsx`; профильные данные —
   из снапшота п.1; **21 wiring → `EaWiringDiagramBinding`** (подпись — матричные
   строки по entries профиля через маппинг F6, match_type=exact, схемы из
   медиабиблиотеки сохраняются); AUMA (TPA/MSP) из каталогов; Rotork — после
   spec-листов (PUB002-039/065). **Гейт перед фазой 6:** сверка полноты —
   каждая строка выгрузки покрыта матрицей, расхождения отчитаны.
6. **Конфигуратор:** полный переход на матрицу (слоты single-choice, слот
   PROTOCOL из Р1, bundle); ext-коды — из матричных строк (расширение
   `_get_ext_code_data_dict` на матричный источник); отображение схемы —
   из `EaWiringDiagramBinding` («есть или нет»). **Шаблоны серий ЭП + локализация:**
   плейсхолдеры сигналов в `name_template`/`description_template` серий резолвятся
   через `name_path='...__name'` → `_resolve_data_dict_target` читает `name_i18n`
   справочника/матричной строки (уроки 13/15 lang.md); матричная строка получает
   `localized_name(locale)` (сигнал/устройство + суффикс «(Стандарт)/(Опция)»).
7. **Удаление старого:** через-опции переключателей из конструктора/UI;
   `AllowedSignalProfileOption`; `ControlUnitWiring` целиком +
   `ElectricControlUnitOption.control_unit_wiring`;
   `ControlUnitSignalProfile`+Entry (после подтверждения заливки).
8. **Генератор wiring-диаграмм:** по выбранному набору сигналов строит клеммную
   схему (SVG/канвас: клеммы X1/XK, номера проводов, формы сигналов, БУ×напряжение);
   данные клемм — поле `wires` на сигналах; покрывает комбинации без готовой
   привязки (дополнение к «есть или нет»).
9. **ai_assistant:** `TermGlossaryEntry` + инъекция в extract-промпты + эндпоинт
   поиска и виджет подсказок; позже — FILTER_DEFINITIONS ЭП + handler на
   матричный резолвер (для extract фильтров ЭП в пайплайне).
10. **Проверка:** спот-чек резолвинга против таблицы AOX (3 модели × 2 напряжения
   × 2 режима); юнит-тесты резолвера (наследование/override, слот single-choice,
   bundle-атомарность, na-запреты, конфликты, поиск схемы по подписи);
   идемпотентность заливки (повторный импорт без дублей); CheckConstraint «ровно
   один signal»; тест локализации + smoke ru/en/cn; `manage.py check`.

Критерий готовности фазы 6: для серии AOX-R резолвинг матрицы совпадает с
колонками исходной таблицы; артикулы собираются без «плавающих» значений.

## 11. Отложенные задачи (вне фаз)

- **QuestionGraph (core):** РЕШЕНО (2026-10-18) — импорт возвращён в
  `core/models/__init__.py` (`from .question_graph import QuestionGraph` +
  `__all__`); `makemigrations --check` чист, предупреждение тест-раннера ушло.

---

## 13. Пакет исправлений после ревью выгрузки (согласовано 2026-10-18)

### 13.1 Справочники и модели

1. **Температурное исполнение = источник обогревателя привода.**
   `ElectricTemperatureOption`: + `code` (STD/LT/VLT) и + FK `heater_supply`
   (`params.ActuatorHeaterSupply`). Плоские строки серии:
   STD→NO_HEATER (std); LT+SEPARATE_LINE (std, дефолт); LT+MOTOR_CIRCUIT (opt);
   VLT+SEPARATE_LINE (std); VLT+MOTOR_CIRCUIT (opt). Селектор в конфигураторе —
   один, без вложенных ссылок (скорость поиска). Данные строк LT/VLT существующих
   серий — data-миграция (существующим LT/VLT строкам проставить SEPARATE_LINE и
   добавить дубли MOTOR_CIRCUIT opt).
2. **Слот `HEATER_ACTUATOR` из матрицы УДАЛЯЕТСЯ** (питание обогрева привода живёт
   в температурной опции). Слот `HEATER_CONTROL_UNIT` остаётся — обогреватель БУ
   как опция: NO_HEATER (std), CU_CIRCUIT (новое значение ActuatorHeaterSupply
   «От цепей питания блока управления»), SEPARATE_LINE; строки только для
   интеллектуальных БУ (kind=INTEGRATED); для `none` слот не показывается.
3. **Слот `THERMAL_SENSOR`** («Датчик температуры/теплозащита»): строки NO_SENSOR
   (none-строка), «датчик без выхода ОС» (device + name, без сигнала — валидацию
   `device` ослабить), FB_OVERHEAT_NC, FB_OVERHEAT_SPDT.
4. **`EaFeedbackDevice`:** + поле `kind` (POSITION_SENSOR / THERMAL_SENSOR).
   Типы теплозащиты: `THERMAL_RELAY` (биметаллическое термореле),
   `PTC_THERMISTOR` (PTC-термистор + реле оценки). THERMAL_FUSE НЕ включаем.
   В AOX тип не указан — заливщик ставит THERMAL_RELAY (по указанию), в выгрузке
   device — колонка-код (термореле/PTC-схема редактируемы).
5. **Новые слоты (дополнение 2026-10-18):**
   - `CMD` — команды управления: OPEN/STOP/CLOSE/EMERGENCY/MODE
     (EaControlSignal, формы DISC_AC/DISC_DC + voltage). Могут отсутствовать:
     в модулирующих БУ — только уставка; в дешёвых приводах без БУ — управление
     подачей напряжения на мотор (строк CMD нет вообще). Строка-опция «нет» —
     none-строка. Колонки AOX 61–68.
   - `SETPOINT` — уставка положения 4-20 мА актив/пассив (EaControlSignal
     AN_4_20_*), колонки AOX 79–82; у HART-БУ — с HART (отдельная строка).
   - `INDICATOR` («Индикатор работы привода») — перенос legacy-опции блинкера:
     строки BLINKER (мигающий светодиод; характерно без БУ), LCD_POSITION
     (индикация позиции на дисплее; характерно для int-БУ AOX), LCD+BLINKER
     (требование бывает). Все три — none-строки с названием (клеммного сигнала
     нет); availability — по БУ из матрицы.
   - `TURN_COUNTER` (счётчик оборотов) — legacy `params.TurnCounterOption`
     (механические, разные по числу оборотов) переносится в слот; строки:
     NONE, MECH (конкретные TurnCounterOption как device/name),
     ELECTRONIC (функция БУ — none-строка), MECH+ELECTRONIC, MECH+FB
     (механический с ОС FB_TURN_COUNTER_NO — сигнал уже в каталоге),
     MECH+ELECTRONIC+FB. AOX не умеет механический+электронный — для своей
     линейки ставим na/нет; структура готова для других производителей.
6. **Слот `LOCAL_CONTROL` (вид органов местного управления)** — из сводной
   БУ Архимед: базовый = КНОПКИ Открыто/Закрыто/Стоп; INT/O, INT/L, INT/N =
   СЕЛЕКТОР Местное/Удалённое + СЕЛЕКТОР Открыто/Закрыто/Стоп. Строки:
   BUTTONS, SELECTOR, NONE (без БУ — управление мотором напрямую);
   availability — по БУ; у AOX возможны опции — структура готова.
7. **Расширение INDICATOR (по сводной):** базовый БУ имеет не только блинкер,
   но и НАБОР светодиодов (ОТКРЫТО/ЗАКРЫТО/ХОД/АВАРИЯ/СТОП). Строки слота:
   LED_SET, BLINKER, LED_SET+BLINKER, LCD_POSITION, LCD+BLINKER.
8. **Новые сигналы ОС (по сводной, колонка «Сигналы обратной связи (разъёмы)»):**
   FB_STOP (Останов, сухой контакт), FB_LOCAL_REMOTE (Удалённое/местное
   управление), FB_SELECTOR_POSITION (Положение ключа-селектора),
   FB_PHASE_LOSS (Авария: потеря фазы). В CMD добавить CMD_REMOTE (вход
   «Удалённое управление») и CMD_ESD уже есть. Роли — в EaFeedbackSignal/EaControlSignal
   choice-списки.
9. **capabilities (JSON) наполняется из сводной** (БУ int-*):
   non_intrusive_setup, torque_sensor_setup, display:{position,commands,status,
   error,overload,torque}, menu_languages:[en,ru], datalogger:{events,torque,
   temperature,vibration}, start_counter, runtime_counter, torque_bypass,
   anti_water_hammer, password_protection, wall_mount, motor_temp_control,
   phase_loss_control, phase_auto_correction, fail_safe_action:{alarm,close,open},
   namur_ne107, menu_settings:{dead_zone,calib_4ma,calib_20ma,direction,
   intermediate_position,two_speed}, parallel_interface, protocol-опции (HART/
   ModBus/ProfiBus/FF — в слот PROTOCOL). НОВЫХ таблиц не создаём — поле
   capabilities JSONField уже есть (фаза 3).
10. **Ввод кабелей (без новой модели):** в `CableGlandHolesSet` добавляется
    поле `kind` (GLAND_SET по умолчанию / CONNECTOR_PLUG) и запись-вариант
    CONNECTOR_PLUG (разъём «подсолнух», отверстий нет — валидация cg1..cg4
    пустые); приводы прописывают её как обычный вариант опции
    CableGlandHolesSetBodyOption (через корпус). Тот же паттерн применим к
    соленоидным клапанам (при необходимости — вынести «вид ввода» в params).
    Влияет на описание присоединения корпуса и на позицию артикула.
11. **Все опции — записи справочников с локализацией, БЕЗ хардкода:** каждая
    новая опция (слоты LOCAL_CONTROL/INDICATOR/CMD/SETPOINT/TURN_COUNTER/
    THERMAL_SENSOR, значения heater_supply, CONNECTOR_PLUG, температурные
    строки) — модель с LocalizedDictFieldsMixin + name_i18n (ru/en/cn) и
    выводится в плейсхолдеры шаблонов описаний фронта и спецификаций
    (name_path/ext_code_path в TemplateFieldMapping, уроки 13/15 lang.md).
    Чек в пакете проверки: для каждой опции есть запись каталога + placeholder
    в шаблоне серии + smoke ru/en/cn.

Открытый вопрос РЕШЁН: питание БУ отдельно от питания привода (у int-* БУ
Архимед «да») — **свойство/опция БУ, НЕ ось матрицы**: поле `cu_power_supply`
(FK PowerSupplies, null = от питания привода) добавляется в
`AllowedControlUnitOption` (серия×БУ) — участвует в кодировке (позиция ext),
выбирается в конфигураторе и выводится в спецификацию плейсхолдером.
12. **Питание БУ:** см. выше — `AllowedControlUnitOption.cu_power_supply` +
    ext-позиция `{cu_p}` (пусто=от привода; иначе код PowerSupplies, напр.
    24/110). Дефолт — от питания привода.

### 13.2 Заливщик AOX (`load_ea_aox_matrix`)

- `availability='std'` → `is_default=True` (заливщик, импорт, существующие строки).
- **Пары контактов — ДВЕ строки** OPEN+CLOSE с общим bundle
  (END_SPDT/END_DPDT, WAY_*, TORQUE_*): FB_*_OPEN_* + FB_*_CLOSE_* (сигналы CLOSE
  уже в каталоге). Режимы on_off/modulating — отдельными строками, как колонки AOX.
- **OverHeat:** колонки 21/23 (Basic) и 55/57 (INT) → слот THERMAL_SENSOR
  (21/55 SPST→FB_OVERHEAT_NC, 23/57 SPDT→FB_OVERHEAT_SPDT), device=THERMAL_RELAY.
- **Heater:** 73–76 (Basic) — больше НЕ строки матрицы (см. 13.1); 83–88 (INT) →
  слот HEATER_CONTROL_UNIT для int-*: separate wire→SEPARATE_LINE,
  from actuator→CU_CIRCUIT. Ячейки «No heater, but…» — строку не создаём.
- **«Customizable» → opt** (текстовые маркеры больше не игнорируются).
- 24В: в AOX напряжения не кодируются; при ручном заполнении 24DC ставить
  NO_SENSOR (у AOX на 24В датчика нет).

### 13.3 Экспорт-каркас и импорт (`ea_matrix_io.py`)

- **Экспорт — полный каркас рабочей таблицы:** все модели серии × пары
  (БУ × напряжение), собранные из (а) фактических строк матрицы серии/бренда и
  (б) legacy-структуры `ElectricPowerSupplyOption`×`ElectricControlUnitOption`
  (напряжения модели и БУ на них) × режимы × слоты × опции (словарь слота =
  union сигналов/устройств/heater_supply по серии/бренду). Ячейки без строки —
  пустая availability (импорт пропускает); std/opt — upsert; na — запрет.
- **Импорт:** device по коду, bundle, mode; `std` → `is_default=True`;
  новые пары (в т.ч. 380/24DC) создаются из заполненного Excel без правки AOX.
- Кнопки экспорт/импорт — на странице редактирования серии (сделано);
  admin action на списке серий — для мультисерийного экспорта (оставлен).

### 13.4 Резолвер

- Слоты THERMAL_SENSOR / HEATER_CONTROL_UNIT — обычная логика; HEATER_CONTROL_UNIT
  не показывается для БУ kind=NONE. Обогрев привода — вне резолвера (свойство
  выбранной температурной опции, отдаёт конфигуратор). Привязки схем — без
  температурной оси до фазы генератора схем (8).

### 13.5 Legacy-связки (результат проверки использования)

- `AllowedControlUnitOption` — ЖИВ: `ElectricControlUnitOption.resolved_encoding`
  (encoding артикула из серии). В новой схеме encoding переезжает в строки матрицы
  (поля encoding/ext_encoding уже есть) → удалить в фазе 7.
- `AllowedSignalProfileOption` — МЁРТВ (только админка/инлайны/списки копирования,
  runtime-использований нет) → удалить.
- `AllowedTurnCounterOption` — мёртв кроме encoding; счётчик станет опцией слота
  матрицы (сигнал FB_TURN_COUNTER_NO уже в каталоге) → удалить в фазе 7.
- `ElectricPowerSupplyOption` — ОСТАЁТСЯ: моторные данные (токи/время/момент) +
  источник пар «модель×напряжение» для каркаса (13.3).
- `ControlUnitInstalledOption.control_voltage` — оставить (каталоговая
  характеристика для AUMA/Rotork; сейчас пусто).

### 13.6 Порядок выполнения и проверка

1) модели+миграции (13.1) → 2) заливщик (13.2, перезаливка AOX delete-first) →
3) экспорт-каркас+импорт (13.3) → 4) резолвер (13.4) → 5) тесты (23→~30:
пары OPEN/CLOSE+bundle, OverHeat+device, heater БУ по БУ, каркас полноты,
round-trip импорта, is_default) → 6) `manage.py check` +
`makemigrations --check` → 7) сверка выгрузки AR21E с AOX вручную.

Критерий: выгрузка AR21E содержит ВСЕ 15 моделей серии, у 007 — пары
Откр/Закр (бандлы), OverHeat с device, is_default у std; у остальных моделей —
пустые ячейки для заполнения.

---

## 14. Система ext-кода заказа (образец — AUMA; согласовано 2026-10-18)

### 14.0 Реализация ext-кодировок в моделях (2026-10-18)

- `EaSlotOption.ext_encoding` (миграция 0064) — код позиции каждой опции
  слота (E1/E2, W1/W2, T1/T2, P/T/TA, C/S, D/B/DB/L/LB, M/E/EM/MF/EMF,
  DC/R/R2, A/P, S/N, T0/T1/T2…); пусто — стандарт.
- `ElectricTemperatureOption.ext_encoding` — ''/L/LM/V/VM (STD/LT±обогрев/
  VLT±обогрев); `AllowedControlUnitOption.ext_encoding` — CU_EXT
  (IO/IL/IN/IM/IP/IH/PT/TR/T0/PR/P0; basic — '').
- `ext_encoding_template` прописан во все серии ЭП:
  `{cu}{cu_p}{ps}{mode}{proto}.{end}{way}{torq}.{pos}{hart}.{temp}{h_cu}{therm}.{lc}{cmd}{setp}{cnt}{ind}`.
- Конструктор: `generated_ext_code` резолвит все позиции (cu/ps/temp — из
  выбора; сигнальные позиции пусты до матричного выбора, фаза 6).
- `EquipmentType` («Электропривод», code=electric-actuator): `name_template`
  (краткое наименование из набора артикула) и `spec_template` (полная
  спецификация со всеми опциями) + `*_template_i18n` (ru/en/cn). Плейсхолдеры
  зарезолвятся карточкой каталога (TemplateMixin) — см. фазу 6.

### 14.1 Принцип

- Код заказа = **основной артикул** (серия+модель+механика: IP/Exd/покрытие/
  угол/штурвал/цвет — существующие encoding через-опций) + **ext-блок**
  (сигнальная часть: БУ, напряжение, режим, слоты матрицы).
- ext-блок — **позиционный, как у AUMA** (SA 07.2/AC 01.2 + буквенные коды
  опций): каждая позиция = одна группа опций, пусто = стандарт серии.
- Значения — из `ext_encoding` через-опций и матричных строк (у строки
  EaSignalMatrixEntry поля encoding/ext_encoding уже есть); шаблон —
  `ElectricActuatorModelLine.ext_encoding_template` с плейсхолдерами
  `{...}` (механизм `generated_ext_code` в core.models.mixins уже готов).
- Своя система там, где AUMA избыточна/недостаточна: у нас фиксированные
  позиции на каждый слот (у AUMA набор опций зависит от типа БУ), дефолт
  кодируется пустотой (у AUMA — явными кодами), тип датчика термозащиты —
  отдельной подпозицией (у AUMA не кодируется).

### 14.2 Позиции и коды (явные коды — аналог хэша, 2026-10-18)

**Правило: пустых кодов нет** — каждый вариант (включая «нет»/стандарт) имеет
явный код; собранный ext-код имеет фиксированную длину (все позиции всех
блоков), как хэш-функция конфигурации. Разделитель блоков — точка.

Шаблон (блоки через «.»):

    {cu}{cu_p}{ps}{mode}{proto} . {ip}{exd} . {end}{way}{torq} . {pos}{hart} . {temp}{h_cu}{therm} . {lc}{cmd}{setp}{cnt}{ind}{bat}

**Блок БУ** `{cu}{cu_p}{ps}{mode}{proto}`:
- cu: NO=нет управления · BA=basic · LCU=int-o (ICU) · INT=int-l (SRCU) ·
  AINT=int-n (ICU полн.) · AINT-HR/AINT-MB/AINT-PB — протокольные варианты ·
  PT=pote · TR=tr-4-20 · T0=tr10 · PR=posi-4-20 · P0=posi10
- cu_p: P0=от питания привода · X=отдельно (24 V DC)
- ps: 220AC / 380AC / 24DC
- mode: O=on-off · M=modulating · B=оба
- proto: N0=нет · MB/MT/PB/PN/FF/PS/DN/EI

**Блок защиты** `{ip}{exd}`:
- ip: IP54…IP69 (код IpOption) · IP00=без защиты
- exd: EX0=без Ex · иначе exd_short записи ElectricExdOption («IIC T5 Gb X»)

**Блок коммутации** `{end}{way}{torq}`: 0=нет · 1=SPDT · 2=DPDT (E/W/T-префикс)

**Блок ОС** `{pos}{hart}`:
- pos: N0=нет · P=потенциометр · T=4-20 пасс · TA=4-20 акт · TV=0-10 В
- hart: H0=без HART · H=HART

**Блок климата** `{temp}{h_cu}{therm}`:
- temp: ST=STD · L=LT+отд.кабель · LM=LT+от мотора · V=VLT+отд.кабель · VM=VLT+от мотора
- h_cu: H0=нет · C=от цепей БУ · S=отдельная линия
- therm: T0=нет датчика · TX=датчик без выхода · T1=термореле НЗ · T2=термореле SPDT
  (PTC-варианты P1/P2 — по данным пользователя)

**Блок опций** `{lc}{cmd}{setp}{cnt}{ind}{bat}`:
- lc: B=кнопки · S=селекторы · N=нет
- cmd (команды управления): N0=нет · O=О/С/З 220AC · D=О/С/З 24DC ·
  R=Remote 220AC · RD=Remote 24DC · LK/LD=Lock 220/24 · MK/MD=Manual 220/24 ·
  EO/EB=ESD Откр 220/24 · EC/EQ=ESD Закр 220/24 · IO/ID=Interlock Откр 220/24 ·
  IC/IK=Interlock Закр 220/24 · DV/DW=Drive enable 220/24 · MO/MW=Mode 220/24
- setp: N0=нет · A=4-20 акт · P=4-20 пасс · A0=0-10 акт · P0=0-10 пасс
- cnt: N0=нет · M=мех · E=эл · EM=эл+мех · MF=мех с ОС · EMF=эл+мех с ОС от мех
- ind: N0=нет · D=LED-набор · B=blinker · DB=LED+blinker · L=LCD · LB=LCD+blinker
- bat: B0=нет · BAT=батарея положения безопасности (опция ElectricBatteryOption,
  серия AR11E; с ней положение безопасности выбирается НЗ/НО, без неё — только
  «оставаться в текущем положении»)

Коды внутри позиции попарно не префиксы друг друга (расшифровка greedy
longest-match однозначна).

### 14.3 Проверка покрытия (все ли опции покрыты) — пробелы

Покрыто: позиционная ОС (3–6, 19–20, 49–51), End/Way/Torque (7–18, 25–48),
OverHeat (21–23, 55–57), обогрев привода (73–76, через TEMP), обогрев БУ
(83–88), позиционер (89–92 — как БУ PR/P0), индикатор/blinker (77–78,
серийные опции), температурное исполнение (серийные LT/VLT).

НЕ покрыто (добавить в план фазы 5/6):
1. **Команды Open/Close/Stop + Remote (61–72)** — РЕШЕНО: слоты CMD и SETPOINT
   (см. 13.1 п.5); заливка колонок 61–68/69–72 — в пакете 13.2.
2. **Позиционер как БУ** — kind=POSITIONER есть, но матрица позиционера
   пустая; заливка 89–92 отложена до подтверждения семантики (отдельное
   устройство с собственной платой).
3. **S2/стартер** — позиции ext есть, данных в AOX нет (примечание про 380В
   starter — учитывать при заливке 380В).
4. **MWG-аналог** (магнитный датчик = концевые+момент+ОС одним устройством) —
   у AOX нет; покрывается механизмом bundle в матрице, кода MWG не вводим
   до появления в каталоге.
5. **ОС «открыто/закрыто»** — покрыто слотами LIMIT/WAY (FB_END_OPEN/CLOSE,
   FB_WAY_*); «стоп» как ОС — ЕСТЬ в сводной Архимед («Останов 'сухой'
   контакт») → новый сигнал FB_STOP (см. 13.1 п.8); статус «не в работе» —
   FB_READY_NO / FB_ALARM_*. Отсутствие ОС — none-строка слота (для дешёвых
   приводов без БУ и без концевых).
6. **Индикатор/счётчик** — РЕШЕНО: слоты INDICATOR и TURN_COUNTER (13.1 п.5),
   legacy-через-опции блинкера/счётчика переносятся в матрицу (фаза 7).
7. **Органы местного управления (кнопки/селекторы)** — РЕШЕНО: слот
   LOCAL_CONTROL (13.1 п.6) — из сводной БУ Архимед 2025-06-24.
8. **Индикация БУ** — расширено LED-набором (13.1 п.7): у базового БУ Архимед
   светодиоды ОТКРЫТО/ЗАКРЫТО/ХОД/АВАРИЯ/СТОП, у int-* — LCD.
9. **Функции интеллектуальных БУ** — в capabilities JSON (13.1 п.9): перечень
   из сводной 2025-06-24; отдельных таблиц не добавляем.
10. **Вид ввода кабелей (КВ vs разъём «подсолнух»)** — РЕШЕНО: through-опция
    серии, НЕ матрица (13.1 п.10).
11. **Питание БУ отдельно от питания привода** (сводная: int-* «да») —
    открытый вопрос: ось матрицы cu_power_supply или свойство БУ.

### 14.4 Задачи в план

- ext_encoding проставить: строки матрицы (по 14.2), температурные строки
  (L/LM/V/VM), CU (в `AllowedControlUnitOption` до фазы 7, затем — в матрицу),
  устройства (не выводится в код, только описания).
- `ext_encoding_template` для серий ЭП — шаблон из 14.2 с плейсхолдерами;
  TemplateFieldMapping: ext_code_path на матричные строки/слоты (резолвер
  отдаёт коды выбранных строк — расширение `_get_ext_code_data_dict` на
  матричный источник, фаза 6 плана).
- **Сервис `services/ea_ext_code.py`:**
  - `decode_ext_code(model_line, ext_code)` — расшифровщик: по записям опций
    серии/каталога разбирает код на {позиция: опция} с локализованными
    именами; неизвестные коды → предупреждения в результате;
  - `coding_rules(model_line)` — правила кодирования серии (легенда):
    позиции, допустимые коды, имена опций (локализованные), дефолты — для
    админки/каталога и подсказок ai_assistant (связка с TermGlossaryEntry);
  - сборка кода остаётся на `generated_ext_code` (core.models.mixins);
    декодер — обратная функция, тесты: build→decode round-trip.
- Тест: полный выбор конфигуратора → ext-код собирается без «плавающих»
  позиций; дефолты дают пустой ext-блок; decode(build(x)) == x.

Открытые мини-вопросы: читаемость ps (`3` vs `380`), коды cmd после заливки
61–68, коды счётчика из TurnCounterOption.
