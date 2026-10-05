# SESSION.md — Текущее состояние проекта

> Обновлено: 2026-10-05. Актуальные факты, механизмы и задачи. Подробности контракта
> каталогов — `template_mixin.md`, терминология/признаки карточки + правило fork —
> `CATALOG_PATTERN.md`, материализация ПП — `pa_card_pattern.md`, SKU/MBOM — `sku-mbom.md`,
> взрывозащита (Exd) — `exd-option.md`.

---

## 1. Итог сессии 2026-10-02 (карточки + SKU)

### 1.1 Карточка ПП — переименование
- `PneumaticActuatorItem` → **`PneumaticActuatorCatalogItem`** (конвенция `*CatalogItem`, пока только ПП).
- Производные: `PneumaticActuatorCatalogItemAdmin`, `...ListView/DetailView`.
- Миграция `pneumatic_actuators/0046_rename_...`.

### 1.2 origin — происхождение карточки
- Поле `origin` (choices `generated`/`manual`, default `generated`) на `PneumaticActuatorCatalogItem`.
- Админка: новая карточка вручную → `origin=manual`.
- Генератор `generate_pa_cards`: создаёт `generated`, **не трогает** `manual` (не реактивирует/не пересчитывает `code`), `--archive` только `generated`.
- Миграция `0047_..._origin`.

### 1.3 config_hash — общий миксин на всех карточках
- `core/models/config_hash.py` — **`ConfigHashMixin`**: поле `config_hash` (unique, null) +
  `compute_config_hash()` (неймспейс `app_label.model` + каноничный кортеж полей) +
  `_check_config_hash_unique()`; `_hash_part()` поддерживает FK/M2M/скаляр/JSON.
- `m2m_changed`-приёмник `config_hash_m2m_receiver` (подключён в `core/apps.py`) — пересчитывает хэш после M2M.
- Подключено к **9** карточным моделям (у каждой свой `config_hash_fields`):
  - `PneumaticActuatorCatalogItem` (10), `CableGland` (5), `DirectionValve` (16),
    `FilterRegulator` (9), `GearBox` (8), `PneumaticFitting` (6), `SensorComponent` (5, с `brand`),
    `PosiModelLineItem` (10, M2M `exd_options`), `LimitSwitchBox` (16, M2M `exd` + скаляры).
- Миграции: cable_glands 0017, solenoid_valves 0023, filter_regulator 0014, gearbox 0025,
  pneumatic_fittings 0020, pa_controls 0066 (Sensor) + 0067 (Posi+LSB).

### 1.4 Правило fork (зафиксировано в CATALOG_PATTERN.md)
- Хэш тот же, код другой → **та же SKU** (переименование `code`).
- Хэш другой → **новый продукт** → новая карточка + SKU (старая архивируется).
- Код обязан быть **инъективен** к хэшу (иначе — баг шаблона артикула).

### 1.5 hand_wheel → manual_override (только ПП)
- Through-модель `PneumaticHandWheelOption` → **`PneumaticManualOverrideOption`**, родитель `model_line` → `model_line_item`.
- `selected_hand_wheel` → `selected_manual_override` (item + constructor + legacy selected).
- Плейсхолдер `{hand_wheel}` → `{manual_override}` (реестр + шаблоны серий + `EquipmentType` fallback).
- **Data-перенос**: серия `AIR-SY` (code='AIR-SY') — все опции в каждый типоразмер; остальные — «Не установлен».
- Админка: inline ручного дублера перенесён из серии в «модель в серии» (`model_line_item` admin).
- Фронт (исходники) переведён; `ea-constructor` (ЭП) — **не трогали**.
- Миграция `0049` (RenameModel + RenameField + data-миграция).
- НЕ переименованы (общие с ЭП): справочник `params.HandWheelInstalledOption`, базовое поле `hand_wheel_option`.


### 1.8 Вес привода × ручной дублер (РЕАЛИЗОВАНО)
- **Проблема**: у кулисных AIR-SY SR вес зависит от опции ручного дублера; у остальных дублера нет. У кулисных возможны несколько кулисных блоков.
- **Принятая модель**: вес = **сумма аддитивных компонентов**: `вес_привода(body, пружины)` + `вес_дублера(body, опция)` + (будущее) `блоки × вес_блока`.
- **Решение (итоговое)**: вес дублера хранится полем `mo_weight` (Decimal, null/blank, default 0) на through-модели `PneumaticManualOverrideOption` — отдельная таблица `PneumaticManualOverrideWeight` **не создавалась**.
- Миграция `0050_pneumaticmanualoverrideoption_mo_weight_and_more` (+ `AlterField weight_spring` на `PneumaticActuatorBody`).
- `calculate_actuator_weight(body, variety, spring, manual_override_weight=None)` прибавляет вес дублера ко всем веткам с определённым базовым весом; `None` → возврат `None`.
- Хелпер `resolve_manual_override_weight(model_line_item, hand_wheel_option)` в `pa_weight.py` ищет through-строку по паре (model_line_item, опция дублера) и возвращает `mo_weight`; «Не установлен»/нет строки → `0`.
- Три вызова обновлены: `PneumaticActuatorConstructor.get_weight()` (резолв через `selected_model_line_item`), `PneumaticActuatorSelected.get_weight()` (через `selected_manual_override.mo_weight` напрямую — там FK уже на through), `PneumaticActuatorCatalogItem.calculated_weight` (резолв через `source_model_line_item`).
- **config_hash/SKU не затрагиваются** (вес — derived-значение, не идентичность).
- Админка: `mo_weight` добавлен в inline `PneumaticManualOverrideOptionInline` (`pa_model_line_item_admin.py`).
- Продолжение (хранимое поле `weight` + `manual_override_option`) — см. §3.

---

## 2. Факты (проверено в этой сессии)

- **Инъективность** (1 конфигурация = 1 код = 1 хэш), все 5 серий ПП — OK:
  серия 4 = 3036, серия 5 = 2024, серия 6 = 456, серия 11 = 141, серия 12 = 452.
- Приоритет шаблонов name/description: **серия (`model_line`) → `EquipmentType` → `{model_code}`**.
- `EquipmentType «Пневмопривод» (id=3)` в `content_type` → legacy `PneumaticActuatorModelLineItem` (НЕ исправлено, известный пункт).

---

## 3. Итог сессии 2026-10-05 (вес в карточке + мастер подбора)

### 3.1 Вес привода — материализация в карточке
- На `PneumaticActuatorCatalogItem` добавлено хранимое поле `weight` (DecimalField, null/blank) — вес **материализуется при генерации**, а не считается динамически.
- `compute_weight()` — расчёт (корпус + пружины + ручной дублер); `calculated_weight` (property) теперь читает **сохранённое** `weight`.
- `pa_item_fields.py`: плейсхолдер `{weight}` → `path: 'weight'` (хранимое поле).
- `generate_pa_cards`: `probe.weight = probe.compute_weight()` перед сохранением; вес синхронизируется и при реактивации/обновлении существующих карточек.
- Ручные карточки (`origin=manual`): вес пересчитывается в `save()` через `compute_weight()`.

### 3.2 manual_override_option — прямое поле ручного дублера
- На `PneumaticActuatorCatalogItem` добавлено поле `manual_override_option` (FK → `PneumaticManualOverrideOption`) — несёт `mo_weight` напрямую, без мостика `source_model_line_item`.
- `selected_manual_override` (базовая `params.HandWheelInstalledOption`) остаётся полем идентичности/encoding (в `config_hash_fields`).
- `save()`: если задана `manual_override_option`, базовая опция выводится из `hand_wheel_option` (до расчёта config_hash).
- Админка `pa_item_admin.py`: `manual_override_option` фильтруется по выбранному корпусу (`formfield_for_foreignkey` → `model_line_item__body_id`); если корпус не выбран — все.
- `from_constructor()` и генератор прокидывают through-опцию.

### 3.3 Миграции ПП (все применены)
- `0050` — `mo_weight` на `PneumaticManualOverrideOption` + `AlterField weight_spring` (decimal_places 2→3).
- `0051` — `weight` на `PneumaticActuatorCatalogItem`.
- `0052` — `manual_override_option` на `PneumaticActuatorCatalogItem`.
- ⚠️ Инцидент: `0051`/`0052` были созданы, но не применены → любой запрос к `PneumaticActuatorCatalogItem` падал с `OperationalError: no such column ... manual_override_option_id`. Исправлено применением миграций (`python manage.py migrate pneumatic_actuators`).

### 3.4 Мастер подбора (QuestionGraph) — фронт и контент
- Фронт `QuestionGraphFlow.vue`: кнопки «+ Страница/Ветвление» добавляли узел за экраном (`x = count*320 + 80`). Исправлено: `newPosition()` ставит узел под последним + `fitView()` после добавления.
- Фронт `QuestionGraphAdmin.vue`: у селектора «Тип оборудования» не было обработчика. Добавлен `@change` → подгружает граф типа (или дефолты code/name).
- Формат графов: плоский `type/name/params/match_values` (с 2026-08-07, коммит `0b3bf39d`). Старый `question/description/pages/branches/param_names` (до `afb2133b`) потерял описания и часть параметров при переписывании.
- Восстановлено в `load_question_graph.py` (и перезалито в БД): `description` у всех узлов; потерянные параметры:
  - БКВ (`lsb`): `signal_type_id`, `exd_id`, `contact_form_id`;
  - соленоиды (`directional-valve`): `kv_min`, `climate`;
  - ручные дублёры (`manual-override`): `min_work_torque`, `mounting_plate_top_id`, `work_temp_min`, `work_temp_max`, `climate`.
- Фитинги: `fitting_variety_id` → `equipment_type_id` — намеренное изменение 2026-08-24 (`947de6f6`), не откатывалось.

---

## 4. Осталось

- [ ] **Снэпшот документа при `POSTED`** — на паузе; решить: хранить снимок в тех же моделях или в документах.
- [ ] **Материализация карточек ПП** — `python manage.py generate_pa_cards` (~8к карточек + SKU). Блокер §14 снят (инъективность есть), вес уже материализуется в `weight` (§3.1); прогон не запускали.
- [x] **Вес × ручной дублер (§1.8 + §3)** — `mo_weight` + хранимое `weight` + `manual_override_option` + `calculate_actuator_weight` + админка.
- [x] Пересборка фронта — `vite build` + `collectstatic --clear` сделаны (пользователь).
- [ ] `manage.py test` не прогонялся (известная медленная тестовая БД).
- [ ] В корне репо — устаревшие скрипты `seed_etp.py` / `fill_etp.py` / `_qa_check.py` / `_fix_etp.py` / `_seed_etp.py` импортируют удалённый `ParameterSource` — удалить.

