# SESSION.md — Текущее состояние проекта

> Обновлено: 2026-09-08. История изменений удалена; здесь — только актуальные факты,
> механизмы и задачи. Детали контракта каталогов — в `template_mixin.md` (корень репо).

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

**Модели на контракте** (8 активных): `DirectionValve`, `LimitSwitchBox`, `PosiModelLineItem`,
`FilterRegulator`, `GearBox`, `PneumaticFitting`, `PneumaticActuatorItem`, `SensorComponent`
(шаблон с опции `variety`). У `SensorComponent` — ручной `_get_data_dict`; у остальных
семи словари выводятся из `TEMPLATE_FIELDS`.

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
8. **Фикс 500 на `/api/core/catalog-wizard/<code>/`** — `CatalogWizardAdapterView`
   (`core/question_graph_views.py:541`) сначала дёргает `QuestionGraph.objects.get(...)`,
   но таблица `core_questiongraph` удалена миграцией `0012_delete_questiongraph`
   (вылетает `OperationalError`, а не `DoesNotExist` → 500). Все 5 каталогов уже работают
   через `SelectionWizard` (активные строки: `lsb`, `directional-valve`, `manual-override`,
   `fr`, `fittings`). Сделать: убрать graph-ветку из адаптера, оставить только
   `_flat_config` (SelectionWizard) — тогда `/catalog-wizard/<code>/` вернёт `type: 'flat'`.
9. **Полная зачистка QuestionGraph** (старая схема, заменена SelectionWizard): модель
   `core/models/question_graph.py`, `core/question_graph_views.py`, роуты `question-graph/*`
   и `catalog-wizard/*` в `core/urls.py`, команда `core/management/commands/load_question_graph.py`,
   тест `core/tests/test_question_graph_options.py`; фронт: `QuestionGraphWizard.vue`,
   `QuestionGraphAdmin.vue`, `QuestionGraphDemo.vue`, `BranchNodeForm.vue`, а также graph-ветки
   в 5 каталогах (`graphAvailable`/`page==='graph'`/`QuestionGraphWizard` в App.vue) и
   `useCatalogWizard.js` — перевести на flat-only. Миграцию `0012_delete_questiongraph`
   оставить как есть (таблица уже удалена).

## 8. Кабельные вводы (cable_glands) — рефакторинг под каталог

**Статус: модели + админки зафиксированы; миграции 0001–0005 применены (2026-09-09).**

### Структура (3 уровня, паттерн пневмо/электроприводов)

- **`CableGlandModelLine`** — серия: `ImageGalleryMixin, TechDocMixin, CertDocMixin,
  EquipmentTypeMixin, CopyMixin, StructuredDataMixin`. Шаблоны `name_template` /
  `description_template` / `model_item_code_template`. `equipment_type` — **единственный тип
  на серии** (nullable, `SET_NULL` — переходный, ужесточить до PROTECT после заполнения;
  FK `cable_gland_type` → `CableGlandItemType` **удалён**). `ip` — **одиночный FK**
  (был M2M; эталон Posi). `exd` — **through-модель `CableGlandExdOption`**
  (`BaseM2MExdThroughOption`: кодировка + M2M видов; 2026-09-09 заменил старый M2M `exd`).
  Материал корпуса — **through-модель `CableGlandBodyMaterialOption`** (`BaseThroughOption`:
  `model_line` + `body_material` + `encoding`, `unique_together` model_line/body_material/encoding;
  inline в админке серии). Удалены
  `CableGlandMaterialOption` (копия резьбовой) и `get_full_description`.
- **`CableGlandModelLineItem`** — «модель в серии»: `model_line`/`body`/
  `metal_sleeve_body`/`weight`, `CopyMixin`. TemplateMixin НЕ наследует.
- **`CableGland`** (`cg_actual.py`, была не зарегистрирована!) — **артикул каталога**:
  `TemplateMixin, CopyMixin, ImageGalleryMixin, TechDocMixin, SKUMixin`. FK `model_line` →
  серия (денормализуется из `model_line_item` в `save()`), `model_line_item`, `thread` →
  `ThreadSize` (классом! строка `'ThreadSize'` без app_label не резолвилась), `body_material`.
  `update_name/update_description` не затирают ручные name/description без кода и без
  шаблона серии; `code` обязателен в админке до автогенерации (guard в
  `CableGlandAdminForm`); временный `_get_data_dict` (будет заменён реестром). SKU —
  `sync_sku()` в save.
- Справочники: `CableGlandBody` (+ опции резьбы `CableGlandThreadOption`),
  `CableGlandMetalSleeveBody` (+ M2M `MetalSleeve`), `CableGlandBodyMaterial`,
  `CableGlandModelLineCertRelation`. `CableGlandItemType` **оставлен без потребителей**
  (админка есть) — решить: удалить или перенести признак «ввод/адаптер/заглушка/кольцо».
- Починены конфликты `related_name` (`cg_metal_sleeve_body_brand`, `cg_material_body`
  [модель удалена], дублей больше нет).

### Админки (cable_glands/admin) — все переписаны

- `CopyMixin` на 5 моделях + `AdminCopyMixin` c `copy_selected_objects` на 5 админках:
  `CableGlandModelLine`, `CableGlandModelLineItem`, `CableGlandBody`
  (хук `_copy_custom_relations` дублирует `CableGlandThreadOption`),
  `CableGlandMetalSleeveBody`, `CableGland`. M2M копируются `.set()`, `sku` сбрасывается.
- Серия: `TemplatePlaceholdersAdminMixin` (`template_item_model=CableGland`,
  `template_placeholders_fieldset=«Шаблоны названия, описания и артикула»`).
- Удалён мёртвый `cg_item_admin.py` (импортировал несуществующий `CableGlandItem`);
  добавлен `cg_actual_admin.py`; `MetalSleeve` и `CableGlandMetalSleeveBody` получили админки.

### Миграции и БД

- Цепочка `0001…0007` удалена (разошлась с моделями — не было RenameModel и т.п.),
  **пересоздана `0001_initial.py`** (10 моделей).
- **Применена 2026-09-08**: в dev-БД `db.sqlite3` удалены все старые таблицы
  `cable_glands_*` (12 шт., включая `cableglanditem*`, M2M `ip`) и ОБЕ устаревшие
  цепочки истории (старая `0002_remove…/0008_…` + `0002_metalsleeve…/0007_…`),
  затем `migrate cable_glands --skip-checks` → `cable_glands.0001_initial` OK.
  Данные cable_glands в dev-БД утеряны (дампы `cable_glands-02-26.json` — под старую
  схему, не применимы) — нужен повторный ввод по новой структуре.
- Живой смоук пройден: создание серии/корпуса/«модели в серии»/артикула, генерация
  name из шаблона серии, денормализация `model_line` из `model_line_item`, SKU,
  копирование артикула/серии/корпуса (с дублированием `CableGlandThreadOption`).

- Внимание: у моделей, наследующих и `CopyMixin`, и `StructuredDataMixin`, `CopyMixin`
  должен стоять РАНЬШЕ в bases (иначе побеждает `StructuredDataMixin.copy` без сохранения;
  исправлено для `CableGlandBody`/`CableGlandMetalSleeveBody`).

### Блокеры / остаток

- **GraphQL убран (2026-09-08)**: root `djangoProject1/urls.py` больше не импортирует
  `graphql_api.schema` и не монтирует `/graphql/`; `graphql_api/schema.py` очищен от
  `cableGlandsSchema`; удалены legacy-файлы cable_glands: `graphql/*`, `serializers.py`,
  `views.py`, `urls.py` (были мёртвыми ссылками на `CableGlandItem`).
  `manage.py check` → **System check identified no issues** (runserver/check разблокированы).
- L1–L4 закрыты: `get_temp_range_display`/`get_cable_diameter_display` не выводят `None`
  (диаметр фильтрует нули-дефолты); дефолтные шаблоны name/description без висячих
  разделителей; `CableGland.code` — `unique=True` (миграция 0003 применена; дубликат кода
  → IntegrityError).
- **Шаг 3 — РЕЕСТР ГОТОВ**: `cable_glands/models/cg_item_fields.py`
  (`CG_ITEM_TEMPLATE_FIELDS`); артикул переведён на `CatalogSerializerMixin` +
  `SmartCatalogMixin`; `NAME/CODE/VARS/SPEC_FIELD_KEYS`, `SPEC_GROUP_TITLES`;
  временный `_get_data_dict` удалён; **автогенерация артикула активна**
  (`model_item_code_template` серии + encodings `thread__code`/`body_material__code`/
  `model_line_item__code`; пример: `ABRA.DN100.NPT-1_4.BR`); display-свойства
  `get_exd_display/get_cable_diameter_display/get_temp_range_display/
  get_cable_flags_display`; `required_model_line_fields` включает
  `model_item_code_template`; guard «код обязателен» в админке снят.
  Миграция `0002_alter_...` применена (help_text/verbose); дальнейших изменений
  модели нет (`makemigrations --check` — No changes).
- **Поиск** по `thread/exd/ip/⌀ кабеля/флагам/temp/brand` — позже (анализ проведён:
  нужен плоский артикул, thread-кодировки, exd через денормализованную M2M на артикуле).
- Ограничение копирования: повторное копирование → одинаковый код «X Копия» → конфликт
  SKU; при необходимости — перебор суффиксов как у Posi.

---

## 9. Как продолжить с другой машины

- `git pull`/переключение ветки; зависимости не менялись.
- Миграции применены (`manage.py migrate` — no-op); dev-БД — `db.sqlite3`.
  cable_glands: применена свежая `0001_initial` (2026-09-08), старые данные
  приложения в dev-БД утеряны.
- Фронт: при необходимости `npm --prefix frontend run build`.
- Проверки: `manage.py check` + смоук-скрипты (тест-БД не работает, см. п. 6).
- Документация контракта: `template_mixin.md`.
