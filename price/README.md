# price — Цены и ценообразование

Управление ценами, документами формирования цен и правилами скидок/наценок.

**Дата:** 2026-05-20

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
Справочник валют: код (ISO 4217), символ (₽, $, €).

### PriceVariety
Вид цены: РРЦ, оптовая, дилерская, партнёрская, закупочная.

### PriceHistory
Денормализованная таблица для быстрого поиска актуальной цены.
- GFK → любой товар (PneumaticFitting, ElectricActuatorModelLineItem...)
- `name`/`code` — денормализованные поля (авто из `content_object`)
- `is_current` — актуальная запись (одна на товар+вид)
- `source_document` — из какого PriceDocument
- `get_current_price(instance, variety)` — быстрый поиск

### PriceDocument + PriceDocumentItem
Документ формирования цен — группирует позиции.
- `item_content_type` — все строки одного типа товара
- `apply_prices()` — погасить старые `is_current`, создать новые PriceHistory
- Неприменённый документ можно редактировать

### PricingRule
Правила скидок/наценок:
- `target` (кому): партнёр (ProjectCustomer) или клиент (Company)
- `scope` (на что): бренд, тип оборудования, серия, товар
- `rule_type`: discount / markup
- `value` — проценты
- `priority` — при конфликте правил
- `apply(base_price)` → цена после правила

---

## API

```
GET    /api/admin/prices/                      каталог цен (фильтры: search, variety, currency, date)
GET    /api/admin/prices/filters/              опции фильтров
GET    /api/admin/prices/documents/            журнал документов
POST   /api/admin/prices/documents/            создать документ
GET    /api/admin/prices/documents/<id>/       детали документа + строки
PUT    /api/admin/prices/documents/<id>/       обновить документ (черновик)
DELETE /api/admin/prices/documents/<id>/       удалить
POST   /api/admin/prices/documents/<id>/apply/ применить → PriceHistory
GET    /api/admin/prices/documents/<id>/items/ строки документа
POST   /api/admin/prices/documents/<id>/items/ добавить строку
DELETE /api/admin/prices/documents/<id>/items/?id=X удалить строку
```

---

## Views

| Файл | Класс | Методы |
|------|-------|--------|
| `views/price_catalog.py` | `PriceCatalogView` | GET |
| `views/price_filters.py` | `PriceFilterOptionsView` | GET |
| `views/document_journal.py` | `PriceDocumentListView` | GET, POST |
| `views/document_detail.py` | `PriceDocumentDetailView` | GET, PUT, DELETE, POST (apply) |
| `views/document_detail.py` | `PriceDocumentItemView` | GET, POST, DELETE |

---

## Фронтенд

Мини-приложение: `frontend/src/apps/price-catalog/`
- Вкладка «Каталог цен» — таблица + фильтры
- Вкладка «Документы» — таблица + создание/применение/удаление

---

## Что дальше

- Редактор документа (страница с таблицей строк)
- Импорт цен из Excel в документ
- Автоматический расчёт цены для партнёра (apply_rules)
- Конструктор цен для сложного оборудования (пневмоприводы, электроприводы)
- Интеграция с 1С (справочник «Номенклатура»)
