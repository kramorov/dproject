# Отчёт: сигналы управления/обратной связи ЭП (AOX) vs через-опции приложения

Источник: `available-options-ea-AOX.xlsx` (лист «Лист1», 55 строк × 96 колонок).
Дата анализа: 2026-10-16.

---

## 1. Что описывает таблица

Таблица — матрица «модель ЭП × доступная опция». Строки — модели производителя
(AR01E… = серия **R**, AR11E… = серия **Q**, AR21E… = серия **M**). Колонки — сигналы
и опции, сгруппированные по четырём блокам:

| Блок | Колонки | Смысл |
|---|---|---|
| **Feed back** (обратная связь) | 3–60 | Выходные сигналы от привода |
| **Control** (управление) | 61–88 | Входные команды приводу |
| **Positioner option** | 89–92 | Опциональная плата позиционера |
| **Other options** | 93–96 | Режим S2, обогрев −60°, встроенный пускатель 380В, примечания |

Маркеры ячеек: `√` — есть, `×` — нет, `/` — не применимо (нет такого типа БУ/режима),
`st` — стандарт, `opt?` — опция, `no` — нет, текст — условия/примечания.

Ключевая ось разбиения **Feed back** и **Control** — тип блока управления:

- **Basic (No INT)** — без интегратора (простой on-off или modulating без ИБУ).
- **INT** — с интегратором (интеллектуальный БУ), три подтипа: **ICU / SRCU / LCU**.

Вторая ось — **режим**: `on-off` (двухпозиционное) и `modulating` (модулирующее).

---

## 2. Декодирование колонок (точная раскладка)

### 2.1 Feed back (кол. 3–60)

**Basic (No INT)** — каждая опция разбита на 2 колонки: `on-off` / `modulating`.

| Колонки | Сигнал | Подопция | Статус (row5) |
|---|---|---|---|
| 3–4 | 4-20 мА Active — интегрированная аналоговая ОС положения | активная | no |
| 5–6 | 4-20 мА Passive — интегрированная аналоговая ОС положения | пассивная | no |
| 7–8 | End switches (концевые) | SPDT | st |
| 9–10 | End switches | DPDT | opt? |
| 11–12 | Way/middle switches (путевые) | SPDT | opt? |
| 13–14 | Way/middle switches | DPDT | opt? |
| 15–16 | Torque switches (моментные) | SPDT | st |
| 17–18 | Torque switches | DPDT | opt? |
| 19–20 | Аналоговый сигнал о положении (позиционный трансмиттер) | 4-20 мА Passive | opt? |
| 21–22 | OverHeat (тепловая защита) | SPST | opt? |
| 23–24 | OverHeat | SPDT | opt? |

**INT** — каждая опция разбита на 3 колонки: `ICU` / `SRCU` / `LCU`.

| Колонки | Сигнал | Подопция | Статус (row5) |
|---|---|---|---|
| 25–27 | 4-20 мА Active — интегрированная аналоговая ОС положения | ICU/SRCU/LCU | opt? |
| 28–30 | 4-20 мА Passive — интегрированная аналоговая ОС положения | ICU/SRCU/LCU | st |
| 31–33 | End switches SPDT | ICU/SRCU/LCU | st |
| 34–36 | End switches DPDT | ICU/SRCU/LCU | opt? |
| 37–39 | Way switches SPDT | ICU/SRCU/LCU | opt? |
| 40–42 | Way switches DPDT | ICU/SRCU/LCU | opt? |
| 43–45 | Torque switches SPDT | ICU/SRCU/LCU | st |
| 46–48 | Torque switches DPDT | ICU/SRCU/LCU | opt? |
| 49–51 | Аналоговый сигнал о положении (позиционный трансмиттер) | 4-20 мА Passive — ICU/SRCU/LCU | opt? |
| 52–54 | OverHeat SPST | ICU/SRCU/LCU | opt? |
| 55–57 | OverHeat SPDT | ICU/SRCU/LCU | opt? |
| 58–60 | Mechanical **and digital** position indicator | ICU/SRCU/LCU | opt? |

### 2.2 Control (кол. 61–88)

| Колонки | Сигнал | Разбиение |
|---|---|---|
| 61–62 | Open/Close/Stop signals | 220AC (61–62) |
| 63–64 | Open/Close/Stop signals | 24DC (63–64) |
| 65–66 | Remote Control signal | 220AC (65–66) — `st` |
| 67–68 | Remote Control signal | 24DC (67–68) — `opt?` |
| 69–70 | LOCK (блокировка) | on-off / modulating |
| 71–72 | Manual override (ручное дублирование) | on-off / modulating |
| 73–74 | Heater power supply (питание обогрева) | separate wire — on-off/modulating |
| 75–76 | Heater power supply | from actuator — on-off/modulating |
| 77–79 | 4-20 мА Active (командный вход) | ICU/SRCU/LCU |
| 80–82 | 4-20 мА Passive (командный вход) | ICU/SRCU/LCU |
| 83–85 | Heater power supply (separate wire) | ICU/SRCU/LCU |
| 86–88 | Heater power supply (from actuator) | ICU/SRCU/LCU |

### 2.3 Positioner option (кол. 89–92)

| Колонка | Опция |
|---|---|
| 89 | Open/Close/Stop signals — 220AC |
| 90 | Open/Close/Stop signals — 24DC |
| 91 | 4-20 мА Active |
| 92 | 4-20 мА Passive |

### 2.4 Other options (кол. 93–96)

| Колонка | Опция | Примечание |
|---|---|---|
| 93 | S2 — 30 min | стандарт S2-15min, опционально |
| 94 | Heater minus 60 (обогрев −60°, для INT-модуля, отдельно от основного питания) | стандарт — отдельный провод |
| 95 | built-in starter (встроенный пускатель) | для 380В: все кроме стандартного on-off идут с пускателем |
| 96 | Примечания | R003 не имеет ICU; AOX-R не имеет SRCU и LCU |

---

## 3. Сравнение с моделями приложения «Электроприводы»

### 3.1 Что уже смоделировано как through-опции (паттерн «через»)

`reference-опция (params) + encoding + is_default + sorting_order`, привязка к серии/модели:

| Excel-сигнал | Модель приложения | Reference | Ключ |
|---|---|---|---|
| End switches SPDT/DPDT | `ElectricEndSwitchesOption` | `params.SwitchesParameters` | model_line_item |
| Way/middle switches SPDT/DPDT | `ElectricWaySwitchesOption` | `params.SwitchesParameters` | model_line_item |
| Torque switches SPDT/DPDT | `ElectricTorqueSwitchesOption` | `params.SwitchesParameters` | model_line_item |
| Mech. position indicator | `ElectricMechanicalIndicatorOption` | `params.MechanicalIndicatorOption` | model_line |
| БУ (Basic/INT/ICU/SRCU/LCU) | `ElectricControlUnitOption` (+ `AllowedControlUnitOption` для encoding серии) | `params.ControlUnitInstalledOption` | power_supply_option (т.е. БУ×напряжение) |
| Напряжение (220AC/24DC/380VAC) | `ElectricPowerSupplyOption` | `params.PowerSupplies` | model_line_item |
| Питание обогрева (separate/from actuator) | `ControlUnitWiring.heater_supply` | `params.ActuatorHeaterSupply` | **через схему**, не через-опция |

### 3.2 Что сейчас моделируется через «профиль сигналов + схема»

`ControlUnitWiring` = (БУ + напряжение + `signal_profile` + изображение схемы).
Доступные сигналы задаются `ControlUnitSignalProfile.entries`:
`SignalRole → SensorComponent` (выходные) или `SignalRole → InputSignalSpec` (входные).

Сюда сейчас попадают:

| Excel-сигнал | Текущая модель | Через-опция? |
|---|---|---|
| 4-20 мА Active/Passive (ОС) | `SignalRole` + `SensorComponent` (трансмиттер) | ✗ только в профиле |
| OverHeat SPST/SPDT | `SignalRole` + `SensorComponent` | ✗ только в профиле |
| Open/Close/Stop 220AC/24DC | `SignalRole` + `InputSignalSpec` | ✗ только в профиле |
| Remote Control 220AC/24DC | `SignalRole` + `InputSignalSpec` | ✗ только в профиле |
| LOCK / Manual override | `SignalRole` + `InputSignalSpec` | ✗ только в профиле |
| End/Way/Torque switches | дублируются: и через-опция `SwitchesParameters`, и роль в профиле | **дублирование** |

---

## 4. Взаимосвязи сигналов с типом БУ, напряжением, режимом, серией

### 4.1 Тип блока управления

- Два непересекающихся набора колонок: **Basic (No INT)** и **INT**.
- **INT** делится на ICU / SRCU / LCU — каждый сигнал тиражируется на 3 колонки.
- **AOX-R**: нет SRCU и LCU (INT = только ICU); **R003** — нет ICU вообще.
- **AOX-M**: нет modulating-типа → все modulating-колонки `/` (в т.ч. командный 4-20 мА — только on-off).
- Командный вход 4-20 мА (кол. 77–82) существует только в **INT** (ICU/SRCU/LCU) — в Basic его нет.

### 4.2 Напряжение питания

- **Open/Close/Stop** и **Remote Control** — это команды, приходящие напряжением **220AC** или **24DC** (напряжение цепи управления). 220AC Remote = стандарт, 24DC Remote = опция.
- **380В**: встроенный пускатель (кроме стандартного on-off); тепловая защита уже заведена в цепь управления (вывод наружу — кастомизация).
- **24DC**: стандартно **без** выведенного теплового реле (OverHeat не выводится).
- **Обогрев**: у DC24V/AC380V on-off типов Q-005/008/010 обогрева нет; у modulating — есть.

### 4.3 Режим (on-off vs modulating)

- Modulating-продукты **стандартно** идут с аналоговой ОС (4-20 мА) → средний (путевой) выключатель не нужен; при необходимости добавляется доп. средний сигнал ОС.
- LOCK / Manual override / Heater — разбиты на on-off/modulating (разные допустимые наборы).

### 4.4 Серия (R / Q / M)

| Признак | R | Q | M |
|---|---|---|---|
| Torque switch (перегрузка) | ✗ нет | ✗ у 005/008/010 | есть (SPDT) |
| Modulating | есть | есть | **нет** |
| SRCU / LCU | **нет** | есть | есть |
| 4-20 Active/Passive | есть (R003 нет ICU) | есть | **нет** |
| Средний выключатель | AC220V трёхпозиц. управление / ОС | аналогично, через ОС | — |

### 4.5 Ограничение по клеммам (кол. 54, note)

> Для серий **Q** и **M**: из-за лимита клемм нельзя одновременно выбрать
> **DPDT-выключатель + сегментный (средний) выключатель + центральный выключатель + моментный выключатель**.

Это готовое правило совместимости опций (аналог `visible_when`/«конфликт опций» в конфигураторе).

---

## 5. Выводы и рекомендация

1. **End/Way/Torque switches уже переведены на through-опции** (`SwitchesParameters`) — это ровно тот паттерн, который предлагается распространить на остальные сигналы. Дублирование с сигнальными ролями нужно устранить.

2. **4-20 мА, OverHeat, командные сигналы (Open/Close/Stop, Remote, LOCK, Manual override) и обогрев** сейчас «зашиты» в `ControlUnitSignalProfile` и доступны только как часть выбранной схемы `ControlUnitWiring`. Их нельзя выбрать независимо в конфигураторе — в отличие от концевых/путевых/моментных.

3. **Предлагаемое направление (по вашему замыслу):**
   - Каждый сигнал/опция — отдельная through-модель (как `ElectricEndSwitchesOption`), с `encoding/is_default/sorting_order`, привязанная к паре **БУ×напряжение** (`ElectricControlUnitOption`) или к `model_line_item`.
   - **SignalRole остаётся как метаданные/гибкий слой ролей** (OPEN_LIMIT, TORQUE_OPEN, POS_4_20MA, ALARM…), но перестаёт быть механизмом доступности: доступность задаётся через-опциями, а роли — только теги/группировка для отображения и генерации описания.
   - Зависимости «только для INT», «только 220AC/24DC», «нет для серии R», «нет torque у Q-005/008/010», «конфликт клемм Q/M» — оформляются как правила доступности/конфликтов на уровне through-опций (по аналогии с существующим `parent_field`/`visible_when`).

4. **Колонки 19–20 и 49–51 («4-20 мА Passive»)** — это **возможность получить аналоговый сигнал о положении** (отдельный позиционный трансмиттер/аналоговый выход, добавляемый поверх механических переключателей), а не дубль кол. 5–6 / 28–30. Последние — интегрированная аналоговая ОС положения в БУ.

5. **Позиционер (кол. 89–92)** — это отдельное оборудование (позиционер), у него свои через-опции в `pa_controls` (`POSI-*` профили/датчики). В рамках ЭП его стоит трактовать как отдельную опцию-ссылку, не смешивать с сигналами БУ.

---

---

## 6. Предложение по модели (единый список опций + матрица БУ×напряжение)

Согласен с базовой идеей: **один справочник всех значений опций** + **матрица
«тип БУ × напряжение → доступные опции», привязанная к бренду (производителю)** +
**сужение до серии/модели через наследование с переопределением** (не прописывать на
каждую модель). Позиционер трактуем как ещё один «блок управления» — тогда все колонки
таблицы (включая 89–92) ложатся в ту же матрицу.

### 6.1 Три уровня

**Уровень 1 — единый справочник значений опций (`EaOptionDefinition`)**
Одна строка = одно выбираемое значение опции (по всем БУ и напряжениям сразу):

```python
class EaOptionDefinition(LocalizedDictFieldsMixin, CopyMixin):
    code      # FB_END_SPDT, FB_ANALOG_ACTIVE, FB_POS_TX_PASSIVE, CMD_OCS_220AC,
              # CMD_REMOTE_24DC, HEAT_SEPARATE, DUTY_S2_30, STARTER_380V, ...
    name
    category  # feedback_switch | feedback_analog | command | heater |
              # duty | starter | indicator | counter | safety
    variant   # SPDT/DPDT/SPST/ACTIVE/PASSIVE/AC220/DC24/SEPARATE/FROM_ACTUATOR/...
    # nullable-ссылки на технические reference-объекты (заполняется одна по category):
    switch_param         FK params.SwitchesParameters, null=True
    heater_supply        FK params.ActuatorHeaterSupply, null=True
    input_signal         FK params.InputSignalSpec, null=True
    sensor               FK pa_controls.SensorComponent, null=True
    mechanical_indicator FK params.MechanicalIndicatorOption, null=True
    turn_counter         FK params.TurnCounterOption, null=True
    safety_position      FK params.SafetyPositionOption, null=True
    description, sorting_order, is_active
```

Reference-справочники (`SwitchesParameters`, `ActuatorHeaterSupply`, `InputSignalSpec`,
`SensorComponent` …) остаются источником техданных; `EaOptionDefinition` — тонкая
обёртка-каталог, дающая единый список и кодировку.

**Уровень 2 — матрица «БУ × напряжение → опция», привязана к бренду (сужение до серии/модели)**

БУ и их наборы опций различаются у производителей (ICU/SRCU/LCU — номенклатура AOX),
и внутри одного производителя серии/модели отличаются. Поэтому матрица **НЕ глобальная** —
она привязана к бренду, а серия и модель наследуют её с переопределением.

```python
class ControlUnitOptionMatrixEntry:
    # скоуп (уровень принадлежности строки, по убыванию специфичности):
    brand            FK producers.Brands, null=True, blank=True   # матрица производителя
    model_line       FK ElectricActuatorModelLine, null=True, blank=True
    model_line_item  FK ElectricActuatorModelLineItem, null=True, blank=True

    control_unit   FK params.ControlUnitInstalledOption   # Basic/ICU/SRCU/LCU/Positioner
    power_supply   FK params.PowerSupplies                # 220AC/24DC/380VAC
    option         FK EaOptionDefinition

    availability   # 'std' | 'opt' | 'na'   ('na' на более специфичном уровне ЗАПРЕЩАЕТ унаследованную опцию)
    modes          # on_off | modulating | both
    encoding       # код для артикула
    is_default
    sorting_order
    conflicts      M2M self   # «нельзя DPDT + средний + моментный одновременно» (Q/M)
```

**Правило резолвинга (наследование + override):**

Для модели берём строки по специфичности и «перекрываем» менее специфичные:
`model_line_item` → `model_line` → `brand` (матрица производителя = файл AOX целиком).
Строка `availability='na'` на более специфичном уровне явно отключает опцию, унаследованную
с бренда (напр. бренд говорит «моментные есть», серия Q-005/008/010 — «na»).

### 6.2 Как это решает текущие проблемы

1. **Единый список** вместо трёх разрозненных механизмов (through-опции переключателей,
   сигнальный профиль схемы, отдельный обогрев) — всё становится строками `EaOptionDefinition`.
2. **БУ×напряжение** — ось матрицы совпадает с осями Excel (Basic/INT и 220AC/24DC/380VAC).
   Позиционер добавляется как ещё один БУ — колонки 89–92 описываются теми же строками.
3. **Режим** (on-off/modulating) — поле `modes` на строке матрицы, а не отдельные колонки.
4. **Конфликты** (лимит клемм Q/M) — `conflicts` M2M на строке.
5. **Привязка к бренду + сужение до модели** — строки матрицы живут на трёх уровнях
   (`brand` → `model_line` → `model_line_item`) и перекрываются по специфичности.
   Исключения (R без SRCU/LCU и моментных, Q-005/008/010 без моментных, M без
   modulating/4-20) закрываются точечными строками `na` на уровне серии, не дублируя
   всю матрицу на каждую модель.

### 6.3 Что происходит с существующими моделями

- `ElectricEndSwitchesOption` / `ElectricWaySwitchesOption` / `ElectricTorqueSwitchesOption` —
  сворачиваются в `EaOptionDefinition` (категория feedback_switch). Данные переносятся миграцией.
- `ControlUnitSignalProfile` — перестаёт быть механизмом доступности; либо удаляется, либо
  остаётся как **пресет** («Стандартные механические SPDT»), который разворачивается в строки
  матрицы (удобно при массовом заполнении).
- `SignalRole` — остаётся как метаданные/роли для отображения и генерации описания
  (OPEN_LIMIT, POS_4_20MA, ALARM…), но доступность им больше не задаётся.
- `ControlUnitWiring` — остаётся только как «(БУ×напряжение) → изображение схемы»;
  измерение `signal_profile` из него убирается (схема одна на пару, сигналы — в матрице).
- `ElectricControlUnitOption` / `ElectricPowerSupplyOption` — остаются как декларация
  «какие БУ доступны при каком напряжении для конкретной модели»; матрица отвечает на
  «какие опции у этой пары». Резолвинг в конфигураторе: модель → серия → бренд →
  напряжение → БУ → матрица(brand→серия→модель) → опции.

### 6.4 Открытые вопросы / развилки

1. **GenericFK vs nullable typed FK** в `EaOptionDefinition`. Рекомендую nullable typed FK
   (валидация строже, без GenericForeignKey), но если число категорий будет расти — можно
   перейти на content_type+object_id.
2. **Позиционер как БУ** — согласен, но физически это отдельное устройство с собственной
   базой в `pa_controls` (`POSI-*` датчики/профили). Нужно решить: это отдельная запись
   `ControlUnitInstalledOption` (тогда сигналы позиционера в общей матрице) или отдельный
   equipment_type с переиспользованием той же схемы матрицы.
3. **Скоуп справочника БУ.** `params.ControlUnitInstalledOption` сейчас глобальный; коды
   ICU/SRCU/LCU фактически принадлежат конкретному производителю. Варианты: оставить
   глобальным (уникальные коды на бренд) или добавить опциональный FK на бренд.
4. **`modes` как поле строки vs отдельная ось.** Поле проще; ось (БУ×напряжение×режим)
   точнее, но раздувает матрицу. Предлагаю начать с поля.
5. **Что есть «опция» vs «характеристика».** S2-режим и встроенный пускатель 380В — это,
   скорее, характеристики модели, а не выбираемые опции; их можно держать в матрице как
   `availability='std'` с незаблокированным выбором, либо вынести в поля модели.

---

## 7. Физическая модель (датчики → маршрутизация → БУ → сигналы)

Раздел 6 (плоская матрица «БУ×напряжение×опция») страдает тем, что при правках одного БУ
приходится трогать все строки матрицы, а на модель по сути нужна своя копия. Ниже —
композиционная модель по физическому принципу: матрицу доступности **не храним, а вычисляем**.

### 7.1 Три сущности (как предложено)

1. **Датчики** — физические источники (концевые/путевые/моментные/температура/счётчик).
2. **Сигналы управления** — входы (команды приводу).
3. **Сигналы обратной связи** — выходы (от привода наружу).

Разделение «управление / ОС» уже есть в `params.SignalRole.direction` (input/output).
Недостаёт явного «датчик» (физика + технология) и маршрутизации.

### 7.2 Каталоги (по одному на сущность)

**Датчик** — роль + технология + параметры:

```python
class EaSensor:
    role          # END | WAY | TORQUE | TEMP | TURN_COUNTER | POSITION
    technology    # MECHANICAL | ELECTRONIC
    contact_form  # SPDT/DPDT/SPST/NONE — для MECHANICAL
    signal_type   # 4-20mA / NAMUR / PNP / dry — для ELECTRONIC
    turns         # кол-во оборотов (для TURN_COUNTER mechanical); null иначе
    sensor_component  FK pa_controls.SensorComponent, null=True  # техданные
```

**Сигнал** — `SignalRole` (уже есть), direction:

- управление (input): `OPEN_CLOSE_STOP_220AC`, `OPEN_CLOSE_STOP_24DC`, `REMOTE_220AC`,
  `REMOTE_24DC`, `LOCK`, `MANUAL_OVERRIDE`, `CMD_4_20MA`;
- ОС (output): `POS_4_20MA`, `END_OPEN/END_CLOSE`, `WAY_*`, `TORQUE_*`, `OVERHEAT`,
  `POSITION_INDICATOR`, `TURN_COUNTER_SIGNAL`.

**Блок управления** — включая «без БУ» как отдельный БУ:

```python
class EaControlUnit:                 # = params.ControlUnitInstalledOption + поля
    kind     # NONE | BASIC | INTEGRATED | POSITIONER
    accepts  # M2M SignalRole(input)  — какие команды принимает
    emits    # M2M SignalRole(output) — какие сигналы ОС способен выдать
```

### 7.3 Композиция на модели (минимум, не матрица)

```python
class ModelSensor:                   # какие датчики стоят на модели
    model_line_item FK
    sensor          FK EaSensor
    is_default / is_optional / encoding / sorting_order

class ModelSignalRoute:              # куда идёт сигнал датчика
    model_sensor FK
    route    # DIRECT_FEEDBACK | TO_CONTROL_UNIT | BOTH
```

(Какие БУ допустимы при каком напряжении на модели — уже есть:
`ElectricControlUnitOption` + `ElectricPowerSupplyOption`.)

### 7.4 Доступность вычисляется (не хранится)

- **ОС** = сигналы датчиков с route `DIRECT/BOTH` ∪ (`emits` выбранного БУ для датчиков с route `TO_CU/BOTH`).
- **Управление** = `accepts` выбранного БУ, фильтр по напряжению (220AC/24DC) и режиму (on-off/modulating).
- **«Без БУ»** = `EaControlUnit(kind=NONE)`: `emits=∅`, `accepts=∅` → ОС только из DIRECT-датчиков.
- **Конфликт клемм (Q/M)** = правило на БУ/маршрутизации (запрет одновременных DPDT+средний+моментный).

### 7.5 Почему это снимает проблему редактирования

- Изменили возможности БУ (`emits/accepts`) — в **одном** месте, все модели обновились.
- Сменили технологию датчика (мех→электронный) — в **одном** справочнике, модели наследуют.
- Различия моделей — только «какие датчики установлены» + «какие БУ/напряжение допустимы»,
  а не полная матрица опций на каждую модель.

### 7.6 Счётчик оборотов (AOX-M)

`role=TURN_COUNTER` как датчик: `technology` (mech/electronic), `turns` (мех. на N оборотов).
«Механический вдобавок к электронному как опция» = два `ModelSensor` с role=TURN_COUNTER:
один electronic (по умолчанию), один mechanical (опция).

### 7.7 Маппинг на таблицу AOX

| Excel | Модель |
|---|---|
| End/Way/Torque/Temp switches | `EaSensor` role END/WAY/TORQUE/TEMP, MECHANICAL, contact_form SPDT/DPDT/SPST |
| 4-20 мА ОС (3–6 / 25–30) | `EaSensor` role POSITION, ELECTRONIC, signal_type 4-20mA |
| Позиционный трансмиттер (19–20 / 49–51) | `EaSensor` role POSITION (transmitter), route DIRECT |
| OverHeat SPST/SPDT | `EaSensor` role TEMP, MECHANICAL |
| Open/Close/Stop, Remote 220AC/24DC | `SignalRole` input → `EaControlUnit.accepts` |
| LOCK / Manual override | `SignalRole` input → accepts |
| Командный 4-20 мА (77–82) | `SignalRole` CMD_4_20MA → accepts (только INT) |
| Обогрев separate/from actuator | параметр БУ×напряжение (не датчик) |
| S2 / стартер 380В | характеристики модели/БУ |
| Positioner (89–92) | `EaControlUnit(kind=POSITIONER)` |
| Mech.+digital indicator | опция indicator (датчик/индикатор) |

### 7.8 Открытые вопросы

1. Вести физическую базу датчиков через `pa_controls.SensorComponent` (она уже есть) или
   отдельный EA-справочник `EaSensor` со ссылкой на него.
2. `technology` — поле на `SensorComponent` или отдельный EA-классификатор поверх.
3. Оставить ли `ControlUnitSignalProfile` как **пресет маршрутизации** (быстрый способ задать
   типовой набор датчиков+маршрутов для БУ) — тогда профиль не источник истины, а шаблон.
4. Напряжение входных команд: поле `voltage` на `SignalRole` (input) или отдельные роли
   (`OPEN_CLOSE_STOP_220AC` vs `..._24DC`).

---

## 8. Уточнение: сигналы вместо физических датчиков (ЭП-специфично)

Раздел 7 предлагал физическую модель датчиков (`EaSensor` + `ModelSensor` +
маршрутизация) и ссылку на `pa_controls.SensorComponent`. Уточняем:

- **Не переиспользуем** `pa_controls.SensorComponent` — это датчики БКВ/позиционеров,
  у них своя детализация (variety, contact_form, Ex, конкретные модели). Для ЭП связи нет.
- **Убираем физическую модель датчиков.** По датчикам ЭП данных нет, и потребителю
  физика не важна.
- Для ЭП моделируем **сигналы** — то, что потребитель видит на клеммах:
  форма сигнала + максимальное напряжение + максимальный ток.

### 8.1 `EaSignal` — каталог сигналов ЭП (управление + обратная связь)

```python
class EaSignal:
    direction    # INPUT (управление) | OUTPUT (обратная связь)
    role         # смысловая роль: END_OPEN, END_CLOSE, WAY_OPEN, TORQUE_OPEN,
                 # TORQUE_CLOSE, POS_4_20MA, OVERHEAT, TURN_COUNTER,
                 # CMD_OCS_220AC, CMD_OCS_24DC, CMD_REMOTE_220AC, CMD_REMOTE_24DC,
                 # CMD_LOCK, CMD_MANUAL_OVERRIDE, CMD_4_20MA
    form         # форма: DRY_SPST | DRY_SPDT | DRY_DPDT |
                 #        AN_4_20_ACTIVE | AN_4_20_PASSIVE |
                 #        DISC_220VAC | DISC_24VDC | NAMUR | PNP
    max_voltage  # макс. коммутируемое напряжение, В (напр. 250 VAC / 30 VDC)
    max_current  # макс. коммутируемый ток, А (напр. 5 A / 0.5 A)
    name, code, description, is_active, sorting_order
```

«Технология» (мех/электронный) из раздела 7 здесь не нужна отдельным полем — она
выражается формой: механический → сухой контакт (DRY_SPDT/DPDT, высокие V/A),
электронный → аналог/NAMUR/PNP (низкие V/A).

### 8.2 `EaControlUnit` — блок управления (включая «без БУ»)

```python
class EaControlUnit:
    kind     # NONE | BASIC | INTEGRATED | POSITIONER
    accepts  # M2M EaSignal(direction=INPUT)  — команды, которые принимает
    emits    # M2M EaSignal(direction=OUTPUT) — сигналы ОС, которые выдаёт
```

### 8.3 `EaSignalMatrixEntry` — доступность (наследуемая матрица)

```python
class EaSignalMatrixEntry:
    brand / model_line / model_line_item   # скоуп (наследование + override)
    control_unit   FK EaControlUnit
    power_supply   FK params.PowerSupplies
    mode           # on_off | modulating | both
    signal         FK EaSignal
    availability   # std | opt | na
    encoding, is_default, sorting_order, conflicts(M2M self)
```

### 8.4 Итог изменений относительно раздела 7

| Было (раздел 7) | Стало (раздел 8) |
|---|---|
| `EaSensor` + FK на `pa_controls.SensorComponent` | `EaSignal` (форма + V + A), без ссылки на БКВ |
| `ModelSensor` (какие датчики стоят) | строки матрицы `EaSignalMatrixEntry` |
| `ModelSignalRoute` (direct/to_CU) | доступность в матрице (raw = без БУ; processed = через БУ) |
| поле `technology` | поле `form` |

### 8.5 Открытые вопросы

1. **Источник V/A.** В таблице AOX значений напряжения/тока сигналов нет (там только
   формы и примечания). Значит, max_voltage/max_current придётся брать из паспортов/
   спецификаций производителей — это отдельный ввод данных, которого пока нет.
2. **`role`** — переиспользовать `params.SignalRole` (уже есть, с direction) или завести
   отдельный EA-справочник ролей, чтобы не смешивать с БКВ/позиционерами.
3. **Список `form`** — закрытый choices или свободный справочник (чтобы добавлять формы
   без миграций).

---

## 9. Раздельные модели: управление / обратная связь / протоколы

Сигналы управления и ОС отличаются физическим смыслом полей V/A, а HART/Modbus —
двунаправленные цифровые протоколы, которые не ложатся ни во «вход», ни в «выход».
Поэтому делим на три каталога:

### 9.1 `EaControlSignal` — входные команды (однонаправленные)

```python
class EaControlSignal:
    role      # CMD_OCS_220AC, CMD_OCS_24DC, CMD_REMOTE_220AC, CMD_REMOTE_24DC,
              # CMD_LOCK, CMD_MANUAL_OVERRIDE, CMD_4_20MA
    category  # discrete | analog
    form      # DISC_220VAC | DISC_24VDC | AN_4_20_ACTIVE | AN_4_20_PASSIVE
    voltage   # входное напряжение (для discrete), В
    current   # потребляемый ток цепи, мА
    name, code, description, is_active, sorting_order
```

Здесь V/A — это **параметры входа БУ** (какое напряжение/ток он ожидает на клемме).

### 9.2 `EaFeedbackSignal` — выходные сигналы ОС (однонаправленные)

```python
class EaFeedbackSignal:
    role         # END_OPEN, END_CLOSE, WAY_OPEN, TORQUE_OPEN, TORQUE_CLOSE,
                 # POS_4_20MA, OVERHEAT, TURN_COUNTER, ALARM, READY
    category     # contact | analog
    form         # DRY_SPST | DRY_SPDT | DRY_DPDT | AN_4_20_ACTIVE | AN_4_20_PASSIVE
    max_voltage  # макс. коммутируемое напряжение, В (для contacts)
    max_current  # макс. коммутируемый ток, А (для contacts)
    name, code, description, is_active, sorting_order
```

Здесь V/A — это **коммутируемая способность контакта** (какую нагрузку он может замкнуть),
т.е. смысл полей другой, чем у управляющего сигнала — поэтому и отдельная модель.

### 9.3 `EaCommProtocol` — цифровые протоколы (двунаправленные)

```python
class EaCommProtocol:
    code / name   # HART | MODBUS_RTU | MODBUS_TCP | PROFIBUS | ...
    transport     # current_loop (HART) | rs485 | ethernet
    description
```

HART и Modbus — это **не клемма, а способ общения БУ**: один канал несёт и команды,
и ОС. Поэтому протоколы висят на БУ, а не на сигналах:

### 9.4 `EaControlUnit` — обновлённый

```python
class EaControlUnit:
    kind       # NONE | BASIC | INTEGRATED | POSITIONER
    accepts    # M2M EaControlSignal   — дискретные/аналоговые команды
    emits      # M2M EaFeedbackSignal  — контакты / аналоговая ОС
    protocols  # M2M EaCommProtocol    — HART / Modbus / PROFIBUS
```

### 9.5 Матрица доступности (без изменений по идее)

`EaSignalMatrixEntry` из разд. 8.3 остаётся, но ссылается на три каталога через
поле-union (GenericFK на `EaControlSignal`/`EaFeedbackSignal`/`EaCommProtocol`)
или три nullable FK — один заполняется по типу строки.

### 9.6 Открытые вопросы

1. **HART поверх 4-20 мА.** HART едет по аналоговой петле 4-20 мА. Считать его
   протоколом БУ (как выше) или атрибутом конкретного сигнала `AN_4_20_*` (`hart=True`)?
2. **Modbus RTU vs TCP** — одна запись с полем `transport` или разные записи справочника.
3. **GenericFK vs три nullable FK** в матрице доступности.

*Статус: разд. 8 развит в разд. 9 — три каталога сигналов вместо одного. Правок кода нет.*

---

## 10. Сравнение с архитектурой сигналов AUMA и ROTORK

Дата: 2026-10-18. Источник — каталоги производителей из E:\work\Контроль\
Проект_приводы\Конкуренты_каталоги: AUMA «Каталог_технический_AUMA_SA.pdf»
(Y004.388/003, 268 стр., SA/SAR .2 + технические данные AC 01.2), «РАСШИФРОВКА СХЕМ
АУМА.pdf», HART_AUMA.pdf, FieldBus_AUMA.pdf, ba_asr0_vmmc1_ru.pdf; Rotork «PUB002-197-00
IQ3 Pro Range Brochure» (52 стр.). Факты из этих документов помечены «сверено»;
остальное — пометка «проверить».

### 10.1 Общий принцип у обоих производителей

Механика привода и блок управления — отдельные сущности, сигналы принадлежат БУ:

- **AUMA**: механика SA/SAR (многооборотные), SQ/SQR (неполноповоротные) + блок
  управления: **AUMA NORM** (простая клеммная колодка, только контакты) или
  **AUMATIC AC.2** (интеллектуальный БУ с дисплеем, шинами, программированием).
- **ROTORK**: IQ3/IQT3 — БУ интегральный, неинтрузивная настройка (без вскрытия
  корпуса), дисплей без батареи (суперконденсатор).

Это совпадает с осью `EaControlUnit.kind` (NONE/BASIC/INTEGRATED): AUMA NORM ≈ BASIC,
AUMATIC ≈ INTEGRATED.

### 10.2 Номенклатура сигналов AUMA (сверено с каталогом SA/SAR, Y004.388)

Обратная связь (термины AUMA):

- **WSR** (Wegschalter) — концевые выключатели пути; в схемах также LSC/LSO.
- **WOEL** — концевые без отсечки нагрузки (только сигнализация).
- **DSR** (Drehmomentschalter) — моментные выключатели; в схемах также TSC/TSO.
- **DOEL** — моментные без отсечки нагрузки.
- **WDR/WDL** — промежуточные выключатели «DUO» (2 настраиваемых промежуточных
  положения) — аналог «средних выключателей» AOX.
- Термозащита: термовыключатель 140 °C (NC) или PTC-термистор (код «TSR» в каталоге
  не используется).
- **RWG 4020** — потенциометрический позиционный трансмиттер: на основе значения
  потенциометра **генерирует токовый сигнал 0/4–20 мА** в 2/3/4-проводных системах,
  разъём XK. В коде заказа: E = RWG (4-wire), A = «precision potentiometer»
  (голый потенциометр, сопротивление наружу — без преобразователя).
- **EWG 01.1** — бесконтактный позиционный трансмиттер (датчики Холла), 0/4–20 мА,
  2-проводный (пассивный) или 3/4-проводный (активный).
- **MWG** — магнитный датчик пределов и момента (non-intrusive настройка): заменяет
  WSR+DSR+потенциометр **одним устройством**, позиция — через гальванически
  развязанный аналоговый выход 0/4–20 мА; работает только с AC-контроллером.
- **Blinker** — импульсный передатчик (опция в коде заказа).

Управление (входы AC 01.2):

- OPEN/STOP/CLOSE/EMERGENCY — дискретные команды.
- **MODE** — вход переключения режима open-close ↔ modulating.
- Уставка положения: 0/4–20 мА (аналоговые входы E1/E2/E3); 0–10 В — **не
  подтверждено** (в каталоге только 0/4–20 мА). PID-регулятор процесса — встроенная
  функция AC.2.
- **Напряжение цепи управления — характеристика БУ**: 24 V DC (стандарт,
  ~10 мА/вход) или 115 V AC (опция, ~15 мА/вход).

Протоколы (AC 01.2): Profibus DP, Profinet, Modbus RTU, Modbus TCP/IP,
Foundation Fieldbus, HART (+ SIL-варианты). HART у AUMA — «Analogue 4–20 mA
setpoint with digital HART communication» (на уставке) + вариант Current Output
для ОС; точка-точка до 3000 м, multidrop ≤ 8 устройств.

### 10.3 Номенклатура сигналов ROTORK (IQ3 Pro, PUB002-197)

Обратная связь:

- **S1–S4** — 4 конфигурируемых volt-free latching контакта, SPST, NO/NC,
  5 мА–5 А, 120 VAC / 30 VDC (пределы/момент/промежуточные/статус).
- **Monitor relay** — переключающий контакт готовности/аварии, 5 мА–5 А,
  120 VAC / 30 VDC; при аварии обесточивается (роль READY/ALARM).
- **CPT** (current position transmitter) — 4–20 мА пропорционально положению;
  **по умолчанию с внутренним питанием (активный)**, опция — внешнее питание от
  петли (пассивный); при обесточивании привода ток 4 мА.
- **CTT** (current torque transmitter) — аналоговый момент 4–20 мА, 0–120 %
  номинального момента.

Управление:

- Open/Close/Stop (+ Maintain) — 3 оптоизолированных входа, fleeting или maintained,
  полосы **20–60 V DC / 40–120 V AC**; питание от привода 24 V DC (опция 120 V AC);
  «fast remote» 24 V DC (импульсы от 100 мс); вариант negative switching.
- Уставка 4–20 мА (modulating).
- **ESD** (emergency shutdown) — ход в заданный «home»-порт, конфигурируемый
  open/stayput/close от NO/NC контакта, приоритет над всеми остальными сигналами.
- **Interlocks** — open/close interlock: 3 входа, maintained, 20–60 V DC / 40–120 V AC
  (аппаратные «permissive»-блокировки). **Drive enable** — опция (разрешение хода).
- Interrupter timer — пульсирующий режим, период 1–99 с.

Протоколы: Pakscan Classic (токовая петля до 20 км, до 240 устройств, 2 независимые
петли), Modbus (AIM), Profibus DP (EN 50170), Foundation Fieldbus (IEC 61158-2, link
scheduler), DeviceNet, HART («аналоговая часть для управления + наложенный цифровой
сигнал для ОС/диагностики»), EtherNet/IP, Modbus TCP, PROFINET (Integrated Ethernet).

Функции БУ: datalogger (момент/работа/температура/вибрация/события), partial stroke
profile, Bluetooth Setting Tool Pro, IQ Insight 2.

### 10.4 RWG и его место в схеме разд. 9

**RWG 4020 — это не «сопротивление наружу».** Это потенциометр **с электронным
преобразователем**: на выходе — токовый сигнал 0/4–20 мА (2/3/4-проводные системы),
подключается на разъём XK. Голое сопротивление наружу — это другая опция AUMA,
«precision potentiometer» (код A в заказе).

В схеме разд. 9:

- **RWG 4020** = `EaFeedbackSignal` role=POSITION, category=analog,
  form=AN_4_20_PASSIVE (2-wire) / AN_4_20_ACTIVE (3/4-wire) — ложится в
  **существующие** формы, отличается от EWG только технологией датчика
  (потенциометр vs Холл) — деталь, которую потребитель не видит на клеммах.
- **Precision potentiometer** = `EaFeedbackSignal` role=POSITION, новая форма
  RES_POTENTIOMETER; поля max_voltage/max_current не подходят — нужны сопротивление
  (кОм) и допустимая мощность (Вт).
- Доступность — строками `EaSignalMatrixEntry`; RWG/EWG/pot доступны и на AUMA NORM
  (Basic), MWG — только с AC-контроллером.

**Вывод:** разделение role/form подтверждается практикой AUMA — одна роль POSITION
в четырёх исполнениях (precision pot / RWG / EWG / MWG). Значит form должен быть
расширяемым справочником (вопрос №3 — в пользу справочника), а параметры сигнала
должны зависеть от формы (nullable-набор или generic JSON, вопрос №12).

### 10.5 Что нужно расширить в схеме (по итогам сравнения)

1. **Формы**: добавить RES_POTENTIOMETER (голый потенциометр); дискретные команды
   перевести с «номинала в форме» (DISC_220VAC/DISC_24VDC) на DISC_AC/DISC_DC +
   поле voltage — у AUMA/ROTORK напряжение управления это ось БУ, а не сигнала.
2. **Матрица**: добавить ось control_voltage (напряжение цепи управления) отдельно
   от power_supply (питание мотора). Подтверждено обеими фирмами: AUMA 24 V DC std /
   115 V AC opt; Rotork полосы 20–60 V DC / 40–120 V AC.
3. **EaControlUnit.capabilities**: local_controls, display, pst, datalogger,
   bluetooth, esd, pid, interrupter_timer — функции БУ, которые не являются сигналами.
4. **Пакеты/пресеты**: MWG = связка WSR+DSR+аналог положения одним устройством →
   нужен механизм «пакет сигналов» (роль бывшего ControlUnitSignalProfile).
5. **Роли**: CMD_EMERGENCY_OPEN/CLOSE (AUMA EMERGENCY / Rotork ESD), TORQUE_ANALOG
   (Rotork CTT), MODE (переключение режима), INTERLOCK_OPEN/CLOSE, DRIVE_ENABLE;
   READY/ALARM уже есть (monitor relay).
6. **HART**: подтверждено обоими производителями — HART едет по аналоговой петле
   4–20 мА (у AUMA на уставке, у Rotork «аналог для управления + наложенная цифра»)
   → трактовка «протокол, привязанный к сигналу AN_4_20_*» (вопрос №4), а не
   свободный протокол БУ.

*Статус: разд. 10 сверен с каталогами производителей (AUMA SA/SAR Y004.388/003,
AC 01.2 технические данные; Rotork IQ3 Pro PUB002-197-00). Правок кода нет.*

---

## 11. Позиционная ОС: «потенциометр / трансмиттер» — слот, а не блок

Дата: 2026-10-18. Уточнение по собственным БУ пользователя (AOX-линейка) и
решение по вынесению функционала в отдельный блок.

### 11.1 Физика у пользователя

- Есть два отдельных исполнения позиционной ОС: **«потенциометр»** (омическая ОС,
  сопротивление наружу) и **«трансмиттер»** = потенциометр + преобразователь в
  4–20 мА (физически одна сборка, на клеммах — токовая петля).
- В интеллектуальных БУ (ICU/SRCU/LCU) омической ОС отдельно нет — позиция
  выдаётся встроенным 4–20 мА.
- В общей схеме омическую ОС предусмотреть нужно (AUMA «precision potentiometer»,
  другие производители).

### 11.2 Обновление схемы (дельта к разд. 9)

**EaFeedbackSignal:**

- В `form` добавить **RES_POTENTIOMETER** (потенциометр: сопротивление
  пропорционально положению, пассивный, питание — внешнее).
- Параметры, зависящие от формы (решение по вопросу №12 — в пользу
  nullable-набора): для RES_POTENTIOMETER валидны `resistance_kohm`,
  `max_power_w`, `turns`; для контактов — `max_voltage`/`max_current`;
  для AN_4_20_* — признак active/passive (уже в форме).
- Композиция «трансмиттер = потенциометр + преобразователь» в модель **не
  вводится** — это BOM/описание артикула, не выбор конфигуратора.

**EaSignalMatrixEntry:**

- Добавить `slot` (код группы, например POSITION_FEEDBACK): строки одного слота
  в пределах (scope × control_unit × power_supply × mode) — **взаимоисключающие
  альтернативы**: выбрано не более одной (если есть `is_default` — предвыбрана).
  «Нет» = в слоте нет доступных строк.
- `availability='na'` на более специфичном уровне запрещает строку (как в 6.1).

Пример для своей линейки (концептуально, заполнение — отдельным вводом данных):

| scope | БУ | слот | строка | avail |
|---|---|---|---|---|
| brand AOX | Basic | POSITION_FEEDBACK | RES_POT (потенциометр) | opt |
| brand AOX | Basic | POSITION_FEEDBACK | AN_4_20_PASSIVE (трансмиттер) | opt |
| brand AOX | INT ICU/SRCU/LCU | POSITION_FEEDBACK | AN_4_20_PASSIVE (встроенная) | std |
| brand AOX | INT ICU/SRCU/LCU | POSITION_FEEDBACK | RES_POT | na |
| brand AUMA | AUMA NORM | POSITION_FEEDBACK | RES_POT (precision pot) | opt |
| brand AUMA | AUMA NORM | POSITION_FEEDBACK | AN_4_20 (RWG/EWG) | opt |

### 11.3 Оценка «вынести функционал в отдельный блок»

**Решение: НЕ выносить.** Причины:

1. Конфигуратор выбирает сигналы на клеммах — форма уже различает исполнения
   (RES vs AN_4_20); отдельное устройство не добавляет выразительной силы.
2. Отдельный блок-устройство породит вторую матрицу совместимости
   «устройство × БУ» — дублирование `EaSignalMatrixEntry`.
3. Физика (потенциометр, преобразователь) — забота BOM/артикула, а не выбора:
   части трансмиттера отдельно не заказываются.
4. Разд. 7→8 уже отказались от модели физических датчиков; блок-устройство —
   шаг назад.

**Когда блок всё же нужен (критерии для будущего):**

- устройство выбирается **независимо** от типа БУ;
- имеет собственные характеристики подбора (точность, обороты, Ex, температура);
- кодируется **отдельной позицией** артикула;
- допускает раздельную композицию (потенциометр + навесной преобразователь как
  два SKU).

Если любой из критериев появится — тогда отдельный каталог устройств с полем
`emits → EaFeedbackSignal` (одна строка устройства = один выдаваемый сигнал).

*Статус: разд. 11 добавлен — слот вместо блока; схема обновлена (RES_POTENTIOMETER,
slot в матрице, параметры по форме). Правок кода нет.*

---

## 12. Справочник устройств позиционной ОС (требование «замени RWG/EWG»)

Дата: 2026-10-18.

### 12.1 Требование

Потребители формулируют замену явно: «позиционная ОС — аналог AUMA RWG» или
«— аналог AUMA EWG». Для ответа нужны **оба** уровня:

- **форма сигнала** (что на клеммах) — покрыто сигнальной моделью разд. 9–11;
- **устройство/технология датчика** — RWG и EWG дают одинаковый сигнал 4–20 мА,
  но разные технологии (потенциометр + преобразователь vs бесконтактный Холл).
  Сигнальная модель их не различает → нужен справочник устройств.

### 12.2 Решение: тонкий EA-справочник устройств (НЕ pa_controls.SensorComponent)

Смешивать с датчиками БКВ некорректно и не нужно:

- `pa_controls.SensorComponent` — закупаемые компоненты позиционеров
  (variety, contact_form, Ex, конкретные модели); у ЭП — опции производителя
  привода с выходным сигналом; нет общей оси данных и связи между ними.
- Решение разд. 8 («не переиспользуем SensorComponent») остаётся в силе.

```python
class EaFeedbackDevice:          # справочник устройств ОС ЭП (свой)
    code / name                  # RWG_4020, EWG_01_1, MWG, PRECISION_POT,
                                 # TRANSMITTER_4_20 (свой), POT_RAW (свой)
    technology                   # POTENTIOMETER | POT_CONVERTER | HALL | MAGNETIC
    contactless                  # bool
    emits                        # M2M EaFeedbackSignal (MWG: контакты + аналог)
    equivalents                  # M2M self: «наш TRANSMITTER_4_20 ≡ RWG_4020»
    accuracy / life_cycles / temp_range / description   # справочные
```

- `EaSignalMatrixEntry.device` — nullable FK на `EaFeedbackDevice`: строка матрицы
  остаётся **сигнальной**, устройство — её метаданные и база эквивалентности.
  Валидация: `device.emits` должен содержать signal строки. Если device пуст —
  «чистый сигнал» (как сейчас).
- Выбор в конфигураторе не меняется (слот, разд. 11): устройство — НЕ вторая ось
  выбора.
- MWG-пакеты: остаются пресетами (вопрос №14), разворачиваются в сигнальные
  строки с device=MWG.

### 12.3 Как отвечать на «замени RWG/EWG»

- Прямой поиск: `EaFeedbackDevice.equivalents` → строки матрицы нашего бренда
  с этим device → доступные опции (форма + устройство).
- Честные пробелы: если аналога нет (у нас нет бесконтактного трансмиттера = нет
  аналога EWG) — отсутствие equivalents-связи это показывает, а не молчит.
- Два своих опциона с одной формой 4–20, но разной технологией — различимы
  через device.

### 12.4 Что НЕ возвращается из разд. 7

Модель физических датчиков с маршрутизацией (EaSensor + ModelSensor +
ModelSignalRoute) остаётся отменённой: нет маршрутов, нет «какие датчики стоят
на модели». Добавляется только справочный слой устройств с привязкой к сигналам
и эквивалентами — ровно столько, сколько требует «замени RWG/EWG».

*Статус: разд. 12 добавлен — EaFeedbackDevice (справочник устройств ОС +
эквиваленты), device FK на строке матрицы. Правок кода нет.*

---

## 13. Мультибрендовость: AUMA/ROTORK как товары в БД и их кодировки

Дата: 2026-10-18. Требование: со временем в БД заводятся приводы AUMA и Rotork
как собственные товары — модель должна адекватно описывать их структуру и коды
заказа.

### 13.1 Что уже покрыто схемой

- Матрица со скоупом brand → model_line → model_line_item (наследование +
  override) проектировалась под мультибрендовость (разд. 6.1/8.3).
- Ось БУ покрывает номенклатуру AUMA: AUMA NORM ≈ kind=NONE (клеммная колодка),
  AM 01.1/02.1 ≈ BASIC (параллельное управление), AC 01.2 ≈ INTEGRATED;
  Rotork IQ3 ≈ INTEGRATED.
- Оси напряжения (power_supply + control_voltage, разд. 10.5): AUMA 24 V DC std /
  115 V AC opt; Rotork полосы 20–60 V DC / 40–120 V AC.
- Устройства ОС + equivalents (разд. 12) — для «замени RWG/EWG» и описания
  собственных опций.

### 13.2 Факт: кодировка AUMA — позиционная (сверено с «РАСШИФРОВКА СХЕМ АУМА.pdf»)

Код заказа AUMA состоит из 14 позиций, каждая = группа опций со значением.
Актуаторная часть (TPA):

| Поз. | Группа | Значения (примеры) |
|---|---|---|
| 1–2 | мотор | 00 = 3-фазный, 16 = 1-фазный |
| 3 | направление закрытия | R / L |
| 4 | защита мотора | 1 = термовыкл 140 °C (NC), 2 = PTC |
| 5 | моментные выкл. | 0 = без (MWG), A = 2 одинарных, B = 2 тандем |
| 6 | концевые/промежут. | 0 = без (MWG), A = 2 одинарных, B = 2 тандем |
| 7, 11 | резерв | — |
| 8 | сигнализация | 0/1/2/3 (blinker, ручной выкл.) |
| 9 | позиц. трансмиттер | 0 = нет, A = precision pot, E = RWG 4-wire, I = MWG |
| 10 | обогрев | 0 = нет, 1 = 110–250 V / 24 V |
| 12–14 | спецблоки | 000 |

Контроллерная часть (MSP, для AM 01.1/02.1): позиции корпус, разъём (B = шина),
мотор, версия управления (0/7/-), входные сигналы (K/0), выходные сигналы (C/0),
уровень входа 24 V DC (3/-), **программирование/шина (- = стандарт, 1 = Profibus DP,
7 = Modbus RTU)**, БП, силовая часть (F = контакторы, A/Z = тиристоры), селектор,
органы управления, обогрев/blinker, защита мотора.

Ключевые наблюдения:

(a) **Каждая позиция = группа опций = наш `slot`** → нужен `slot.encoding_position`.
(b) **MWG пишется сразу в три позиции** (5, 6, 9) — пакет должен нести несколько
    вкладов в код (вопрос №14 расширить).
(c) **Часть позиций — не сигналы** (мотор, термозащита, обогрев, blinker, корпус,
    силовая часть) → матрице нужны несигнальные атрибутные строки.
(d) **Протокол кодируется на БУ** (MSP поз. 8, «B» в поз. 2) — у `EaControlUnit`
    сейчас нет поля encoding — добавить.

### 13.3 Дельта схемы

1. **`slot.encoding_position`** (nullable int) — позиция группы в коде заказа;
   вклад значения — существующий `EaSignalMatrixEntry.encoding`. Сборка артикула —
   по шаблону бренда (простая конкатенация по позициям).
2. **Атрибутные строки матрицы**: `EaSignalMatrixEntry.kind` = SIGNAL (union FK,
   как сейчас) | ATTRIBUTE (FK на тонкий `EaAttributeDefinition`: code/name/
   category [motor_protection, heater, blinker, motor, housing, switchgear, duty,
   starter, …] + encoding) — для несигнальных позиций кода. Это же закрывает
   вопрос №10 (S2/стартер — атрибуты, а не сигналы).
3. **`EaControlUnit.encoding` + `variant`** — для вариантов AC 01.2
   (Profibus DP / Profinet / Modbus RTU / Modbus TCP / FF / HART), различающихся
   кодом (MSP поз. 8).
4. **Rotork**: структура кода заказа в скачанных PDF не описана (брошюра и
   листовки) — нужны spec-листы (PUB002-039 IQ3 Pro, PUB002-065 IQT3 Pro) —
   *добыть*. Ориентировочно: база модели (IQ10/IQ12/…/IQM/IQT) — на
   model_line_item (SKU-механика приложения), опции — суффиксы из матричных строк.

*Статус: разд. 13 добавлен — позиционные кодировки (slot.encoding_position,
ATTRIBUTE-строки, EaControlUnit.encoding). Правок кода нет.*

---

## 14. Кодировка AUMA через существующий ext_encoding (уточнение разд. 13)

Дата: 2026-10-18. Сверено с кодом приложения.

### 14.1 Что уже есть в коде

- `model_line.ext_encoding_template` — шаблон ext-части артикула с плейсхолдерами
  (`core/models/mixins.py: generated_ext_code`, `_get_ext_code_data_dict`).
- `ext_encoding` — поле уже есть на через-опциях ЭП (migration 0046:
  ElectricControlUnitOption, ElectricEndSwitchesOption, ElectricBlinkerOption, …)
  и cable_glands.
- Плейсхолдер резолвится через `ext_code_path` (фолбэк `code_path`) или **callable
  на модели** — можно тянуть значения с полей модели (напр. motor_thermal_protection,
  направление закрытия).

**Вывод:** позиционная машина уже существует — порядок плейсхолдеров в шаблоне и
есть позиции кода заказа. Числовой `slot.encoding_position` из разд. 13.3.1 **не
нужен**.

### 14.2 Как ложится код AUMA (TPA 14 позиций + MSP)

- TPA: `ext_encoding_template` на серии AUMA из 14 плейсхолдеров; значения:
  - моментные/концевые/промежуточные → ext_encoding через-опций переключателей;
  - позиционный трансмиттер → ext_encoding новой опции (схема разд. 9–12);
  - термозащита, мотор, направление, спецблоки → callable-плейсхолдеры с полей
    модели;
  - обогрев, blinker → существующие опции/поля.
- MSP (контроллер AM): отдельный сегмент шаблона; источник —
  `ElectricControlUnitOption.ext_encoding` (протокол/шина — вариант БУ).
- **MWG в трёх позициях** (5/6/9): пресет (вопрос №14) должен проставлять значения
  сразу трёх через-опций — каждая со своим ext_encoding («0» для 5/6, «I» для 9).
- Rotork: структура кода всё ещё за spec-листами (PUB002-039/065) — *добыть*.

### 14.3 Итог упрощения разд. 13.3

| Было (13.3) | Стало |
|---|---|
| `slot.encoding_position` + row.encoding | ext_encoding_template + ext_encoding (уже есть) |
| ATTRIBUTE-строки матрицы | поля модели через callable + существующие опции; новые группы — через-опция либо callable |
| `EaControlUnit.encoding` + variant | ElectricControlUnitOption.ext_encoding (есть); в новой схеме у EaControlUnit — аналог |

---

## 15. Справочник терминов AUMA/ROTORK и включение в ai-assistant

Дата: 2026-10-18. Назначение: (1) перевод терминов опросного листа/каталогов при
ручном заполнении фильтров; (2) структурные подсказки агенту при извлечении
фильтров из текстовых запросов клиентов.

### 15.1 Модель

```python
class TermGlossaryEntry:            # рекомендую в ai_assistant
    term                # «RWG», «moment cutoff», «ОС положения»
    synonyms            # JSON-список синонимов («потенциометрический датчик»,
                        # «позиционный передатчик»)
    source              # AUMA | ROTORK | AOX | ОЛ | GENERIC
    explanation         # разъяснение для пользователя/агента
    target_filter       # FK ai_assistant.FilterDefinition, null (уровень параметра)
    target_option       # GenericFK (опция: EaFeedbackDevice, через-опция ЭП, ...), null
    code_value          # значение в коде заказа («E» в поз. 9 TPA), null
    context_note        # «в коде заказа AUMA: позиция 9»
    sorting_order, is_active
    # правило: заполнен хотя бы один из target_filter / target_option
```

### 15.2 Интеграция с ai-assistant (по ai-assistant.md)

1. **Extract-промпты (агент).** Генератор промптов v2 уже строит текст из
   `FilterDefinition` + опций БД. Дополнение: для каждого FD/опции узла
   подставляются строки словаря, привязанные к ним (target_filter в наборе узла;
   target_option ∈ опций FD). Ограничение объёма — top-N по sorting_order.
   Результат: LLM видит «RWG = позиционная ОС, трансмиттер 4–20 мА (код E)» и
   корректно ставит filter-значения.
2. **Ручное заполнение фильтров (пользователь).** Эндпоинт
   `GET /api/ai-assistant/glossary/search/?q=...` → записи (термин → параметр/
   опция + код + пояснение). Виджет подсказок на формах фильтров каталогов и в
   AiCatalogSearch (TODO уже в ai-assistant.md).
3. **Связь с equivalents (разд. 12):** `EaFeedbackDevice.equivalents` — машинная
   связь «наш = их»; справочник — человеко/LLM-слой поверх: запись «RWG»
   указывает на устройство/опцию, equivalents дополняет.

### 15.3 Наполнение

- Стартовые данные — из разд. 10/12/13: RWG 4020, EWG 01.1, MWG, WSR/WOEL,
  DSR/DOEL, WDR/WDL, precision potentiometer, CPT, CTT, ESD, monitor relay,
  blinker, DOEL/WOEL и т.д. (term, synonyms, explanation, code_value).
- Плюс термины собственного опросного листа (source=ОЛ) → параметры системы.

*Статус: разд. 14–15 добавлены — ext_encoding закрывает позиционность кода AUMA;
справочник терминов TermGlossaryEntry с инъекцией в промпты и UI-поиском. Правок
кода нет.*
