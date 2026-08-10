# Configurator — концепция

> Снапшот: 2026-08-07

## Проблема

Подбор оборудования для сборки (например, «пневмопривод в комплекте») требует
учёта сложных взаимосвязей между компонентами:

- **Глобальные параметры** (температура, Exd) применяются ко всей сборке, но
  могут быть переопределены для отдельных компонентов (соленоид Ex ia при
  общем Exd).
- **Обязательные поля** зависят от контекста: `safety_position_id` нужен только
  для SR-приводов.
- **Каскад параметров**: выбранная модель привода определяет размер резьбы
  соленоида и фитингов.
- **Совместимость** — не бинарное «подходит/не подходит», а разные модели:
  точное совпадение (резьба), иерархия (Exd), направленное сравнение
  (температура -60°C подходит для требования -20°C).
- **Релаксация**: если точного совпадения нет — найти ближайший вариант с
  минимальными отклонениями.
- **Фитинги**: количество и тип зависят от контекста монтажа (NAMUR на приводе
  vs отдельно стоящий), а не от одного параметра.

Сейчас эти знания размазаны по промптам LLM, CascadeRule и param_semantics.
Configurator собирает их в единую декларативную систему.

## Три слоя

```
Layer 1: КОМПОЗИЦИЯ — из чего состоит сборка
         CompositionGroup (ai_assistant)

Layer 2: ТРЕБОВАНИЯ — что нужно пользователю
         AssemblyRequirements → ComponentRequirement (configurator)

Layer 3: ПРАВИЛА — как параметры связаны
         PropagationRule, DerivationRule, ParameterRule,
         ParameterBinding, FittingPattern (configurator)
```

## Модели

### AssemblyRequirements

Контейнер сессии подбора. Одна запись = одна сборка. Независим от AI —
может быть создан вручную или из AIConversation.

```
AssemblyRequirements
├── composition_group → CompositionGroup  (шаблон сборки: pa-kit)
├── root_node → CompositionGroup | null   (точка входа — для навигации)
├── global_requirements: JSON             (общие требования)
├── status: draft / in_progress / done
└── components → [ComponentRequirement, ...]
```

### ComponentRequirement

Требования и результат подбора для одного типа оборудования в сборке.

```
ComponentRequirement
├── assembly → AssemblyRequirements
├── equipment_type → EquipmentType
├── parent → self | null          (иерархия)
├── path: str                     (materialized path)
│
├── own_requirements: JSON        (что явно указал пользователь/AI)
├── effective_requirements: JSON  (вычисляемое: global + inherited + derived + own)
├── cascade_params: JSON | null   (от DerivationRule после выбора родителя)
│
├── selected_product_type: str | null
├── selected_product_id: int | null
├── selected_product_specs: JSON | null
│
└── status: pending / requirements_filled / filtered / selected / skipped
```

### PropagationRule

Откуда берётся значение параметра для типа оборудования.

```
PropagationRule
├── equipment_type → EquipmentType
├── param_name: str
├── source: user | global | parent | derived
├── source_param: str | null
├── allow_override: bool
├── is_mandatory: bool
├── mandatory_condition: JSON | null
└── priority: int
```

### DerivationRule

Каскад параметров от выбранной модели к зависимым типам.

```
DerivationRule
├── source_type → EquipmentType
├── source_product_field: str       (поле в БД-модели продукта)
├── target_type → EquipmentType
├── target_param: str               (имя параметра требований)
├── transform: JSON | null          ({"map": {"G1/4": "1/4", ...}})
├── condition: JSON | null          ({"field": "variety", "value": "SR"})
└── priority: int
```

### ParameterRule

Семантика сравнения параметра. Переиспользуемый шаблон.

```
ParameterRule
├── code: str unique                ("temperature_min", "exd", "thread_size")
├── name: str
├── match_type: exact | directional | hierarchy | compatible | subset | composite
├── match_config: JSON
├── hardness: hard | soft
├── relaxation_strategy: none | step | percentage | compatible | any
├── relaxation_config: JSON | null
├── parent → self | null              (родительское composite-правило)
├── combine: and | or | null          (только для родителя с match_type=composite)
└── priority: int
```

**match_type:**
- `exact` — точное совпадение (резьба M20 = M20)
- `directional` — направленное сравнение (temp -60 ≤ -20, torque 200 ≥ 150)
- `hierarchy` — иерархия (Exd требует Exd; общепром допускает любой)
- `compatible` — группы совместимости (M20 совместим с M20×1.5)
- `subset` — подмножество (IP67 включает IP66)
- `composite` — составное правило: комбинирует sub_rules через AND/OR

**hardness:**
- `hard` — невыполнение исключает модель из кандидатов
- `soft` — невыполнение даёт штраф, модель остаётся

**relaxation_strategy (для soft):**
- `none` — не релаксировать
- `step` — пошагово (температура: -20 → -15 → -10, шаг 5°C)
- `percentage` — процент (момент: 150 → 145 → 140, шаг 3%)
- `compatible` — перейти к соседним группам совместимости
- `any` — игнорировать ограничение полностью

### Составные правила (composite)

`match_type: composite` + `combine: and|or` позволяет собирать сложные параметры
из нескольких простых. Дочерние правила (sub_rules) имеют `parent → составное`.

```
ParameterRule "exd" (composite, combine=and)
├── ParameterRule "exd_method" (exact)
│     Проверяет метод взрывозащиты: db, ia, tb, ...
├── ParameterRule "exd_group" (hierarchy)
│     Группа опасности: IIC ⊇ IIB ⊇ IIA
└── ParameterRule "exd_temperature" (directional)
      Температурный класс: T6 ⊇ T5 ⊇ ... ⊇ T1
```

Фильтр рекурсивно вычисляет Q для каждого sub_rule и комбинирует через AND/OR.
На ParameterBinding ссылается родительское правило.

### ParameterBinding

Привязка ParameterRule к конкретному типу оборудования.

```
ParameterBinding
├── rule → ParameterRule
├── equipment_type → EquipmentType
└── param_name: str          (имя поля в модели/фильтре)
```

Один ParameterRule может быть привязан к нескольким типам. Меняешь правило —
меняется поведение фильтрации для всех типов сразу.

### FittingPattern

Шаблон фитингов для контекста монтажа. В отличие от PropagationRule и
DerivationRule, не передаёт значения — **создаёт новые ComponentRequirement**.

```
FittingPattern
├── code: str unique
├── name: str
├── applies_to → EquipmentType
├── condition: JSON           (контекст монтажа)
└── items → [FittingPatternItem, ...]

FittingPatternItem
├── pattern → FittingPattern
├── equipment_type → EquipmentType
├── quantity: int
├── config: JSON              ({"angle": "straight", "size_from": "parent.port_size_npt"})
└── order: int
```

## Алгоритм Selection Engine

```
1. РАЗВОРАЧИВАНИЕ
   CompositionGroup → дерево ComponentRequirement

2. ЗАПОЛНЕНИЕ ТРЕБОВАНИЙ
   Для каждого ComponentRequirement:
     effective = resolve_effective(component, assembly)
     ┌─ PropagationRule(source=global) → global_requirements[param]
     ├─ PropagationRule(source=parent) → parent.effective[source_param]
     ├─ PropagationRule(source=user)   → own_requirements[param]
     ├─ allow_override → own имеет приоритет над source
     └─ cascade_params (от DerivationRule) → дополняют effective

3. ПОДБОР (в порядке зависимостей)
   a. HARD FILTER
      Применить все hard-параметры через ParameterRule.match_type
      → candidate_set

   b. Если candidate_set пуст → RELAX
      sorted_soft = sort(soft_params, by=priority)
      Перебрать комбинации релаксаций (от 1 параметра до всех)
      Для каждой комбинации: переприменить фильтры → candidate_set
      Найти комбинацию с минимальным штрафом

   c. SCORE
      Для каждого кандидата:
        score = penalty за каждое отклонение по soft-параметрам
      → отсортированный список

   d. SELECT
      Пользователь выбирает модель

   e. CASCADE
      DerivationRule: выбранная модель → cascade_params дочерних
      FittingPattern: mounting_context → новые ComponentRequirement

4. ПОВТОР для зависимых компонентов (шаг 2–3)
```

## Ручной сценарий

```
1. Создать AssemblyRequirements(composition_group=pa-kit)
   → CompositionGroup разворачивается в дерево ComponentRequirement

2. Форма требований:
   ┌─ Общие ──────────────────────────────┐
   │  Температура: [-40] … [+60]          │
   │  Exd:         [Exd]                  │
   │  Давление:    [6] бар                │
   ├─ Пневмопривод ───────────────────────┤
   │  ★ Момент:    [150] Нм               │
   │  ★ Тип:       [DA]                   │
   │    Exd:       [Exd] ← global         │
   │    Темп.:     [-40..+60] ← global    │
   ├─ Соленоид ───────────────────────────┤
   │  ★ Напряжение: [24V DC]              │
   │    Exd:       [Ex ia] ← переопредел. │
   └──────────────────────────────────────┘

3. «Подобрать» → Selection Engine пошагово:
   привод → соленоид → кабельный ввод → фитинги
```

## AI-интеграция (позже)

```
Пользователь: «Нужен пневмопривод Exd, момент 150 Нм, температура -40..+60»

→ LLM (decompose + extract)
→ Заполняет AssemblyRequirements:
   global_requirements = {temp_min: -40, temp_max: 60, exd: "Exd"}
   components[pneumatic-actuator].own = {torque_nm: 150}

→ Тот же Selection Engine
→ Та же форма для проверки пользователем
```

AI заполняет требования. Подбор делает движок.

## Интеграция с каталогами

ParameterRule через ParameterBinding используется и в Selection Engine,
и в SmartCatalogMixin. Одна точка правды для семантики параметра:

```
FilterType.TEMP_MIN  ← ParameterRule(match_type="directional", direction="min")
FilterType.EXD_COMPATIBLE ← ParameterRule(match_type="hierarchy", levels=[...])
FilterType.THREAD_COMPATIBLE ← ParameterRule(match_type="compatible", groups=[...])
```

## Навигация

Любой узел CompositionGroup может быть точкой входа (`root_node`).
При входе через «ФР со скобой» — дерево обрезается до этой ветки,
но global-требования всё ещё применяются.

## Администрирование

Модели зарегистрированы в Django admin. Раздел «Конфигуратор» доступен
через TopMenu: Администрирование → Конфигуратор.

Права доступа: через `configurator/object_registry.py` → `SystemGroup.object_permissions`.
Для `anonymous_users` автоматически выдаётся `view` на все объекты типа `admin_page`.

### Состав меню

| Пункт | Django-модель |
|---|---|
| Сессии подбора | `AssemblyRequirements` |
| Компоненты сборок | `ComponentRequirement` |
| Правила наследования | `PropagationRule` |
| Правила каскада | `DerivationRule` |
| Правила параметров | `ParameterRule` |
| Привязки параметров | `ParameterBinding` |
| Шаблоны фитингов | `FittingPattern` + `FittingPatternItem` (inline) |

## Статус

Модели созданы (3 миграции). Админка подключена.
Правила параметров засеяны для БКВ (lsb).
Движок фильтрации `parameter_filter.py` написан и протестирован.
Составные правила (composite) — модель готова, логика в движке предстоит.
