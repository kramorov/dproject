# CompositionGroup & EquipmentType — принципы и API

> Снапшот: 2026-07-30

## Назначение

**CompositionGroup** — правило композиции для сборки (BOM). Определяет, какие типы оборудования и подгруппы входят в состав изделия и по какому правилу они выбираются.

**EquipmentType** — тип оборудования. Привязывается к CompositionGroup через M2M.

## Модель CompositionGroup

```
CompositionGroup
├── name, code, description       — идентификация
├── group_type                     — required / optional / xor
├── sorting_order, is_active       — порядок, активность
│
├── parent (FK → self)            — ВЛОЖЕНИЕ: группа внутри другой
│   └── children (rev FK)          —   каскадное удаление
│
├── references (M2M → self)       — ССЫЛКА: группа ссылается на другую
│   └── referenced_by (rev M2M)    —   без каскада
│
├── equipment_types (M2M → ET)    — типы оборудования в группе
│
├── output_schema (FK → JSONSchema)     — схема выходного формата (MBOM/подбор)
└── prompt_template (FK → AIPromptTemplate) — шаблон промпта (MBOM/подбор)
```

## Модель EquipmentType

```
EquipmentType (core)
├── name, code, description       — идентификация
├── sorting_order, is_active       — порядок, активность
├── parent (FK → self)            — иерархия типов
├── level                          — уровень (0-5, авто из parent)
├── icon                           — emoji/класс
├── content_type (FK → ContentType) — Django-модель товара
├── filter_endpoint                — API-эндпоинт для фазы filter
├── param_semantics (JSON)         — семантика параметров для compare
├── title_template                 — шаблон заголовка карточки
├── output_schema (FK → JSONSchema)     — схема для extract
└── prompt_template (FK → AIPromptTemplate) — промпт для extract
```

### Связь схем и промптов

| Уровень | output_schema | prompt_template |
|---|---|---|
| `PipelineSkill` (step + equipment_type) | ✅ | ✅ |
| `CompositionGroup` | ✅ | ✅ |
| `EquipmentType` | ✅ | ✅ |

## Три типа элементов внутри группы

| Элемент | item_type | В БД | Семантика |
|---|---|---|---|
| 📦 EquipmentType | `equipment_type` | M2M `equipment_types` | Базовый тип |
| 📁 CompositionGroup | `composition_group` | FK `parent` | Вложенная группа |
| 🔗 Reference | `reference` | M2M `references` | Ссылка на другую группу |

### Правила

- **Вложение ≠ Ссылка**: группа не может быть одновременно ребёнком и ссылкой для одной группы-родителя
- **Ссылка** нужна, чтобы избежать дублирования: группа создаётся один раз, ссылаются из многих сборок
- **EquipmentType не может быть в корне дерева** — только внутри CompositionGroup

## API

Базовый URL: `/api/ai-assistant/`

### CompositionGroup CRUD

| Метод | URL | Описание |
|---|---|---|
| `GET` | `/composition-groups/` | Список (включает output_schema, prompt_template) |
| `POST` | `/composition-groups/` | Создать |
| `PATCH` | `/composition-groups/:id/` | Обновить (включая parent, output_schema, prompt_template) |
| `DELETE` | `/composition-groups/:id/` | Удалить (каскадно) |

### Ссылки

| Метод | URL | Описание |
|---|---|---|
| `POST` | `/composition-groups/:id/add_reference/` | Добавить ссылку |
| `POST` | `/composition-groups/:id/remove_reference/` | Убрать ссылку |
| `GET` | `/composition-groups/:id/referenced_by/` | Кто ссылается |

### Деревья

| Метод | URL | Описание |
|---|---|---|
| `GET` | `/composition-tree/` | Дерево CompositionGroup + EquipmentType + ссылки |
| `GET` | `/equipment-type-tree/` | Дерево EquipmentType |

### Схемы

| Метод | URL | Описание |
|---|---|---|
| `POST` | `/schemas/generate-from-model/` | Генерация схемы из FILTER_DEFINITIONS модели |

## Frontend

### BomConfigPage (`/admin/bom-config`)

Вкладки:
- **🌳 Дерево** — обзорное дерево CompositionGroup + EquipmentType
  - Двойной клик на группе → модалка: родитель, схема, промпт
  - Двойной клик на ET → модалка: название, код, родитель, уровень, иконка, схема, промпт, кнопка «Взять из модели»
  - Двойной клик на ссылке → модалка «Редактирование ссылки» (только смена родителя)
- **🏗️ Конструктор** — drag-and-drop
  - Левая панель: EquipmentType (drag-source)
  - Правая панель: CompositionGroup (drop-target)
  - Подсветка цели при наведении
  - Drag в пустую область → перенос в корень
  - Drag на группу → диалог «Перенести / Сделать ссылку»
- **📋 MBOM** — таблица спецификаций

### CompositionGroupNode

Рекурсивный компонент. Ключевые механики:
- **Подсветка при drag-over** — синяя пунктирная рамка (`.drag-over`)
- **stopPropagation на drop** — предотвращает двойной дроп на вложенных узлах
- **edit-reference** — отдельное событие для ссылок (двойной клик)
- **remove-reference** — передача parentId через rest-аргументы, защита от потери на глубине 3+

### Редактор схемы

Вызывается из ET-модалки:
- **✏️** — открыть существующую схему
- **🔄 Взять из модели** — вызвать `POST /schemas/generate-from-model/`, заполнить поля из FILTER_DEFINITIONS
- Таблица полей: параметр, тип, выпадающий список «Опция»/«Обязательно»
- Живой JSON-preview
- Сохранить → создаёт/обновляет JSONSchema

### Переиспользуемые компоненты

| Компонент | Путь |
|---|---|
| `TreeNode.vue` | `src/components/bom/TreeNode.vue` |
| `CompositionGroupNode.vue` | `src/components/bom/CompositionGroupNode.vue` |
| `EquipmentTypeNode.vue` | `src/components/bom/EquipmentTypeNode.vue` |
| `MBOMItemNode.vue` | `src/components/bom/MBOMItemNode.vue` |
| `shared.css` | `src/components/bom/shared.css` |
| `ConfirmDialog.vue` | `src/shared/components/ConfirmDialog.vue` |

## Связь с MBOM

`MBOMItem` ссылается на:
- `equipment_type` (FK → EquipmentType)
- `composition_group` (FK → CompositionGroup)
- `parent` (self-FK) — иерархия элементов внутри спецификации

## TODO

- **Вкладка Schemas** в BomConfigPage — CRUD схем с авто-генерацией из моделей, без захода в PipelineConfigPage
- **Перенос PipelineConfigPage** в BomConfigPage как вкладка — единый центр настройки AI
- **AiCatalogSearch** — AI-помощник на страницах каталогов: текстовый ввод → extract фильтров → применение
- **Валидация parent** на фронте — исключать саму группу и потомков из списка родителей (сейчас на бэкенде)
- **Интеграция с configurator** — ParameterRule + ParameterBinding для EquipmentType в каталогах (см. [`configurator.md`](configurator.md))
