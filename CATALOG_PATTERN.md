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
