# SESSION.md — Текущее состояние проекта

> Обновлено: 2026-09-07. История изменений удалена; здесь — только актуальные факты,
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

---

## 8. Как продолжить с другой машины

- `git pull`/переключение ветки; зависимости не менялись.
- Миграции применены (`manage.py migrate` — no-op); dev-БД — `db.sqlite3`.
- Фронт: при необходимости `npm --prefix frontend run build`.
- Проверки: `manage.py check` + смоук-скрипты (тест-БД не работает, см. п. 6).
- Документация контракта: `template_mixin.md`.
