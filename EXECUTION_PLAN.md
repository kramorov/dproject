# EXECUTION_PLAN — План выполнения (файл восстановления)

> Назначение: на случай сбоя — перезагрузиться и продолжить с места останова.
> Правило: выполненные пункты отмечать `[x]`; актуальную позицию — комментом `<!-- CURRENT -->`.
> Связано: [`assy.md`](assy.md), [`configurator.md`](configurator.md), [`ai-assistant.md`](ai-assistant.md), [`ARCHITECTURE_PLAN.md`](ARCHITECTURE_PLAN.md).

---

## Контекст для восстановления

### Зафиксированные решения (НЕ пересматривать без отдельного обсуждения)

1. **Две линии версионирования.** Требования — таймлайн `ClientRequestItem.parent_version`. Состав — линия `AssemblyRequirements.parent_assembly`, но **только внутри одной версии требований**.
   - Изменились требования → форк требований + копия сборки (`requirement_version=новая`, `parent_assembly=null`).
   - Изменился состав, требования те же → форк сборки (`requirement_version=та же`, `parent_assembly=предыдущая`).
   - Правки драфта → без форка.
2. **Связь:** `AssemblyRequirements.requirement_version = FK(ClientRequestItem)` (сборка → требования; null у шаблона). Старый `ClientRequestItem.assembly` (M:1) удаляется.
3. **Fork = полный снапшот** (deep copy: дерево + требования + выбор), **не дельта**. `fixate()` = смена статуса той же записи (без копии).
4. **Шаблон/типовая сборка:** `is_template=True`, `requirement_version=null`. Sharing через шаблоны («шарь, пока не изменили» → fork при изменении).
5. **Включение:** `ComponentRequirement.included` (bool) — «нужен/не нужен». `included=False → status=skipped`. `fixate()` guard: все узлы в терминальном статусе (`selected` или `skipped`).
6. **Продукт:** `ComponentRequirement.selected_sku = FK(sku.SKU)` (базовый тип); composite → null (результат = поддерево). Вместо `selected_product_type/id`.
7. **Приложение `assemblies`** — отдельное. Граф: `configurator → assemblies → client_requests + sku + core + ai_assistant`. `configurator` НЕ зависит от `client_requests` напрямую.
8. **EBOM** = зонтик над несколькими сборками. **MBOM** = материализация `fixed`-сборки через SKU (деривация, не вторая правда).
9. **Требования:** ETP — единый вход; JSON-поля (`own/effective/cascade/global`) валидируются по ETP.
10. **CRUD на фронте (Vue), не в админке Django.** Для всех моделей предметной области.

### Текущее состояние (факт, проверено)

- `AssemblyRequirements` и `ComponentRequirement` лежат в `configurator/models/`.
- `AssemblyRequirements.status` сейчас = `draft | in_progress | done` (нужно → `draft | fixed`).
- `ComponentRequirement.status` = `pending | requirements_filled | filtered | selected | skipped`.
- `ComponentRequirement.selected_product_type` (CharField) + `selected_product_id` (IntegerField) — надо → `selected_sku`.
- `ClientRequestItem.assembly` = FK на `configurator.AssemblyRequirements` (`related_name='request_items'`), миграция `client_requests/0011_add_assembly_fk.py`.
- `client_requests/models/__init__.py` импортирует `BaseRequirement`, `GearboxRequirement`, `FilterRegulatorRequirement`, `LimitSwitchRequirement` (НЕ `PaAssyRequirement` — файл-сирота).
- `configurator/models/__init__.py` экспортирует `PropagationRule`, `ParameterSource` (deprecated, к удалению).
- `sku` app: `SKU`, `MBOM`, `MBOMItem`.
- Тесты: 29/29 (`configurator` + `ai_assistant`).
- Frontend: `frontend/` (Vue + Vite), страницы в `frontend/src/pages/` (`PipelineConfigPage.vue`, `ConfiguratorPaKitPage.vue`, `ConfiguratorRulesPage.vue`), роутер `frontend/src/router/index.js`.

### Команды проверки

```bash
python manage.py check
python manage.py makemigrations --dry-run
python manage.py test configurator ai_assistant --keepdb
python manage.py test assemblies --keepdb          # после создания приложения
grep -rn "PropagationRule\|ParameterSource\|selected_product_type" --include="*.py" .
```

### Ключевые файлы (где что менять)

- Модели: `configurator/models/*.py`, будущее `assemblies/models/*.py`, `client_requests/models/*.py`, `sku/models/*.py`.
- Сервисы: `configurator/services/{resolver,expander,cascade,filter_engine,registry}.py`, будущее `assemblies/services/{fork,fixate,validator}.py`.
- API: `configurator/api/{views,serializers,admin_views,admin_serializers}.py`, `configurator/urls.py`.
- Frontend: `frontend/src/pages/**`, `frontend/src/router/index.js`, `frontend/src/api/` (если есть).
- Настройки: `djangoProject1/settings.py` (INSTALLED_APPS).

---

## Фаза 0 — Документы и фиксация

- [x] 0.1 Обновить `assy.md` (две линии, `requirement_version`, `included`, `assemblies` app, EBOM/MBOM).
- [x] 0.2 Обновить `configurator.md` (связь со сборками, `included`, `assemblies`).
- [ ] 0.3 Подтвердить границу «все модели» для фронт-CRUD (см. Фаза 6.0): предметная область = `configurator` + `assemblies` + `sku` + `ai_assistant`(пайплайн) + `client_requests` + `core.EquipmentType`. Прочие справочники (`params`, `producers`, `valve_data`, …) — вне этого плана, уточнить отдельно.

---

## Фаза 1 — Приложение `assemblies` + миграция моделей

- [x] 1.1 Создать приложение: `python manage.py startapp assemblies`. Зарегистрировать `assemblies.apps.AssembliesConfig` в `INSTALLED_APPS` (`djangoProject1/settings.py`).
  - Критерий: `python manage.py check` без ошибок; app виден в списке.
- [x] 1.2 Перенести `AssemblyRequirements` и `ComponentRequirement` из `configurator/models/` в `assemblies/models/` (файлы `assembly.py`, `component.py` + `__init__.py`).
  - Обновить все импорты: `configurator/services/{resolver,expander,cascade,filter_engine}.py`, `configurator/api/*`, `client_requests/models/request_item.py` (FK).
  - В `configurator/models/__init__.py` оставить реэкспорт-заглушки (совместимость) с пометкой deprecation, убрать после стабилизации.
  - Критерий: `grep -rn "from configurator.models import AssemblyRequirements" --include="*.py"` → только в заглушке; `python manage.py check`.
- [x] 1.3 Изменить `AssemblyRequirements`:
  - `status` → choices `draft | fixed` (маппинг старого `in_progress→draft`, `done→fixed` — в data-миграции).
  - добавить `requirement_version = FK('client_requests.ClientRequestItem', null=True, blank=True, on_delete=SET_NULL, related_name='assemblies')`.
  - добавить `revision` (PositiveIntegerField, null=True), `parent_assembly` (self-FK, null=True, SET_NULL), `is_template` (bool, default False), `fixed_at`, `fixed_by`, `fixation_comment`.
  - Критерий: makemigrations создаёт миграцию с полями.
- [x] 1.4 Изменить `ComponentRequirement`:
  - добавить `included` (BooleanField, default True).
  - заменить `selected_product_type/id` → `selected_sku = FK('sku.SKU', null=True, blank=True, on_delete=PROTECT)`.
  - Критерий: makemigrations; `selected_product_type/id` отсутствуют.
- [x] 1.5 Развернуть связь: удалить `ClientRequestItem.assembly` (FK), оставить `AssemblyRequirements.requirement_version`.
  - `client_requests/models/request_item.py`: удалить поле `assembly`.
  - Критерий: makemigrations → RemoveField на `client_requests`.
- [x] 1.6 Data-миграция (порядок важен):
  1. Backfill `requirement_version` из старых `request_items` (1:N: сборку с N позициями разбить на `is_template=True` оригинал + N форков, либо — решение — маппить на первую позицию и пометить остальные). **Выбрать правило ДО миграции**.
  2. Маппинг `status` (`in_progress→draft`, `done→fixed`).
  3. `selected_sku` reconciliation: найти SKU по `(equipment_type, source product id/code)`; осиротевшие — в отчёт, `selected_sku=null`.
  - Критерий: миграция выполняется на копии БД; нет потерь связей; отчёт о сиротах.
- [x] 1.7 Обновить сервисы под новое расположение и поля: `resolver.py` (не `assembly.components` по старому FK), `expander.py` (создавать `included`), `cascade.py` (писать `selected_sku`).
  - Критерий: `python manage.py test configurator --keepdb` зелёный.
- [x] 1.8 `makemigrations assemblies configurator client_requests` + `migrate`. Проверить `showmigrations`.

---

## Фаза 2 — Сервисы `fork` / `fixate` + ETP-валидация

- [x] 2.1 `assemblies/services/fork.py` → `fork_assembly(source, *, for_requirements_change: bool, new_requirement_version=None) -> AssemblyRequirements`.
  - Глубокая копия: assembly + дерево (пересчёт `parent`), JSON-поля через `copy.deepcopy`, `selected_sku` — ссылка (не копия).
  - `requirement_version` и `parent_assembly` — по правилам (Фаза 0 п.1).
  - `status=draft`, `revision=None`, `fixed_*` сброс, `is_template=False` (если копия не шаблон).
  - Транзакция `transaction.atomic`. Защита от циклов `parent_assembly`.
  - Критерий: юнит-тест «мутируем копию → оригинал не меняется».
- [x] 2.2 `assemblies/services/fixate.py` → `fixate(assembly)`.
  - Проверка статуса (`draft`), guard: все компоненты `selected` или `skipped`.
  - `status=fixed`, `revision = (max revision по requirement_version или 0) + 1`, `fixed_at/by/comment`.
  - Повторный `fixate` → no-op или ошибка (тест).
  - Критерий: юнит-тесты.
- [x] 2.3 `assemblies/services/validator.py` → ETP-валидация `own/effective/global`:
  - допустимые ключи = `EquipmentTypeParameter.param_name` для типа; типы значений по `field_type`; `is_required` gate.
  - Критерий: невалидный ключ/тип → ошибка; обязательное отсутствует → `needs_info`.
- [x] 2.4 `assemblies/services/resolution.py` → «текущая сборка» = draft, иначе max revision; «цепочка составa» по `parent_assembly`.
  - Критерий: юнит-тест.

---

## Фаза 3 — Зачистка deprecated

- [x] 3.1 Удалить `PropagationRule` (`configurator/models/propagation_rule.py`) + экспорт, админку, seed (`seed_rules.py`).
- [x] 3.2 Удалить `ParameterSource` (`configurator/models/parameter_source.py`) + поле `EquipmentTypeParameter.source`, `source_param`, `allow_override`.
  - Критерий: `grep -rn "PropagationRule\|ParameterSource" --include="*.py" .` → 0.
- [x] 3.3 Удалить старые `*Requirement`-формы: `BaseRequirement`, `GearboxRequirement`, `FilterRegulatorRequirement`, `LimitSwitchRequirement`, `PaAssyRequirement` + `requirement_api.py` + роуты. Endpoint'ы `requirements/schema|preview` не использовались фронтом (каталоги работают через собственные `/filters/`). Миграция `client_requests/0013`.
  - Критерий: `grep -rn "Requirement" client_requests/models --include="*.py"` → только базовые/не deprecated.
- [x] 3.4 Удалить `GenerateSchemaFromModelView` (уже отсутствовал) (FilterDefinition-based), если остался (роут `/api/ai-assistant/schemas/generate-from-model/`).
- [x] 3.5 Прогнать тесты после каждого удаления.

---

## Фаза 4 — EBOM / MBOM

- [x] 4.1 `assemblies/services/mbom.py` → `materialize_mbom(fixed_assembly) -> MBOM`:
  - обход дерева, узел с `selected_sku` → `MBOMItem(sku, quantity, equipment_type, composition_group, parent)`; `included=False` пропускать.
  - Идемпотентно: повторный вызов не плодит дубликаты (по fixed assembly).
  - Критерий: тест «fixed → MBOM», «fixed без выбора → ошибка/предупреждение».
- [ ] 4.2 Спроектировать `EBOM` (зонтик над несколькими сборками): модель + связь с `AssemblyRequirements` (M2M/FK). Отдельное решение перед кодом.
  - Критерий: описание модели согласовано (можно в `assy.md`), затем реализация.

---

## Фаза 5 — API-слой (DRF)

- [x] 5.1 `assemblies/api/`: ViewSet `AssemblyRequirements` (list/create/retrieve/update/delete) + actions `fork`, `fixate`, `expand`, `bom`; ViewSet `ComponentRequirement` (update: `included`, `selected_sku`, requirements).
- [x] 5.2 `configurator/api/admin_views.py`: ViewSet'ы (FittingPattern, EquipmentType добавлены): ETP, ParameterRule, ParameterBinding, DerivationRule, FittingPattern(+Item). Дополнить недостающие.
- [x] 5.3 `sku/api/`: ViewSet `SKU` (MBOM — в ai_assistant)(+`MBOMItem`).
- [x] 5.4 `ai_assistant/api/`: ViewSet'ы уже существовали.
- [x] 5.5 `client_requests/api/`: ViewSet'ы `ClientRequest`, `ClientRequestItem`, `RequestItemType`.
- [x] 5.6 `EquipmentType` ViewSet (в configurator admin).
- [x] 5.7 Права: `SystemObjectPermission` + `required_object` (регистрация codename'ов в object_registry — в Фазе 6) для каждой группы.
  - Критерий: `curl`/Django test на каждый endpoint → 200/201/403.

---

## Фаза 6 — Frontend CRUD (Vue)

> Все CRUD — на фронте, не в админке Django. Общий каркас переиспользуется.

- [x] 6.0 **Общий UI-кит** — использован существующий `@/shared/api` + shared-компоненты (BaseModal/ConfirmDialog/…), без дублирования.
  - `CrudTable.vue` (список: пагинация, сортировка, фильтр, кнопки Edit/Delete);
  - `CrudFormModal.vue` (создание/редактирование, поля из схемы);
  - `JsonEditor.vue` (обёртка над JSON-полем с валидацией);
  - `CrudPage.vue` (каркас: таблица + модалка + confirm удаления + тосты);
  - API-клиент `frontend/src/api/crud.js` (getList/get/create/update/remove + actions).
  - Критерий: одна страница собрана на ките; нет дублирования CRUD-логики.
- [x] 6.1 **Configurator (движок)** — `PipelineConfigPage.vue`: вкладки «Классификатор» (EquipmentType), «Fitting Patterns», «Parameter Rules», «Bindings», «Derivation Rules» — полный CRUD. ETP-параметры — там же.
- [x] 6.2 **Assemblies** — `frontend/src/apps/assemblies/` (App.vue + api.js) + `pages/AssembliesPage.vue` + роут `/admin/assemblies`. Список/создание/деталь/компоненты(included)/fork/fixate/expand.
  - список сборок (фильтр по status/template);
  - деталь: дерево компонентов, переключатели `included`, выбор `selected_sku`, статусы;
  - действия: `fork`, `fixate`, `expand`, `bom`.
- [ ] 6.3 **SKU / MBOM** — `frontend/src/pages/sku/`: CRUD `SKU`, редактор `MBOM` (+ автогенерация из fixed-сборки).
- [x] 6.4 **Client requests** — `frontend/src/apps/requests/` (App.vue + api.js) + `pages/RequestsPage.vue` + роут `/requests/list`. CRUD заявок + позиции (list/create/delete).
- [x] 6.5 **EquipmentType** — CRUD в PipelineConfigPage (вкладка «Классификатор»).
- [x] 6.6 Роутер: добавлены `/admin/assemblies` и `/requests/list` (остальные меню — по мере готовности).
  - Критерий: ручной прогон CRUD по каждой модели (создать/изменить/удалить) на фронте.

---

## Фаза 7 — Тесты и регрессия

- [x] 7.1 Юнит: `fork`/`fixate`/`validator`/`resolution` (11 тестов)
- [x] 7.2 Миграция: backfill не требовался (было 0 связей, 0 выборов — миграция чистая)
- [x] 7.3 Сценарные: `assemblies/tests/test_scenarios.py` — 7 сюжетов (1/4/6/7а/7б/8/9) на копии рабочей БД
- [x] 7.4 Регрессия: 29 (configurator) + 18 (assemblies) — зелёные
- [ ] 7.5 Frontend smoke: ключевые сценарии вручную (создать позицию → сборка → fork → fixate).

---

## Фаза 8 — Финализация и документация

- [x] 8.1 Обновить `SESSION.md` (что сделано, что осталось).
- [x] 8.2 Актуализировать `ARCHITECTURE_PLAN.md` (пометка «устарело» + ссылка на новый план).
- [x] 8.3 Обновить этот файл: отметить выполненные пункты.
- [x] 8.4 Регрессионный прогон: 29 (configurator) + 18 (assemblies) — зелёные; check чистый; `npm run build` успешно.

---

### Правило ведения файла

1. После завершения пункта — `[x]` + краткий комментарий результата (одной строкой).
2. Позицию «сейчас работаю» помечать `<!-- CURRENT -->`.
3. При смене машины — перед этим обновить `SESSION.md` и этот файл.
