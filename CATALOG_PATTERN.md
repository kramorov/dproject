# CATALOG_PATTERN.md — паттерн каталога оборудования

## Новая система фильтрации (ParameterRule)

С 2026-08-07 добавлена система декларативных правил фильтрации через `configurator`.
См. [`configurator.md`](configurator.md) — полная концепция.

### Как это работает

`FilterDefinition` может ссылаться на `ParameterRule` через `parameter_rule_code`:

```python
fd_temp_min = FilterDefinition(
    filter_type=FilterType.TEMP_MIN,          # фронтенд-тип (для UI)
    parameter_rule_code='temperature_min',    # бэкенд: ParameterRule
    ...
)
```

`build_filter_lookup` проверяет `parameter_rule_code` до старой логики:

```python
if self.parameter_rule_code:
    rule = ParameterRule.objects.get(code=self.parameter_rule_code)
    return _build_q_from_parameter_rule(rule, self.model_field, value)
```

### Типы правил

| match_type | Пример | Описание |
|---|---|---|
| `exact` | thread M20 = M20 | Точное совпадение |
| `directional` | temp -60 ≤ -20 | Направленное сравнение (min/max) |
| `hierarchy` | Exd требует Exd | Иерархия уровней |
| `compatible` | M20 ~ M20×1.5 | Группы совместимости |
| `subset` | IP67 ⊇ IP66 | Подмножество |
| `composite` | exd = method + group + temp | Составное правило (AND/OR дочерних) |

### Текущий статус

- [x] БКВ (lsb)
- [x] solenoid_valves
- [x] pneumatic_fittings
- [x] filter_regulator
- [x] gearbox
- [ ] cable_glands (нет FilterDefinition)
- [ ] pneumatic_actuators (нет каталоговых FilterDefinition)

### QuickSelect — defaults из FilterSet

`FilterSet` поддерживает поле `defaults` — стратегии автовыбора чипсов:

```python
'quickselect': FilterSet(
    definitions=[fd_sensor, fd_temp_min, fd_temp_max, ...],
    scoped=True,
    show_compatible=False,
    defaults={
        'sensor_variety_id': 'first',
        'work_temp_min': 'first',
        'work_temp_max': 'first',
    },
)
```

Стратегии: `'first'` (первая опция из API), `'min'`, `'max'`.
API возвращает `defaults` в ответе QuickSelect, фронт применяет автоматически.

### Роли filter_type и parameter_rule_code

| | filter_type | parameter_rule_code |
|---|---|---|
| Бэкенд | fallback (жёсткая логика) | приоритет (декларативная) |
| Фронт | выбор UI-компонента | не используется |
| AI | не используется | через ParameterBinding |

`parameter_rule_code` имеет приоритет в `build_filter_lookup`.
При ошибке — fallback на `filter_type`.

### Презентационные подсказки: `group` и `visible_when` (2026-09-24)

Два необязательных атрибута `FilterDefinition`, которые не влияют на бэкенд-фильтрацию,
а управляют тем, как фронт рендерит фильтры (`EngineerFilterBar.vue` / `FilterSidebar.vue`):

```python
fd_cable_diameter_outer_min = FilterDefinition(
    ...,
    group='Диаметры',                                # блок с заголовком на фронте
    visible_when={'cable_type_id': ['armored', 'armored_ms']},
)
```

- **`group`** (str | None) — человекочитаемая метка блока. Фильтры с одинаковым
  `group` группируются на фронте в отдельный блок с заголовком (аналог блока
  «Взрывозащита + температура»). `None` — обычный ряд без группировки.
- **`visible_when`** (dict | None) — условная видимость: `{param_name: [codes]}`.
  Фильтр виден, только когда у родительского фильтра (`param_name`) выбран option
  с `code` из списка (пример — «Броня» видна только для `armored`/`armored_ms`,
  «Металлорукав» — только для `unarmored_ms`/`armored_ms`).

Семантика и гарантии:
- Оба атрибута **опциональны** и имеют дефолты `None` в конструкторе — дублировать
  их во всех `FilterDefinition` не нужно; описывать следует только там, где нужны.
- Если родительский фильтр **отсутствует в текущем наборе** (`FilterSet`/`scope`),
  условие не применимо и фильтр остаётся видимым (важно для `model_line`-скоупа,
  где `cable_type_id` нет — «Броня» показывается как раньше).
- Фронт: скрытые фильтры очищаются на клиенте, а `useCatalog.fetchData()`
  (`syncVisibility`) гарантирует, что они **не уходят на бэкенд** — условные
  параметры не участвуют в подборе, когда неактуальны.
- Атрибуты сериализуются `BaseFilterOptionsView` в ответ фильтров
  (`group` / `visible_when`); остальные каталоги получают `null` и поведение
  не меняется.

Эталон использования: `cable_glands/catalog/filter_defs.py` (броня, металлорукав).

---

## Шаблоны title и спецификации (title_template / spec_template)

Единый паттерн формирования заголовка карточки и спецификации (деталки).
Реализация — `core/models/mixins.py` (TemplateMixin) и
`core/models/catalog_serializer.py` (CatalogSerializerMixin).

### title (заголовок карточки)

Приоритет источника (сверху вниз):

1. `_get_title_template_source()` — обычно `model_line.title_template`;
2. `EquipmentType.title_template` — глобальная настройка типа оборудования;
3. `_get_default_title_template()` — fallback-текст модели.

Заполняется плейсхолдерами реестра `TEMPLATE_FIELDS`, аналогично
`name_template`/`description_template`.

### spec (спецификация)

Приоритет источника (JSON, сверху вниз):

1. `model_line.spec_template` — на серии;
2. `EquipmentType.spec_template` — глобальная настройка типа оборудования;
3. `{model_code}` — fallback (только артикул).

Формат `spec_template` (вложенный, без `order`):

```json
{
  "Основные": {
    "Температура, °С": "temp_range",
    "IP": "ip",
    "Взрывозащита": "exd_short"
  },
  "Присоединения": {
    "Резьба": "thread",
    "Материал корпуса": "body_material",
    "Вес, кг": "weight"
  }
}
```

Ключ — готовая подпись (с единицей), значение — ключ поля реестра
`TEMPLATE_FIELDS`. Порядок — по вставке ключей. Пустые значения автоматически
скрываются. Фронт получает уже заполненные значения
(`sections[type=specs].data` = `{группа: {подпись: значение}}`).

Реестр `TEMPLATE_FIELDS` хранит только резолв значений и строковые шаблоны
(`key`, `placeholder`, `path`, `name_path`, `code_path`, `resolver`);
`label`/`unit`/`type`/`group`/`order` убраны — подписи задаются в `spec_template`.

Эталон: кабельные вводы (`CableGland` / `CableGlandModelLine`).

---

## Терминология: уровни номенклатуры и карточка каталога (`*CatalogItem`)

Уровни оборудования (сверху вниз):

1. **`EquipmentType`** — тип оборудования (классификатор: пневмопривод, электропривод,
   позиционер, БКВ…).
2. **`ModelLine` / `model_line`** — серия (входит в тип оборудования): шаблоны
   name/description/артикула, набор доступных опций, бренд.
3. **`ModelLineItem` / `model_line_item`** — модель/типоразмер в серии. У ПП/ЭП это
   отдельный уровень (корпус + DA/SR); у остальных каталогов типоразмер отдельно не
   выделен, и карточка совпадает с «моделью в серии».
4. **Карточка — `*CatalogItem`** — конкретная модель с выбранными опциями: единица
   каталога, имеет `code` (артикул) и SKU.

**Конвенция (2026-10-02):** карточка называется `*CatalogItem`. Пока применяется только
к пневмоприводам (`PneumaticActuatorCatalogItem`, затем `ElectricActuatorCatalogItem`).
Остальные каталоги используют устоявшиеся имена карточек (`LimitSwitchBox`,
`PosiModelLineItem`, `CableGland`, `DirectionValve`, `FilterRegulator`, `GearBox`,
`PneumaticFitting`, `SensorComponent`) и переименовываются в `*CatalogItem` точечно,
только при переписывании модели — массовое переименование не делаем (широкая
поверхность регрессий без функциональной выгоды).

### Три независимых признака карточки

- **`config_hash`** — семантическая идентичность конфигурации. Хэш от канонического
  кортежа: типоразмер + все выбранные опции. НЕ входят производные: encoding и `code`
  (смена кодировки не меняет хэш). Хэш есть и у сгенерированных, и у ручных карточек;
  `unique` → «1 конфигурация = 1 карточка». Ключ диффа генератора. Сам по себе хэш не
  участвует в цене/SKU — SKU дедупится по `(code, brand)`, цены висят на `sku_id`;
  хэш — идентичность карточки, стоящая выше SKU.
- **`origin`** (choices: `generated` / `manual`) — владелец жизненного цикла карточки.
  `generated` — карточкой управляет генератор (создаёт, архивирует при исчезновении,
  пересчитывает `code` при смене encoding); `manual` — создана человеком, генератор не
  трогает (не архивирует, не пересоздаёт, не пересчитывает `code`). Ручная нестандартная
  карточка отображается в каталоге, но не перегенерируется.
- **`exclude_from_catalog`** (bool) — видимость в листингах каталога; глобальный поиск
  и деталка работают всегда (идут через SKU).

### Правило fork: переименование vs новый продукт

- Хэш **тот же**, код другой (смена кодировки или ручное переименование) → **та же SKU**:
  `sync_sku()` обновляет `code` (переименование), ссылки по `sku_id` не рвутся.
- Хэш **другой** (сменилась опция) → **новый продукт** → новая карточка + новая SKU
  (старая архивируется).
- Условие корректности: код **инъективен** к хэшу — каждой конфигурации свой артикул.
  Если хэш сменился, а код нет — это баг шаблона артикула (править кодировку).
- `origin=manual` защищает и код, и опции ручной карточки: генератор и encoding их
  не перезаписывают.
