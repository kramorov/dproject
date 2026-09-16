# SESSION.md — Текущее состояние проекта

> Обновлено: 2026-09-16. История изменений удалена; здесь — только актуальные факты,
> механизмы и задачи. Детали контракта каталогов — в `template_mixin.md` (корень репо),
> паттерн фильтрации каталогов — в `CATALOG_PATTERN.md`, взрывозащита (Exd) — в `exd-option.md`.

---

## 1. Каталоги: единый контракт (TemplateMixin)

**Механизм** (код: `core/models/mixins.py` — класс `TemplateMixin`):

- Шаблоны `name_template` / `description_template` живут на **серии** (model_line).
- **Артикул** (item) определяет `_get_data_dict()` — словарь «плейсхолдер → путь к характеристике».
- Генерация name/description происходит в `save()` (флаг `skip_auto_generate=True` отключает).
- Title: цепочка `model_line.title_template` (`_get_title_template_source`) → `EquipmentType.title_template` → `{model_code}`.
- SKU создаётся из артикула через `SKUMixin.sync_sku()` (в `save()` после `super().save()`).
- **Реестр полей (2026-09-07 → упрощён 2026-09-14)**: `TEMPLATE_FIELDS` + `TemplateFieldSpec`
  (`core/models/template_fields.py`) — единый источник правды для `_get_data_dict`,
  `_get_code_data_dict`, `_get_template_vars`; теперь только `key`/`placeholder`/`path`/
  `name_path`/`code_path`/`resolver` (метаданные `label`/`unit`/`type`/`group`/`order` убраны).
  Составы словарей — списками ключей (`NAME/CODE/VARS_FIELD_KEYS`; `SPEC_FIELD_KEYS` и
  `SPEC_GROUP_TITLES` удалены). Сериализация — `CatalogSerializerMixin`
  (`core/models/catalog_serializer.py`). Подробно: `template_mixin.md` §7.
  Пилоты: `PosiModelLineItem`, `LimitSwitchBox` (списковые поля `signals`/`sensors` → JSON).
  Переведены на реестр 2026-09-07: `DirectionValve`, `FilterRegulator`, `GearBox`,
  `PneumaticFitting`, `PneumaticActuatorItem` (с `CODE_FIELD_KEYS`/`code_path`).
  Реестры — в `*_fields.py` рядом с моделями. На ручном `_get_data_dict()` — `SensorComponent`.
- **Спецификация/заголовок (2026-09-14)**: спецификация — вложенный JSON `spec_template`
  (приоритет `model_line.spec_template` → `EquipmentType.spec_template` → фоллбэк
  `{model_code}`); формат `{группа: {подпись: ключ_поля}}`. `_get_spec_sections()` отдаёт
  `{группа: {подпись: значение}}`; секция спеки в `to_dict()` — `data` (вместо `groups`).
  Фронт: `TabSpecs.vue` рендерит `data` напрямую (без meta/order). `get_field_meta()`
  → deprecated (`{}`); `to_values_dict()['values']` = `template_vars`. У `EquipmentType`
  добавлен `spec_template` (core 0014); в админке серии/типа — поля `title_template`/`spec_template`.

**Модели на контракте** (9 активных): `DirectionValve`, `LimitSwitchBox`, `PosiModelLineItem`,
`FilterRegulator`, `GearBox`, `PneumaticFitting`, `PneumaticActuatorItem`, `CableGland`,
`SensorComponent` (шаблон с опции `variety`). У `SensorComponent` — ручной `_get_data_dict`;
у остальных словари выводятся из `TEMPLATE_FIELDS`. `CableGland` — encodings через
through-опции (`code_path` → `*_encoding`-свойства артикула).

**Legacy** (не удалять без подтверждения): `PneumaticActuatorModelLineItem` — миксин снят,
`to_dict` отдаёт хранимые name/description; `PneumaticActuatorSelected`,
`PneumaticActuatorConstructor`, `ConstructorViewSet` — работают (конструктор = форма).

**Инфраструктура**:

- Массовая перегенерация: `python manage.py regenerate_catalog_descriptions [--model app.Model] [--inactive]`.
- Админка серий: `TemplatePlaceholdersAdminMixin` (справочник плейсхолдеров из `_get_data_dict()`
  модели-артикула; клик вставляет в поле шаблона; «Скопировать все»). Опция
  `template_placeholders_fieldset = _('Шаблоны')` встраивает блок в конкретный fieldset.
  Подключено: DV, LSB, Posi, FR, GB, PF, PA.
- Админка артикулов: `AdminCopyMixin` + `actions = ['copy_selected_objects']`; `sku` — readonly.

---

## 2. Пневмоприводы

- **`PneumaticActuatorItem`** — эталонная модель каталога: опции прямыми FK
  (`selected_safety_position`, `selected_springs_qty`, `selected_temperature`, `selected_ip`,
  `selected_exd`, `selected_body_coating`, `selected_hand_wheel`), артикул автогенерируется
  из `PneumaticActuatorModelLine.model_item_code_template`, name/description — из шаблонов
  серии, SKU — из модели. Переходный мостик `source_model_line_item` (для encodings
  item-уровневых опций; удалить при полном переносе).
- **Конструктор = форма**: `POST /api/pneumatic_actuators/constructor/` сохраняет черновик
  И материализует `PneumaticActuatorItem` + SKU (в ответе — `item`, `sku`).
  `create-sku` endpoint — тот же путь. Дедуп SKU — по итоговому коду
  (`sku_service.get_or_create_sku`).
- **REST-каталог**: `GET /api/pneumatic_actuators/items/` (?model_line_id, ?variety),
  `GET /api/pneumatic_actuators/items/<id>/`.
- **Подбор**: selector принимает `torque_without_safety` + `safety_factor`
  (нормализация в `_normalize_selection_params`: момент с запасом, 6 бар по умолчанию, DA).
- **Фронт**: `pa-catalog` (каталог + подбор + createSku), `pa-constructor` (форма;
  ключи опций маппятся в `buildSkuOptionsPayload`, save показывает SKU). Сборка `vite build` — ОК.

---

## 3. Позиционеры

- Опции позиционеров выводятся по `sorting_order` (2026-09-01): Meta.ordering
  всех through-опций серии и справочника LeverOption — `['sorting_order', ...]`
  (без is_default/acting_type впереди).
- **Тип действия — прямой FK на серии** (`PosiModelLine.acting_type`, миграция 0056;
  through-модель PosiActingTypeOption удалена, данные перенесены). У модели —
  собственный FK-переопределение, fallback через свойство `get_acting_type`;
  encoding для артикула — code справочника (свой или от серии).
- **SmartCapabilitySet привязан к through-опции «Профиль сигналов»**
  (`PosiSignalProfileOption.smart_capability_set`); уникальность — **серия + профиль + набор**.
  У модели (`PosiModelLineItem.smart_capability_set`) — переопределение; fallback:
  модель → опция профиля (`get_smart_capability_set`).
- В `_get_data_dict` позиционера есть `{smart_capabilities}`
  (свойство `get_smart_capabilities_display`).
- **Шаблон артикула**: `PosiModelLine.model_item_code_template` (fieldset «Шаблоны»).
  Плейсхолдеры: `{model_code}` (код серии), `{acting_type}`, `{body_connection}`, `{lever}`,
  `{temperature}` (дефолт серии), `{signal_profile}`, `{alarm}`, `{exd}`, `{ip}`, `{smart}`
  (encodings — из through-опций). `save()` автозаполняет `code`.
- Данные: серия TS900 (id 1) — набор id 5 перенесён на 4 опции профилей (миграция 0053).

---

## 4. Админка (группировка)

- `djangoProject1/admin_site.py`: разделы в `ADMIN_BLOCKS`, привязка моделей —
  `ADMIN_MODEL_BLOCK` `(app_label, ObjectName) → id раздела`. Модель без записи попадает
  в раздел «Новые модели». При старте — warning о ключах, отсутствующих в реестре.

---

## 5. Факты БД

- Профиль сигналов «Нет сигнала» (code `NONE`, id 46); роль сигнала `OUTPUT_ALARM_2` (id 25).
- `PosiExdOption` (миграция 0051): model_line + encoding + M2M `exd_options`; «Общепром» —
  отдельная строка с пустым M2M.
- Наборы смарт-возможностей: сиды `SMART_CAPABILITY_SEED` (posi_options.py), отдельный
  набор «Нет смарт возможностей» (`SMART-NONE`).
- Миграции этой сессии применены: pneumatic_actuators 0036–0037; pa_controls 0053–0055.

---

## 6. Известные ограничения

- **`manage.py test` не строит тестовую БД**: FK-mismatch в миграциях electric_actuators
  (`electricactuatorselected → cableglandholessetbodyoption`). Проверки — смоук-скриптами
  с откатом данных. Тесты `pneumatic_actuators/tests.py` написаны, но не исполняются.
- **NULL-семантика unique_together** (`PosiSignalProfileOption`): пустые наборы считаются
  разными — при необходимости добавить условный `UniqueConstraint`.
- **Постоянный `model_item_code_template`** (без плейсхолдеров опций) даёт одну SKU на все
  конфигурации серии — шаблон обязан различать конфигурации.
- `item.sku` в памяти сразу после `save()` — `None` (SKUMixin обновляет связь через
  queryset) — стандартно, использовать `refresh_from_db()`.
- **Каталоги на едином сериализаторе** (2026-09-07): `to_dict`/`to_values_dict` пяти
  каталогов теперь из `CatalogSerializerMixin` — форма API изменилась (особенно PF:
  вложенные объекты карточки → стандартная схема `template_vars`+секции); фронт
  фитингов/глушителей/заглушек ждёт адаптации. Списки GB/PF стали тяжелее
  (полный `to_dict` на элемент); метки реестров — без gettext (мультиязычность —
  отдельная задача).
- **Устаревшие имена DV в БД**: шаблон серии RP в БД без `{brand}`, имена записей —
  старые (с брендом); перегенерация `regenerate_catalog_descriptions` их обновит —
  пока не запускалась (кроме FR: 0 изменений).
- `ai/ai` (JSON-артефакт лога сессий) отслеживается git → мусорный diff; желательно
  добавить в `.gitignore`.
- **Ловушка makemigrations + QuestionGraph** (подробно: `sw.md` §0): модель регистрируется
  только через импорт URLconf; `call_command('makemigrations')` из шелла (по умолчанию
  `skip_checks=True`) «не видит» модель и генерирует `DeleteModel` — так появилась
  `0012_delete_questiongraph` (2026-09-08). Макмиграции запускать только через `manage.py`.

---

## 7. Бэклог (актуальные задачи)

1. **Расшифровка кода артикула → характеристики**: ввод кода → конфигуратор с
   проставленными (распознанными) опциями; разбор по `model_item_code_template` серии
   + encodings through-опций (у разных серий наборы отличаются).
2. **Расширить реестры плейсхолдеров**: PF — выполнено 2026-09-07 (`body_material`,
   `pipe_material`, `pressure_min/max`, `temp_min/max` добавлены в реестр). Осталось:
   LSB — `is_pneumatic`, `has_namur_interface`, `visual_indicator_type`;
   FR — `ip`, `has_shut_off_valve`; PA item — характеристики корпуса,
   `model_line_name/code`; GB — `body_material`.
3. **Фронт**: сверстать список/карточки для `paCatalog.items` (REST готов).
4. **P8-остаток**: перенос логики Selected/Constructor в сервисы; удаление Selected,
   Constructor, legacy `PneumaticActuatorModelLineItem` и мостика `source_model_line_item` —
   **после подтверждения**.
5. `ai/ai` в `.gitignore` / перестать отслеживать.
6. Коммит контрольной точки текущего состояния (15 изменённых + 4 новых файла:
   CableType/граф/QuickSelect; `db.sqlite3` изменён).
7. **Согласовать реестр полей с assy.md/cg.md**: проанализировать, как новый
   `TEMPLATE_FIELDS` + `TemplateFieldSpec` (`key/placeholder/path/name_path/code_path/
   resolver/label/unit/type/order/group`) и `CatalogSerializerMixin` (`to_dict`/
   `to_values_dict`/`_get_spec_sections`) соотносятся с понятиями `EquipmentType`/
   `CompositionGroup` из `cg.md` и сборочными требованиями/позициями из `assy.md`.
   Цель: единая JSON-схема поля (для MCP) как мост между карточкой каталога и структурой
   сборки/позиций; определить, какие `key`/`group`/`type` должны быть общими (EquipmentType)
   и как списковые поля (`signals`/`sensors`) лягут в состав сборки. Результат — правки
   реестра и/или `template_mixin.md`.
8. **Закрыто 2026-09-09 — восстановлением QuestionGraph** (было: фикс 500 на
   `/api/core/catalog-wizard/<code>/`): применена `core/migrations/0013_questiongraph.py`
   (CreateModel после `0012`), `load_question_graph` пересоздал 5 графов
   (`pneumatic_fittings`, `lsb`, `directional-valve`, `fr`, `manual-override`);
   адаптер снова отдаёт `type: 'graph'`, 500 ушёл, `makemigrations --check` чистый.
   Подробности и ловушка makemigrations: `sw.md` §0.
9. ~~Полная зачистка QuestionGraph~~ — **отменено 2026-09-09**: QuestionGraph восстановлен
   (см. п. 8) и остаётся основным мастером; плоский `SelectionWizard` — fallback.
   Зачем нужен граф и где используется: `sw.md` §0.

## 8. Кабельные вводы (cable_glands) — артикул на through-опциях + конструктор

**Статус (2026-09-15): артикул на through-строках; конструктор; каталог REST;**
**справочник CableType вместо булевых флагов серии; ParameterRule для ip/exd/temp;**
**графовый мастер (6-й граф `cable-gland`) + быстрый подбор на фронте;**
**миграции применены по cable_glands 0016 и core 0016; `makemigrations --check` — No changes.**

### Сессия 2026-09-15: CableType + ParameterRule + мастер подбора

- **Справочник `CableType`** (`cable_glands/models/cg_dicts.py`, миграция `0015_cabletype`):
  поля `name/code/description/sorting_order/is_active` + булевы атрибуты записи
  (`for_armored_cable`/`for_metal_sleeve_cable`/`for_pipelines_cable` — сохраняют семантику
  на будущее). Админка `CableTypeAdmin` (`admin/cg_dicts_admin.py`).
- **FK `cable_type` на `CableGlandModelLine`** вместо трёх булевых полей (поля удалены).
  Data-миграция `0016_remove_cableglandmodelline_for_armored_cable_and_more`: 4 записи
  («Под небронированный кабель», «… в металлорукаве», «Под бронированный кабель»,
  «… в металлорукаве»; codes unarmored/unarmored_ms/armored/armored_ms) + перенос всех
  8 серий; reverse написан (не прогонялся).
- **Плейсхолдер `{cable_types}`** → `get_applicable_cable_types_display` теперь отдаёт
  `name` из CableType (раньше собирал строку из флагов).
- **ParameterRule** (`catalog/filter_defs.py`): `fd_ip→'ip'` (subset «не хуже»),
  `fd_exd→'exd'` (hierarchy; для каталогового пути декоративен — fallback на
  EXD_COMPATIBLE, как у БКВ), `fd_temp_min/max→'temperature_min/max'` (directional).
  Три boolean fd заменены на `fd_cable_type` (`cable_type_id`, `model_line__cable_type`, EXACT).
- **config/quickselect**: `fd_cable_type` в list/engineer/quickselect (в quickselect — без
  default, чтобы автовыбор не занулял серии); `views_quickselect.py` — чипс `cable_type_id`.
- **`select_related`**: `model_line__cable_type` добавлен в `CABLE_GLAND_CONFIG` и в
  админку серий (иначе N+1 на сериализации).
- **Мастер подбора**: в `load_question_graph.py` добавлен 6-й граф `code='cable-gland'`
  (ET 12, «Подбор кабельных вводов»): `page_cable_type` (cable_type_id) →
  `page_thread` (thread_id, body_material_id) → `page_protection` (ip_id, exd_id),
  линейные рёбра. Температуры в шагах нет — у всех 8 серий -60…+130.
- **`content_type` ET 12**: data-миграция `core/0015_cablegland_content_type` →
  `cable_glands.cablegland` (без неё опции/результаты графового мастера пустые).
- **core/0016_alter_equipmenttype_spec_template** — догенерён предсуществующий долг
  (только help_text у `spec_template`; на БД не влияет). После этого
  `makemigrations --check` по всему репо — No changes.
- **Фронт**: `apps/cable-gland-catalog/App.vue` — графовый мастер по паттерну БКВ
  (`useCatalogWizard('cable-gland')` + `QuestionGraphWizard`, page `'graph'`, fallback на
  плоский WizardSelection), подпись чипса `cable_type_id:'Тип кабеля'`.
  `shared/components/catalog/QuickSelect.vue` — чипсы серий из `api.getSections()`
  (если метод есть) с fallback на `api.list` (иначе у КВ видны только 2/8 серий из-за
  серверного капа 200 записей).
- **Данные**: 1042 артикула, 8 серий (КНК, КБУ, КБУ-МР, КМР — BLOCK; BA, BAМр, BН, BНМр —
  Нордэкс). Все серии: temp -60…+130. «Под трубу» — у всех серий флаг был 0.
- **Проверено смоук-скриптами** (Django Client): catalog-wizard → type graph; опции
  entry — 4 названия; advance 1→2→3 со скоупом; results: бронированный 210,
  небронированный 138, бронированный в МР 338; quickselect — чипс cable_type_id с count;
  `vite build` — без ошибок (12.6s).

### Иерархия (3 уровня)

- **CableGlandModelLine** — серия (шаблоны name/description/model_item_code_template,
  equipment_type, ip, бренд/производитель, флаги кабеля, температуры). Взрывозащита —
  through-модель **CableGlandExdOption** (`BaseM2MExdThroughOption`: кодировка + M2M
  `exd_options`, parent `model_line`). Материал — through-модель
  **CableGlandBodyMaterialOption** (`BaseThroughOption`: `model_line` + `body_material`
  + `encoding`). Обе inline в админке серии.
- **CableGlandBody** — корпус (диапазон обжимаемого кабеля `cable_diameter_inner_min/max`,
  длина резьбы). Резьбы — through-модель **CableGlandThreadOption**
  (`ThreadSizeThroughOption`: `cable_gland_body` + `thread_size` + `encoding`,
  `unique_together` body/thread_size; inline в админке корпуса).
- **CableGlandModelLineItem** — «модель в серии» (body + metal_sleeve_body + weight +
  `cable_diameter_outer_min/max`). TemplateMixin НЕ наследует.
- **CableGland** (`cg_actual.py`) — артикул каталога (`TemplateMixin, CatalogSerializerMixin,
  SmartCatalogMixin, CopyMixin, ImageGalleryMixin, TechDocMixin, SKUMixin`).
  Прямые FK на through-строки: `thread_option`, `body_material_option`, `exd_option`
  (nullable, SET_NULL); `model_line_item` (корпус/вес/МР) + `model_line` (денормализуется
  в save). Старые FK `thread`→ThreadSize и `body_material` **удалены** (миграции 0008–0010
  с переносом данных). encoding читается напрямую из строк: свойства `thread_encoding`,
  `body_material_encoding`, `exd_encoding` (fallback exd — дефолт серии).
  `code` — `unique=True`, автогенерируется из `model_line.model_item_code_template`.

### Правила артикула (cg_actual.py)

- `_validate_option_consistency()` — инварианты (резьба↔корпус, материал/exd↔серия);
  вызывается в `clean()` И в `save()`.
- **Дедупликация в save()**: сочетание (model_line_item + thread_option +
  body_material_option + exd_option) — идентичность артикула; при создании дубля
  патчится существующая строка (`_get_duplicate` + перевод `_state.adding` в update).
- `save()` → `sync_sku()` (SKUMixin, как в solenoid_valves/gearbox).
- `_generate_fallback_code` = model_line_item.code + thread_encoding + body_material_encoding.

### Реестр (cg_item_fields.py)

- `{model_code}` → code_path `model_line_item__code`; `{size}` удалён.
- `{thread}` → path `thread_option__thread_size__name`, code_path `thread_encoding`.
- `{body_material}` → code_path `body_material_encoding`.
- `{exd}` → path `get_exd_display` (теперь из `name` опций, не `code`), code_path `exd_encoding`.
- `{exd_short}` → path `get_exd_short_list` (короткий вид «Ex db / Ex ta / …», паттерн позиционеров).
- `{flags}` заменён на `{cable_types}` (path `get_applicable_cable_types_display`).
- `{cable_diameter_outer}` → `get_outer_cable_diameter_display`.
- Диаметры/МР/корпус (2026-09-11): `{metal_sleeve_body_code}`,
  `{metal_sleeve_inner}`/`{metal_sleeve_outer}` (сырые Decimal), `{metal_sleeve_range}`
  (path `get_metal_sleeve_range_display` — диапазон с `rstrip('0').rstrip('.')`),
  `{metal_sleeve}` (список металлорукавов через `get_metal_sleeve_display`),
  `{body_code}` (код корпуса). Все при пустом `model_line_item.metal_sleeve_body` → `''`.
- `{extra_params}` (2026-09-11) → path `get_extra_params` (JSON `model_line.extra_params`
  в строку «ключ: значение; …»), доступен в NAME/VARS/SPEC.

### Конструктор (новый, 2026-09-10)

- Модель **CableGlandConstructor** (`models/cg_constructor.py`): форма с
  `selected_model_line` / `selected_model_line_item` / `selected_thread_option` /
  `selected_body_material_option` / `selected_exd_option` (прямые FK на through-строки).
  Методы: `get_available_options`, `_ensure_valid_options`, `build_preview_item`
  (временный CableGland → генерация code/name/description), `materialize`
  (get_or_create CableGland+SKU по коду), `save` (валидация → генерация).
- API **CableGlandConstructorViewSet** (`api/views_constructor.py`), роут
  `api/cable-glands/constructor/` (`cable_glands/urls.py`, подключён в `djangoProject1/urls.py`).
  Эндпоинты: CRUD + `model-lines/`, `model-lines/<id>/items/`, `options/`
  (?model_line & model_line_item), `preview/`. `required_section='configurator_cg'`.
- `object_registry.py`: `configurator.cg`, `catalog.cg`. Админка `CableGlandConstructorAdmin`.
- Фронт: `frontend/src/apps/cg-constructor/` (App.vue, api.js, main.js, index.html),
  страница `pages/admin/CgConstructorPage.vue`, маршрут `/admin/cg-constructor`
  (section `configurator_cg`), пункт меню «Конфигуратор Кабельных вводов» в TopMenu.vue
  (раздел «Конфигураторы»), `cgConstructor` в `shared/endpoints.js`, entry в `vite.config.js`.

### Каталог для фронта (новый, 2026-09-11)

- Пакет `cable_glands/catalog/`: `filter_defs.py` (15 фильтров), `config.py`
  (`CABLE_GLAND_CONFIG`), views `list/detail/filters/engineer/engineer_filters/
  quickselect/meta/sections`. Паттерн — `solenoid_valves/catalog/`.
- Фильтры: серия, бренд, резьба (`thread_option__thread_size`), материал корпуса
  (`body_material_option__body_material`), exd (EXD_COMPATIBLE через
  `exd_option__exd_options`), IP (IP_RANK через `model_line__ip`), диаметры
  (числовые «от/до»: `gte/lte`), температура («от/до» + `fd_climate` =
  `CLIMATE_CASCADE`, как в БКВ), булевы флаги серии (бронированный/металлорукав/
  трубопровод, `FilterType.BOOLEAN` + CHOICES «Да/Нет»).
- `views_sections.py` — `/api/cable-glands/sections/` (серии со счётчиками/фото);
  отдельный эндпоинт нужен, т.к. fallback фронта на `list({limit: 1000})`
  серверно режется до 200 записей (при 972 артикулах терялись бы серии).
- Мастер подбора (Selection Wizard): `CableGland` зарегистрирован в
  `core/wizard_filter_registry.py` → `cable_glands.catalog.filter_defs`.
- Фронт: `frontend/src/apps/cable-gland-catalog/` (App.vue, api.js, main.js,
  index.html, README.md) + страница `pages/catalog/CableGlandPage.vue` (обёртка
  App.vue), маршрут `/catalog/cable-glands` в `router/index.js` (был
  PlaceholderPage), `cableGlands` в `shared/endpoints.js`, entry
  `cable-gland-catalog` в `vite.config.js`. `equipment_type_id=12`, `eqCode='cable-gland'`.
- `core/views.py`: добавлена ветка `FilterType.MAX` в
  `BaseQuickSelectView._get_filter_options` (чипсы «от» в быстром подборе).
- Фронт-компоненты `EngineerFilterBar.vue`/`FilterSidebar.vue`: числовой `<input>`
  для `filter_type` `gte/lte` (диаметры), `ClimateFilter` для `climate_cascade`.

### Генерация артикулов (команда, 2026-09-11)

- `cable_glands/management/commands/generate_cable_gland_combinations.py`:
  перебирает thread × body_material × exd для всех серий бренда БЛОК/BLOCK
  (опции `--brand`, `--dry-run`). Дедуп: сочетание (model_line_item + 3 опции)
  + fallback по `code` (подхват legacy-записей без опций). Перегенерирует
  name/code/description из шаблонов + синхронизирует SKU (и `SKU.code`, если
  код артикула поменялся). Результат: **972 артикула** (971 создан, 1 обновлён —
  legacy `id=10 «20s16 КНК»`), у всех — SKU и опции.

### Админка артикула (2026-09-11)

- `cg_actual_admin.py`: добавлены фильтры по диаметру (внутр./внеш. «от/до»,
  кастомные `SimpleListFilter` с `gte`/`lte`) и булевы фильтры серии
  (`model_line__for_armored_cable`, `for_metal_sleeve_cable`, `for_pipelines_cable`).

### Миграции (все применены)

- `0007_fix_model_line_templates` — данные: `{flags}`→`{cable_types}`, удалён `{size}`.
- `0008` — AddField `thread_option`/`body_material_option`/`exd_option` (nullable).
- `0009` — data: перенос `thread`/`body_material` → through-строки (`QuerySet.update()`,
  создание недостающих строк с encoding из кода справочника; без побочной генерации).
- `0010` — RemoveField `thread`/`body_material`.
- `0011` — CreateModel `CableGlandConstructor`.
- `0012` — AddField `title_template`/`spec_template` в `CableGlandModelLine` (2026-09-14).
- `0013`/`0014` — промежуточные (вкл. `0014_populate_cableglandmodelline_ip_m2m`).
- `0015_cabletype` — CreateModel `CableType` (2026-09-15).
- `0016_remove_cableglandmodelline_for_armored_cable_and_more` — AddField `cable_type`
  (FK) + RunPython (4 записи справочника, перенос флагов 8 серий) + RemoveField трёх
  булевых полей (2026-09-15).
- core: `0015_cablegland_content_type` (data: ET 12 → content_type), `0016_alter_equipmenttype_spec_template` (help_text).

### Исправлено в этой сессии

- `get_outer_cable_diameter_display` / `get_outer_max_cable_diameter_display` —
  AttributeError из-за обращения к несуществующим полям (inner на MLI, outer на Body).
- `get_applicable_cable_types_display` — `', '.join(str(p) ...)` (ленивый перевод `__proxy__`);
  2026-09-15 переписан: отдаёт `name` из справочника `CableType` (флаги удалены).
- API конструктора — широкий `except ObjectDoesNotExist` (был узкий → 500).
- Удалена осиротевшая SKU (код `КБУ-МР G-1_4 BR`) после смены кода артикула.

### Остаток / риски

- Фронт собран `vite build` 2026-09-15 (12.6s, без ошибок). Браузерная проверка вкладок
  «Быстрый подбор»/«Мастер подбора» кабельных вводов и регресс тех же вкладок у
  БКВ/соленоидных (общий QuickSelect.vue менялся) — остались на пользователя
  (серверы останавливались вручную).
- Типа кабеля «Под трубу» в справочнике нет (у всех 8 серий флаг был 0) — добавить
  запись, когда появятся данные; фильтр `fd_cable_type` и мастер готовы к этому.
- AI-подбор кабельных вводов не настроен: нет `ParameterBinding` для cable-gland и пусты
  AI-поля ET 12 (`param_semantics`, `filter_endpoint`).
- Дедупликация артикула — на уровне приложения (гонка при параллельной записи возможна);
  жёсткого `UniqueConstraint` нет (NULL-семантика на SQLite).
- Секция прав `configurator_cg` в SiteSection не создана (суперюзер работает).
- `sync_sku()` не переписывает `SKU.code` при смене кода артикула; в команде генерации
  есть обход `_sync_sku_code`, в общем `save()` — нет (осиротевшие SKU при переименовании).
- У серии `КБУ` (ml 20) не было `model_item_code_template` → fallback-код с точками
  (`20 КБУ.M25x1,5.Ni`); пользователь исправил шаблон — перепроверить генерацию кодов КБУ.
- Диаметровые фильтры (`MIN/MAX`) входят в `SPLITTABLE_TYPES` → при `show_compatible=true`
  могут стать split-фильтром (классификация exact/compatible по числу) — косметика.
- `QuickSelect.vue` при `brandId` + `getSections()` игнорирует скроупинг по бренду
  (sections не принимает brand_id) — неактуально, пока ни один каталог не передаёт brandId.

---

## 9. Как продолжить с другой машины

- `git pull`/переключение ветки; зависимости не менялись.
- Миграции применены (`manage.py migrate` — no-op); dev-БД — `db.sqlite3`.
  cable_glands: применены до `0016_remove_cableglandmodelline_for_armored_cable_and_more`
  (вкл. `0015_cabletype`); core: до `0016_alter_equipmenttype_spec_template`
  (вкл. `0015_cablegland_content_type`). Данные — **1042 артикула CableGland, 8 серий**
  (BLOCK + Нордэкс), справочник CableType — 4 записи; у всех артикулов SKU и опции.
  `makemigrations --check` по всему репо — No changes.
- Каталог кабельных вводов: бэкенд `cable_glands/catalog/` + эндпоинты
  `/api/cable-glands/catalog|filters|engineer|quickselect|meta|sections/`;
  фронт `frontend/src/apps/cable-gland-catalog/` + `/catalog/cable-glands` в SPA-роутере.
- QuestionGraph: сид `manage.py load_question_graph` (пересоздаёт **6** графов, включая
  `cable-gland`). ET 12 (cable-gland) имеет content_type (data-миграция core/0015).
- Фронт: `npm --prefix frontend run build` — собран 2026-09-15 без ошибок.
- Проверки: `manage.py check` + смоук-скрипты через Django Client (тест-БД не работает, см. п. 6).
- Документация контракта: `template_mixin.md`; фильтрация — `CATALOG_PATTERN.md`.
- Мастер подбора (Selection Wizard) для CableGland зарегистрирован в `core/wizard_filter_registry.py`.
- **Остаток сессии 2026-09-15**: (1) браузерный проход вкладок «Быстрый подбор»/«Мастер»
  кабельных вводов + регресс БКВ/соленоидных; (2) коммит (15 изменённых + 4 новых файла,
  `db.sqlite3` изменён); (3) TODO фазы 5: ParameterBinding/AI-поля для cable-gland,
  запись CableType «Под трубу» при появлении данных, привязка марок кабеля к CableType.

---

## 10. Сессия 2026-09-16 — глобальный поиск, КП, цена, быстрый подбор КВ

### Глобальный поиск по артикулу (SKU)

- Бэкенд `sku/api/search.py`:
  - `SKUSearchView` — `GET /api/admin/sku/search/?q=...` (AllowAny), ищет по `SKU.code`
    без учёта регистра; для кириллицы — casefold-фоллбэк (SQLite `LIKE` регистронезависим
    только для ASCII). До 10 результатов + `source_content_type`/`source_object_id`.
  - `SKUModelDetailView` — `GET /api/admin/sku/model-detail/?sku_id=...` → `to_dict()` + price + schema;
    `to_dict()`/`get_display_price` обёрнуты в try/except (аккуратный 500 при сбое сериализации).
- `sku/urls.py`: `search/`, `model-detail/` (под `/api/admin/sku/`).
- Фронт: `components/header/GlobalSearch.vue` (в шапке, все страницы; дебаунс 300 мс,
  выпадающий список, подсветка по `@mouseenter`) + страница `/sku/:id`
  (`pages/SkuProductPage.vue`) + роут в `router/index.js`.

### Модуль `commercial` — КП (quotation) из корзины

- Отдельное приложение `commercial/` (`CommercialConfig`, в INSTALLED_APPS).
- `GET /api/commercial/quotation/<uuid:cart_id>/` (`CartQuotationView`) → `.docx`
  (attachment `Quotation_<hex>.docx`).
- `services/quotation.py::build_cart_quotation` — таблица (№ подпункта/Артикул/Описание/
  Количество/Цена/Сумма + строка «Итого») + спецификации по уникальным SKU (дедуп по `sku_id`).
- `services/numbering.py::generate_quotation_number` — `RequestNumberCounter` (компания+
  пользователь) + `UserParameter` `quotation_number_template` (дефолт
  `КП-{year}-{company_seq}-{user_seq}`); фоллбэк `DocumentNumerator` (префикс «КП»).
- Шаблон `commercial/templates/quotation_template.docx` (шапка редактируется в Word);
  таблица/спеки добавляются программно (`python-docx`), т.к. `{%tr %}`-циклы в docxtpl 0.20.2 ненадёжны.
- Команда `manage.py create_quotation_template` — пересоздать дефолтный шаблон.
- Кнопка «Сформировать КП» — `pages/CartDetailPage.vue` (только на странице корзины).

### Цена в корзине (read-only)

- `cart/serializers.py::_resolve_sku_price` — больше не пишет в БД: читает
  `PriceHistory.get_current_price_by_sku()`, валюту конвертирует в RUB на лету
  (`ExchangeRate`), кеш только in-memory на запрос.
- `cart/models/cart_item.py`: поля `price_snapshot`/`price_date`/`price_currency`
  **закомментированы** (колонки в БД остались, миграция 0003).
- `cart/admin.py` `CartItemInline.fields` → `('sku', 'quantity', 'notes', 'added_at')`
  (убраны `price_snapshot` и устаревшие `content_type`/`object_id`).

### Быстрый подбор кабельных вводов

- `cable_glands/catalog/views_quickselect.py` — `get()` переопределён: `model_line_id`
  не обязателен (подбор по всем сериям); топ-уровнем — «Тип кабеля» (`cable_type_id`).
- Фронт: `apps/cable-gland-catalog/components/QuickSelectCableType.vue` (топ-селектор
  «Тип кабеля», остальные фильтры чипсами); `App.vue`/`api.js` переключены.

### Остаток / риски 2026-09-16

- Браузерная проверка глобального поиска и кнопки «Сформировать КП» — за пользователем.
- Шаблон КП — из файла; после отладки перенести в админку/модель (и, возможно, историю КП).
- Удалить закомментированные `CartItem.price_*` поля миграцией — при желании.
- `db.sqlite3` изменён в ходе тестов (инкременты счётчика КП).

---

## 11. Сессия 2026-09-16 (вечер) — Exd-опция: единый M2M-паттерн, миграции, фильтры

> Полный контракт и инвентаризация — **`exd-option.md`** (корень репо). Этот раздел — краткий факт-репорт + решения.

### 11.1. Единый паттерн Exd (задача 1)

**Доменная модель**: вид взрывозащиты (`params.ExdOption`) ↔ **опция-с-кодировкой**
(through-строка `BaseM2MExdThroughOption`: `encoding` + M2M `exd_options` видов) ↔
**артикул/item**, который выбирает опцию из списка серии (FK `exd_option`/`selected_exd`
на строку или денормализованный M2M видов). Серия = `model_line`.

**Через-модели (6)**: `CableGlandExdOption`→`CableGlandModelLine`, `PosiExdOption`→`PosiModelLine`,
`LimitSwitchExdOption`→`LimitSwitchModelLine`, `DirectionValveExdOption`→`DirectionalValveModelLine`
(новая, `solenoid_valves/models/dv_exd_option.py`), `ElectricExdOption`→`ElectricActuatorModelLine`,
`PneumaticExdOption`→`PneumaticActuatorModelLine`.

**Сделано в эту сессию**:
- DV: FK `exd` → `exd_option` (FK на строку) + дата-миграция `solenoid_valves/0022`
  (84 артикула перепривязаны к 3 строкам); шаблоны `{exd}`/`{exd_short}` (как у КВ/позиционеров).
- EA: `ElectricExdOption` переведён с legacy `BaseExdThroughOption` на `BaseM2MExdThroughOption`;
  удалены legacy `default_exd`/`allowed_exd` (+raw-SQL «обход»); `ElectricActuatorConstructor.selected_exd`
  — теперь FK на СТРОКУ (было на ExdOption); миграция `electric_actuators/0042` (10 строк + 14 конструкторов).
- PA: то же для `PneumaticExdOption`; `PneumaticActuatorItem`/`PneumaticActuatorConstructor.selected_exd`
  → FK на строку; миграция `pneumatic_actuators/0038` (3 строки + конструкторы).
- LSB: добавлен `{exd_short}` в `lsb_item_fields.py` и ключи; позиционеры/КВ уже были на паттерне.
- Все три миграции — reversable (проверены round-trip на реальной базе; для EA/PA потребовался
  промежуточный `AlterField(exd_option → null=True)` — исходный FK был NOT NULL).
- `cart/cart_item.py`: сводка Ex через display-методы с фолбэком на M2M-атрибут.
- Шаблоны: `{exd}` полный список / `{exd_short}` короткий («Ex db / Ex ia») во всех каталогах.

**Исключения (не трогать)**: `GearboxInterlock.interlock_exd` (плоский M2M, нет серии),
`EttElectricOptionsCombination.exd_choice` (справочник ЕТТ), мёртвый `AbstractActuatorMixin.exd` (удалён).

### 11.2. Унификация кода (шаги 1–5 идеальной архитектуры)

- **`options/exd.py`** — вынесены `BaseThroughOptionNoDefault`, `BaseThroughOption`,
  `ExdFormattingMixin`, `BaseM2MExdThroughOption`, `ExdOptionsConsumerMixin`;
  `options.models` реэкспортирует (старые импорты работают).
- **`ChosenExdRowMixin`** (`options/exd.py`) — новый: `_get_effective_exd_row`,
  `get_exd_display`, `get_exd_short_list`, `exd_encoding`, `clean()` (валидация «строка ↔ серия»);
  на нём — `CableGland` и `DirectionValve` (дубли ~50 строк удалены). Настройки:
  `exd_row_field`/`exd_through_model`/`exd_parent_field`.
- **`options/admin.py::BaseExdOptionInline`** — общий инлайн (`exd_options`, `encoding`,
  `is_default`, `sorting_order`, `is_active` + `filter_horizontal`); все 6 инлайнов на нём.
- **Legacy вычищено**: `BaseExdThroughOption` (нет подклассов), `AbstractActuatorMixin.exd`.

### 11.3. Фильтры и подбор (задача 2)

**Семантика (решения пользователя, не переигрывать)**:
- «Не хуже чем»: модель проходит, если **∃ вид** из её списка, совместимый с запрошенным
  (лестница `общепром < Ex ia < Ex ib < Ex e < Ex d < Ex d IIC`; группа: та же среда + rating>=;
  температура: `rating>=` (газ) / `dust<=` (пыль)).
- **Соглашение**: вид БЕЗ температурного класса в маркировке подходит под ЛЮБОЙ запрос по
  температуре (покрывает кабельные вводы — отдельный фильтр не нужен).
- EXACT = запрошенный вид присутствует в списке модели.
- `resolve_compatible`: `type_id` → все типы ЕГО МЕТОДА (db → db+da; семантика «не хуже»).

**Код**:
- `params/exd_models.py::resolve_compatible(method_id, type_id, group_id, temp_id) → (ids, exact_id)` —
  один SQL вместо цикла; эндпоинт `/core/exd/compatible/` отдаёт `exact_id`.
- `configurator/services/parameter_filter.py::_resolve_hierarchy_compatible_ids` — иерархия одним
  OR-запросом + кэш (LocMem, timeout 300 с), инвалидация сигналами `params/exd_signals.py`
  (версия `exd_compat_version`; подключается в `params/apps.py.ready`).
- `core/models/filter_definition.py::classify_match(obj, value, exact_value)` — M2M-aware
  (`_get_m2m_ids`/`_walk_m2m` поддерживают `exd`, `exd_option__exd_options`, reverse-менеджеры;
  prefetch-aware). FK-путь сохранён для THREAD/FUNCTION/IP_RANK.
- `core/models/smart_catalog_mixin.py::apply_filters_and_split` — проброс `exact_value`;
  режим `{param}_match=exact` + `{param}_exact` (например `exd_id_match=exact&exd_id_exact=4`).
- Фронт: `ExdFilter.vue` эмитит `exactId`; `FilterSidebar`/`EngineerFilterBar` шлют `exd_id_exact`
  (мастер — НЕ шлёт: split'а у мастера нет, параметр убран как инертный).
- PA-подбор: exd-матчинг перенесён в РЕАЛЬНЫЙ селектор `actuator_selector_handler.py`
  (`_match_exd_for_model_lines`: hard-фильтр серий «∃ совместимый вид», аннотирует
  `exd_option_id`/`exd_encoding`/`exd_short`; `filter_engine._filter_pa_selector` несёт их в кандидатах).
- `pneumatic_actuators/actuator_selector_helper.py` — ЗАКОММЕНТИРОВАН целиком (вероятно мёртвый
  код: никем не импортируется, несовместим с моделями); в шапке файла — пояснение.

### 11.4. Проверено / риски / что осталось

**Проверено**: `manage.py check` чист; configurator 29/29; smoke: иерархия «Ex d» = 2 запроса
(было ~50), кэш 0; DV/CG split exact/compatible; round-trip миграций DV/EA/PA; PA-селектор
(exd_id=67 → только серия с видом 67).

**Осталось / риски**:
- **cart-дрейф**: колонки `price_*` есть в БД (данные: 12/5/5 строк), в модели закомментированы;
  миграцию НЕ создавал — удаление данных, ждёт решения.
- `pneumatic_actuators` и `pneumatic_fittings` тесты не догнаны (запуск прерван таймаутом);
  `core` тесты не запускаются из-за конфликта `core/tests.py` ↔ пакет `core/tests/` (предсуществующий).
- `db.sqlite3` в git — изменён миграциями/тестами; уточнить конвенцию.
- Внешние потребители `ExdFilter` (`ConfiguratorPaKitPage`, `PaSelectionPage`, `RequirementForm`)
  не слушают `exactId` — им EXACT не проброшен (не ломаются).
- Перенести шаблон КП в модель/админку (п. 10) — не делалось.
- Следующий шаг: браузерный проход каталогов (exd-фильтр + секция «Точно подходят»), затем коммит.
