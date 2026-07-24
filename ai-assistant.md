# AI Assistant — архитектура и документация

> Последнее обновление: 2026-07-24

## Общая схема работы

```
Пользователь → /ai-debug (фронт) → /api/ai-assistant/analyze/
                                        │
                                        ▼
                              ┌─────────────────┐
                              │  QueryOrchestrator│
                              │  Фаза 1: analyze  │
                              └────────┬────────┘
                                       │
                          ┌────────────┴────────────┐
                          │   1. Decompose (v4-pro)  │
                          │   Промпт из БД или код   │
                          │   Анализ + валидация      │
                          └────────────┬────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
               ✅ ready          ⚠️ needs_info        ❌ rejected
          «Всё понятно»     «Уточните: ...»     «Не наша тематика»
                    │
                    ▼
          Кнопка «▶ Продолжить»
                    │
                    ▼
          POST /api/ai-assistant/execute/
                    │
                    ▼
              ┌───────────┐
              │ TaskGraph  │
              │ Топологич. │
              │ сортировка │
              └─────┬─────┘
                    │
         ┌──────────┼──────────┐
         ▼          ▼          ▼
    Уровень 1   Уровень 2   Уровень 3
    (привод,    (БКВ,       (каб.вводы,
    фильтр)     соленоид)   фитинги)
         │          │          │
         ▼          ▼          ▼
    _run_actuator  _run_bkv  _run_solenoid
    _pipeline()   (заглушка) (заглушка)
         │
         ▼
    process_selection_params()
    (существующий подбор)
```

### Модели DeepSeek

| Этап | Модель | Настройка |
|------|--------|-----------|
| Decompose + отладка | `deepseek-v4-pro` | `AI_ASSISTANT_MODEL_DEBUG` |
| Извлечение фильтров | `deepseek-v4-flash` | `AI_ASSISTANT_MODEL_EXTRACTION` |
| Классификация | `deepseek-chat` | `AI_ASSISTANT_MODEL_CLASSIFICATION` |

Один API-ключ на все модели. Настройки в `djangoProject1/settings.py`.

---

## Что уже сделано

### Бэкенд

- **Модели** (6): `AIConversation`, `AIMessage` (+ `parent` FK, `context_summary`), `AITokenUsage`, `AIClientProvider`, `AIQuerySample`, `AIPromptTemplate`
- **API endpoints**:
  - `POST /api/ai-assistant/analyze/` — Фаза 1: decompose + валидация
  - `POST /api/ai-assistant/execute/` — Фаза 2: выполнение графа задач
  - `GET/POST/PATCH/DELETE /api/ai-assistant/samples/` — CRUD семплов запросов
  - `GET/POST/PATCH/DELETE /api/ai-assistant/prompts/` — CRUD промптов
- **QueryOrchestrator** — двухфазная обработка
- **TaskGraph** — граф зависимостей с топологической сортировкой
- **InstructorClassifier** — классификация запросов
- **DeepSeekClient** — обёртка над OpenAI API + Instructor
- **Token tracker** — учёт токенов и стоимости
- **Schema registry** — DB-first, code-fallback схемы и промпты
- **Seed command** — `python manage.py seed_ai_prompts --force`
- **Decompose V2** — промпт в БД, редактируется через админку/фронт

### Фронтенд

- **`/ai-assistant`** (`AiAssistantPage.vue`) — публичная страница: textarea, результат, Pass 0 анализ, Pass 1/2 фильтры, статистика токенов
- **`/ai-debug`** (`AiDebugPage.vue`) — страница отладки (трёхпанельная):
  - Левая панель: список запросов, CRUD, кнопка «→» в поле ввода
  - Центр: textarea + кнопка «Анализировать», статус-панель (ready/needs_info/rejected), прогресс-лог выполнения
  - Правая панель: список промптов, чекбокс выбора, CRUD
  - Модальные окна для редактирования запросов и промптов
  - Статистика: токены за запрос / за сессию, avg, стоимость

### Интеграция

- **Пневмоприводы**: `_run_actuator_pipeline()` → `process_selection_params()` — работает
- **Остальные типы**: заглушки (`skipped` с сообщением «нет схемы»)

---

## Модели данных

| Модель | Назначение | Ключевые поля |
|--------|-----------|---------------|
| `AIConversation` | Диалог / цепочка запросов | customer, session_key, status, intent, source |
| `AIMessage` | Одно сообщение | parent (FK→self), role, structured_content, reasoning, context_summary, prompt_used |
| `AITokenUsage` | Учёт токенов | message (1:1), model, prompt/completion/reasoning tokens, cost_estimate |
| `AIClientProvider` | AI-провайдер клиента | customer, provider_type, api_url, api_key |
| `AIQuerySample` | Тестовая выборка | text, response_text, expected_intent, prompt_template FK, comment |
| `AIPromptTemplate` | Версионируемые промпты | name, version, template_text, schema_json, is_active |

---

## Файловая структура

```
ai_assistant/
├── __init__.py
├── apps.py                          # AiAssistantConfig
├── models.py                         # 6 моделей
├── admin.py                          # Админка для всех моделей
├── urls.py                           # analyze/, execute/, samples/, prompts/
├── orchestrator.py                   # QueryOrchestrator (двухфазный)
├── task_manager.py                   # TaskGraph + DECOMPOSE_V2_PROMPT
├── classifiers/
│   └── __init__.py                   # InstructorClassifier
├── schemas/
│   ├── __init__.py                   # SCHEMA_REGISTRY + get_schema_config()
│   ├── actuator_selection.py         # JSON Schema + prompt для подбора
│   └── decompose.py                  # V1 decompose (reference)
├── services/
│   ├── __init__.py
│   ├── deepseek_client.py            # DeepSeekClient + singleton
│   └── token_tracker.py              # save_token_usage, estimate_cost
├── api/
│   ├── __init__.py
│   ├── views.py                      # AnalyzeView, ExecuteView, QueryView, ViewSets
│   └── serializers.py
├── prompts/                          # Текстовые копии промптов (dev)
│   ├── classify.txt
│   └── actuator_selection.txt
├── management/
│   └── commands/
│       └── seed_ai_prompts.py        # Загрузка промптов в БД
└── migrations/                       # 5 миграций
```

---

## Как тестировать

1. Запустить Django + Vite dev сервер
2. Открыть `http://localhost:8000/ai-debug`
3. Ввести запрос: «подбери пневмопривод для дискового затвора ДУ300 с моментом 150 Нм»
4. Нажать «Анализировать» → зелёная панель «Всё понятно»
5. Нажать «▶ Продолжить» → прогресс-лог
