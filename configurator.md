# Configurator — концепция

> Снапшот: 2026-08-11

## Архитектура

Три уровня:

```
УРОВЕНЬ 1: Композиция (CompositionGroup)
    ├── Описывает, из каких EquipmentType состоит сборка
    └── pa-kit: pneumatic-actuator (req) + solenoid-valve (opt) + ...

УРОВЕНЬ 2: Параметры (EquipmentTypeParameter) — единый источник правды
    ├── Для каждого EquipmentType → полный список параметров
    ├── Три секции: Каталог, AI, UI (см. ниже)
    └── Единый источник для схем, фильтров и форм

УРОВЕНЬ 3: Связи (DerivationRule + ParameterRule)
    ├── DerivationRule: межтиповой fallback (actuator.port → solenoid.connection)
    ├── ParameterRule: семантика сравнения (exact, directional, hierarchy, subset)
    └── ParameterBinding: привязка ParameterRule к EquipmentType.param_name

УРОВЕНЬ 4: Сборка (AssemblyRequirements) — результат подбора
    ├── Структура (CompositionGroup) + требования (по ETP) + выбранные SKU
    ├── Жизненный цикл: draft → fixed; изменения — fork
    └── Связь с требованиями: requirement_version (сборка → требования)
```

## Сборка (AssemblyRequirements) — результат подбора

`AssemblyRequirements` + `ComponentRequirement` — **результат** конфигурации:
структура из типов, требования (по ETP) и выбранные позиции (`selected_sku`).

- `draft` — рабочая версия (mutable, не версионируется).
- `fixed` — закреплённая версия («сделали КП / счёт / в работу»), immutable.
- Изменения — `fork()`: полное копирование в новый draft (не дельта).
- Связь с требованиями: `AssemblyRequirements.requirement_version` (сборка → требования; у шаблона null).
- `fixate()` допустим только когда все узлы в терминальном статусе (`selected`/`skipped`); `included` помечает «нужен/не нужен».
- Хранится в отдельном приложении **`assemblies`** (не в `configurator`).

Подробно о связке «сборки ↔ заказы клиентов»: [`assy.md`](assy.md). Пошаговый план: [`EXECUTION_PLAN.md`](EXECUTION_PLAN.md).

## EquipmentTypeParameter — три секции

```
EquipmentTypeParameter
├── КАТАЛОГ (FilterDefinition-совместимость)
│   ├── filter_type        ← IP_RANK, EXD_COMPATIBLE, TEMP_MIN, exact...
│   ├── data_source_type   ← field_values, global_model, foreign_key, choices, custom
│   └── options_config     ← {model: "params.IpOption", field: "coating"}
│
├── AI
│   ├── param_type, unit, description, enum_values, ai_extraction_hint
│   └── → generate_json_schema(variant='ai'|'configurator')
│
└── UI (Configurator)
    ├── label, field_type, is_required
    └── → filter-schema API (filter_type, data_source_type, options)
```

### get_options() — 6 стратегий

| data_source_type | Откуда берёт опции |
|---|---|
| `global_model` | `options_config['model']` — все записи справочника |
| `foreign_key` | Related model поля через `field_path` |
| `field_values` | `SELECT DISTINCT field FROM products` |
| `choices` | Django `field.choices` |
| `custom` | `options_config['method']` — кастомный метод |
| (none/default) | `global_model` |

## Резолвинг требований (простой приоритет)

```
effective = {}
effective.update(cascade_params)        # 3. DerivationRule fallback
effective.update(global_requirements)   # 2. global (контекст сборки)
effective.update(own_requirements)      # 1. own (пользователь, высший приоритет)
translated = translate_keys(effective)  # field_path (унифицированные имена → поля БД)
```

## Унификация имён параметров

Все типы используют одинаковые `param_name`. `field_path` указывает, куда маппить:

```
temp_min → LimitSwitchBox.work_temp_min, GearBox.work_temp_min, ...
exd     → LimitSwitchBox.exd_id, DirectionValve.exd, CableGland.exd_id
ip      → LimitSwitchBox.ip_id, DirectionValve.ip, CableGland.ip_id
```

## Модели

### EquipmentTypeParameter
```
EquipmentTypeParameter
├── equipment_type → FK
├── param_name, label, field_type
├── field_path: str
├── is_required: bool
├── filter_type: str          ← ex: ip_rank, exd_compatible, temp_min
├── data_source_type: str     ← ex: global_model, field_values, foreign_key
├── parameter_rule → FK
├── param_type, unit, description, enum_values
├── options_config: JSON
└── sorting_order, is_active
```

### DerivationRule
```
DerivationRule
├── source_type → EquipmentType
├── source_product_field: str
├── target_type → EquipmentType
├── target_param: str
├── transform: JSON | null
├── condition: JSON | null
└── priority: int
```

### ParameterRule + ParameterBinding
```
ParameterRule: code, match_type, hardness, relaxation_strategy
ParameterBinding: rule → ParameterRule, equipment_type → EquipmentType, param_name: str
```

### AssemblyRequirements (сборка)
```
AssemblyRequirements
├── requirement_version → FK(ClientRequestItem)   # какие требования; null у шаблона
├── composition_group → FK (шаблон структуры)
├── root_node → FK (точка входа)
├── global_requirements: JSON (валидируется по ETP)
├── status: draft | fixed
├── revision: int (итерация состава внутри одного requirement_version)
├── parent_assembly → self-FK (состав-линия: только внутри одних требований)
├── is_template: bool
└── components → ComponentRequirement (дерево)
```

### ComponentRequirement (узел сборки)
```
ComponentRequirement
├── assembly → FK
├── equipment_type → FK
├── parent → self-FK, path, level, order
├── included: bool (нужен/не нужен; False → skipped)
├── own/effective/cascade_params (по ETP)
├── filter_results: JSON
└── selected_sku → FK(SKU)   (базовый тип; composite = null)
```

## API endpoints

```
POST   /api/configurator/assemblies/
GET    /api/configurator/assemblies/{id}/
PATCH  /api/configurator/assemblies/{id}/
POST   /api/configurator/assemblies/{id}/expand/
GET    /api/configurator/assemblies/{id}/bom/

GET    /api/configurator/components/{id}/
PATCH  /api/configurator/components/{id}/requirements/
POST   /api/configurator/components/{id}/filter/
POST   /api/configurator/components/{id}/select/

GET    /api/configurator/equipment-types/{id}/filter-schema/
GET    /api/configurator/admin/equipment-type-parameters/schema/?equipment_type=ID&variant=ai|configurator

# Admin CRUD
/api/configurator/admin/equipment-type-parameters/
/api/configurator/admin/parameter-rules/
/api/configurator/admin/parameter-bindings/
/api/configurator/admin/derivation-rules/
```

## Статус

- ✅ `EquipmentTypeParameter` — 34 записи, три секции (каталог, AI, UI)
- ✅ `DerivationRule` — модель готова
- ✅ `ParameterRule` + `ParameterBinding` — модель готова
- ✅ `resolver.py` — own > global > cascade
- ✅ `filter_engine.py` — ParameterRule + PA selector delegation
- ✅ `cascade.py` — DerivationRule после выбора
- ✅ `expander.py` — CompositionGroup → дерево CR
- ✅ `get_options()` — 6 стратегий (global_model, foreign_key, field_values, choices, custom)
- ✅ `generate_json_schema()` — два варианта (ai, configurator)
- ✅ Frontend: `/configurator/pa-kit` + `/admin/pipeline-config`
- ✅ Тесты: 29/29 pass
- ✅ `field_path` — установлен из FilterDefinition
- ✅ `filter_type` + `data_source_type` — мигрированы из FilterDefinition (5 записей)
- ✅ `PropagationRule` + `ParameterSource` — deprecated, удалены из resolver/админки/фронта
- ✅ `AssemblyRequirements` + `ComponentRequirement` — модели готовы, связь `requirement_version` (сборка → требования)
- ⏳ Перенос `AssemblyRequirements` + `ComponentRequirement` в приложение `assemblies`
- ⏳ Жизненный цикл сборки (`draft → fixed`, fork), `included`, терминальные статусы — в [`EXECUTION_PLAN.md`](EXECUTION_PLAN.md)
- ⏳ `ComponentRequirement.selected_*` → `selected_sku = FK(SKU)`; требования типизируются по ETP
