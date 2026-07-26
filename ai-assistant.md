# AI Assistant — архитектура и документация

> Последнее обновление: 2026-07-26

## Общая схема работы

```
Пользователь → /ai-debug (фронт) → POST /api/ai-assistant/decompose/
                                         │
                                         ▼
                               ┌──────────────────┐
                               │   TreeProcessor   │
                               │   Фаза 1: decompose│
                               └────────┬─────────┘
                                        │
                           ┌────────────┴────────────┐
                           │   LLM (deepseek-chat)    │
                           │   Промпт: decode v2      │
                           │   из StepConfig БД       │
                           └────────────┬────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
               ✅ ready           ⚠️ needs_info         ❌ rejected
          «Дерево построено»  «Уточните: ...»    «Не наша тематика»
                    │
                    ▼
          Фаза 2: extract (для каждого узла)
          Промпт + JSON-схема из StepConfig
                    │
                    ▼
          Фаза 3: filter (вызов API-фильтра)
          Эндпоинт из EquipmentType.filter_endpoint
                    │
                    ▼
          Фаза 4: select (выбор продукта + каскад)
          CascadeRule: parent_type → child_type
                    │
                    ▼
          Фаза 5: compare (требования vs факт)
          param_semantics из EquipmentType
                    │
                    ▼
          GET /ebom/  +  GET /mbom/
```

---

## Модели данных (13)

### Конвейер подбора

| Модель | Назначение | Ключевые поля |
|---|---|---|
| `AIConversation` | Сессия подбора | customer, status, intent, selection_tree (JSON-кеш) |
| `SelectionNode` | Узел дерева подбора | parent (self-FK), equipment_type FK, level, path, status, extract_output, cascade_params, filter_output, selected_product_*, compare_output |
| `EquipmentType` | Справочник типов оборудования | code, label, level, param_semantics (JSON), filter_endpoint |
| `CascadeRule` | Правило каскада параметров родитель→ребёнок | parent_type FK, child_type FK, mapping (JSON) |

### Конфигурация шагов

| Модель | Назначение | Ключевые поля |
|---|---|---|
| `StepConfig` | Конфигурация шага конвейера | step, equipment_type FK, prompt_template FK, output_schema FK, model_role |
| `StepConfigOverride` | Переопределение для клиента | customer FK, step_config FK, prompt_template FK, prompt_suffix, model_role |
| `AIPromptTemplate` | Версионируемый текст промпта | name, version, template_text, is_active |
| `JSONSchema` | Версионируемая JSON-схема ответа | name, version, schema_json, is_active |

### AI-провайдер

| Модель | Назначение | Ключевые поля |
|---|---|---|
| `AIProvider` | Настройки API-провайдера | code, base_url, api_key, model_mapping (JSON), is_active |

### Сообщения и токены

| Модель | Назначение | Ключевые поля |
|---|---|---|
| `AIMessage` | Одно сообщение в диалоге | conversation FK, role, content, parent (self-FK), prompt_template FK, intent |
| `AITokenUsage` | Учёт токенов на сообщение | message (1:1), model, prompt_tokens, completion_tokens, reasoning_tokens |

### Обучающие данные и клиенты

| Модель | Назначение | Ключевые поля |
|---|---|---|
| `AIQuerySample` | Сэмпл запроса для отладки/обучения | text, expected_intent, expected_filters, tree_json, final_selections_json, category |
| `AIClientProvider` | API-ключ клиента (WordPress и др.) | customer FK, provider_type, api_url, api_key |

---

## 6 фаз конвейера

| Фаза | Endpoint | Метод | Описание |
|---|---|---|---|
| 1. Decompose | `/api/ai-assistant/decompose/` | POST | Текст → дерево SelectionNode (LLM) |
| 2. Extract | `/api/ai-assistant/extract/{node_id}/` | POST | Узел → структурированные фильтры (LLM) |
| 3. Filter | `/api/ai-assistant/filter/{node_id}/` | POST | Фильтры → варианты (API) |
| 4. Select | `/api/ai-assistant/select/{node_id}/` | POST | Выбор продукта + каскад параметров |
| 5. Compare | `/api/ai-assistant/compare/{node_id}/` | POST | Требования vs фактические характеристики |
| — EBOM | `/api/ai-assistant/ebom/{conv_id}/` | GET | Инженерная спецификация (требования) |
| — MBOM | `/api/ai-assistant/mbom/{conv_id}/` | GET | Производственная спецификация (артикулы) |
| — Tree | `/api/ai-assistant/tree/{conv_id}/` | GET | Полное дерево подбора |

Плюс legacy-эндпоинты: `analyze/`, `execute/`, `query/`, `run-query/`.

---

## Как настраивать промпты и схемы

Всё хранится в БД, редактируется через **Django Admin** (`/admin/ai_assistant/`):

### Фаза 1 (decompose)
- **Step Configs** → `decompose / *` → указывает `prompt_template` и `model_role`
- **AI Prompt Templates** → `decode v2` — текст промпта (можно создать `v3` и переключить StepConfig)
- JSON-схема не используется (свободный текст, парсится из markdown)

### Фаза 2 (extract) — для каждого типа оборудования своя пара:
- **Step Configs** → `extract / actuator` → промпт `extract_actuator v1` + схема `actuator_filters v1`
- Аналогично для: `solenoid`, `bkv`, `cable_gland`, `pneumatic_fitting`, `filter_regulator`

### Выбор модели
- **AI Providers** → поле `model_mapping` (JSON):
  ```json
  {"classification": "deepseek-chat", "extraction": "deepseek-v4-flash", "debug": "deepseek-v4-pro"}
  ```
- `DeepSeekClient._model_for(role)` читает этот маппинг при каждом вызове
- Для переопределения под клиента: **Step Config Overrides**

---

## Файловая структура

```
ai_assistant/
├── __init__.py
├── apps.py
├── models/                            # 13 моделей (распакованы из models.py)
│   ├── __init__.py                    #   реэкспорт всех моделей
│   ├── ai_conversation.py
│   ├── ai_message.py
│   ├── ai_token_usage.py
│   ├── ai_client_provider.py
│   ├── ai_provider.py
│   ├── ai_query_sample.py
│   ├── ai_prompt_template.py
│   ├── equipment_type.py
│   ├── json_schema.py
│   ├── selection_node.py
│   ├── cascade_rule.py
│   ├── step_config.py
│   └── step_config_override.py
├── models.py                          #   реэкспорт (обратная совместимость)
├── admin/                             #   Админка (распакована из admin.py)
│   ├── __init__.py
│   ├── admin_ai_conversation.py
│   ├── admin_ai_message.py
│   ├── admin_ai_token_usage.py
│   ├── admin_ai_client_provider.py
│   ├── admin_ai_provider.py
│   ├── admin_ai_query_sample.py
│   ├── admin_ai_prompt_template.py
│   ├── admin_equipment_type.py
│   ├── admin_json_schema.py
│   ├── admin_selection_node.py
│   ├── admin_cascade_rule.py
│   ├── admin_step_config.py
│   └── admin_step_config_override.py
├── admin.py                           #   реэкспорт
├── urls.py
├── api/
│   ├── views.py                       #   AnalyzeView, DecomposeView, ExtractView, ...
│   └── serializers.py
├── services/
│   ├── tree_processor.py              #   TreeProcessor — центральный сервис (672 строки)
│   ├── deepseek_client.py             #   DeepSeekClient + get_deepseek_client()
│   └── token_tracker.py               #   save_token_usage, estimate_cost
├── classifiers/
│   └── __init__.py                    #   InstructorClassifier
├── schemas/
│   ├── __init__.py                    #   SCHEMA_REGISTRY
│   └── actuator_selection.py
├── management/commands/
│   └── seed_ai_prompts.py
├── test_pipeline.py                   #   45 тестов (модели + API + TreeProcessor)
└── migrations/                        #   7 миграций
```

Фронтенд: `frontend/src/pages/AiDebugPage.vue` + `frontend/src/components/TreeNodeDisplay.vue`.

---

## Как тестировать

```bash
# Прогнать тесты (файловая тестовая БД — быстро)
python manage.py test ai_assistant.test_pipeline --keepdb --verbosity=2

# Прогнать сэмплы через реальный LLM
python _debug_decompose.py            # все 8 сэмплов → _sample_output.txt
python _run_one.py 1                  # один сэмпл → _sample_1.json

# Быстро переключить модель (без админки)
python manage.py shell -c "
from ai_assistant.models import AIProvider
p = AIProvider.objects.filter(is_active=True).first()
p.model_mapping['debug'] = 'deepseek-chat'  # быстро
p.model_mapping['debug'] = 'deepseek-v4-pro'  # точно
p.save()
"
```
