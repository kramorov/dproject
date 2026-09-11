# SESSION.md — Текущее состояние проекта

> Обновлено: 2026-09-11. История изменений удалена; здесь — только актуальные факты,
> механизмы и задачи. Детали контракта каталогов — в `template_mixin.md` (корень репо),
> паттерн фильтрации каталогов — в `CATALOG_PATTERN.md`.

---

## 1. Каталоги: единый контракт (TemplateMixin)

**Механизм** (код: `core/models/mixins.py` — класс `TemplateMixin`):

- Шаблоны `name_template` / `description_template` живут на **серии** (model_line).
- **Артикул** (item) определяет `_get_data_dict()` — словарь «плейсхолдер → путь к характеристике».
- Генерация name/description происходит в `save()` (флаг `skip_auto_generate=True` отключает).
- Title: цепочка `_get_title_template_source` → `EquipmentType.title_template` → `{model_code}`.
- SKU создаётся из артикула через `SKUMixin.sync_sku()` (в `save()` после `super().save()`).
- **Реестр полей (новое, 2026-09-07)**: `TEMPLATE_FIELDS` + `TemplateFieldSpec`
  (`core/models/template_fields.py`) — единый источник правды для `_get_data_dict`,
  `_get_code_data_dict`, `_get_template_vars`, `_get_spec_sections`; составы словарей —
  списками ключей (`NAME/CODE/VARS/SPEC_FIELD_KEYS`), сериализация —
  `CatalogSerializerMixin` (`core/models/catalog_serializer.py`). Подробно: `template_mixin.md` §7.
  Пилоты: `PosiModelLineItem`, `LimitSwitchBox` (списковые поля `signals`/`sensors` → JSON).
  Переведены на реестр 2026-09-07: `DirectionValve`, `FilterRegulator`, `GearBox`,
  `PneumaticFitting` (точечное переопределение `_get_spec_sections()` — состав спеков
  по виду оборудования), `PneumaticActuatorItem` (единственная с `CODE_FIELD_KEYS`/
  `code_path` для автогенерации артикула). Реестры — в `*_fields.py` рядом с моделями.
  На ручном `_get_data_dict()` осталась `SensorComponent`.

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
6. Коммит контрольной точки текущего состояния (46 файлов рабочего дерева).
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

**Статус (2026-09-10): артикул CableGland переведён на прямые FK на through-строки;**
**добавлен конструктор кабельных вводов (модель + REST API + фронт + пункт меню);**
**миграции 0001–0011 применены (`makemigrations --check` — No changes).**

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

### Исправлено в этой сессии

- `get_outer_cable_diameter_display` / `get_outer_max_cable_diameter_display` —
  AttributeError из-за обращения к несуществующим полям (inner на MLI, outer на Body).
- `get_applicable_cable_types_display` — `', '.join(str(p) ...)` (ленивый перевод `__proxy__`).
- API конструктора — широкий `except ObjectDoesNotExist` (был узкий → 500).
- Удалена осиротевшая SKU (код `КБУ-МР G-1_4 BR`) после смены кода артикула.

### Остаток / риски

- Фронт `cg-constructor` и `cable-gland-catalog` не собраны (`npm --prefix frontend run build` нужен локально);
  полная сборка Vite не проверялась (SFC `App.vue`/`CableGlandPage.vue` не компилировались).
- Дедупликация артикула — на уровне приложения (гонка при параллельной записи возможна);
  жёсткого `UniqueConstraint` нет (NULL-семантика на SQLite).
- Секция прав `configurator_cg` в SiteSection не создана (суперюзер работает).
- `sync_sku()` не переписывает `SKU.code` при смене кода артикула; в команде генерации
  есть обход `_sync_sku_code`, в общем `save()` — нет (осиротевшие SKU при переименовании).
- У серии `КБУ` (ml 20) не было `model_item_code_template` → fallback-код с точками
  (`20 КБУ.M25x1,5.Ni`); пользователь исправил шаблон — перепроверить генерацию кодов КБУ.
- Диаметровые фильтры (`MIN/MAX`) входят в `SPLITTABLE_TYPES` → при `show_compatible=true`
  могут стать split-фильтром (классификация exact/compatible по числу) — косметика.
- Булевы флаги серии (armored/metal_sleeve/pipelines) — nullable; фильтр «Нет» не включает NULL.

---

## 9. Как продолжить с другой машины

- `git pull`/переключение ветки; зависимости не менялись.
- Миграции применены (`manage.py migrate` — no-op); dev-БД — `db.sqlite3`.
  cable_glands: применены `0001_initial` … `0011_cableglandconstructor`; данных —
  **972 артикула CableGland** (сгенерены командой `generate_cable_gland_combinations`,
  4 серии бренда BLOCK/БЛОК), у всех SKU и опции. Новых миграций в этой сессии нет.
- Каталог кабельных вводов: бэкенд `cable_glands/catalog/` + эндпоинты
  `/api/cable-glands/catalog|filters|engineer|quickselect|meta|sections/`;
  фронт `frontend/src/apps/cable-gland-catalog/` + `/catalog/cable-glands` в SPA-роутере.
- QuestionGraph: `manage.py migrate core` + сид `manage.py load_question_graph` (пересоздаёт 5 графов).
- Фронт: при необходимости `npm --prefix frontend run build`.
- Проверки: `manage.py check` + смоук-скрипты (тест-БД не работает, см. п. 6).
- Документация контракта: `template_mixin.md`; фильтрация — `CATALOG_PATTERN.md`.
- Мастер подбора (Selection Wizard) для CableGland зарегистрирован в `core/wizard_filter_registry.py`.
