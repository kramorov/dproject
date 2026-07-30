# AI Assistant — архитектура и документация

> Снапшот: 2026-07-30

## Конвейер подбора

```
Запрос → Classify (LLM) → intent + types
  → Decompose (LLM) → плоский список [{type, summary}]
  → Expand Tree (Python) → CompositionGroup: required/optional/XOR
  → Extract (LLM) → для каждого узла: summary → фильтры
  → Filter (API) → поиск вариантов
  → Select → Compare → EBOM/MBOM
```

## Модели

### Конвейер подбора

| Модель | Назначение |
|---|---|
| `AIConversation` | Сессия: customer FK, source, status, intent, selection_tree |
| `SelectionNode` | Узел дерева подбора: parent (self-FK), equipment_type FK, статусы фаз |
| `PipelineSkill` | Скилл: step + equipment_type → prompt_template + output_schema + model_role |
| `SkillOverride` | Клиентское переопределение скилла |
| `CascadeRule` | Каскад параметров: parent_type → child_type |
| `AIPromptTemplate` | Версионируемый промпт с подстановкой `{code}`. Имеет встроенный `schema_json` |
| `JSONSchema` | Отдельная версионируемая JSON Schema для structured output. Имя + версия уникальны |
| `AIMessage` | Сообщение: content, prompt_used, prompt_template FK, latency_ms |
| `AITokenUsage` | Токины + биллинг |
| `AIProvider` | API-ключ провайдера, model_mapping |
| `AIQuerySample` | Размеченный сэмпл для отладки |
| `AIClientProvider` | API-ключ для внешних сайтов (WordPress) |

### BOM Конструктор

| Модель | Модуль | Назначение |
|---|---|---|
| `CompositionGroup` | ai_assistant | Группа композиции: parent (self-FK), equipment_types (M2M), references (M2M), group_type, output_schema FK, prompt_template FK |
| `MBOM` | sku | Производственная спецификация: customer FK, user FK, conversation FK |
| `MBOMItem` | sku | Элемент MBOM: parent (self-FK), equipment_type FK, composition_group FK, sku FK, quantity |

### Классификатор

| Модель | Модуль | Назначение |
|---|---|---|
| `EquipmentType` | core | Тип оборудования: parent (self-FK), level, icon, content_type FK, filter_endpoint, param_semantics, title_template, output_schema FK, prompt_template FK |

### Связь схем и промптов с моделями

| Модель | output_schema | prompt_template |
|---|---|---|
| `PipelineSkill` | FK → JSONSchema (через пару step+equipment_type) | FK → AIPromptTemplate |
| `CompositionGroup` | FK → JSONSchema (для группы, MBOM/подбор) | FK → AIPromptTemplate |
| `EquipmentType` | FK → JSONSchema (для extract) | FK → AIPromptTemplate |

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
| `/composition-groups/` | CRUD | CompositionGroup (включает output_schema, prompt_template) |
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

### Генерация схемы из модели

```
POST /api/ai-assistant/schemas/generate-from-model/
{ "equipment_type_id": 3 }

→ читает EquipmentType.content_type → model_class
→ извлекает FILTER_DEFINITIONS
→ маппит FilterType в JSON Schema типы (EXACT→integer, TEMP_MIN→number, ...)
→ возвращает schema_json + fields[]
```

## Frontend

### Страницы

| Маршрут | Компонент | Назначение |
|---|---|---|
| `/ai-assistant` | AiAssistantPage | Пользовательский интерфейс подбора |
| `/ai-debug` | AiDebugPage | Отладка: запросы, скиллы, дерево |
| `/admin/pipeline-config` | PipelineConfigPage | CRUD скиллов, промптов, схем, EquipmentType AI-настроек |
| `/admin/bom-config` | BomConfigPage | BOM Конструктор + редактор схем |

### BomConfigPage (`/admin/bom-config`)

Вкладки:
- **🌳 Дерево** — раскрывающиеся узлы CompositionGroup + EquipmentType
  - Двойной клик на группе → модалка редактирования (родитель, схема, промпт)
  - Двойной клик на ET → модалка редактирования (название, код, родитель, уровень, иконка, схема, промпт, кнопка «Взять из модели»)
  - Двойной клик на ссылке → модалка «Редактирование ссылки» (только смена родителя)
- **🏗️ Конструктор** — drag-and-drop: слева EquipmentType, справа CompositionGroup
  - Подсветка цели при наведении (синяя пунктирная рамка)
  - Drag группы в пустую область → перенос в корень
  - Drag группы на группу → диалог «Перенести / Сделать ссылку»
- **📋 MBOM** — таблица спецификаций с inline-редактированием

### Редактор схемы

Вызывается из ET-модалки (✏️) или кнопкой «🔄 Взять из модели». Модалка:
- Имя схемы, версия
- Таблица полей с выпадающими списками «Опция» / «Обязательно»
- Живой JSON-preview
- Кнопка «Сохранить» → создаёт/обновляет JSONSchema

### Компоненты

- `TreeNode.vue` — рекурсивное отображение узла дерева (вкладка Дерево)
- `CompositionGroupNode.vue` — узел группы: drag-and-drop, подсветка цели, события edit-node/edit-reference/remove-reference
- `EquipmentTypeNode.vue` — drag-source узел для левой панели
- `MBOMItemNode.vue` — рекурсивный узел для MBOM-дерева
- `TreeNodeDisplay.vue` — узел с кнопками фаз (для AiDebugPage)
- `ProgressBar.vue` — заполняющаяся полоса с расчётом из avg_latency_ms
- `JsonTableViewer.vue` — табличный просмотр JSON
- `ConfirmDialog.vue` — диалог подтверждения

## Композиция промптов

`_resolve_prompt(template_text, **extra)` разрешает `{code}`:
- Ищет `AIPromptTemplate` с таким `code` → подставляет `template_text`
- Если нет в БД → ищет в `**extra` (user_text, requirements, ...)
- Если нет нигде → оставляет `{code}` как есть

Системный промпт (`code="system_prompt"`) содержит каталог типов оборудования.

## Клиенты

`resolve_customer(source, email, api_key)`:
- `web_form` → anonymous_web
- `email` → ProjectCustomer
- `api` → CustomerApiKey
- `messenger` → anonymous_web

## Как тестировать

```bash
# Тесты пайплайна
python manage.py test ai_assistant.test_pipeline --keepdb

# Миграции
python manage.py makemigrations ai_assistant sku core
python manage.py migrate

# Отладка через AiDebugPage
# 1. Открыть /ai-debug
# 2. Выбрать скилл DECOMPOSE
# 3. Вставить запрос клиента
# 4. Нажать «Анализировать»

# Посмотреть что отправилось в LLM
python manage.py shell -c "
from ai_assistant.models import AIMessage
m = AIMessage.objects.filter(intent='decompose').order_by('-id').first()
print(m.prompt_used)
"

# Генерация схемы из модели
curl -X POST /api/ai-assistant/schemas/generate-from-model/ \
  -H 'Content-Type: application/json' \
  -d '{"equipment_type_id": 3}'
```

## TODO

### AiCatalogSearch — AI-помощник в каталогах

Компонент на страницах каталогов (LimitSwitchPage, FilterRegulatorPage, ...). Двухшаговый конвейер:

```
Текст пользователя
  → Classify (LLM) — определить intent + equipment_type
    ├── "подбери БКВ IP66"              → intent=search, type=limit_switch
    ├── "БКВ к приводу артикул XXX"     → intent=search_by_parent, type=limit_switch, зависит от actuator
    ├── "покажи самый дешевый БКВ"      → intent=search, type=limit_switch, sort=price
    ├── "нужен БКВ и позиционер"         → intent=multi, types=[limit_switch, positioner]
    └── "какие датчики лучше?"          → intent=discuss, needs_clarification
  → Extract (LLM) — использует EquipmentType.prompt_template + output_schema
  → Filter — применяет извлечённые параметры к каталогу
```

**Зачем нужен Classify:**
- Защита от спама и нерелевантных запросов
- Маршрутизация: поиск по родительскому оборудованию (найти привод → взять параметры → подобрать БКВ)
- Обработка множественных позиций (decompose)
- Отсев запросов-обсуждений (нужна уточняющая ветка диалога)

**Эндпоинт:** `POST /api/ai-assistant/catalog-search/`

```json
// Request
{
  "equipment_type_id": 3,
  "text": "БКВ с индуктивным датчиком IP66, температура -40"
}

// Response
{
  "intent": "search",
  "filters": {
    "sensor_variety_id": 2,
    "ip_id": 5,
    "work_temp_min": -40
  },
  "confidence": 0.92,
  "explanation": "Индуктивный датчик, IP66, от -40°C"
}
```

**PipelineSkills для catalog-search:**
- `classify / *` → общий classification-промпт, модель=classification
- `extract / {equipment_type}` → EquipmentType.prompt_template + output_schema

- **Перенос PipelineConfigPage** в BomConfigPage как дополнительная вкладка — единый центр настройки AI
- **Фаза Compare**: сравнение требований пользователя с характеристиками продуктов
- **EBOM/MBOM**: сохранение результатов подбора в модели MBOM/MBOMItem
- **Интеграция MBOMViewSet** с TreeProcessor для автоматического заполнения MBOMItem
- **Кеширование** дерева CompositionGroup + EquipmentType
- **Вкладка Schemas** в BomConfigPage — CRUD схем с авто-генерацией из моделей
