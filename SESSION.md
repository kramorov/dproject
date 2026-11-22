# SESSION — 2026-11-22 (итог)

Перенос данных AUTORUN (серии **BTS / NRT / BTL**) + шести- и четырёхточечный
подбор приводов. Основные артефакты: `mig.md` (состояние/план, актуально),
`pa_quote_ru/arun.md` (§1–11 описание источника, §12 состояние переноса),
`.codewhale/handoff.md` (детальная история).

## Сделано в этой сессии

- **Справочники**: пружины `PneumaticActuatorSpringsQty` +kind (count/block)
  +spring_count, коды 13–16, блоки S1–S5, модуль `S` (линейные SR);
  дублёр `clutch` (HandWheelInstalledOption id=8); variety **LN** (id=3);
  точки `valve_data.TorquePoint` (bto…etc) и набор rotary-6; long-формат
  `BodyThrustTorqueTable` (body×pressure×spring_qty×point×value).
- **Серии/данные** (команды идемпотентны; db.sqlite3):
  - `import_autorun_series`: NRT (id=14, RP, 18 тел/34 MLI, физика из T.NTR.26.1),
    BTS (id=15, SY, 42 тела/81 MLI, блоки S1–S4, НЗ/НО).
  - `import_autorun_torque`: 1739 строк моментов (сверено с каталогами).
  - `import_autorun_btl`: BTL (id=16, LN/LINEAR, 30 тел/60 MLI, прайс ходов в
    extra_params MLI). `import_autorun_btl_thrust`: 900 строк усилий.
  - `import_valve_coefficients`: 8 типов арматуры (rotary-6).
  - `generate_pa_cards`: **561 карточка BTL** по ходам таблицы Autorun
    (stroke в config_hash_fields, миграция 0079 пересчитала хэши всех карточек).
- **Подбор**: движок `pointwise_selector.py` (DA-огибающая, SR НЗ/НО, пропуск
  отсутствующих средних точек; у линейных точки пружины читаются из строк
  рабочего давления); `process_pointwise_selection`: mode four/six, ручная
  кривая (`required_points`), ход (`stroke_mm`×запас) с фильтром `stroke_max`,
  four→только LN, six→без LN, карточки фильтруются по ходу и safety (SR);
  ответ `unit` Нм/Н. Фронт `PaEngineerSelector.vue`: 3 режима (обычный/6 точек/
  4 точки-линейные), форма 4 усилий + ход + запас, i18n ru/en/cn.
- **Модель хода**: поле `stroke` на Constructor/Selected/CatalogItem (0078),
  реестр `{stroke}` (code_path `stroke_code`), from_constructor, описания
  («Ход: … мм» только при наличии). Ход — параметр запроса, не опция.

## Канон БД (актуально)

- Серии ПП: PA(4), AIR(5), AIR-SY(6), AIR-S(11), RT(12), HGP(13), NRT(14),
  BTS(15), BTL(16). Бренд AUTORUN id=40; оборудование id=3 «Пневмопривод».
- Давление 6 бар — id=13; пружины: DA id=1, S1–S5, 05–16, модуль S id=27.
- Карточки: 5999 (ротационные) + 561 BTL = 6560.
- Канон — `db.sqlite3`; тесты на `test_db.sqlite3` (устарела — 1 skip
  коэффициентов; по решению пользователя не пересоздавать) + `--keepdb`.
- Миграции pneumatic_actuators 0065–0079, valve_data 0071–0073.

## Проверено

- Тесты pneumatic_actuators 12/12 (skipped=1); manage.py check — чисто;
  makemigrations --check — чисто; py_compile OK; npm run build OK.
- Смоуки: pointwise 6 точек (RT/NRT/PA/AIR-S, кривая 130/117/130), 4 точки
  DA/SR НЗ/НО (BTL125D запас 3770; BTL125SR запас 200; фильтр хода; карточки
  по ходу), six без BTL, four отклоняет коэффициенты, запас хода ≤0 — ошибка.
- Сверка данных: DA-моменты NRT 18/18, SR 482 точки — 0 расхождений; хэши
  карточек после 0079 — 0 несовпадений; BTL 561 карточка без дублей кодов.
- Идемпотентность всех import-команд и generate_pa_cards — повторный запуск
  не дублирует.

## Не закоммичено

- Модели/сервисы: pa_item.py, pa_item_fields.py, pa_options.py, pa_params.py,
  pa_model_line.py, pa_body.py, pa_torque.py, pa_actuator_selected.py,
  pa_actuator_constructor.py, pointwise_selector.py,
  actuator_engineer_handler.py, valve_data/models/torque_characteristics.py.
- Команды: import_autorun_series.py, import_autorun_torque.py,
  import_autorun_btl.py, import_autorun_btl_thrust.py, generate_pa_cards.py,
  valve_data/management/commands/import_valve_coefficients.py.
- Миграции: pneumatic_actuators 0065–0079, valve_data 0071–0073.
- Фронт: PaEngineerSelector.vue, locales ru/en/cn.
- docs: mig.md, pa_quote_ru/arun.md, SESSION.md, .codewhale/handoff.md.
- db.sqlite3 (данные серий/карточек).

## Что дальше

1. **Чистка данных пользователем** в админке: физика BTS/BTL (массы, габариты,
   расход), spring_count блоков S1–S5, дефолтные пружины серий, штоки NRT032/040.
2. **Перегенерация описаний** всех серий (батчами) + **полный generate_pa_cards**
   (бэклог ~11 500: NRT/BTS + новые опции PA/AIR).
3. **Ценовой механизм ПП** (вариант Б — PneumaticActuatorPrice; решение за
   пользователем) + импорт цен/наценок/дублёров; цены BTL по ходам.
4. **valveTorqueLookup** — решение: переносить таблицы момента по DN/PN или нет.
5. **Сквозная сверка** подборов с desktop-приложением.
6. Закоммитить накопленное; проверить `configurator/services/filter_engine.py`
   (bto/rto/eto product-атрибуты) и сквозной UI точечного режима.
