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
