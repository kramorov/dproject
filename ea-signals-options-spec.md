# Опции управления и обратной связи электроприводов — полное описание и план

Дата: 2026-10-18. Состояние: согласовано с пользователем, готово к реализации.

Источники: таблица AOX `available-options-ea-AOX.xlsx`; сводная БУ Архимед
`Управление_приводами_блоки_Сводная_АРХИМЕД_2025-06-24.xlsx`; каталоги AUMA
(SA/SAR Y004.388, AC 01.2) и Rotork (IQ3 Pro PUB002-197) — см. разд. 10
`ea-aox-signals-report.md`.

---

## 1. Справочники (модели)

| Модель | Назначение |
|---|---|
| `EaSignalForm` | Форма сигнала (DRY_SPST/SPDT/DPDT, AN_4_20_ACTIVE/PASSIVE, RES_POTENTIOMETER, DISC_AC/DISC_DC, …) |
| `EaControlSignal` | Входные команды (OPEN/STOP/CLOSE/EMERGENCY/MODE/REMOTE/SETPOINT 4-20) |
| `EaFeedbackSignal` | Сигналы ОС (контакты/аналог/сопротивление) |
| `EaCommProtocol` | Шины: ProfiBus/Profinet/Modbus RTU/TCP/FF/HART |
| `EaFeedbackDevice` | Устройство/датчик ОС (RWG/EWG-эквиваленты, потенциометр, термореле, PTC) + поле `kind` (POSITION_SENSOR/THERMAL_SENSOR) |
| `EaSignalSlot` | Группа взаимоисключающих опций |
| `EaSignalMatrixEntry` | Строка матрицы доступности (БУ×напряжение×режим → опция) |
| `EaWiringDiagramBinding` | Привязка схемы подключения к набору строк |
| `ElectricTemperatureOption` | Температурное исполнение (через-опция серии): + `code`, + `heater_supply` |
| `AllowedControlUnitOption` | БУ, разрешённый для серии, с кодировкой: + `cu_power_supply` |
| `CableGlandHolesSet` | Наборы отверстий под КВ: + `kind` (GLAND_SET/CONNECTOR_PLUG) |
| `params.ActuatorHeaterSupply` | NO_HEATER/SEPARATE_LINE/MOTOR_CIRCUIT + новое CU_CIRCUIT |
| `params.ControlUnitInstalledOption` | Типы БУ (+ `capabilities` JSONField — функции интеллектуальных БУ) |

Все опции — записи справочников с локализацией (`LocalizedDictFieldsMixin`,
`name_i18n` ru/en/cn) и выводятся плейсхолдерами шаблонов описаний/спецификаций
(`name_path`/`ext_code_path`, уроки 13/15 lang.md). Хардкода нет.

---

## 2. Слоты и опции

### 2.1 LOCAL_CONTROL — органы местного управления
BUTTONS (кнопки Открыто/Закрыто/Стоп — базовый БУ) · SELECTOR (селекторы
Местное/Удалённое + Открыто/Закрыто/Стоп — int-*) · NONE (без БУ, мотор
напрямую). Ext: пусто/B/S/N.

### 2.2 CMD — входные команды (слот матрицы)
OPEN, CLOSE, STOP, EMERGENCY, MODE, REMOTE («Удалённое управление»); формы
DISC_AC/DISC_DC + voltage (напряжение цепи управления — характеристика БУ:
AUMA 24VDC std/115VAC opt; Rotork 20–60VDC/40–120VAC). Могут отсутствовать:
modulating БУ — только уставка; приводы без БУ — команд нет. Ext: пусто
(OPEN/STOP/CLOSE 220AC)/D(24DC)/R(REMOTE)/N(нет).

### 2.3 SETPOINT — уставка положения (слот матрицы)
AN_4_20_ACTIVE, AN_4_20_PASSIVE, AN_4_20_HART (HART поверх 4-20; 0–10В —
не подтверждено у AUMA, при необходимости добавляется формой). Ext:
пусто/A/P/H.

### 2.4 LIMIT_SWITCHES / WAY_SWITCHES / TORQUE_SWITCHES (слоты матрицы)
Пары контактов Откр/Закр — ДВЕ строки (OPEN+CLOSE) с общим `bundle`:
- End: FB_END_OPEN/CLOSE_SPDT (E1), _DPDT (E2);
- Way: FB_WAY_OPEN/CLOSE_SPDT (W1), _DPDT (W2);
- Torque: FB_TORQUE_OPEN/CLOSE_SPDT (T1), _DPDT (T2).
Режимы on_off/modulating — отдельными строками, как колонки AOX.

### 2.5 POSITION_FEEDBACK — позиционная ОС (слот матрицы)
FB_POS_4_20MA_ACTIVE (TA), _PASSIVE (T), _HART (TH), FB_POS_POT_1K (P,
RES_POTENTIOMETER, resistance_kohm/max_power_w/turns). Устройства:
TRANSMITTER_4_20 ≡ RWG_4020, HALL ≡ EWG_01_1, POT_RAW, MWG (магнитный,
только с int-БУ — через bundle). Встроенная 4-20 пассив у int-* — std
(пусто в ext).

### 2.6 PROTOCOL — шина (слот матрицы)
PB ProFiBus · PN Profinet · MB Modbus RTU · MT Modbus TCP · FF Foundation
Fieldbus · HART (привязан к аналоговой петле — позиция {hart}). Ext-композиция:
одна позиция, взаимоисключающие коды.

### 2.7 THERMAL_SENSOR — датчик температуры/теплозащита (слот матрицы)
NO_SENSOR (none-строка; у AOX 24В — стандарт) · «датчик без выхода ОС»
(device + name, сигнала нет — валидация device ослаблена) ·
FB_OVERHEAT_NC (T1) · FB_OVERHEAT_SPDT (T2). Устройства: THERMAL_RELAY
(биметаллическое термореле), PTC_THERMISTOR (PTC + реле оценки); THERMAL_FUSE
не используем. AOX не указывает тип — заливщик ставит THERMAL_RELAY.

### 2.8 HEATER_CONTROL_UNIT — обогреватель блока управления (слот матрицы)
NO_HEATER (std) · CU_CIRCUIT (C, от цепей питания БУ — новое значение
ActuatorHeaterSupply) · SEPARATE_LINE (S). Строки только для интеллектуальных
БУ; для none слот скрыт. Обогреватель ПРИВОДА — не слот: свойство
температурной опции (см. 3).

### 2.9 INDICATOR — индикация (слот матрицы)
LED_SET (D — светодиоды ОТКРЫТО/ЗАКРЫТО/ХОД/АВАРИЯ/СТОП, базовый БУ) ·
BLINKER (B) · LED_SET+BLINKER (DB) · LCD_POSITION (L, int-*) · LCD+BLINKER (LB).

### 2.10 TURN_COUNTER — счётчик оборотов (слот матрицы)
NONE · MECH (M, конкретные `params.TurnCounterOption` — число оборотов) ·
ELECTRONIC (E, функция БУ) · MECH+ELECTRONIC (EM) · MECH+FB (MF, ОС
FB_TURN_COUNTER_NO от механического) · MECH+ELECTRONIC+FB (EMF). AOX не умеет
MECH+ELECTRONIC — na для своей линейки; структура готова для других.

### 2.11 ОС состояния (сигналы, слоты LIMIT/WAY и отдельные)
FB_END_OPEN/CLOSE, FB_WAY_OPEN/CLOSE, FB_TORQUE_OPEN/CLOSE, FB_STOP (Останов
сухой контакт), FB_LOCAL_REMOTE (Удалённое/местное), FB_SELECTOR_POSITION
(положение ключа-селектора), FB_READY_NO (Готовность), FB_ALARM_SPDT/
FB_ALARM2_SPDT (Авария), FB_PHASE_LOSS (Авария: потеря фазы),
FB_TORQUE_4_20MA (аналоговый момент — Rotork CTT), FB_TURN_COUNTER_NO.

---

## 3. Температурное исполнение и обогрев привода

`ElectricTemperatureOption` (через-строка серии) + `code` (STD/LT/VLT) +
`heater_supply` FK. Плоская шкала строк серии:
- STD, NO_HEATER — std;
- LT, SEPARATE_LINE — std (дефолт);
- LT, MOTOR_CIRCUIT — opt;
- VLT, SEPARATE_LINE — std;
- VLT, MOTOR_CIRCUIT — opt.
Ext-позиция {temp}: пусто/L/LM/V/VM. Селектор один, без вложенности.

---

## 4. Питание БУ

`AllowedControlUnitOption.cu_power_supply` (FK PowerSupplies, null = от питания
привода; у int-* Архимед — отдельно, например 24VDC). Выбор в конфигураторе,
вывод в спецификацию плейсхолдером, ext-позиция {cu_p}.

## 5. Ввод кабелей

`CableGlandHolesSet.kind` (GLAND_SET/CONNECTOR_PLUG) + запись CONNECTOR_PLUG
(разъём «подсолнух», cg1..cg4 пустые). Приводы прописывают её вариантом
CableGlandHolesSetBodyOption. Паттерн применим к соленоидным клапанам.

## 6. Функции интеллектуальных БУ (capabilities JSON)

non_intrusive_setup, torque_sensor_setup, display:{position,commands,status,
error,overload,torque}, menu_languages:[en,ru], datalogger:{events,torque,
temperature,vibration}, start_counter, runtime_counter, torque_bypass,
anti_water_hammer, password_protection, wall_mount, motor_temp_control,
phase_loss_control, phase_auto_correction, fail_safe_action:{alarm,close,open},
namur_ne107, menu_settings:{dead_zone,calib_4ma,calib_20ma,direction,
intermediate_position,two_speed}, parallel_interface. Отдельных таблиц нет —
JSONField `ControlUnitInstalledOption.capabilities`.

---

## 7. Матрица доступности (правила)

- Скоуп: brand → серия → корпус → модель (ровно один); специфичнее перекрывает.
- Ключ строки: (БУ, напряжение питания мотора, режим on_off/modulating/both).
- availability: std (стандарт, → is_default=True) / opt / na (запрет
  унаследованной).
- Слот — single-choice; bundle — атомарный выбор (пары Откр/Закр, MWG);
  conflicts — парные запреты.
- Режимы on_off/modulating — отдельные строки (разные моторы/БУ; у некоторых
  БУ нет OPEN/CLOSE — только уставка 4-20).
- Строка ссылается на контроль/ОС/протокол либо none-строка (нет опции).
- device — с feedback_signal; для «датчика без выхода ОС» — с none-строкой.
- heater_supply — только слоты HEATER_*.

## 8. Привязки схем (EaWiringDiagramBinding)

Схема «есть или нет»: скоуп + БУ/напряжение/режим + подпись строк
(match_type exact/superset). Генератор схем (фаза 8) дополнит; питание
обогрева/БУ учитывается при генерации (в привязку пока не входит).

## 9. Расширенный код заказа (ext)

Шаблон (блоки через `.`, пусто = стандарт):
`{cu}{cu_p}{ps}{mode}{proto} . {end}{way}{torq} . {pos}{hart} . {temp}{h_cu}{therm} . {lc}{cmd}{setp}{cnt}{ind}{s2}`
Коды позиций — см. разд. 2 (в скобках после каждого варианта). Сборка —
`generated_ext_code` (core.models.mixins). Сервис `services/ea_ext_code.py`:
`decode_ext_code(model_line, code)` — расшифровка в {позиция: опция} с
локализованными именами и предупреждениями; `coding_rules(model_line)` —
легенда позиций/кодов/дефолтов (админка, каталог, ai_assistant).
Тест round-trip: decode(build(x)) == x.

---

## 10. План работ (порядок и проверка)

1. **Справочники/модели (13.1):** ElectricTemperatureOption (+code,
   +heater_supply), EaFeedbackDevice (+kind), ActuatorHeaterSupply (+CU_CIRCUIT),
   CableGlandHolesSet (+kind), AllowedControlUnitOption (+cu_power_supply),
   слоты (LOCAL_CONTROL, CMD, SETPOINT, INDICATOR, TURN_COUNTER, THERMAL_SENSOR;
   HEATER_ACTUATOR деактивировать), новые сигналы (FB_STOP, FB_LOCAL_REMOTE,
   FB_SELECTOR_POSITION, FB_PHASE_LOSS, FB_OVERHEAT_* уже есть; CMD_REMOTE),
   валидация device на none-строке; миграции; seed-каталог (идемпотентный).
2. **Заливщик AOX (13.2):** std→is_default; пары OPEN+CLOSE с bundle;
   OverHeat 21/23, 55/57 → THERMAL_SENSOR (device=THERMAL_RELAY); heater
   83–88 → HEATER_CONTROL_UNIT (separate wire→SEPARATE_LINE, from actuator→
   CU_CIRCUIT); «Customizable»→opt; «No heater…» — строки нет; 73–76 больше
   не матрица (обогрев привода — в температурные строки data-миграцией);
   перезаливка delete-first.
3. **Экспорт-каркас + импорт (13.3):** полная таблица: все модели × пары
   БУ×напряжение (из матрицы серии/бренда + `AllowedControlUnitOption` — новая
   связка «разрешённые БУ×напряжение», значения в неё перенесены из старой
   схемы ОДНОКРАТНОЙ data-миграцией 0058) × режимы × слоты × опции слота
   (каталог `EaSlotOption`); пустые ячейки пропускаются импортом; std/opt —
   upsert, na — запрет; device по коду; новые пары (380/24DC) — из заполненного
   Excel.
4. **Резолвер (13.4):** THERMAL_SENSOR/HEATER_CONTROL_UNIT/новые слоты —
   обычная логика; HEATER_CONTROL_UNIT скрыт для kind=NONE.
5. **Ext-код (14):** ext_encoding на строках/опциях; ext_encoding_template
   серий; TemplateFieldMapping ext_code_path; сервис ea_ext_code.py
   (decode_ext_code, coding_rules).
6. **Тесты:** пары+bundle, OverHeat+device, heater по БУ, каркас полноты,
   round-trip импорта, is_default, decode/build round-trip; 23→~35 тестов;
   `manage.py check`; `makemigrations --check`; сверка выгрузки AR21E с AOX.
7. **Фаза 7 (после заливки):** удаление старого (AllowedSignalProfileOption,
   ControlUnitWiring, ControlUnitSignalProfile, через-опции переключателей;
   encoding БУ переносится в матрицу; AllowedControlUnitOption/
   AllowedTurnCounterOption — после переноса encoding).
8. **Фаза 8:** генератор wiring-диаграмм (SVG).

Критерий готовности: выгрузка AR21E содержит все 15 моделей; у 007 — пары
Откр/Закр с bundle, OverHeat с device, is_default у std; у остальных — пустые
ячейки; ext-код собирается/расшифровывается без «плавающих» позиций; для каждой
опции есть запись каталога + placeholder + smoke ru/en/cn.

## 11. Открытые мелочи

- Коды напряжений в ext: `3`/`2` (кратко) — принято; при желании заменить на
  380/24 (правила кодирования это переживут — коды из записей PowerSupplies).
- Коды механических счётчиков — из params.TurnCounterOption (encoding) при
  заливке.
- Позиционер (AOX 89–92) — как БУ kind=POSITIONER; матрица позиционера —
  после подтверждения семантики.
- S2/стартер 380В — позиции ext готовы; данные — по мере появления.
