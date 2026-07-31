# AI Assistant — архитектура и документация

> Снапшот: 2026-07-31

## Конвейер подбора

```
Запрос → Decompose (LLM) → дерево типов + global_requirements
  → Expand Tree (Python) → CompositionGroup: required/optional/XOR
  → Extract (LLM) → для каждого узла: фильтры
  → Validate mandatory → проверка обязательных полей
  → Filter (API/handler) → поиск вариантов
  → Select → Compare → EBOM/MBOM
```

### Описание фаз

| Фаза | Метод | Назначение |
|---|---|---|
| **Decompose** | `decompose_v4` | Текст → дерево типов + global_requirements |
| **Expand** | Python | Разворачивает CompositionGroup (references → inline) |
| **Extract** | `extract-{code}-v2` | Текст → фильтры (param_name = FilterDefinition.param_name) |
| **Validate** | `_validate_required` | Проверка обязательных полей (mandatory='yes') |
| **Filter** | `filter_handlers.*` | Фильтры → список вариантов |
| **Select** | — | Выбор продукта + cascade |
| **Compare** | — | Сравнение требований |
| **EBOM/MBOM** | — | Спецификация |

---

## Модели

### Конвейер подбора

| Модель | Назначение |
|---|---|
| `AIConversation` | Сессия: customer FK, source, status, intent, selection_tree |
| `SelectionNode` | Узел дерева подбора: parent (self-FK), equipment_type FK, статусы фаз |
| `PipelineSkill` | Скилл: step + equipment_type → prompt_template + output_schema + model_role |
| `SkillOverride` | Клиентское переопределение скилла |
| `CascadeRule` | Каскад параметров: parent_type → child_type |
| `AIPromptTemplate` | Версионируемый промпт с подстановкой `{code}`. Имеет `schema_json` |
| `JSONSchema` | Отдельная версионируемая JSON Schema для structured output |
| `AIMessage` | Сообщение: content, prompt_used, prompt_template FK, latency_ms |
| `AITokenUsage` | Токины + биллинг |
| `AIProvider` | API-ключ провайдера, model_mapping |
| `AIQuerySample` | Размеченный сэмпл для отладки |
| `AIClientProvider` | API-ключ для внешних сайтов (WordPress) |

### BOM Конструктор

| Модель | Модуль | Назначение |
|---|---|---|
| `CompositionGroup` | ai_assistant | Группа композиции: parent (self-FK), equipment_types (M2M), references (M2M), group_type, output_schema FK, prompt_template FK |
| `MBOM` | sku | Производственная спецификация |
| `MBOMItem` | sku | Элемент MBOM: parent (self-FK), equipment_type FK, composition_group FK, sku FK, quantity |

### Классификатор

| Модель | Модуль | Назначение |
|---|---|---|
| `EquipmentType` | core | Тип оборудования: parent (self-FK), level, icon, content_type FK, filter_endpoint, param_semantics, title_template, output_schema FK, prompt_template FK |

---

## CompositionGroup & EquipmentType

### CompositionGroup — правило композиции для BOM

```python
CompositionGroup
├── name, code, description       # идентификация
├── group_type                     # required / optional / xor
├── sorting_order, is_active       # порядок, активность
├── parent (FK → self)            # ВЛОЖЕНИЕ: группа внутри другой
│   └── children (rev FK)          # каскадное удаление
├── references (M2M → self)       # ССЫЛКА: группа ссылается на другую
│   └── referenced_by (rev M2M)    # без каскада
├── equipment_types (M2M → ET)    # типы оборудования в группе
├── output_schema (FK → JSONSchema)     # схема выходного формата (MBOM/подбор)
└── prompt_template (FK → AIPromptTemplate) # шаблон промпта (MBOM/подбор)
```

### Три типа элементов внутри группы

| Элемент | item_type | В БД | Семантика |
|---|---|---|---|
| 📦 EquipmentType | `equipment_type` | M2M `equipment_types` | Базовый тип оборудования |
| 📁 CompositionGroup | `composition_group` | FK `parent` | Вложенная группа |
| 🔗 Reference | `reference` | M2M `references` | Ссылка на другую группу |

- **Вложение ≠ Ссылка**: группа не может быть одновременно ребёнком и ссылкой
- **Reference** нужно разворачивать (inline) при построении дерева для AI-пайплайна

### Структура групп (текущая)

```
Пневмопривод - комплект (pa-kit, required)
├── ET: Пневмопривод
└── ПП - дополнительно (optional)
    ├── ET: МК ISO
    ├── ref: БКВ со скобой и КВ
    │   └── БКВ дополнительно (optional)
    │       ├── ET: MK - БКВ к приводу
    │       └── ET: Кабельный ввод
    ├── ref: ФР со скобой
    │   └── Скоба, фитинги к ФР (optional)
    │       ├── ET: MK - ФР к приводу
    │       └── ET: Фитинг резьба-трубка
    ├── ref: Ручной дублер с МК
    │   ├── ET: Ручной дублер
    │   └── МК к ручному дублеру (optional)
    │       └── ET: МК ISO
    └── Управление: соленоид или позиционер (xor)
        ├── ref: Пневмопозиционер с КВ и фитингами
        │   ├── ET: Позиционер для ПП
        │   └── КВ, фитинги, скоба (optional)
        │       ├── ET: MK - позиционер к приводу
        │       ├── ET: Фитинг резьба-трубка
        │       └── ET: Кабельный ввод
        ├── ref: БКВ со скобой и КВ
        └── ref: Соленоидный клапан с КВ и фитингами
            ├── ET: Соленоидный клапан
            └── КВ и скоба к приводу (optional)
                ├── ET: MK - распределителя к приводу
                ├── ET: Фитинг резьба-трубка
                └── ET: Кабельный ввод
```

---

## Система фильтров

### FilterDefinition

Декларативное описание одного фильтра. Поля:

```
FilterDefinition(
    param_name,          # имя параметра в API/JSON
    model_field,         # поле модели Django
    filter_type,         # EXACT, MIN, MAX, TEMP_MIN, IP_RANK, EXD_COMPATIBLE, ...
    data_source_type,    # FIELD_VALUES, FOREIGN_KEY, GLOBAL_MODEL, CUSTOM, ...
    label,               # человекочитаемое название
    order,               # порядок сортировки
    source_model,        # модель-источник для CUSTOM/FOREIGN_KEY
    mandatory='any',     # 'any' | 'yes' — обязательность (добавлено 2026-07-31)
)
```

### Где живут FILTER_DEFINITIONS

| Модель | Источник |
|---|---|
| `LimitSwitchBox` | `pa_controls/catalog/filter_defs.py` + модель |
| `DirectionValve` | `solenoid_valves/catalog/filter_defs.py` |
| `GearBox` | `gearbox/catalog/filter_defs.py` |
| `FilterRegulator` | `filter_regulator/catalog/filter_defs.py` |
| `PneumaticFitting` | `pneumatic_fittings/catalog/filter_defs.py` |
| `PneumaticActuatorModelLineItem` | на классе модели (для AI, не для каталога) |

### mandatory — обязательные поля

Добавлено в `FilterDefinition.__init__` (2026-07-31):

| Модель | Поле | mandatory |
|---|---|---|
| PA actuator | `actuator_variety_id` (DA/SR) | yes |
| PA actuator | `torque_nm` | yes |
| Solenoid valve | `power_supply_id` | yes |
| GearBox | `min_work_torque` | yes |
| LSB | — | — |
| Filter regulator | — | — |
| Fittings | — | — |

Проверка: `tree_processor._validate_required()` после extract. Если нет → `status="needs_info"`, сообщение с `fd.label`.

### filter_handlers.py

Прямые вызовы (без HTTP) из `tree_processor._call_filter_handler`. Маппинг:

| Эндпоинт | Handler |
|---|---|
| `/api/pneumatic_actuators/selector/search/` | `process_selection_params` |
| `/api/solenoid_valves/filter/` | `solenoid_valves_filter` |
| `/api/options/bkv/filter/` | `limit_switch_filter` |
| `/api/manual_override/filter/` | `gearbox_filter` |
| `/api/filter_regulator/filter/` | `filter_regulator_filter` |
| `/api/pneumatic_fittings/filter/` | `pneumatic_fittings_filter` |

### Генерация промптов и схем

Промпты v2 генерируются из FilterDefinition + опций БД:

- **Ключи полей** = `FilterDefinition.param_name` (совпадают с API фильтров)
- **Опции** = `fd.get_options(model_class)` — реальные id/name из БД
- **mandatory** поля помечены `[ОБЯЗАТЕЛЬНО]` в промпте
- **MIN/MAX/TEMP** фильтры: «Тип: число», не список опций
- **CUSTOM** фильтры (Exd): опции из `ExdOption`

Схемы: `{et.code}-extract-v2`, промпты: `extract-{et.code}-v2`.

### PipelineSkill — приоритет над EquipmentType

`tree_processor._get_config()` сначала ищет `PipelineSkill` (step='extract', equipment_type=...). Если найден — использует его `prompt_template` и `output_schema`. `EquipmentType.prompt_template` используется только если `PipelineSkill` отсутствует.

⚠️ При обновлении промптов нужно обновлять **оба**: `PipelineSkill` и `EquipmentType`.

### Валидация и лейблы

- **`_validate_required(node)`** — после extract. Проверяет поля с `mandatory='yes'`. Если нет → `status='needs_info'`, `status_message` с названиями полей.
- **`_resolve_labels(node)`** — разрешает ID в человекочитаемые значения через `FilterDefinition.get_options()`. Результат — `_labels` внутри `extract_output` для фронтенда.
- **`user_text`** — кэшируется в `selection_tree` **до** auto-extract, чтобы промпты резолвились корректно.

### Отладка через AIMessage

При `needs_info` AIMessage всё равно создаётся (логирование до валидации). Сырой ответ LLM доступен: `AIMessage.objects.filter(conversation_id=N, intent='extract')`.

---

## API endpoints

Базовый URL: `/api/ai-assistant/`

### Конвейер

| Endpoint | Метод | Назначение |
|---|---|---|
| `/decompose/` | POST | text → дерево + extract |
| `/extract/{node_id}/` | POST | Ручной extract узла |
| `/filter/{node_id}/` | POST | Фильтр оборудования |
| `/select/{node_id}/` | POST | Выбор продукта + каскад |
| `/compare/{node_id}/` | POST | Сравнение требований |
| `/tree/{conv_id}/` | GET | Полное дерево подбора |
| `/ebom/{conv_id}/` | GET | EBOM |
| `/mbom/{conv_id}/` | GET | MBOM из TreeProcessor (legacy) |

### BOM Конструктор

| Endpoint | Метод | Назначение |
|---|---|---|
| `/composition-groups/` | CRUD | CompositionGroup (+ output_schema, prompt_template) |
| `/composition-groups/:id/add_reference/` | POST | Добавить ссылку |
| `/composition-groups/:id/remove_reference/` | POST | Убрать ссылку |
| `/composition-groups/:id/referenced_by/` | GET | Кто ссылается на группу |
| `/composition-tree/` | GET | Дерево CompositionGroup + EquipmentType |
| `/equipment-type-tree/` | GET | Дерево EquipmentType |
| `/mboms/` | CRUD | MBOM |
| `/mbom-items/` | CRUD | MBOMItem |

### Конфигурация пайплайна

| Endpoint | Метод | Назначение |
|---|---|---|
| `/skills/` | CRUD | PipelineSkill |
| `/overrides/` | CRUD | SkillOverride |
| `/prompts/` | CRUD | AIPromptTemplate |
| `/schemas/` | CRUD | JSONSchema |
| `/schemas/generate-from-model/` | POST | Генерация JSON Schema из FILTER_DEFINITIONS модели |
| `/equipment-types/` | GET/PATCH | EquipmentType AI-поля |
| `/customers/` | GET | ProjectCustomer |
| `/model-roles/` | GET | Роли из AIProvider.model_mapping |

---

## Система промптов

`PromptResolver.resolve(template_text, **extra)` разрешает `{code}`:
- Ищет `AIPromptTemplate` с таким `code` → подставляет `template_text`
- Если нет в БД → ищет в `**extra` (user_text, requirements, ...)
- Если нет нигде → оставляет `{code}` как есть

Системный промпт (`code="system_prompt"`) содержит каталог типов оборудования.

### Ключевые промпты

| code | Шаг | Версия |
|---|---|---|
| `system_prompt` | — | каталог продукции |
| `decompose_v4` | decompose | 4 |
| `decode_prompt` | decode (legacy) | 1 |
| `extract-{code}-v2` | extract | 2 (опции из БД) |
| `mbom-{code}` | MBOM | 1 |

---

## Клиенты

`resolve_customer(source, email, api_key)`:
- `web_form` → anonymous_web
- `email` → ProjectCustomer
- `api` → CustomerApiKey
- `messenger` → anonymous_web

---

## Frontend

### Страницы

| Маршрут | Компонент | Назначение |
|---|---|---|
| `/ai-assistant` | AiAssistantPage | Пользовательский интерфейс подбора |
| `/ai-debug` | AiDebugPage | Отладка: запросы, скиллы, дерево |
| `/admin/skill-config` | SkillConfigPage | CRUD скиллов, промптов, схем, BOM Конструктор |
| `/admin/pipeline-config` | PipelineConfigPage | Pipeline настройка (legacy → объединить с SkillConfigPage) |

### SkillConfigPage (`/admin/skill-config`)

Вкладки:
- **🌳 Дерево** — раскрывающиеся узлы CompositionGroup + EquipmentType
  - Двойной клик: модалка редактирования группы или ET
  - Двойной клик на ссылке: «Редактирование ссылки»
- **🏗️ Конструктор** — drag-and-drop: EquipmentType ↔ CompositionGroup
- **📋 MBOM** — таблица спецификаций

### Переиспользуемые компоненты

| Компонент | Путь |
|---|---|
| `TreeNode.vue` | `src/components/bom/TreeNode.vue` |
| `CompositionGroupNode.vue` | `src/components/bom/CompositionGroupNode.vue` |
| `EquipmentTypeNode.vue` | `src/components/bom/EquipmentTypeNode.vue` |
| `MBOMItemNode.vue` | `src/components/bom/MBOMItemNode.vue` |
| `SelectionResultGrid.vue` | `src/shared/components/catalog/SelectionResultGrid.vue` |

### Меню админки

Администрирование → группы с подменю: Номенклатура и цены, Клиенты, Оборудование, Настройка системы, Инструменты, AI (Skill настройка, Pipeline Config, AI Ассистент, AI Отладка).

---

## Как тестировать

```bash
# Тесты пайплайна
python manage.py test ai_assistant.test_pipeline --keepdb

# Отладка через AiDebugPage
# 1. Открыть /ai-debug
# 2. Выбрать скилл DECOMPOSE
# 3. Вставить запрос клиента
# 4. Нажать «Анализировать»

# Посмотреть промпт, отправленный в LLM
python manage.py shell -c "
from ai_assistant.models import AIMessage
m = AIMessage.objects.filter(intent='decompose').order_by('-id').first()
print(m.prompt_used)
"

# Генерация схемы из модели
curl -X POST /api/ai-assistant/schemas/generate-from-model/ \
  -H 'Content-Type: application/json' \
  -d '{"equipment_type_id": 3}'

# Ручная проверка фильтров
python -c "
import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')
import django; django.setup()
from ai_assistant.services.filter_handlers import solenoid_valves_filter
r = solenoid_valves_filter({'power_supply_id': 3, 'ip_id': 2})
print(r['total'], 'results')
"
```

---

## TODO

- **Унифицировать filter_handlers.py или FILTER_DEFINITIONS** — сейчас хендлеры дублируют логику Q-фильтров, а CatalogConfig/SmartCatalogMixin уже умеют это делать. Либо перевести хендлеры на вызов существующих фильтров, либо добавить во все модели FILTER_DEFINITIONS.
- **Генерация JSON-схем из модели** — сейчас промпты генерируются текстом в скрипте. Нужна обёртка: `generate_schema_from_model(equipment_type) → JSONSchema` с опциями из БД. Вызывать из админки (кнопка «Взять из модели»).
- **mandatory на фронте каталогов** — проверить, как сейчас работает проверка обязательных полей, и прикрутить `FilterDefinition.mandatory` как флаг required.
- **Перенос PipelineConfigPage в SkillConfigPage** — единый центр настройки AI.
- **AiCatalogSearch** — AI-помощник на страницах каталогов: текстовый ввод → extract фильтров → применение.
- **Неполный фильтр-маппинг** — в `filter_handlers.py` нет `FUNCTION_COMPATIBLE`, `CLIMATE_CASCADE`, `THREAD_COMPATIBLE`.
- **Фильтр для пайплайна** — следующий шаг: настроить передачу extracted в filter_handlers и визуализацию результатов через SelectionResultGrid с пагинацией.
- **required/optional в JSON-схемах** — сейчас `required` заполняется из `FilterDefinition.mandatory='yes'`. Для пайплайна этого достаточно, но в общем случае нужна поддержка conditional required (например, `safety_position_id` только для SR-приводов).
