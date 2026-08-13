> ⚠️ **УСТАРЕЛО (частично).** Этот план относится к рефакторингу «FilterDefinition/CascadeRule → ETP/DerivationRule».
> Перефакторинг сборок выполнен по новому плану [`EXECUTION_PLAN.md`](EXECUTION_PLAN.md) и описан в [`assy.md`](assy.md).
> Ниже — историческая справка и метрики, частично снятые.

# ARCHITECTURE PLAN — Гармонизация системы

> Составлен: 2026-08-12
> Основание: архитектурный аудит ai_assistant + configurator
> Фаза: завершение миграции с FilterDefinition/CascadeRule/QueryOrchestrator → EquipmentTypeParameter/DerivationRule/TreeProcessor

---

## Сводка текущего состояния (факты)

| Артефакт | Статус | Данные |
|----------|--------|--------|
| `QueryOrchestrator` + `TaskGraph` | Жив в коде, помечен "Legacy" в urls.py | 2 endpoint-а: `/analyze/`, `/execute/` |
| `/execute/` на фронте | Используется | `AiDebugPage.vue:217` |
| `TreeProcessor` (новый конвейер) | Основной | `/decompose/`, `/extract/`, `/filter/`, `/select/`, `/compare/` |
| `EquipmentType.prompt_template` + `output_schema` | Мёртвые поля | 0 использований в коде |
| `CascadeRule` | Жив, используется | 7 записей, `tree_processor.py:609` |
| `DerivationRule` | Модель готова, админка готова | **0 записей** |
| `_validate_required` / `_resolve_labels` | Всё ещё на FilterDefinition | `tree_processor.py:445,469` → `get_filter_definitions_for_ct()` |
| `EquipmentTypeParameter` | Готов, 82 записи | `is_required` не подключён к AI |
| Кодировка `.py` | Повреждена | double-encoding Windows-1251→UTF-8 |
| `configurator.md` | Устарел | 34 записи ETP (факт: 82) |
| `PipelineConfigPage` | Неполный CRUD | 5 вкладок: Skills✅, Overrides✅, Prompts✅, Schemas❌(только генерация), EquipmentTypes🟡(частично) |
| `ConfiguratorRulesPage` | Страница-заглушка | 3 вкладки: 2 редиректа на PipelineConfig + read-only источники |

---

## План: 5 фаз + Фаза 0 (PipelineConfig)

### Фаза 0: Консолидация PipelineConfigPage — единый центр управления (Priority)

> **Цель**: все компоненты системы должны иметь CRUD на `/admin/pipeline-config`.
> Сейчас часть настроек разбросана по ConfiguratorRulesPage и Django admin.

#### Текущее состояние PipelineConfigPage (5 вкладок)

| Вкладка | Компонент | CRUD | Проблема |
|---------|-----------|------|----------|
| Pipeline Skills | `PipelineSkill` | ✅ Полный | — |
| Overrides | `SkillOverride` | ✅ Полный | — |
| Prompt Templates | `AIPromptTemplate` | ✅ Полный | — |
| JSON Schemas | `JSONSchema` | ❌ Нет CRUD | Только авто-генерация из ETP, нет таблицы записей |
| Equipment Types | `EquipmentType` + `EquipmentTypeParameter` | 🟡 Частично | Нет: filter_type, data_source_type, options_config, source, ai_extraction_hint |

#### Что нужно добавить на PipelineConfigPage

##### 0.1 Вкладка «JSON Schemas» — полноценный CRUD

**Сейчас**: показывает только генератор схем из ETP. Нет таблицы существующих `JSONSchema` записей.

**Нужно**:
- Таблица всех `JSONSchema` записей (name, version, description, is_active)
- Кнопки: Create, Edit (JSON editor в модалке), Delete
- Кнопка «Generate from ETP» (то, что уже есть) — оставить внизу или справа

**API**: `/ai-assistant/schemas/` — ViewSet уже существует, просто не используется на фронте.

---

##### 0.2 Вкладка «Cascade Rules» — DerivationRule CRUD

**Сейчас**: `DerivationRule` — нигде на фронте (только Django admin). `CascadeRule` — в Django admin.

**Нужно**:
- Таблица всех `DerivationRule` записей: source_type, target_type, source_product_field, target_param, transform, condition, priority, is_active
- CRUD: Create, Edit (inline), Delete
- После миграции `CascadeRule` → `DerivationRule` (Фаза 3.1) здесь будут все 7+ правил

**API**: `/configurator/admin/derivation-rules/` — ViewSet уже существует.

---

##### 0.3 Вкладка «Parameter Rules» — ParameterRule + ParameterBinding CRUD

**Сейчас**: нигде на фронте (только Django admin).

**Нужно**:
- Подвкладка «Rules»: таблица `ParameterRule` — code, match_type, hardness, relaxation_strategy
- Подвкладка «Bindings»: таблица `ParameterBinding` — rule → EquipmentType + param_name
- CRUD для обоих

**API**:
- `/configurator/admin/parameter-rules/` — ViewSet
- `/configurator/admin/parameter-bindings/` — ViewSet

---

##### 0.4 Вкладка «Sources» — ParameterSource (read-only)

**Сейчас**: на `ConfiguratorRulesPage` → вкладка «Источники» (read-only, 4 записи).

**Нужно**: перенести таблицу в PipelineConfigPage как отдельную вкладку «Sources». Read-only — 4 записи (user, global, parent, derived), менять не предполагается.

**API**: `/configurator/admin/parameter-sources/` — ViewSet.

---

##### 0.5 Вкладка «Composition Groups» — CompositionGroup CRUD

**Сейчас**: нигде на фронте (только Django admin).

**Нужно**:
- Таблица всех `CompositionGroup`: name, code, group_type, parent, equipment_types (M2M), references (M2M)
- CRUD: Create, Edit (с выбором equipment_types и references), Delete
- Визуализация дерева (parent/children)

**API**: `/ai-assistant/composition-groups/` — ViewSet уже существует.

---

##### 0.6 Вкладка «Equipment Types» — добавить недостающие поля ETP

**Сейчас в таблице**: param_name, field_path, param_type, unit, compare_direction, compare_label, is_required, is_active.

**Нужно добавить колонки**:
- `filter_type` — select: IP_RANK, EXD_COMPATIBLE, TEMP_MIN, TEMP_MAX, exact, ...
- `data_source_type` — select: global_model, field_values, foreign_key, choices, custom
- `options_config` — text input (JSON)
- `source` — select из ParameterSource (user, global, parent, derived)
- `ai_extraction_hint` — text input

**API**: `/configurator/admin/equipment-type-parameters/` — ViewSet, поля уже есть в модели.

---

##### 0.7 Депрекейт `ConfiguratorRulesPage`

После переноса всех вкладок на PipelineConfigPage:
- `ConfiguratorRulesPage.vue` → заменить на редирект: `router.replace('/admin/pipeline-config')`
- `frontend/src/router/index.js` → route `/admin/configurator-rules` → redirect
- `TopMenu.vue` → убрать ссылку «Правила конфигуратора», оставить только «Настройка AI Pipeline»

---

##### 0.8 (Опционально) AIProvider — если нужен CRUD на фронте

Добавить ViewSet для `AIProvider` и вкладку «Providers». Пока можно оставить в Django admin.

---

#### Итоговая структура PipelineConfigPage после консолидации

```
/admin/pipeline-config
├── Pipeline Skills      ← было
├── Overrides            ← было
├── Prompt Templates     ← было
├── JSON Schemas         ← БЫЛО: только генератор → СТАЛО: CRUD + генератор
├── Equipment Types      ← БЫЛО: частично → СТАЛО: +5 колонок ETP
├── Cascade Rules        ← НОВОЕ: DerivationRule CRUD
├── Parameter Rules      ← НОВОЕ: ParameterRule + ParameterBinding CRUD
├── Sources              ← НОВОЕ: ParameterSource (из ConfiguratorRulesPage)
└── Composition Groups   ← НОВОЕ: CompositionGroup CRUD
```

9 вкладок (было 5). Все компоненты системы — в одном месте.

---

### Фаза 1: Удаление мёртвого/дублирующего кода (Critical)

Эти изменения не ломают работающий функционал — только чистят.

#### 1.1 Депрекейт `analyze/` + `execute/`, удаление `QueryOrchestrator`

**Затрагивает:**
- `ai_assistant/api/views.py` — классы `AnalyzeView`, `ExecuteView`
- `ai_assistant/urls.py` — строки 26-27
- `ai_assistant/orchestrator.py` — весь файл (371 строка)
- `ai_assistant/task_manager.py` — `TaskGraph`, `EQUIPMENT_REQUIREMENTS`, `DECOMPOSE_V2_PROMPT`
- `frontend/src/pages/AiDebugPage.vue` — строка 217 (`/execute/`)

**Шаги:**
1. `AiDebugPage.vue:217` — заменить вызов `api.post('/ai-assistant/execute/', ...)` на последовательный вызов нового конвейера (`/decompose/` → для каждого узла `/filter/`). Либо просто удалить кнопку «Execute», если отладка идёт через новый конвейер.
2. `ai_assistant/urls.py` — закомментировать `analyze/` и `execute/`, добавить комментарий `# DEPRECATED: удалить после 2026-09-01`
3. `ai_assistant/api/views.py` — закомментировать `AnalyzeView` и `ExecuteView`
4. **Не удалять** `orchestrator.py` и `task_manager.py` сразу — оставить на 1 спринт, чтобы убедиться, что ни один внешний клиент не дёргает эти endpoint-ы (проверить логи).
5. Через спринт — удалить `orchestrator.py`, `task_manager.py`, и классы `AnalyzeView`/`ExecuteView`.

**Верификация:**
- `grep -r "analyze/\|execute/" frontend/` — только закомментированное
- `curl -X POST /api/ai-assistant/analyze/` → 404 или 410
- `python manage.py test ai_assistant` — все тесты проходят

---

#### 1.2 Удалить `prompt_template` и `output_schema` из `EquipmentType`

**Затрагивает:**
- `core/models/equipment_type.py` — поля `output_schema` (строка 95) и `prompt_template` (строка 101)
- `ai-assistant.md` — строка 207 (предупреждение про двойное обновление)
- Миграция `core`

**Шаги:**
1. Убедиться: `grep -r "equipment_type.*prompt_template\|equipment_type.*output_schema" --include="*.py"` → 0 совпадений (уже проверено — 0).
2. Создать миграцию, удаляющую поля `output_schema` и `prompt_template` из `core_equipmenttype`.
3. Обновить `ai-assistant.md` — убрать предупреждение про двойное обновление промптов.

**Верификация:**
- `python manage.py makemigrations core` — создаёт миграцию RemoveFields
- `python manage.py migrate` — без ошибок
- `grep -r "equipment_type.*prompt_template\|equipment_type.*output_schema"` → пусто

---

### Фаза 2: Переключение AI-конвейера на ETP (Critical)

Здесь меняется логика — нужна осторожность.

#### 2.1 `_validate_required` → `EquipmentTypeParameter.is_required`

**Затрагивает:**
- `ai_assistant/services/tree_processor.py` — метод `_validate_required` (строки 443-461)
- `ai_assistant/api/views.py` — дубликат логики в `ExtractView` (строка ~384)

**Текущий код:**
```python
def _validate_required(self, node) -> str:
    from core.wizard_filter_registry import get_filter_definitions_for_ct
    defs = get_filter_definitions_for_ct(node.equipment_type.content_type_id)
    for fd in defs:
        if getattr(fd, 'mandatory', 'any') != 'yes':
            continue
        ...
```

**Целевой код:**
```python
def _validate_required(self, node) -> str:
    if not node.equipment_type:
        return None
    from configurator.models import EquipmentTypeParameter
    etp_params = EquipmentTypeParameter.objects.filter(
        equipment_type=node.equipment_type,
        is_required=True,
        is_active=True,
    )
    missing = []
    for p in etp_params:
        value = node.extract_output.get(p.param_name) if node.extract_output else None
        if value is None or value == '':
            missing.append(p.label or p.param_name)
    if not missing:
        return None
    labels = '», «'.join(missing)
    return f"Не удалось определить: «{labels}» для {node.equipment_type.name}. Уточните запрос."
```

**Шаги:**
1. Заменить тело `_validate_required` в `tree_processor.py`.
2. Найти и заменить дубликат в `ai_assistant/api/views.py` (в `ExtractView.post`).
3. Проверить: все ли ETP с `is_required=True` имеют те же `param_name`, что и `FilterDefinition.mandatory='yes'`. При несовпадении — дополнить ETP.

**Верификация:**
- `python manage.py test ai_assistant` — тесты проходят
- Ручной тест: отправить `/decompose/` с неполным запросом → `needs_info` с корректным списком полей

---

#### 2.2 `_resolve_labels` → `EquipmentTypeParameter.get_options()`

**Затрагивает:**
- `ai_assistant/services/tree_processor.py` — метод `_resolve_labels` (строки 463-488)
- `ai_assistant/api/views.py` — дубликат

**Текущий код:**
```python
def _resolve_labels(self, node) -> dict:
    from core.wizard_filter_registry import get_filter_definitions_for_ct
    defs = get_filter_definitions_for_ct(node.equipment_type.content_type_id)
    model_class = node.equipment_type.content_type.model_class()
    for fd in defs:
        field_labels[fd.param_name] = fd.label or fd.param_name
        opts = fd.get_options(model_class) if model_class else []
        ...
```

**Целевой код:**
```python
def _resolve_labels(self, node) -> dict:
    labels = {}
    field_labels = {}
    eo = node.extract_output or {}
    if not eo or not node.equipment_type or not node.equipment_type.content_type:
        return {'_field_labels': field_labels}
    from configurator.models import EquipmentTypeParameter
    etp_params = EquipmentTypeParameter.objects.filter(
        equipment_type=node.equipment_type,
        is_active=True,
    )
    model_class = node.equipment_type.content_type.model_class()
    for p in etp_params:
        field_labels[p.param_name] = p.label or p.param_name
        value = eo.get(p.param_name)
        if value is None or value == '':
            continue
        try:
            opts = p.get_options(model_class) if model_class else []
            for o in opts:
                if o.get('id') == value:
                    labels[p.param_name] = o.get('name', str(value))
                    break
        except Exception:
            pass
    labels['_field_labels'] = field_labels
    return labels
```

**Шаги:**
1. Заменить тело `_resolve_labels` в `tree_processor.py`.
2. Заменить дубликат в `views.py`.

**Верификация:**
- Ручной тест: `/extract/{node_id}/` → в ответе есть `_labels` с человекочитаемыми значениями

---

### Фаза 3: Унификация каскада (Critical)

#### 3.1 `CascadeRule` → `DerivationRule`

**Текущее состояние:**
- `CascadeRule`: 7 записей, используется в `tree_processor.py:609` (`select_product`)
- `DerivationRule`: **0 записей**, модель + API + админка готовы
- `configurator/services/cascade.py` — реализует каскад через DerivationRule

**Затрагивает:**
- `ai_assistant/services/tree_processor.py` — метод `select_product` (строки ~600-640)
- `ai_assistant/models/cascade_rule.py` — удалить
- `ai_assistant/admin/admin_cascade_rule.py` — удалить
- `ai_assistant/management/commands/seed_pipeline.py` — убрать CascadeRule, добавить DerivationRule
- `ai_assistant/test_pipeline.py` — `CascadeRuleTests` → `DerivationRuleTests`
- Миграция `ai_assistant`

**Шаги:**
1. **Перенос данных**: написать management-команду `migrate_cascade_to_derivation`:
   ```python
   for cr in CascadeRule.objects.filter(is_active=True):
       for src_field, tgt_param in cr.mapping.items():
           DerivationRule.objects.get_or_create(
               source_type=cr.parent_type,
               target_type=cr.child_type,
               source_product_field=src_field,
               target_param=tgt_param,
               defaults={'is_active': True}
           )
   ```
   Запустить.
2. Проверить: `DerivationRule.objects.count()` → 7+ (может быть больше из-за нескольких полей в mapping).
3. `tree_processor.py` → заменить `CascadeRule.objects.filter(...)` на `DerivationRule.objects.filter(...)` с соответствующей логикой применения (она уже есть в `configurator/services/cascade.py` — можно вызвать `apply_derivation_rules`).
4. Удалить `CascadeRule` из `models/__init__.py`, админки, тестов.
5. Создать миграцию, удаляющую таблицу `CascadeRule`.

**Верификация:**
- `DerivationRule.objects.count() >= 7`
- `python manage.py test ai_assistant` — тесты проходят
- `python manage.py test configurator` — 29/29 pass
- Ручной тест: выбрать привод → каскад на соленоид отрабатывает

---

### Фаза 4: Документация и гигиена кода (Substantial)

#### 4.1 Починить кодировку `.py`-файлов

**Затрагивает:** большинство `.py`-файлов в проекте (русские комментарии).

**Шаги:**
1. Создать скрипт `fix_encoding.py` в корне:
   ```python
   import os
   for root, dirs, files in os.walk('.'):
       if '__pycache__' in root or '.git' in root or 'node_modules' in root:
           continue
       for f in files:
           if not f.endswith('.py'):
               continue
           path = os.path.join(root, f)
           with open(path, 'rb') as fh:
               raw = fh.read()
           try:
               text = raw.decode('utf-8')
           except UnicodeDecodeError:
               continue
           # Проверяем, есть ли моджибаке-паттерн
           if 'Р В' not in text and 'РЎвЂ' not in text:
               continue
           # Пробуем обратную перекодировку
           try:
               fixed = text.encode('cp1251').decode('utf-8')
               with open(path, 'w', encoding='utf-8') as fh:
                   fh.write(fixed)
               print(f'FIXED: {path}')
           except Exception as e:
               print(f'SKIP: {path} — {e}')
   ```
2. Запустить на одном файле (`orchestrator.py`) — проверить результат.
3. Если ок — запустить на всех.
4. Пройти глазами 5-10 случайных файлов — убедиться, что русский текст читаем.

**Верификация:**
- `grep -r "Р В\|РЎвЂ" --include="*.py"` → 0 совпадений

---

#### 4.2 Актуализировать `configurator.md`

**Изменения:**
- Строка «34 записи» → «82 записи»
- Добавить примечание: «PropagationRule + ParameterSource — удалены из кода и БД (миграция 0004-0008)»
- Удалить упоминания PropagationRule из списка моделей

---

#### 4.3 Актуализировать `ai-assistant.md`

**Изменения:**
- Убрать строку 207: «⚠️ При обновлении промптов нужно обновлять оба: PipelineSkill и EquipmentType»
- В разделе «Интеграция с Configurator» — обновить статус: CascadeRule → DerivationRule
- Обновить TODO-список: вычеркнуть выполненные, добавить новые

---

#### 4.4 Документировать `filter_engine.py` и `cascade.py` в `ai-assistant.md`

Добавить в раздел «Интеграция с Configurator»:
```markdown
### filter_engine.py
- `FilterEngine.filter(component)` — hard-filter (обязательные параметры) + soft-filter (scoring)
- При отсутствии точных совпадений — релаксация (последовательное ослабление фильтров)
- `_filter_pa_selector` — делегация в TorqueSelectorService для пневмоприводов

### cascade.py
- `apply_derivation_rules(source_type, product_specs, target_type)` → dict cascade_params
- Поддерживает `condition` (применять правило только если)
- Поддерживает `transform` (преобразование значений: regex, map, round)
```

---

### Фаза 5: Финализационный TODO (Moderate)

#### 5.1 Актуализировать TODO-список в `ai-assistant.md`

Текущие пункты и их статус:

| Пункт | Статус |
|-------|--------|
| Унифицировать filter_handlers.py или FILTER_DEFINITIONS | Актуален |
| Генерация JSON-схем из модели | **Сделано** — `GenerateSchemaFromModelView` |
| mandatory на фронте каталогов | Актуален |
| Перенос PipelineConfigPage в SkillConfigPage | Актуален |
| AiCatalogSearch | Актуален |
| Неполный фильтр-маппинг | Актуален |
| Фильтр для пайплайна | Актуален |
| required/optional в JSON-схемах | Актуален |

Добавить новые пункты:
- [ ] Заменить `_validate_required` и `_resolve_labels` на ETP (→ Фаза 2)
- [ ] Мигрировать `CascadeRule` → `DerivationRule` (→ Фаза 3)
- [ ] Удалить `EquipmentType.prompt_template` и `output_schema` (→ Фаза 1.2)

---

## Итоговая очерёдность выполнения (ПРИОРИТЕТЫ 2026-08-12)

### Приоритет 1: Очистка хвостов и неиспользуемого кода (Неделя 1)

```
  ├── 1.2 Удалить EquipmentType.prompt_template/output_schema  ← мёртвые поля, 0 использований
  ├── 1.1 Депрекейт analyze/execute → пометить deprecated      ← старый конвейер
  ├── 4.1 Починить кодировку .py файлов                        ← моджибаке
  ├── Удалить GenerateSchemaFromModelView (FilterDefinition-based) ← ДУБЛИКАТ ETP-генератора
  │     Роут: /api/ai-assistant/schemas/generate-from-model/
  │     Заменён на: /configurator/admin/equipment-type-parameters/schema/?variant=ai
  ├── Удалить PropagationRule + ParameterSource (уже deprecated в SESSION.md)
  ├── Удалить CascadeRule (после миграции данных в DerivationRule, см. Приоритет 3)
  └── Удалить QueryOrchestrator + task_manager                 ← после проверки логов
```

> **JSON Schema генерация (ETP → 2 формата) — УЖЕ РЕАЛИЗОВАНА:**
> - `EquipmentTypeParameter.generate_json_schema(et, variant='ai'|'configurator')` — единый источник
> - API: `GET /configurator/admin/equipment-type-parameters/schema/?equipment_type=ID&variant=ai`
> - Frontend: `PipelineConfigPage.vue` → вкладка «JSON Schemas» → Generate
> - Старый `GenerateSchemaFromModelView` (FilterDefinition-based) — подлежит удалению

### Приоритет 2: Отладка EquipmentTypeParameter на ConfiguratorPaKitPage (Неделя 1-2)

```
  ├── Страница: /configurator/pa-kit (ConfiguratorPaKitPage.vue) ← ВОЗВРАЩЕНА в меню
  ├── Проверить filter-schema API: /configurator/equipment-types/{id}/filter-schema/
  ├── Проверить get_options() — все 6 стратегий (global_model, foreign_key, field_values, choices, custom)
  ├── Проверить filter_engine.py — hard/soft фильтры на реальных данных
  ├── Проверить cascade.py — DerivationRule после выбора продукта
  ├── 2.1 _validate_required → ETP (переключить с FilterDefinition на is_required)
  ├── 2.2 _resolve_labels → ETP (переключить с FilterDefinition.get_options на ETP.get_options)
  └── Ручной прогон полного цикла: выбор типа → ввод параметров → подбор → выбор → каскад
```

### Приоритет 3: PipelineConfigPage + унификация каскада (Неделя 3-4)

```
  ├── 3.1 CascadeRule → DerivationRule (миграция 7 записей + кода)
  ├── 0.1 JSON Schemas: CRUD-таблица + генератор
  ├── 0.2 Cascade Rules: DerivationRule CRUD
  ├── 0.3 Parameter Rules: ParameterRule + ParameterBinding CRUD
  ├── 0.4 Sources: ParameterSource (из ConfiguratorRulesPage)
  ├── 0.5 Composition Groups: CRUD
  ├── 0.6 Equipment Types: +5 колонок ETP
  └── 0.7 Депрекейт ConfiguratorRulesPage → redirect
```

### Приоритет 4: Документация и финализация (Неделя 5)

```
  ├── 4.2 Актуализировать configurator.md (34→82 записи)
  ├── 4.3 Актуализировать ai-assistant.md
  ├── 4.4 Документировать filter_engine и cascade
  ├── 5.1 Актуализировать TODO
  └── Регрессионное тестирование всего конвейера
```

---

## Метрики успеха

| Критерий | Как проверить |
|----------|---------------|
| Старый конвейер не отвечает | `curl /api/ai-assistant/analyze/` → 404/410 |
| Мёртвых полей EquipmentType нет | `grep -r "prompt_template\|output_schema" core/models/equipment_type.py` → только не от EquipmentType |
| Валидация через ETP | `_validate_required` не импортирует `wizard_filter_registry` |
| Каскад через DerivationRule | `DerivationRule.objects.count() >= 7` при `CascadeRule.objects.count() == 0` |
| Кодировка исправлена | `grep -r "Р В\|РЎвЂ" --include="*.py"` → 0 |
| Документация актуальна | `configurator.md` → «82 записи», `ai-assistant.md` → нет предупреждения про двойное обновление |
| Тесты проходят | `python manage.py test ai_assistant configurator` → все green |
