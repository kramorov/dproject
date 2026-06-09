# documents — Документы и журналы

Универсальное приложение для документов любого типа: цены, заказы, счета, КП.
Архитектура в стиле 1С: документ → проведение → движения по регистрам.

**Дата:** 2026-06-09

---

## Структура

```
documents/
├── apps.py                              # AppConfig
├── models/
│   ├── abstract_document.py             # AbstractDocument     — заголовок + статусная модель
│   ├── abstract_document_item.py        # AbstractDocumentItem — строка табличной части
│   └── document_numerator.py            # DocumentNumerator    — сквозная нумерация
├── catalog/
│   ├── filter_defs.py                   # Готовые FilterDefinition для журналов
│   └── config.py                        # DocumentJournalConfig — конфигурация журнала
├── views/
│   ├── document_journal.py              # BaseDocumentJournalView  — список + создание
│   └── document_detail.py               # BaseDocumentDetailView   — карточка + проведение
└── admin/
    └── base_document_admin.py           # BaseDocumentAdmin — админка с soft-delete
```

---

## Статусная модель

```
DRAFT ──→ ON_APPROVAL ──→ POSTED
  │            │              │
  └────────────┼──────────────┘
               ↓
           DELETED
```

| Статус | Описание | Что можно |
|--------|----------|-----------|
| `draft` | Черновик | Редактировать реквизиты и строки |
| `on_approval` | На согласовании | Только сменить статус |
| `posted` | Проведён | Только отменить проведение или удалить |
| `deleted` | Помечен на удаление | Только физически удалить из БД |

**Правила:**
- `POSTED → DELETED`: автоматически вызывает `unregister_changes()` (отмена движений)
- Физическое удаление — только через админ-действие `action_hard_delete`
- `mark_deleted()` идемпотентен, атомарен (`select_for_update`)

---

## Компоненты

### AbstractDocument — заголовок документа

Наследуйтесь от него для любого типа документа.

**Поля (общие):**
`name`, `code`, `description`, `document_date`, `status`, `sorting_order`, `is_active`, `created_at`, `updated_at`

**Обязательно переопределить:**

| Метод | Назначение |
|-------|-----------|
| `register_changes()` | Провести: создать движения + `self.status = POSTED` + `self.save()` |
| `unregister_changes()` | Отменить: удалить движения + `self.status = DRAFT` + `self.save()` |
| `get_items_related_name()` | Вернуть `'items'` / `'rows'` — имя related_name строк |

**Опционально переопределить:**

| Метод | Назначение |
|-------|-----------|
| `get_compact_data()` | Дополнить словарь своими полями (вызвать `super()`) |
| `get_allowed_status_transitions()` | Другой граф переходов |
| `get_available_features()` | Автоопределение по переопределённым методам — обычно не нужно |
| `get_print_html()` | Печатная форма |
| `export_word()` / `export_excel()` / `export_pdf()` | Экспорт |
| `import_from_file(uploaded_file)` | Импорт данных |

**Атрибут класса:**
- `NUMERATOR_PREFIX = 'ДОК'` — префикс для автонумерации. Если `None` — нумератор не используется.

### AbstractDocumentItem — строка табличной части

**Поля (общие):**
`sorting_order`, `is_active`, `comment`, `created_at`, `updated_at`

**Обязательно добавить в подклассе:**
- FK на документ: `document = models.ForeignKey(MyDocument, on_delete=models.CASCADE, related_name='items')`
- Содержательные поля: `sku`, `price`, `quantity`, ...

### DocumentNumerator — нумератор

```python
code = DocumentNumerator.get_next_code('ДОК')          # → 'ДОК-000001'
code = DocumentNumerator.get_next_code('ЦЕН', year=2026)  # → 'ЦЕН-000001'
```

Атомарный инкремент через `select_for_update()` + `F('counter') + 1`.

### DocumentJournalConfig — конфигурация журнала

Dataclass. Связывает модель документа с фильтрами и UI-метками.
Формат `get_filter_options()` совместим с `FilterSidebar` на фронте.

### BaseDocumentJournalView — список + создание

**URL:** `GET /api/.../journal/`, `POST /api/.../journal/`

Подкласс задаёт `journal_config = DocumentJournalConfig(...)` и переопределяет `get_create_fields(data)`.

### BaseDocumentDetailView — карточка + проведение

**URL:**
| Метод | URL | Действие |
|-------|-----|----------|
| GET | `/<pk>/` | Карточка со строками |
| PUT | `/<pk>/` | Реквизиты + статус |
| DELETE | `/<pk>/` | Пометить на удаление |
| POST | `/<pk>/register/` | Провести |
| POST | `/<pk>/unregister/` | Отменить проведение |
| POST | `/<pk>/print/` | Печатная форма |
| POST | `/<pk>/export/word/` | Скачать Word |
| POST | `/<pk>/export/excel/` | Скачать Excel |
| POST | `/<pk>/export/pdf/` | Скачать PDF |
| POST | `/<pk>/import/` | Загрузить из файла |

---

## Чек-лист: добавление нового типа документа

Допустим, делаем `Invoice` (счёт) в приложении `billing`.

### Бэкенд

- [ ] **Модель документа** — наследовать `AbstractDocument`
  - [ ] Задать `NUMERATOR_PREFIX = 'СЧТ'`
  - [ ] Добавить свои FK (контрагент, договор, валюта, ...)
  - [ ] Реализовать `register_changes()` — создать записи в регистре расчётов
  - [ ] Реализовать `unregister_changes()` — удалить записи из регистра
  - [ ] Реализовать `get_items_related_name()` → `'items'`
  - [ ] Переопределить `get_compact_data()` — вызвать `super()` и добавить свои поля
- [ ] **Модель строки** — наследовать `AbstractDocumentItem`
  - [ ] Добавить `document = FK(Invoice, related_name='items')`
  - [ ] Добавить поля: `product`, `quantity`, `price`, `amount`
- [ ] **Миграции** — `makemigrations billing && migrate`
- [ ] **Админка** — наследовать `BaseDocumentAdmin`, добавить свои поля в `list_display`

### API

- [ ] **Журнал** — наследовать `BaseDocumentJournalView`
  - [ ] Задать `journal_config = INVOICE_JOURNAL_CONFIG`
  - [ ] Реализовать `get_create_fields(data)`
- [ ] **Детали** — наследовать `BaseDocumentDetailView`
  - [ ] Задать `document_model = Invoice`
  - [ ] Переопределить `_get_doc()` для `select_related`
  - [ ] Переопределить `serialize_detail()` для своих строк
  - [ ] Переопределить `get_editable_fields()` для своих полей
- [ ] **URL** — добавить `urls.py` с `path('journal/', ...)`, `path('<int:pk>/', ...)`, `path('<int:pk>/register/', ...)`, ...

### Конфигурация журнала

- [ ] **`billing/catalog/filter_defs.py`** — добавить свои `fd_*` (контрагент, период)
- [ ] **`billing/catalog/config.py`** — `INVOICE_JOURNAL_CONFIG = DocumentJournalConfig(...)`

### Экспорт / печать (опционально)

- [ ] **`get_print_html()`** — HTML счёта
- [ ] **`export_excel()`** — выгрузка в Excel
- [ ] **`export_pdf()`** — PDF счёта
- [ ] **`import_from_file()`** — загрузка из Excel
- [ ] Методы автоматически активируют `features` в API — фронт покажет кнопки

### Фронтенд

- [ ] **api.js** — методы для журнала и карточки
- [ ] **Компонент журнала** — список + форма создания
- [ ] **Компонент карточки** — заголовок + строки + кнопки действий
- [ ] **Маршрут** в роутере
- [ ] **Пункт меню** в TopMenu

---

## Что уже готово (не требует переопределения)

- Статусная машина: `can_transition_to()`, `get_allowed_status_transitions()`
- `mark_deleted()` с авто-отменой проведения
- `save()` с авто-присвоением кода из нумератора
- `get_compact_data()` — базовый словарь (`features`, `is_posted`, `is_deleted`, ...)
- `features` — автоопределение переопределённых export/print/import методов
- `BaseDocumentDetailView` — PUT с атомарным статус+реквизиты, контракт `register_changes()`/`unregister_changes()`
- `BaseDocumentJournalView` — фильтрация через FilterDefinition, пагинация
- `BaseDocumentAdmin` — `action_mark_deleted`, `action_hard_delete`, readonly для проведённых
- URL-роутинг: `register`, `unregister`, `print`, `export/word`, `export/excel`, `export/pdf`, `import`
- Filename с URL-encode для не-ASCII
