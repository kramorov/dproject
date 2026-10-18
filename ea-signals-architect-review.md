# Ревью финальной схемы сигналов ЭП — Chief System Architect

Дата: 2026-10-18. Рецензируемый документ: `ea-signals-final-scheme.md`.
Сверено с кодом: `electric_actuators/models/*` (ea_options, ea_allowed_options,
ea_control_unit_wiring, ea_actuator_constructor, миграции 0046), `params/*`
(control_unit_signal_profile, signal_role, input_signal_spec, models),
`core/models/mixins.py` (ext_encoding), `ai-assistant.md`.

---

## Вердикт

Схема **утверждаема** с тремя обязательными доработками (Р1–Р3) и рядом
рекомендаций. Базовая конструкция правильная: сигналы как источник истины,
наследуемая матрица, переиспользование существующих механизмов
(through-опции, ext_encoding_template, ControlUnitInstalledOption) вместо
параллельных структур. Факты в схеме соответствуют коду.

---

## Что подтвердилось (факт-чек)

- `ext_encoding` есть на through-опциях ЭП (migration 0046, в т.ч.
  ElectricControlUnitOption) и на cable_glands. ✓
- `model_line.ext_encoding_template` + плейсхолдеры с callable — в
  `core/models/mixins.py`. ✓
- `params.ControlUnitInstalledOption`, `PowerSupplies`, `SwitchesParameters`,
  `SignalRole` (direction input/output/bidirectional), `InputSignalSpec`,
  `ActuatorHeaterSupply` существуют. ✓
- `ControlUnitWiring` = БУ×напряжение×signal_profile×схема + heater_supply +
  cached_json. ✓
- `ControlUnitSignalProfile` + Entry (SignalRole → SensorComponent/InputSignalSpec)
  — текущий механизм «доступности» сигналов. ✓
- `AllowedControlUnitOption` — encoding БУ на уровне серии (вторая точка
  кодировки наряду с through-опциями). ✓
- Конструктор EA: `ElectricActuatorConstructor.get_available_options`,
  `_get_option_encoding/_get_option_ext_encoding` — резолвинг опций и кодов
  уже сервисный, точка интеграции матрицы найдена. ✓

---

## Обязательные доработки

### Р1 [High] Модель выбора шины не зафиксирована — ПРИНЯТО (2026-10-18)

**Решение (принято пользователем):** базовые записи БУ, шины — M2M `protocols`;
в конфигураторе — слот PROTOCOL; ext-код БУ = композиция «база БУ + код шины»
(MSP поз. 8, «B» в поз. 2). Для AOX слот пуст.

### Р2 [High] Три механизма доступности — РЕШЕНО (2026-10-18): полный переезд

**Решение пользователя:** старый путь не сохраняем, костыли не делаем —
конфигуратор переводится на матрицу целиком, без флага `is_matrix_driven`.
Электроприводы в отладке, ломать можно. Механика переезда:

- скрипт выгружает значения старых моделей (профили, `ControlUnitWiring`,
  через-опции переключателей с encoding/ext_encoding) → JSON-снапшот;
- сверка с таблицей AOX → заливка в матрицу (п. 5 плана в финальной схеме);
- после подтверждения заливки удаляются: `AllowedSignalProfileOption`,
  `ControlUnitWiring.signal_profile`, `ControlUnitSignalProfile`+Entry,
  через-опции переключателей из конструктора/UI;
- сценарии рассинхрона (правка профиля vs матрица, двойная кодировка, схемы)
  снимаются удалением старого источника, а не флагами.

### Р3 [High] Slot как строка-код без модели — ПРИНЯТО (2026-10-18)

**Решение (принято пользователем):** модель `EaSignalSlot`
(code/name/required/sorting_order/is_active) + FK с матричной строки.

---

## Рекомендации (принять по ходу реализации)

### С1 [Medium] Трёхуровневый скоуп vs двухуровневая кодировка

Существующая кодировка живёт на двух уровнях (серия — AllowedControlUnitOption;
item — through). Матрица добавляет brand-уровень. Для своей линейки строки
brand-уровня не нужны (данные и так посерийно) — иначе encoding окажется в
трёх местах. **Рекомендация:** brand-уровень заполнять только для AUMA/Rotork;
для AOX — серия+item; в админке — «эффективные строки» (resolved view), чтобы
не гадать, что перекрыто.

### С2 [Medium] mode строки vs default_output_type модели

`ElectricActuatorModelLine.default_output_type` (on-off/modulating) уже
существует. Правило резолвинга должно фильтровать строки по режиму модели
(строка mode=modulating не видна для on-off модели). Зафиксировать в сервисе
резолвинга + тест.

### С3 [Medium] Историческая связь ЭП→БКВ в профилях

`ControlUnitSignalProfileEntry.sensor → pa_controls.SensorComponent` — ровно
та связь, которую схема (разд. 8/12) признала некорректной. Профили **не
удалять** (на них висят `ControlUnitWiring.signal_profile` и cached_json),
но для matrix-driven серий они перестают быть источником; при наполнении
матрицы строки получают `device=EaFeedbackDevice`, а не SensorComponent.

### С4 [Medium] control_voltage FK на PowerSupplies

PowerSupplies — справочник напряжений питания; полосы Rotork (20–60 V DC,
40–120 V AC) в него семантически не ложатся. Варианты: новые записи
PowerSupplies с «диапазонными» кодами или CharField на БУ. Решить при вводе
данных Rotork (не блокирует первые фазы).

### С5 [Medium] Конфликты: M2M self vs ParameterRule

Для «лимита клемм Q/M» M2M `conflicts` достаточно. Более сложные правила —
уже существующий `configurator.ParameterRule` (не строить вторую машину
правил). Границу провести: конфликты только парные и безусловные — M2M;
всё остальное — ParameterRule.

### С6 [Low] Пресеты — без отдельной модели

Раньше предлагалось переиспользовать `ControlUnitSignalProfile` как пресет.
После решения о полном переезде (Р2) пресеты в рантайме не нужны: MWG-пакет —
три матричные строки с общим `bundle` (каждая со своим ext-кодом, позиции
TPA 5/6/9); профили используются только как шаблон при выгрузке старых данных
и удаляются. См. разд. 5 финальной схемы.

### С7 [Low] ext_encoding_template: фиксированные позиции

TPA-код AUMA имеет резервные позиции (7, 11 = «-») и позиции-константы.
Проверить поддержку фиксированных/пустых сегментов в шаблоне mixins до
написания шаблонов; при необходимости — литералы в шаблоне.

### С8 [Low] cached_json ControlUnitWiring

При переходе серии на матрицу кэш wiring (содержит profile) нужно
перегенерировать — сигналы на фронте должны прийти из матрицы, а не из кэша.

### С9 [Low] Производительность резолвинга

Резолвинг матрицы (наследование + слоты + конфликты + mode) — кэшировать по
паттерну cached_json в конструкторе; инвалидация по сигналам строк матрицы.

---

## Данные и внедрение

- Seed: AOX-матрица генерируется скриптом из `available-options-ea-AOX.xlsx`
  (паттерн `init_migrations_template` уже есть); AUMA — из каталогов E:\work;
  Rotork — после spec-листов PUB002-039/065.
- Объём работ (оценка): 5 новых моделей + EaSignalSlot + расширение
  ControlUnitInstalledOption + сервис резолвинга + UI слотов в конструкторе +
  seed-скрипты + тесты. Фазы из разд. 9 финальной схемы корректны; добавить
  в фазу 5 пункт «выбор шины (Р1)» и в фазу 3 «EaSignalSlot (Р3)».
- Критерий приёмки фазы 3: для серии AOX-R резолвинг матрицы совпадает с
  колонками таблицы AOX (спот-чек по 3 моделям × 2 напряжениям × 2 режимам).

---

## Итог

Схема совместима с существующей архитектурой и зафиксирована:
Р1 (слот PROTOCOL) и Р3 (EaSignalSlot) приняты; Р2 решён полным переездом
(без флагов и костылей — выгрузка данных, удаление старого пути).
Дополнительные требования 2026-10-18: локализация названий из справочников
(паттерн lang.md) и подробные докстринги каждой модели — включены в финальную
схему (разд. 8, 9) и план (разд. 10). К реализации можно приступать с фазы 1
(выгрузка данных).

---

## Ревью №2 (2026-10-18, после решения о полном переезде)

Второй проход по обновлённому `ea-signals-final-scheme.md`. Найденные
несостыковки помечены статусом: **исправлено** (схема поправлена сразу) или
**требует решения**.

### F1 [исправлено] Слот PROTOCOL не укладывался в схему строки

Р1 («шина = слот PROTOCOL внутри матрицы») противоречил схеме строки: там были
только control_signal/feedback_signal. Исправлено: у строки **три nullable FK**
(control_signal / feedback_signal / protocol), protocol — только для строк слота
PROTOCOL.

### F2 [исправлено] MWG-позиции «0» не были представимы

«0 = Without torque switches (MWG)» — это отсутствие, а не сигнал. Введены
**явные строки «нет»**: signal=None, имя «Без переключателей»/«Без обогрева»;
валидация «ровно один signal ИЛИ все три null» — CheckConstraint. Это же
покрывает AUMA-позиции «0» и слота HEATER.

### F3 [исправлено] Семантика bundle не была атомарной

«влечёт остальные строки пакета (если доступны)» допускало частичный пакет.
Исправлено: если хоть одна строка пакета недоступна — пакет целиком недоступен;
выбор/снятие — одной операцией.

### F4 [исправлено] Парные конфликты не покрывают лимит клемм Q/M

Правило «нельзя DPDT + средний + моментный + центральный одновременно» — запрет
**набора**, а не пар: парные M2M запретили бы и допустимые пары. Разведено:
парные — `conflicts` M2M; составные — `configurator.ParameterRule` (добавлено в
фазу 4).

### F5 [исправлено] Двойной источник оси БУ×напряжение

`ElectricControlUnitOption`/`ElectricPowerSupplyOption` объявляют доступные пары,
и матричные строки тоже несут control_unit+power_supply. Добавлено правило
валидации при заливке (п. 6 правил резолвинга): пары строк должны быть
объявлены доступными; несовпадения — в отчёт заливки.

### F6 [требует решения до фазы 1] Таблицы маппинга выгрузки

Выгрузка профилей нетривиальна: `SignalRole` (OPEN_LIMIT, CLOSE_LIMIT,
TORQUE_OPEN, POS_4_20MA, ALARM, READY, …) → роли Ea*; `InputSignalSpec` →
`EaControlSignal` (form/voltage/current); `SensorComponent` →
`EaFeedbackDevice`/сигнал или «нет эквивалента» (в отчёт). **Решение:**
маппинг-словарь в коде скрипта выгрузки с явным списком «не распознано».
Без него выгрузка превратится в ручную работу. Внесено в фазу 1 плана.

### F7 [требует решения в фазе 3] backfill kind

`kind` на `ControlUnitInstalledOption` — обязательное поле для существующих
записей (Basic, INT ICU/SRCU/LCU…). Нужна data-миграция классификации; иначе
поле поломает существующий справочник БУ. Внесено в фазу 3.

### F8 [внесено в план] Точки интеграции, которые легко забыть

- `_get_ext_code_data_dict` (core/models/mixins.py): после удаления через-опций
  переключателей их плейсхолдеры должны резолвиться из **матричных строк** —
  расширение механизма в фазе 6.
- AI-пайплайн для ЭП: `FilterDefinition`/handler на матричный резолвер — добавлено
  в фазу 8 (после словаря терминов, не блокирует 1–7).
- Идемпотентность заливки (повторный импорт без дублей) и юнит-тесты резолвера
  добавлены в фазу 9.

### F9 [наблюдение, решения не требует] required-слот и строка «нет»

`EaSignalSlot.required=True` + строка «нет» (signal=None) согласованы: «нет» —
доступная строка слота, пользователь явно выбирает «без обогрева». Наполнение
данных должно помнить это при выставлении required.

**Вердикт после второго прохода:** план внутренне согласован. К реализации
готовы фазы 1–3 при условии закрытия F6 (маппинг выгрузки) и F7 (backfill kind).

### Дополнение 2026-10-18 (по решению пользователя): диаграмма как привязка

`ControlUnitWiring` не переживает переезд даже как «БУ×напряжение → схема»:
диаграмма подходит лишь части комбинаций опций, поэтому введена отдельная
`EaWiringDiagramBinding` (скоуп × БУ × напряжение × режим × **подпись сигналов**
× match_type → diagram из медиабиблиотеки). Семантика «есть или нет»: нет
совпадения подписи — нет схемы. Плюс новая задача — **генератор
wiring-диаграмм** по выбранным сигналам (фаза 8 плана; для него в справочники
сигналов добавлено поле `wires`). 21 существующая связка мигрирует в привязки
в фазе 5 (подпись строится по entries профиля через маппинг F6, match_type=exact).
Открытые вопросы — №21 (match_type по умолчанию, обогрев в подписи, приоритет
привязок, формат генератора).

---

## Ревью №3 (2026-10-18): код фаз 1–2

Скоуп: `export_ea_signal_data.py` (фаза 1), модели `ea_signal_form.py`,
`ea_signals.py`, `ea_comm_protocol.py`, `ea_feedback_device.py`,
`ea_signal_slot.py`, админка `ea_signals_admin.py`, миграция 0049.
Проверено фактически: `manage.py check` — 0 issues, миграция применена,
sanity-создание записей + валидация hart + i18n sync — работают.

### H1 [High] У EaFeedbackSignal нет различия NO/NC — ИСПРАВЛЕНО (2026-10-18)

Добавлено поле `contact_normal` (NO/NC/CHANGEOVER, только для контактов) +
валидация + миграция 0050 + тесты.

### M1 [Medium] «Копировать» в админке падает на unique code — ИСПРАВЛЕНО

Всем 6 моделям добавлен `CopyMixin` (суффикс кода « Копия»), тест на копию.

### M2 [Medium] N+1 в скрипте выгрузки — ИСПРАВЛЕНО

`select_related` расширен (`power_supply_option__model_line_item__model_line`
и т.п.); экспорт перепроверен — те же счётчики.

### M3 [Medium] Мусор в скрипте выгрузки — ИСПРАВЛЕНО (убраны sys/Entry).

### L1 [Low] Валидация HART по категории формы — ИСПРАВЛЕНО

### L2 [Low] Тесты — ИСПРАВЛЕНО: `electric_actuators/tests.py`, 10 тестов, все зелёные.

Смежная находка (вне скоупа): `core` имеет изменения моделей без миграции
(предупреждение тест-раннера) — существующий дрейф, разобрать отдельно.

### Residual risk

- Справочники созданы, но **не наполнены** (seed отложен): формы — 8 sanity-записей,
  сигналы — 2; полный seed по F6 + AOX — следующий шаг.
- Миграция backfill kind (F7) и маппинг SensorComponent→contact_normal — зависят
  от H1.
- Схема/матрица/привязки (фазы 3–4) ещё не реализованы — резолвинг не проверен.

**Вердикт:** код фаз 1–2 рабочий (check/migrate/sanity зелёные), мёржить можно;
до фазы 5 обязательно закрыть H1, желательно — M1–M3.

---

## Ревью №4 (2026-10-18): фаза 3 — расширение ControlUnitInstalledOption

Скоуп: `params/models.py` (kind/accepts/emits/protocols/capabilities/
control_voltage), миграции `params/0073` (схема) и `0074_backfill_control_unit_kind`
(data), `params/admin.py` (админка БУ). Проверено: миграции применены, backfill
корректен (none/pote/tr→NONE, posi→POSITIONER, int-*→INTEGRATED), M2M работают
live, `manage.py check` — 0 issues, 10 тестов — OK.

### М1 [Medium, принятый трейдофф] params теперь зависит от electric_actuators

`params` — общий справочный апп, а M2M `accepts/emits/protocols` ведут в доменное
приложение `electric_actuators` (миграция 0073 имеет зависимость от
`electric_actuators.0050`). Инверсия направления зависимости: общие справочники
ссылаются на доменные модели. Это осознанный трейдофф решения Q8 (расширяем
существующую модель, а не плодим EaControlUnit), но зафиксировать как
residual risk: если другой доменный апп начнёт использовать БУ — связь придётся
пересматривать (альтернатива: EaControlUnit в electric_actuators + data-миграция).

### М2 [Medium] Админка: M2M и FK без фильтров — ИСПРАВЛЕНО

`autocomplete_fields` на все новые поля; PowerSuppliesAdmin получил search_fields.

### М3 [Low] capabilities — json-editor — ИСПРАВЛЕНО

`capabilities_display` в форме (виджет json-editor, как feature_list) + парсинг
в clean; fieldset обновлён.

### L1 [Low] print() в data-миграции 0074 — ИСПРАВЛЕНО (убран).

### L2 [Low] Тесты — ИСПРАВЛЕНО: 3 теста расширения БУ (kind default/choices,
M2M related names), всего 13 тестов зелёные.

Seed: `seed_ea_signal_catalog` — 8 форм/14 команд/24 ОС/8 протоколов/6 устройств
(+equivalents)/7 слотов; повторный запуск — 0 новых (идемпотентно).

### Residual risk

- Зависимость params → electric_actuators (М1).
- Протокольные варианты int-n-hr/mb/pb пока не разнесены в `protocols`
  (отложено до seed EaCommProtocol).

**Вердикт:** фаза 3 корректна — принять; желательно закрыть М2 (админка) и L2
(тесты) при ближайшей правке.

---

## Ревью №5 (2026-10-18): фаза 4 — матрица, привязки схем, резолвер

Скоуп: `ea_signal_matrix.py` (EaSignalMatrixEntry, EaWiringDiagramBinding),
`services/ea_signal_resolver.py`, админки, миграция 0051. Проверено: миграции
применены, 20 тестов зелёные (7 резолверных), check 0; SQL NULL-ловушка
(`__in=(None, x)`) найдена тестом, исправлена Q-условиями.

### F1 [Low] Суффикс «(Стандарт)/(Опция)» собран вручную

`EaSignalMatrixEntry.localized_name` делает `f' ({_("Стандарт")})'`, тогда как
паттерн through-опций (lang.md, урок 18) — `localize_service_word('(Стандарт)')`:
переводит скобочную единицу целиком и держит единообразие с остальными опциями.
Рекомендация: перевести на `localize_service_word`.

### F2 [Low] Ключ none-строки в резолвере — по row.id

`_row_key` для строк «нет» возвращает `('none', row.id)`: none-строки разных
уровней скоупа не перекрывают друг друга, и `na` не может точечно запретить
none-строку. Практично одна none-строка на слот; предложение на будущее — ключ
`('none',)` на слот (тогда na на специфичном уровне убирает none-строку).
Сейчас не блокирует (данных MWG-позиций ещё нет) — задокументировать при
заливке фазы 5.

### F3 [Low] N+1 в резолвере

`conflicts.all()` без prefetch и запрос на каждый bundle-код. Для
конфигураторного вызова терпимо; при введении кэша (план фазы 4) — неважно.
Perf-note.

### F4 [Info, вне скоупа] Пре-экзист баг дефолтных опций серии

`ElectricActuatorModelLine.ensure_all_default_options_exist` передаёт СЕРИЮ в
`ElectricWaySwitchesOption` (ожидает model_line_item) — исключение ловится и
логируется, дефолтные way-опции новых серий не создаются. Отмечен в handoff;
разбирать при фазе 7 (удаление через-опций).

### F5 [Info] Схеме соответствует: у матричной строки нет `is_active`

Мягкое отключение — только `availability='na'` на специфичном уровне; так и
задумано (скоуп-механика).

### F6 [Info] Autocomplete-цели проверены

Все цели (brands/model_line/item/control_unit/power_supply/slot/signals/
protocols/devices/heater/diagram) имеют search_fields; `BrandsAdmin` дописан
(search_fields + list_display).

**Вердикт:** фаза 4 корректна — принять. Желательно: F1 (localize_service_word)
при следующей правке; F2/F3 — при фазе 5 (заливка данных + кэш).

---

## Ревью №6 (2026-10-18): экспорт/импорт матрицы (ea_matrix_io)

Скоуп: `services/ea_matrix_io.py`, команды export/import_ea_signal_matrix,
админка серии (action + import view). Проверено: round-trip AR21E (66 строк →
0 создано/66 обновлено/0 ошибок), check 0, 21 тест зелёный.

### F1 [исправлено] Протокольные строки экспортировались как heater

kind определялся без protocol_id → строки слота PROTOCOL уехали бы в heater
(латентный баг, сейчас таких строк нет). Исправлено: kind='protocol' + код
протокола в signal_code (оба места — эффективные и na-строки).

### F2 [Low] Q(brand=None) в парах экспорта

`Q(brand=line.brand)` при бренде=None матчит все строки с пустым брендом
(строки серии/корпуса) — на distinct-парах не сказывается, но запрос шире
нужного. Косметика.

### F3 [Low] Импорт строки с пустым mode упадёт

`mode` обязателен на модели; экспорт всегда его пишет, но внешний файл с
пустой ячейкой даст ошибку в отчёт (не молча). Приемлемо; при желании —
валидация с понятным сообщением.

### F4 [Info] Формат файла жёсткий

Колонки сопоставляются по порядку (zip(FIELDS, values)) — перестановка колонок
сломает импорт. Документировано в разделе 12 схемы; для внутреннего обмена — ОК.

**Вердикт:** принять; F1 закрыт сразу, остальное — на усмотрение.

---

## Ревью №7 (2026-10-18): пакеты 13.3–14 — каркас выгрузки, EaSlotOption, ext-код

Скоуп: `services/ea_matrix_io.py` (каркас), `services/ea_ext_code.py`,
`models/ea_slot_option.py`, `AllowedControlUnitOption` (power_supply +
ext_encoding), резолвер (bundle/HEATER), заливщик v2, миграции 0055–0059,
тесты 32. Проверено: каркас AR21E (14400 строк / 15 моделей / 50 заполненных),
round-trip импорта, ext round-trip, check 0.

### F1 [серьёзно] Импорт none-строк: коллизия внутри слота

`apply_import` для none-строк ставит в lookup только (БУ, напряжение, режим,
слот) — без имени/опции. Две разные none-опции одного слота (например
INDICATOR: LED_SET и BLINKER в одной паре) при импорте затирают друг друга
(update_or_create найдёт одну и ту же строку). Нужно добавить в lookup `name`
(или `option`, когда option_code распознан) для kind='none'.

### F2 [серьёзно] Неоднозначность кодов внутри блока опций ext

Позиция cmd содержит код 'D' (CMD_OCS_24DC), а позиция ind — 'D' (LED_SET) и
'DB' (LED_SET_BLINKER). Строка «DB» декодируется как cmd='D' + ind='B'
(жадный разбор по порядку позиций), а не ind='DB'. Решение: коды cmd сделать
непрефиксными к ind — cmd: ''/DC/R/R2 (24DC→'DC', REMOTE 24DC→'R2').
Проверить и остальные пары позиций внутри блока (сейчас: lc S/N, setp A/P,
cnt M/E/EM/MF/EMF, ind D/B/DB/L/LB — после правки cmd коллизий нет).

### F3 [Low] Экспорт теряет encoding/ext_encoding для heater/none-строк

`_work_row` для kind=heater и none передаёт пустые encoding/ext_encoding
(данные есть у entry) — round-trip импорта обнулит кодировки таких строк.
Передавать entry.encoding/ext_encoding как для signal.

### F4 [Low] `coding_rules`: мёртвый код

Локальная функция `loc()` и параметр locale объявлены, но не используются
(имена берутся из справочников как есть; локализация придёт через
localized_name в фазе 6). Убрать или задействовать — при фазе 6.

### F5 [Info] Производительность экспорта

Каркас: резолвер на каждую пару (модель×БУ×напряжение×режим) + N+1
`EaSignalMatrixEntry.objects.get(pk=...)` на каждую эффективную строку.
Для AR21E — секунды; для полных каталогов стоит предзагрузить строки по
скоупам и убрать get-по-пэка. Отложить до больших данных.

### F6 [Info] Ограничения, принятые осознанно

- Напряжения: AOX не кодирует напряжение — каркас живёт на 220AC;
  380/24 появляются через заполненный Excel (AllowedControlUnitOption —
  источник пар, админка серии).
- Позиция s2 ext-кода отсутствует до появления каталога S2/стартера
  (зафиксировано в ea-signals-options-spec.md разд. 9).
- EaSlotOption THERMAL_SENSOR: PTC-варианты (P1/P2) не засеяны — в ext-кодах
  пока только T0/T1/T2 (термореле); PTC — по данным пользователя.

**Вердикт:** F1 и F2 исправить немедленно (теряют данные/однозначность кода),
F3 — вместе с ними, F4/F5 — при фазе 6. Принять после F1–F3.

---

## Ревью №8 (2026-10-18): фаза 7 — удаление legacy сигнальных моделей (212c934)

Скоуп: миграция 0060, очистка Selected/Constructor/админки/API/urls,
`price/views/ea_configurator.py`, `admin_site.py`, удаление команд и мёртвых
файлов. Проверено: grep по 10 удалённым именам во всём репо (живых ссылок
в импортах нет), миграция 0060 (корректна: RemoveField только у остающихся
моделей), `manage.py check` = 0, тесты 35 OK, зонды-скрипты на живых путях.

**Вывод:** сама миграция и внешние связи чисты (params ссылается только на
живые EaControlSignal/EaFeedbackSignal/EaCommProtocol — cross-app FK не
порваны). Но **чистка неполная**: конструктор и обе админки (Selected,
Constructor) оставлены со ссылками на удалённые поля и сейчас падают в
рантайме. `check` и 35 тестов это не ловят. Ревью **НЕ принято** — требуется
доработка F1–F7 (механика ниже).

### F1 [Критично] save() конструктора падает всегда

`ElectricActuatorConstructor.save()` → `_generate_short_description()` →
`get_description_data()` → блоки blinker/mechanical_indicator/end/way/torque
(`self.selected_blinker_option` и пр., строки 1024–1079) — поля удалены
миграцией 0060 → `AttributeError`. Зонд: падает на первой же строке.
Конструктор невозможно сохранить ни из API, ни из админки (которая и сама
не открывается — F3).

### F2 [Критично] get_available_options() → KeyError

`_OPTION_CONFIG` очищен от 5 сигнальных ключей, но циклы в
`get_available_options()` (строки 437, 483–484) всё ещё итерируют
`['selected_blinker_option', 'selected_mechanical_indicator_option']` и
`['selected_end_switches_option', 'selected_way_switches_option',
'selected_torque_switches_option']` → `KeyError: 'selected_blinker_option'`
(зонд с реальным model_line_item). Падает API-экшен
`ConstructorViewSet.options` (зонд 9).

### F3 [Критично] Админка конструктора не открывается

`ea_constructor_admin.py`: fieldsets «Индикация» и «Выключатели» ссылаются
на 5 удалённых полей; `list_display` содержит `blinker_display` /
`mechanical_indicator_display`, читающие удалённые поля; `get_queryset()` —
`select_related` удалённых полей. Зонды: форма → `FieldError` (5 неизвестных
полей), queryset → `FieldError`.

### F4 [Критично] Админка Selected не открывается

`ea_actuator_selected_admin.py` fieldsets: `selected_control_unit_option`,
`selected_mechanical_indicator_option`, `selected_blinker_option`,
`selected_end_switches_option`, `selected_way_switches_option`,
`selected_torque_switches_option` — все 6 удалены из модели. Зонд: форма →
`FieldError: Unknown field(s) ... specified for ElectricActuatorSelected`.

### F5 [Критично] ConstructorViewSet сломан целиком

`api/views_constructor.py`: `get_queryset().select_related(...)` — 5
удалённых полей → `FieldError` на любой запрос (зонд 7); `_build_from_request`/
`create` передают удалённые kwarg → AttributeError/TypeError; `update`
ставит `..._id` атрибуты на несуществующие поля; `_serialize`/`_serialize_detail`
читают `obj.selected_blinker_option` и пр. → AttributeError.

### F6 [Серьёзно] create_duplicate() конструктора

Передаёт 5 удалённых kwarg в `ElectricActuatorConstructor(...)` →
AttributeError на `self.selected_blinker_option` (зонд 2).

### F7 [Серьёзно] Дыра в тестах

35 тестов зелёные при полностью сломанном конструкторе — не покрыты:
save()/get_description_data/get_available_options конструктора, формы
админок Selected/Constructor, ConstructorViewSet. Требуются smoke-тесты на
каждый из путей F1–F5.

### F8 [Info] check не ловит такие ошибки

`manage.py check` = 0 при невалидных fieldsets и select_related — Django
не валидирует поля в fieldsets против модели. Опираться на check как на
гарантию целостности админки нельзя.

### F9 [Info] Косметика (остатки имён в документации/коде)

- `ea_model_line.py:35–37` — докстринг с ElectricWaySwitchesOption/
  ElectricControlUnitInstalledOption/ElectricBlinkerOption.
- `ea_allowed_options.py:12` — коммент про ElectricControlUnitOption.
- `params/actuator_heater_supply.py:5` — докстринг упоминает ControlUnitWiring.
- `params/feedback_signals.py:13` — докстринг «ElectricControlUnitOption.
  feedback_signal_set → FK» — неверен после фазы 7.
- `api/views_admin_items.py:187` — мёртвый ключ `'control_unit_options': []`
  в сериализации PS-матрицы.
- `ea_actuator_selected.py:575` — TODO-коммент про selected_way_switches_option.

### Позитив (подтверждено)

- Миграция 0060 корректна и применяется; данные старых таблиц не нужны
  (снапшот ea_signals_export_2026-10-18.json сохранён).
- Внешних FK из других приложений в удалённые модели нет; `params` ссылается
  только на живые модели новой схемы.
- Пре-экзист баг `ensure_all_default_options_exist` (ElectricWaySwitchesOption)
  исчез вместе с моделью; тесты серий проходят.
- Удалены 3 команды и 3 мёртвых файла; urlpatterns очищены;
  `price/views/ea_configurator.py` WaySwitches-блоки убраны.
- `selected_control_unit_option` конструктора (FK на params.ControlUnitInstalledOption)
  остался — корректный мостик до `ElectricActuatorCatalogItem`;
  `_get_option_encoding` возвращает '' для отсутствующего ключа конфига —
  graceful-деградация артикула по `{control_unit}`.

**Вердикт: НЕ принято.** Миграция и внешние связи — ок, но runtime-контур
(конструктор + обе админки + API) остался с мёртвыми ссылками на удалённые
поля. Исправить F1–F7 сейчас (чистка конструктора/админок/API + smoke-тесты),
F9 — вместе с чисткой, затем повторный прогон 35+новых тестов и зондов.

### План доработки (по итогам ревью)

1. `ea_actuator_constructor.py`: убрать 5 блоков из `get_description_data`
   (1024–1079); вычистить имена из циклов `get_available_options` (437,
   483–484); убрать kwarg из `create_duplicate` (1399–1404); проредить
   ключи в `_generate_tech_description`/`_generate_html_description`
   (1161–1162, 1226–1231, 1269–1274) — `data.get` безопасен, но ключи
   мёртвые; проверить `get_structured_data` на остатки.
2. `ea_actuator_selected_admin.py`: убрать 6 удалённых полей из fieldsets.
3. `ea_constructor_admin.py`: убрать поля из fieldsets/list_display/
   select_related; удалить blinker_display/mechanical_indicator_display.
4. `views_constructor.py`: убрать удалённые поля из select_related,
   `_build_from_request`, duplicate-filter, цикла update, `_serialize(_detail)`.
5. Тесты: smoke — save() конструктора, get_available_options с mli,
   `admin.get_form(req)()` для Selected/Constructor, сериализация
   ConstructorViewSet (list).
6. Косметика F9 (докстринги/комменты).

---

## Резолюция ревью №8 (2026-10-18, после «исправь всё»)

Все находки F1–F9 закрыты:

- **F1** — `get_description_data`: блоки blinker/mechanical/end/way/torque
  удалены; `save()` конструктора работает (smoke-тест).
- **F2** — `get_available_options`: удалённые имена убраны из циклов
  (ml-цикл и блок model_line_item-опций удалён целиком);
  `selected_control_unit_option` убран из power_supply-цикла (ключа в
  _OPTION_CONFIG нет → был бы KeyError). API `options` работает.
- **F3** — `ea_constructor_admin`: секции «Индикация»/«Выключатели» убраны,
  list_display и select_related очищены, методы blinker_display/
  mechanical_indicator_display удалены.
- **F4** — `ea_actuator_selected_admin`: 6 удалённых полей убраны из fieldsets.
- **F5** — `views_constructor.py`: select_related, `_build_from_request`,
  duplicate-фильтр, цикл update, `_serialize_detail` очищены от 5 полей.
- **F6** — `create_duplicate`: 5 kwarg удалены.
- **F7** — добавлен `Phase7LegacyRemovalSmokeTests` (7 тестов: save+описание,
  structured_data без удалённых ключей, get_available_options с mli,
  create_duplicate, обе админ-формы, viewset-сериализация).
- **F8** — зафиксировано: check не валидирует fieldsets; smoke-тесты теперь
  страхуют админки/API.
- **F9** — косметика: докстринги ea_model_line/ea_allowed_options/
  params/feedback_signals/params/actuator_heater_supply, мёртвый ключ
  `control_unit_options` в views_admin_items, TODO и отладочный print в
  ea_actuator_selected, мёртвые ветки «особого случая БУ» в
  `get_available_options` Selected.

**Дополнительно найден и исправлен пре-экзист баг:** `_set_default_option`
фильтровал по `is_default`, которого нет у `ElectricPowerSupplyOption` →
конструктор с выбранной моделью, но без напряжения, падал на save.
Добавлена проверка наличия поля `is_default` в through-модели (fallback —
первая активная запись).

**Проверено:** 42 теста OK (35 + 7 новых), `manage.py check` = 0,
`makemigrations --check` — No changes detected; глобальный grep по
удалённым именам полей (без migrations) — 0 совпадений.

Вердикт ревью №8 после доработки: **принято**.

---

## Ревью №9 (2026-10-18): none→basic, каталог 220VAC/0-10В, широкий формат выгрузки (cd35b61 + правки)

Скоуп: миграция 0062 (переименование БУ), дополнения seed_ea_signal_catalog,
wide-экспорт (`export_wide_rows`/`export_device_rows`/`write_wide_xlsx`),
команда/админка на новом формате. Проверено: live-зонды БД, ячейки выгрузок
AR21E/AR01E/AR11E, 46 тестов, `check` 0, `makemigrations --check` чист.

### Подтверждено

- **Переименование `none`→`basic`** корректно: FK матрицы/Allowed целы (по id),
  INDICATOR-строки бренда на месте (2 на basic), `CU_EXT['basic']=''` — ext-сегмент
  пустой, decode/build работают.
- **Каталог**: +13 записей без коллизий кодов (65 опций / 24 команды / 29 ОС /
  10 форм); 220VAC-пары команд и 0-10В уставки/ОС на месте.
- **Wide-формат**: AR21E 45×664; 007×220 — basic END/TORQUE SPDT std, int-o
  4-20 passive std, heater CU_CIRCUIT opt; basic×380 — вся группа 'no'
  (правило стартера). AR01E 147 строк (46 с — см. F3).
- Правило «не хардкодить опции»: NO_HEATER_CU заменён на `_cu_has_heater`
  (kind NONE/BASIC — обогревателя БУ нет), покрыто тестом.

### F1 [Серьёзно] Мусорные записи в справочниках (production-БД)

`EaSignalForm` с кодами `F1`/`F2` и `EaFeedbackSignal` `L1`/`P1` — активные
записи, созданные тестами/экспериментами против обычной БД (в тестовой БД они
не живут). Загрязняют справочники и могут всплыть в выборках/импорте.
**Предложение: удалить** (данные справочников, в выгрузку не попадают —
FB_CODES/CMD_CODES явные). Подтверди.

### F2 [Серьёзно] Роль уставки 0-10 В называется CMD_4_20MA

`CMD_POS_0_10V_ACTIVE/PASSIVE` созданы с role='CMD_4_20MA' (в choice-списке
EaControlSignal нет роли для 0-10 В). Работает, но роль врёт. Варианты:
(а) добавить role `CMD_0_10V` (AlterField-миграция); (б) переименовать роль
в нейтральную `CMD_ANALOG`. Решение за пользователем.

### F3 [Info] Производительность wide-экспорта

`_matrix_availability_map`/`export_device_rows` делают N+1
`EaSignalMatrixEntry.objects.get(pk=...)` на каждую строку резолвера.
AR01E (147 строк × 12 БУ × 2 режима) — ~46 с. Для проверки терпимо; для
полных каталогов — кэшировать entries по id (отложить до задачи импорта).

### F4 [Info] import_ea_signal_matrix несовместима с новым форматом

`read_xlsx`/`apply_import` работают со старым длинным форматом; новый файл
читается как пустой (нет колонки slot) — команда импорта сейчас бесполезна.
Импорт нового формата — отдельная задача (пользователь отложил): парсить
wide-заголовки «БУ|сигнал», std/opt/no → строки матрицы (+na для no),
пары OPEN+CLOSE заводить обеими строками (bundle в wide не выводится —
при импорте восстанавливать автоматически, как в apply_import).

### F5 [Info] Пустые ячейки vs 'no'

В wide пусто = «нет данных» (для заполнения), 'no' = «невозможно»
(недоступная пара БУ×напряжение; обогрев БУ по kind). Если AOX в проверке
проставит 'no' там, где у нас пусто — импорт должен создать na-строки
(учтено в F4).

### F6 [Info] Перегрев в двух местах — осознанно

FB_OVERHEAT_NC/SPDT остаются в основной матрице (сигналы ОС), тип датчика
(THERMAL_RELAY/PTC) — на листе device. Оси разные, не дублирование.

**Вердикт: принято.** Открыты F1 (удаление мусора — подтверждение) и
F2 (роль 0-10 В — решение); F3–F5 отложены до задачи импорта.

---

## Ревью №10 (2026-10-18): явные ext-коды, BAT/SP, CMD multi-choice, опция AD (40ff71e…75965e1)

Скоуп: переделка ext-схемы на явные коды (хэш-аналог), положение безопасности
(nc-no-fl/BAT), CMD multi-choice, опция ограничения доступа (0067), обороты
мехсчётчиков. Проверено: live-зонды всех 6 серий (build/decode), roundtrip
(вкл. multi-cmd O+R+LK и sp BAT), 47 тестов, makemigrations --check.

### Подтверждено

- ext-код полной длины (8 блоков, все позиции заполнены), дефолты явные;
  roundtrip build↔decode без предупреждений для всех серий.
- BAT выражается положением безопасности (nc-no-fl: encoding='BAT',
  ext='BAT'); ElectricBatteryOption/requires_battery удалены корректно
  (миграции 0066/0076), остатков в коде нет (кроме истории миграций).
- CMD multi-choice: слот multi_choice=True, валидация пропускает,
  конкатенация кодов в каноническом порядке; дефолт 'C0' устраняет
  неоднозначность с соседними 'N0' — decode съедает дефолт явно.
- AD-опция: справочник + через-модель БУ×вариант, basic — только NO_DEVICE;
  ext-позиция {ad} AD0/AD1; спецификация EquipmentType дополнена
  плейсхолдером {access_device} (ru/en/cn).
- Обороты мехсчётчиков проставлены на корпусах (060/080/100 — общий корпус
  AR21E060-100 = 144).

### F1 [Серьёзно, исправлено в этом ревью] AR11E дефолт sp был 'FL'

coding_rules позиции sp всегда давал дефолт 'FL' — AR11E (дефолт nc-no-fl)
терял BAT в дефолтном коде. Исправлено: дефолт позиции берётся из
ElectricSafetyPositionOption.is_default серии. Проверено: AR11E → …AD0.BAT,
остальные → …AD0.FL.

### F2 [Info, исправлено] Мёртвый код

BAT_EXT/упоминание ElectricBatteryOption в docstring ea_ext_code — удалены.

### F3 [Info] Декод multi-позиции cmd — ограничение схемы

cmd-коды конкатенируются, decode собирает коды жадно до первого не-кода.
Корректно, пока ни один код команды не является префиксом другого и не
совпадает с дефолтами соседних позиций (проверено попарно). При добавлении
новых команд это инвариант нужно тестировать (существующий тест покрывает).

### F4 [Info] Хэш карточки ЭП

Карточки нет — config_hash_fields (включая M2M матричных строк, BAT/SP,
AD, счётчики) зафиксированы в доке; реализуются с ElectricActuatorCatalogItem.
Пневмо/кабельные хэши полные (проверено ранее).

**Вердикт: принято.** F1/F2 исправлены в этом ревью; F3 — инвариант кодов
под тестами; F4 — с карточкой каталога.

---

## Ревью №11 (2026-10-18): карточка ElectricActuatorCatalogItem, инвариант multi-cmd (7b388af + правки)

Скоуп: F3 (перекодировка команд + check_code_invariants), F4 (карточка, миграция
0068). Проверено live: генерация имени/полного артикула с ext, хэш, поведение
M2M; 49 тестов; makemigrations --check.

### Подтверждено

- F3: коды команд перекодированы без префикс-конфликтов (OA…GB);
  check_code_invariants — все 6 серий чистые; roundtrip multi-cmd однозначен.
- F4: карточка генерирует имя из EquipmentType-шаблона, полный артикул
  (базовый + ext с контекстом), config_hash по 18 опциям + M2M matrix_rows;
  хэш различается по БУ и пересчитывается ресивером при изменении M2M;
  SKU синхронизируется; админка зарегистрирована.

### F1 [Серьёзно, исправлено в этом ревью] code/name не пересобирались после M2M

Ресивер core.ConfigHashMixin обновлял только config_hash — артикул и имя
оставались без сигнальной части после matrix_rows.set(). Исправлено
приёмником m2m_changed в electric_actuators/apps.py (пересбор name/
description/code через update()). Проверено: после set строк LIMIT — code
содержит E1.

### F2 [Info] Плейсхолдеры local_control/indicator/turn_counter

В _flat_data зарезервированы пустыми (заполнятся при переводе UI на
матричный выбор, фаза 6). setpoint выбирает role='CMD_4_20MA' — 0-10В
уставки (CMD_0_10V) в описание не попадут — поправить при наполнении.

### F3 [Info] Локализация шаблонов карточки

update_name/description используют RU-шаблоны EquipmentType напрямую;
*_template_i18n (en/cn) не подключаются — при локализации фронта перейти
на _resolve_template(locale) механизма TemplateMixin.

**Вердикт: принято.** F1 исправлен; F2/F3 — при фазе 6.
