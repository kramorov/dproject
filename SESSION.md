# SESSION — 2026-11-18

Конфигуратор БУ (ea_control): обобщение селектора изделия + кодировки.

## Сделано в этой сессии

- **Селектор изделия → generic `subtype`**: слот-селектор помечается `slot_kind='subtype'`,
  `get_product_type_slot()` (ровно один, иначе ImproperlyConfigured),
  `resolve_product_types` (алиас `resolve_control_units`), опция `kind='product_type'`
  (было `unit`). Роут `series-units/` → `product-types/`. Front: `EaControlConfigurator`
  использует `pkg.product_type_slot`, `productTypes`.
- **Координата контекста**: опция несёт `context_coordinate` (`{param, value_id}`),
  словарь `CONTEXT_COORDINATES` в cu_package; фронт перезапрашивает пакет по ней
  (generic, вместо `CMD_WIRING`/`signal_power_id`).
- **Подсказка КВ** вынесена в `frontend/src/pages/admin/eaControlHints.js` (доменный
  модуль), рендер передаёт выбор + колбэк видимости.
- **Кодировки** (`ea_control/services/cu_code.py`):
  - системный код — структурный, единый, по полной активной структуре (без show/hide);
    шаблон `CuCodeSettings.system_code_template`; плейсхолдеры `{node:}/{slot:}/{opt:}/{slots:}`;
    фоллбэк «узел.слот.опция» через «/».
  - артикульный код — на `ControlUnit.article_code_template`/`ext_article_code_template`,
    значения `encoding`/`ext_encoding` (матрица → опция); `build_article_code_dicts` для ЭП.
  - `assemble_article` делегирует `build_system_code`.
- **Модели/миграции**: `CuCodeSettings` (синглтон, pk=1); миграции core 0027-0028,
  ea_control 0028-0029. Сначала системный шаблон был на EquipmentType + FK
  `ControlUnit.equipment_type` — отменено (противоречие со статичной схемой), заменено
  синглтоном.
- **Данные**: плейсхолдеры узлов (GEN/SNS/SMART/…), слотов и опций (акронимы из `code`,
  уникальные); `system_code_template` заполнен.
- **Фронт**: вкладка «Системные кодировки» (`EaControlSystemCodes.vue`) + вкладка
  «Кодировки» в «Редактор БУ» (`EaControlUnitsEditor.vue`); `units_view` расширен.

## Канон БД (актуально)

- 7 БУ (basic AR01 / POSI AR01 / basic AR21 / posi-4-20 / INT/N / INT/L / INT/O) +
  TR-AR01 (добавлен ранее пользователем).
- ~115 слотов (растёт), ~150 правил; слот-селектор `control_unit` = `slot_kind=subtype`.
- Канон — `db.sqlite3` (коммитится); тесты — на копии `test_db.sqlite3`.

## Проверено

- `python manage.py check` — no issues.
- `python manage.py test ea_control.tests` — 36 OK (валидация + CuProductTypeTests).
- `npm run build` — успешно.
- Смок: `build_system_code`/`build_codes`/`build_article_code_dicts` работают;
  PATCH `/sections/`, `/slot-options/` — 200.

## Не закоммичено

- backend: ea_control (api/urls/models/services/tests), core (equipment_type.py + миграция),
  db.sqlite3.
- frontend: EaControlConfigurator.vue, CuEmulationPage.vue, EaControlAdminPage.vue,
  EaControlUnitsEditor.vue, eaControlHints.js (new), EaControlSystemCodes.vue (new).
- миграции: core/0027_equipmenttype_system_code_template.py,
  core/0028_remove_equipmenttype_system_code_template.py,
  ea_control/0028_controlunit_article_code_template_and_more.py,
  ea_control/0029_cucodesettings_remove_controlunit_equipment_type.py.

## Что дальше

1. Закоммитить накопленное.
2. Ревизия канон-ожиданий `tests_services`/`tests_description`/`tests_bindings`
   (падают на дрейфе данных: 115 слотов vs 45, `basic AR21` vs `BASIC-AR21`,
   `POSITION_FEEDBACK` vs `FB_POSITION`, списки привязок) — вернёт полный прогон в зелёный.
3. Артикульные кодировки БУ: заполнить `article_code_template`/`ext_article_code_template`
   на ControlUnit и `encoding`/`ext_encoding` опций из legacy-каталога (пока пусто).
4. (Опц.) короткие плейсхолдеры — уже сгенерированы акронимами; при желании перегенерить
   по другому правилу (2–3 буквы на слово).
