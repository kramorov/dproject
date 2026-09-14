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
