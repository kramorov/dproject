# AI Assistant — архитектура и документация

> Последнее обновление: 2026-07-30

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

### Конвейер подбора (ai_assistant)

| Модель | Назначение |
|---|---|
| `AIConversation` | Сессия: customer FK, source, status, intent, selection_tree |
| `SelectionNode` | Узел дерева подбора: parent (self-FK), equipment_type FK, статусы фаз |
| `PipelineSkill` | Скилл: step + equipment_type → prompt_template + output_schema + model_role |
| `SkillOverride` | Клиентское переопределение скилла |
| `CascadeRule` | Каскад параметров: parent_type → child_type |
| `AIPromptTemplate` | Версионируемый промпт с подстановкой `{code}` |
| `JSONSchema` | JSON Schema для structured output |
| `AIMessage` | Сообщение: content, prompt_used, prompt_template FK, latency_ms |
| `AITokenUsage` | Токины + биллинг |
| `AIProvider` | API-ключ провайдера, model_mapping |
| `AIQuerySample` | Размеченный сэмпл для отладки |
| `AIClientProvider` | API-ключ для внешних сайтов (WordPress) |

### BOM Конструктор

| Модель | Модуль | Назначение |
|---|---|---|
| `CompositionGroup` | ai_assistant | Группа композиции: parent (self-FK), equipment_types (M2M), group_type (required/optional/xor) |
| `MBOM` | sku | Производственная спецификация: customer FK, user FK, conversation FK |
| `MBOMItem` | sku | Элемент MBOM: parent (self-FK), equipment_type FK, composition_group FK, sku FK, quantity |

### Классификатор

| Модель | Модуль |
|---|---|
| `EquipmentType` | core |

## API endpoints

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
| `/composition-groups/` | CRUD | CompositionGroup |
| `/composition-tree/` | GET | Дерево CompositionGroup + EquipmentType |
| `/equipment-type-tree/` | GET | Дерево EquipmentType |
| `/mboms/` | CRUD | MBOM (user автоустанавливается из сессии) |
| `/mbom-items/` | CRUD | MBOMItem |

### Конфигурация пайплайна

| Endpoint | Метод | Назначение |
|---|---|---|
| `/skills/` | CRUD | PipelineSkill |
| `/overrides/` | CRUD | SkillOverride |
| `/prompts/` | CRUD | AIPromptTemplate |
| `/schemas/` | CRUD | JSONSchema |
| `/equipment-types/` | GET/PATCH | EquipmentType AI-поля |
| `/customers/` | GET | ProjectCustomer |
| `/model-roles/` | GET | Роли из AIProvider.model_mapping |

## Frontend

### Страницы

| Маршрут | Компонент | Назначение |
|---|---|---|
| `/ai-assistant` | AiAssistantPage | Пользовательский интерфейс подбора |
| `/ai-debug` | AiDebugPage | Отладка: запросы, скиллы, дерево |
| `/admin/pipeline-config` | PipelineConfigPage | CRUD скиллов, промптов, схем |
| `/admin/bom-config` | BomConfigPage | BOM Конструктор (3 вкладки) |

### BomConfigPage (`/admin/bom-config`)

Три вкладки:
- **🌳 Дерево** — раскрывающиеся узлы CompositionGroup + EquipmentType. Двойной клик открывает окно редактирования.
- **🏗️ Конструктор** — drag-and-drop: слева EquipmentType, справа CompositionGroup. Вложенность групп, удаление элементов.
- **📋 MBOM** — таблица спецификаций с inline-редактированием.

### Компоненты

- `TreeNode.vue` — рекурсивное отображение узла дерева
- `TreeNodeDisplay.vue` — узел с кнопками фаз (для AiDebugPage)
- `ProgressBar.vue` — заполняющаяся полоса с расчётом из avg_latency_ms
- `JsonTableViewer.vue` — табличный просмотр JSON

## Меню

Администрирование → BOM → **BOM Конструктор**

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
python manage.py makemigrations ai_assistant sku
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
```

## TODO

- Фаза Compare: сравнение требований пользователя с характеристиками продуктов
- EBOM/MBOM: сохранение результатов подбора в модели MBOM/MBOMItem
- Интеграция MBOMViewSet с TreeProcessor для автоматического заполнения MBOMItem
- Кеширование дерева CompositionGroup + EquipmentType
