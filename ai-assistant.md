 # AI Assistant — архитектура и документация                          
                                                                      
 > Последнее обновление: 2026-07-29                                   
                                                                      
 ## Общая схема работы                                                
                                                                      
 Запрос → Classify (LLM) → intent + types                             
   → Decompose (LLM) → плоский список [{type, summary}]               
   → Expand Tree (Python) → CompositionGroup: required/optional/XOR   
   → Extract (LLM) → для каждого узла: summary → фильтры              
   → Filter (API) → поиск вариантов                                   
   → Select → Compare → EBOM/MBOM                                     
                                                                      
 ---                                                                  
                                                                      
 ## Модели данных                                                     
                                                                      
### Конвейер подбора
 | Модель | Назначение |                                                                  
 |---|---|                                                                                
 | `AIConversation` | Сессия: customer FK, source, status, intent, selection_tree |       
 | `SelectionNode` | Узел дерева: parent, equipment_type (→ core), level, path, status |  
 | `EquipmentType` | **core.models** — классификатор + правила комплектации + AI-поля |   
 | `CascadeRule` | Каскад параметров: parent_type → child_type, mapping |                 
                                                                                          
 ### Конфигурация скиллов                                                                 
                                                                                          
 | Модель | Назначение |                                                                  
 |---|---|                                                                                
 | `PipelineSkill` | Скилл: step + equipment_type + prompt + schema + model_role |        
 | `SkillOverride` | Клиентское переопределение скилла |                                  
 | `AIPromptTemplate` | Версионируемый промпт (code-based композиция) |                   
 | `JSONSchema` | Версионируемая JSON-схема |                                             
                                                                                          
 ### Сообщения и биллинг                                                                  
                                                                                          
 | Модель | Назначение |                                                                  
 |---|---|                                                                                
 | `AIMessage` | Сообщение: content, prompt_used, prompt_template, latency_ms |           
 | `AITokenUsage` | Токены + биллинг: customer, prompt_tokens, cost_estimate, latency_ms |
                                                                                          
 ---                                                                                      
                       ·                                                                  
 ## Фазы конвейера                                                                        
                                                                                          
 | Фаза | Кто | Описание |                                                                
 |---|---|---|                                                                            
 | 0. Classify | LLM | intent + types |                                                   
 | 1. Decompose | LLM | плоский список [{type, summary}] |                                
 | 1.5 Expand | Python | CompositionGroup → дерево |                                      
 | 2. Extract | LLM | summary → формальные фильтры |                                      
 | 3. Filter | API | поиск вариантов |                                                    
 | 4. Select | LLM/User | выбор продукта |                                                
    | 5. Compare | Python | param_semantics |                                  
                                                                               
    ---                                                                        
                                                                               
    ## CompositionGroup — правила комплектации (КОНЦЕПЦИЯ)                     
                                                                               
    > Проект: 2026-07-29. Код не написан.                                      
                                                                               
    ### Идея                                                                   
                                                                               
    ИИ не строит дерево. Он возвращает плоский список типов с параметрами.     
    Дерево достраивается автоматически по правилам, описанным в EquipmentType. 
                                                                               
    ### Модели (планируемые)                                                   
                                                                               
▏ EquipmentType — добавляются:                                                 
▏ ────────────────────────────────────────                                     
▏ required_children = M2M('self')   # всегда: БКВ → cable_gland                
▏ optional_children = M2M('self')   # опции: actuator → solenoid | positioner  
▏                                                                              
▏ Новая модель:                                                                
▏ ────────────────────────────────────────                                     
▏ class CompositionRule(models.Model):                                         
▏ equipment_type = FK                                                          
▏ child_type = FK                                                              
▏ exclusive_group = CharField  # одинаковый group = XOR                        
▏ default = BooleanField                                                       
▏ required = BooleanField                                                      
                                                                               
    ### Правила (пример)                                                       
                                                                               
▏ Пневмопривод:                                                                
▏ required: [фитинг]                                                           
▏ Управление (XOR): соленоид (default) | позиционер                            
▏ Контроль (any): БКВ, фильтр-регулятор                                        
БКВ:                                                                                           
required: [кабельный ввод]                                                                     
                                                                                               
Сборка "Кран с ЭП":                                                                            
Арматура (all): ball-valve        ← рекурсия к правилам ball-valve                             
Привод (all): electro-actuator    ← рекурсия к правилам electro-actuator                       
                                                                                               
  ### Почему это лучше free-form decompose                                                     
                                                                                               
  - Промпт decompose в 5 раз короче                                                            
  - Ничего не забывается — required_children гарантирует                                       
  - XOR исключает некорректные комбинации                                                      
  - Вложенность через рекурсию правил                                                          
  - ИИ не строит дерево → парсинг не ломается                                                  
                                                                                               
  ---                                                                                          
                                                                                               
  ## Маршрутизация запросов                                                                    
                                                                                               
  `resolve_customer(source, email, api_key)` — `customer_resolver.py`                          
                                                                                               
  | source | Резолвится |                                                                      
  |---|---|                                                                                    
  | web_form | anonymous_web |                                                                 
  | email | ProjectCustomer.email |                                                            
  | api | CustomerApiKey.lookup() |                                                            
                                                                                             ><
  ---                                                                                          
                                                                                               
  ## Композиция промптов                                                                       
                                                                                               
  `AIPromptTemplate.code` — для `{code}` в template_text. Резолвится через `_resolve_prompt()`.
                                                                                               
  ---                                                                                          
                                                                                               
  ## Latency tracking                                                                          
   `PipelineSkill.avg_latency_ms` — скользящее среднее по 5 вызовам. Обновляется после decompose и extract.
                                                                                                           
   ---                                                                                                     
                                                                                                           
   ## Файловая структура                                                                                   
                                                                                                           
 ai_assistant/                                                                                             
 ├── models/       (ai_conversation, ai_message, ai_token_usage,                                           
 │                  pipeline_skill, skill_override, json_schema, ...)                                      
 ├── services/     (tree_processor, deepseek_client, token_tracker,                                        
 │                  customer_resolver)                                                                     
 ├── classifiers/  (InstructorClassifier — 9 intents)                                                      
 ├── api/          (views, serializers)                                                                    
 ├── admin/        (PipelineSkillAdmin, SkillOverrideAdmin, ...)                                           
 ├── test_pipeline.py  (45 тестов)                                                                         
 └── migrations/       (14 миграций)                                                                       
                                                                                                           
   Фронтенд: `AiDebugPage.vue`, `PipelineConfigPage.vue`.                                                  
                                                                                                           
   ---                                                                                                     
                                                                                                           
   ## Как тестировать                                                                                      
                                                                                                           
 python manage.py test ai_assistant.test_pipeline --keepdb --verbosity=2                                   
                                                                                                           
 Сменить модель                                                                                            
 ────────────────────────────────────────                                                                  
 python manage.py shell -c "                                                                               
 from ai_assistant.models import AIProvider                                                                
 p = AIProvider.objects.filter(is_active=True).first()                                                     
 p.model_mapping['debug'] = 'deepseek-chat'                                                                
 p.save()                                                                                                  
 "                                                                                                         

## Общий поток обработки

```
Запрос пользователя (web_form / email / api)
  │
  ▼
┌── Классификатор (быстрый LLM-вызов) ──────┐
│  9 интентов: selection, price_check, ...   │
│  1.2 сек, модель: classification           │
└──────────────┬────────────────────────────┘
               │ intent == "selection"
               ▼
┌── Decompose (LLM) ─────────────────────────┐
│  Текст → дерево компонентов с типами       │
│  ~3 сек, модель: debug                     │
│  Пример выхода:                            │
│  positions: [{                             │
│    components: [                            │
│      {id:"1.1", type:"pneumatic-actuator",  │
│       depends_on:[], quantity:1},           │
│      {id:"1.1.1", type:"directional-valve", │
│       depends_on:["1.1"]}                   │
│    ]                                        │
│  }]                                         │
└──────────────┬────────────────────────────┘
               │ auto-chain
               ▼
┌── Extract × N (LLM) ──────────────────────┐
│  Для каждого узла: тип → PipelineSkill →   │
│  промпт → JSON с параметрами               │
│  ~2 сек на узел, модель: extraction        │
│  Пример:                                    │
│  {action:"DA", torque_nm:55.5,              │
│   supply_pressure_bar:6, flange:"F05/F07"}  │
└──────────────┬────────────────────────────┘
               ▼
┌── Filter (API — не реализован) ────────────┐
│  Параметры → запрос в каталог              │
└──────────────┬────────────────────────────┘
               ▼
┌── Select (API — не реализован) ────────────┐
│  Выбор продукта + CascadeRule              │
└──────────────┬────────────────────────────┘
               ▼
┌── Compare (API — не реализован) ───────────┐
│  Требования vs факт                        │
└──────────────┬────────────────────────────┘
               ▼
          EBOM / MBOM
```

---

## Модели

### Конвейер

| Модель | Описание |
|---|---|
| `AIConversation` | Сессия. source (web_form/email/api), customer FK, intent, selection_tree (JSON-кеш) |
| `SelectionNode` | Узел дерева. parent (self-FK), equipment_type FK → core.EquipmentType, tree_id (JSON-путь), decompose_output, extract_output, status |
| `PipelineSkill` | Скилл: step + equipment_type → prompt_template + output_schema + model_role. Уник. code. avg_latency_ms |
| `SkillOverride` | Клиентское переопределение: customer → PipelineSkill + другой prompt/model |
| `CascadeRule` | Каскад параметров: parent_type → child_type, mapping (JSON) |
| `core.EquipmentType` | Канонический тип. Поля для AI: param_semantics, filter_endpoint |

### Промпты и схемы

| Модель | Описание |
|---|---|
| `AIPromptTemplate` | Версионируемый промпт. code (уник., для композиции), template_text (`{code}` → подстановка), sorting_order |
| `JSONSchema` | JSON Schema для structured output. name + version уникальны, sorting_order |

### Логирование и биллинг

| Модель | Описание |
|---|---|
| `AIMessage` | Сообщение: content (ответ LLM), prompt_used (что отправили), prompt_template FK, latency_ms |
| `AITokenUsage` | Токены + биллинг: prompt_tokens, completion_tokens, reasoning_tokens, cost_estimate, latency_ms, customer FK |

### Инфраструктура

| Модель | Описание |
|---|---|
| `AIProvider` | API-ключ провайдера. model_mapping: {classification, extraction, debug} → модель |
| `AIQuerySample` | Размеченный сэмпл для отладки: text, expected_intent, tree_json |
| `AIClientProvider` | API-ключ для внешних сайтов (WordPress). customer FK |

---

## Композиция промптов

`_resolve_prompt(template_text, **extra)` разрешает `{code}` в шаблоне:
- Ищет `AIPromptTemplate` с таким `code` → подставляет `template_text`
- Если нет в БД → ищет в `**extra` (user_text, requirements, ...)
- Если нет нигде → оставляет `{code}` как есть

```python
# decompose: {system_prompt} → AIPromptTemplate(code="system_prompt")
#           {user_text}      → extra["user_text"] = запрос клиента
prompt_text = self._resolve_prompt(config["prompt_text"], user_text=text)

# extract: {requirements} → JSON параметров узла
#          {user_text}     → оригинальный запрос (из selection_tree)
prompt = self._resolve_prompt(config["prompt_text"],
    user_text=..., requirements=...)
```

Системный промпт (`code="system_prompt"`) содержит каталог типов оборудования с кодами и правилами.

---

## Pipeline-скиллы

`PipelineSkill` связывает шаг + тип оборудования → промпт + схема + модель:

| code | step | equipment_type | prompt | model_role |
|---|---|---|---|---|
| DECOMPOSE | decompose | * | decompose_v4 | debug |
| PA-SELECT | extract | pneumatic-actuator | pneumatic-actuator v1 | extraction |
| SOLENOID-VALVE-SELECT | extract | directional-valve | directional-valve v1 | extraction |
| END-SWITCHES-BLOCK-SELECT | extract | lsb | lsb v1 | extraction |
| ... | extract | cable-gland, fr, fittings, ... | ... | extraction |

`PipelineSkill.avg_latency_ms` — скользящее среднее по 5 последним LLM-вызовам. Обновляется после каждого decompose и extract.

---

## Юзеры и клиенты

`resolve_customer(source, email, api_key)` → `ai_assistant/services/customer_resolver.py`

| source | customer |
|---|---|
| web_form | anonymous_web (системный клиент) |
| email | ProjectCustomer по email |
| api | API-ключ через CustomerApiKey |
| messenger | anonymous_web |

DecomposeView принимает `source`, `email` в теле, `X-Api-Key` в заголовке. `SkillOverride` применяется автоматически если найден.

---

## Frontend

### AiDebugPage (`/ai-debug`)

Левая панель: выбор запроса из AIQuerySample + текст + кнопка «Анализировать». Правая панель: выбор PipelineSkill. Результат: дерево компонентов с извлечёнными параметрами.

Компоненты:
- `ProgressBar.vue` — заполняющаяся полоса с текстом, расчёт из `avg_latency_ms`
- `TreeNodeDisplay.vue` — рекурсивное отображение узла + параметры + кнопки фаз
- `JsonTableViewer.vue` — табличный просмотр JSON (Key / Value)

### PipelineConfigPage (`/admin/pipeline-config`)

5 вкладок: Pipeline Skills, Overrides, Prompt Templates, JSON Schemas, Equipment Types. CRUD через REST API. JSON-модалки с 3 режимами: Tree (vue-json-pretty), Table (JsonTableViewer), Raw (textarea).

---

## API endpoints

| Endpoint | Метод | Описание |
|---|---|---|
| `/decompose/` | POST | text → дерево + extract. Параметры: text, source, email, skill_code |
| `/extract/{node_id}/` | POST | Ручной вызов extract для узла |
| `/tree/{conv_id}/` | GET | Полное дерево подбора |
| `/skills/` | GET/POST/PATCH | PipelineSkill CRUD |
| `/overrides/` | GET/POST/PATCH | SkillOverride CRUD |
| `/prompts/` | GET/POST/PATCH | AIPromptTemplate CRUD |
| `/schemas/` | GET/POST/PATCH | JSONSchema CRUD |
| `/equipment-types/` | GET/PATCH | core.EquipmentType AI-поля |
| `/customers/` | GET | ProjectCustomer список |
| `/model-roles/` | GET | Роли из AIProvider.model_mapping |
| `/ebom/{conv_id}/` | GET | EBOM (скелет) |
| `/mbom/{conv_id}/` | GET | MBOM (скелет) |

---

## Как тестировать

```bash
# Тесты (45 штук, ~5 сек)
python manage.py test ai_assistant.test_pipeline --keepdb

# Отладка через AiDebugPage
# 1. Открыть /ai-debug
# 2. Выбрать скилл DECOMPOSE
# 3. Вставить запрос клиента
# 4. Нажать «Анализировать»

# Посмотреть что реально отправилось в LLM
python manage.py shell -c "
from ai_assistant.models import AIMessage
m = AIMessage.objects.filter(intent='decompose').order_by('-id').first()
print(m.prompt_used)
"
```
