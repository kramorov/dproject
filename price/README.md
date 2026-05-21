# price — Цены и ценообразование

Управление ценами, документами формирования цен и правилами скидок/наценок.

**Дата:** 2026-05-21

---

## Модели

```
price/models/
├── currency.py          ← Currency (RUB, USD, EUR...)
├── price_variety.py     ← PriceVariety (РРЦ, опт, дилерская...)
├── price_history.py     ← PriceHistory (быстрый поиск, GFK на товар)
├── price_document.py    ← PriceDocument + PriceDocumentItem (документ цен)
├── pricing_rule.py      ← PricingRule (скидки/наценки для партнёров)
└── exchange_rate.py     ← ExchangeRate (курсы валют ЦБ)
```

### Currency
Справочник валют: код (ISO 4217), символ (₽, $, €), is_active.

### PriceVariety
Вид цены: РРЦ, оптовая, дилерская, партнёрская, закупочная.

### PriceHistory
Денормализованная таблица для быстрого поиска актуальной цены.
- GFK → любой товар
- `name`/`code` — авто из content_object при save
- `is_current` — актуальная запись (одна на товар+вид)
- `source_document` — из какого PriceDocument (аудит)
- `get_current_price(instance, variety)` — быстрый поиск
- `get_compact_data()` + `SELECT_RELATED_FIELDS = ['price_variety', 'currency']`

### PriceDocument + PriceDocumentItem
Документ формирования цен — группирует позиции.

**Реквизиты:** название, тип оборудования, дата, тип цены (default), валюта (default).
Строки наследуют тип цены и валюту из шапки.

**Статусы:**
- `draft` — Черновик (можно редактировать реквизиты и строки)
- `on_approval` — На согласовании (реквизиты и строки заблокированы)
- `posted` — Проведён (цены в PriceHistory)

**Методы:**
- `apply_prices()` — создать/обновить PriceHistory, перевести в posted
- `unapply_prices()` — удалить записи PriceHistory, вернуть в draft
- `is_applied` — @property (True если status == 'posted')

**Свойства:**
- `item_content_type` — все строки одного типа товара
- `get_compact_data()` — возвращает status, status_label, items_count

### PricingRule
Правила скидок/наценок:
- `target` (кому): партнёр или клиент
- `scope` (на что): бренд, тип оборудования, серия, товар
- `rule_type`: discount / markup
- `value` — проценты

---

## API

```
# Каталог и справочники
GET    /api/admin/prices/                      каталог цен
GET    /api/admin/prices/filters/              опции фильтров
GET    /api/admin/prices/snapshot/             срез последних цен

# Документы
GET    /api/admin/prices/documents/            журнал документов
POST   /api/admin/prices/documents/            создать документ
GET    /api/admin/prices/documents/<id>/       детали + строки
PUT    /api/admin/prices/documents/<id>/       ред. реквизиты (draft) / статус (draft→on_approval)
DELETE /api/admin/prices/documents/<id>/       удалить
POST   /api/admin/prices/documents/<id>/apply/      провести → posted + PriceHistory
POST   /api/admin/prices/documents/<id>/unapply/    отмена проведения → draft

# Строки документа
GET    /api/admin/prices/documents/<id>/items/ строки документа
POST   /api/admin/prices/documents/<id>/items/ добавить строку (только draft)
DELETE /api/admin/prices/documents/<id>/items/?id=X удалить строку (только draft)
```

### Срез цен
```
GET /api/admin/prices/snapshot/
  ?content_type_id=X          (обязательно)
  &object_ids=1,2,3           (обязательно)
  &price_variety_id=X         (опционально)
  &currency_id=X              (опционально)
  &as_of_date=2026-05-21      (опционально, default сегодня)
```
Возвращает `{snapshots: {object_id: price_data|null}}` — для каждого object_id последнюю цену не старше as_of_date.

---

## Views

| Файл | Класс | Методы |
|------|-------|--------|
| `views/price_catalog.py` | `PriceCatalogView` | GET |
| `views/price_filters.py` | `PriceFilterOptionsView` | GET |
| `views/price_snapshot.py` | `PriceSnapshotView` | GET |
| `views/document_journal.py` | `PriceDocumentListView` | GET, POST |
| `views/document_detail.py` | `PriceDocumentDetailView` | GET, PUT, DELETE, POST (apply/unapply) |
| `views/document_detail.py` | `PriceDocumentItemView` | GET, POST, DELETE |

---

## Фронтенд

Мини-приложение: `frontend/src/apps/price-catalog/`
- **Вкладка «Каталог цен»** — таблица, фильтры (вид, валюта, дата, актуальные)
- **Вкладка «Документы»** — таблица + создание + фильтр по статусу
  - Статус-бейджи: ✎ Черновик, ⟳ На согласовании, ✓ Проведён
  - Кнопки в таблице: Провести / Отмена проведения
- **Редактор документа** — клик по названию:
  - Редактируемые реквизиты (название, дата, тип) — в статусе draft
  - Кнопки: «На согласование» → «Провести» → «Отмена проведения»
  - Таблица позиций, форма добавления (только draft)
  - Поиск товара по подстроке кода (debounce 250мс)

---

## Что дальше

- Импорт цен из Excel в PriceDocument
- Автоматический расчёт цены для партнёра (apply_rules)
- Конструктор цен для сложного оборудования (пневмоприводы, электроприводы)
- Интеграция с 1С (справочник «Номенклатура»)
