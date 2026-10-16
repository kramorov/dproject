# PA Card Pattern — материализованная карточка товара (ПП и сборки)

> Обновлено 2026-10-01. Направление изменено: вместо «не генерировать карточки» —
> материализация карточек (~8к) + конфигуратор как вход/редактор.
> Связано: `SESSION.md` §14, `CATALOG_PATTERN.md`, `assy.md`, `sku-mbom.md`.

## Проблема

У ПП нет готового конечного списка артикулов — артикул появляется только после конфигурации
(`серия × корпус × DA/SR × опции`). Раньше считали, что генерировать все комбинации нельзя
(комбинаторный взрыв). Подсчёт по БД (§14 SESSION.md) показал: полных комбинаций ≈ 8 181 —
мало, выгоднее материализовать реальные карточки.

## Решение (2026-10-01)

Материализовать карточки `PneumaticActuatorCatalogItem` + `SKU` (~8к), скрытые из каталога.

Две идентичности, связанные 1:1 через `SKUMixin.sku`:

- **Карточка** = конфигурация (типоразмер + опции), ключ — `config_hash`.
- **SKU** = связка `(code, brand)` — артикулы у разных производителей совпадают.

## Единый путь создания

И ручное, и авто-создание идут через один `save()`:

1. `equipment_type` — из серии;
2. `config_hash` — из опций (уникальность на `save()` → блок при коллизии);
3. `code` — из encoding (`model_line.model_item_code_template`);
4. `TemplateMixin` — name/description из шаблонов серии;
5. `sync_sku()` — SKU `(code, brand)`.

Вес материализуется при создании: `generate_pa_cards` и
`sku_service.materialize_configuration` считают `weight = compute_weight()` до
`save()` (конфигуратор резолвит `manual_override_option` для точного веса
ручного дублера).

Ручная и сгенерированная карточки неразличимы по поведению; вместо `is_generated` —
`origin` (`generated` / `manual`): он определяет, кто управляет жизненным циклом
(генератор или человек), а не поведение карточки.

## `config_hash`

- Хэш канонического кортежа стабильных id (11 полей, `config_hash_fields`):
  `model_line, body, pneumatic_actuator_variety, selected_safety_position,
  selected_springs_qty, selected_temperature, selected_ip, selected_exd,
  selected_body_coating, selected_body_color, selected_manual_override`;
  отсутствующие = `0`.
- **Не хэшировать** encoding и сам `code` — смена кодировки не трогает хэш.
- `unique=True` + проверка на `save()`.

### Правило fork (переименование vs новый продукт)

- Хэш тот же, код другой → **та же SKU**, обновляем `code`.
- Хэш другой → **новый продукт** → новая карточка + SKU (старая архивируется).
- Код обязан быть инъективен к хэшу (§14 SESSION.md); если хэш сменился, а код нет —
  баг шаблона артикула.

## Регенерация

Дифф по `config_hash`: новый → создать; исчез → `is_active=False`; encoding изменился →
пересчитать `code` (та же карточка, ссылки по FK сохраняются). Никогда не hard-delete
ссылочные SKU.

## Конфигуратор — вход/редактор

Два варианта конфигуратора ПП:

1. **Каталог `/catalog/pa-actuators`** (режим внутри каталога): компонент
   `PaActuatorConfigurator.vue` (`frontend/src/shared/components/catalog/`).
   Вход + редактор: у карточки CTA «открыть в конфигураторе» с предвыбором
   опций (`initialOptions`); эмитит `addToCart` → `create-sku`.
2. **Отдельная страница `/configurator/pa`**: `apps/pa-constructor/App.vue`
   (бэкенд `ConstructorViewSet`). Только вход/создание: серия → вид → модель →
   опции → превью → «Создать» (материализация карточки). Списка «сохранённых
   конфигураций», редактирования и удаления нет.

Дедуп на commit по `config_hash` → переиспользование существующей карточки
(`sku_service.materialize_configuration`; при переиспользовании возвращает
`created=False`).

Терминология: страницу `/configurator/pa` называем **конфигуратор** (не
«конструктор»). Внутренние имена `pa-constructor`/`ConstructorViewSet` —
legacy, переименование — отдельной задачей.

Доступ: в дальнейшем доступ к конфигуратору предполагается ограничить
(права на секцию `configurator_pa`).

## Признаки карточки: origin и видимость

Два независимых признака (плюс `config_hash`):

- `origin` (choices `generated` / `manual`, default `generated`) — владелец жизненного
  цикла. `generated` управляется генератором (архивирование при исчезновении,
  пересчёт `code` при смене encoding); `manual` — создана вручную, генератор не трогает.
- `exclude_from_catalog` (bool, default `False`) — видимость:
  - глобальный поиск и деталка его **игнорируют** (идут через SKU);
  - листинги каталога фильтруют `exclude_from_catalog=False`;
  - у сгенерированных (`generate_pa_cards`) и конфигураторных карточек = `True`
    (нестандартные/неявные карточки не показываем в листингах).
- Конфигураторные карточки: `origin=generated`, `exclude_from_catalog=True`
  (создаются так в `sku_service.materialize_configuration`).

## Статус

- [x] `from_constructor()` + `to_dict()` + `render_spec_html()`
- [x] SKU — единый реестр; MBOM — производная `fixed`-сборки
- [x] `config_hash` + `exclude_from_catalog` на карточке
- [x] SKU: уникальность `(code, brand)`
- [x] `SKUMixin.sync_sku()` → `(code, brand)`
- [x] цены по `sku_id`
- [x] команда генерации карточек (`generate_pa_cards`)
- [x] переименование `PneumaticActuatorItem` → `PneumaticActuatorCatalogItem` (ссылок на старое имя нет)
- [x] поле `origin` (`generated` / `manual`) на карточке; генератор не трогает `manual`
- [x] дедуп конфигуратора по `config_hash` (`sku_service.materialize_configuration`; возвращает `created`)
- [x] карточки конфигуратора: `origin=generated`, `exclude_from_catalog=True`, вес материализуется
- [x] снэпшот цен при проведении документа (`PriceDocument.register_changes` → `PriceHistory`)
- [x] валидация генерации: AIR-S (141 карточка + SKU, 0 ошибок); dry-run полного прогона = 5999 карточек
- [ ] полный прогон генерации (5999 карточек + ~6к SKU) — не запускался

Примечание (2026-10-16): страница `/configurator/pa-legacy` удалена; standalone-страница
`/configurator/pa` переведена на запись в `PneumaticActuatorCatalogItem` (список/редактирование/
удаление убраны). Исправлен маппинг опции `exd` в `sku_service` (был `params.ExdOption`,
стало `PneumaticExdOption`).

Примечание (2026-10-10): в шаблонах EquipmentType «Пневмопривод» плейсхолдер был
`{variety}` (несуществующий в реестре ПП) → исправлен на `{variety_name}` (RU + en/cn,
5 полей); словарь `translate_et_title_templates` синхронизирован. В БД есть 2 «сиротских»
SKU (`AIR.SY`, `AIR03-SYM125-S1-S3.fl`) с source на несуществующие карточки 1/8 — остатки
более ранней генерации, не трогались.
