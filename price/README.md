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
- `item_content_type` — все строки одного типа товара
- `apply_prices()` — создать/обновить PriceHistory, пометить старые `is_current=False`
- Неприменённый документ можно редактировать (добавлять/удалять строки)

### PricingRule
Правила скидок/наценок:
- `target` (кому): партнёр или клиент
- `scope` (на что): бренд, тип оборудования, серия, товар
- `rule_type`: discount / markup
- `value` — проценты

---

## API

```
GET    /api/admin/prices/                      каталог цен
GET    /api/admin/prices/filters/              опции фильтров
GET    /api/admin/prices/documents/            журнал документов
POST   /api/admin/prices/documents/            создать документ
GET    /api/admin/prices/documents/<id>/       детали + строки + content_type_app/model
PUT    /api/admin/prices/documents/<id>/       обновить (черновик)
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
| `views/price_catalog.py` | `PriceCatalogView` | GET (select_related price_variety, currency) |
| `views/price_filters.py` | `PriceFilterOptionsView` | GET |
| `views/document_journal.py` | `PriceDocumentListView` | GET, POST |
| `views/document_detail.py` | `PriceDocumentDetailView` | GET, PUT, DELETE, POST (apply) |
| `views/document_detail.py` | `PriceDocumentItemView` | GET, POST, DELETE |

---

## Фронтенд

Мини-приложение: `frontend/src/apps/price-catalog/`
- Вкладка «Каталог цен» — таблица, фильтры (вид, валюта, дата, актуальные)
- Вкладка «Документы» — таблица + создание/применение/удаление
- **Редактор документа** — клик по названию открывает редактор:
  - Шапка (название, тип, дата, статус)
  - Таблица позиций (код, товар, вид цены, валюта, цена)
  - Форма добавления: поиск товара по подстроке кода (debounce 250мс) + вид цены + валюта + сумма

Создание документа: выбирается EquipmentType → используется его `content_type` для поиска товаров.

---

## Что дальше

- Импорт цен из Excel в PriceDocument
- Автоматический расчёт цены для партнёра (apply_rules)
- Конструктор цен для сложного оборудования (пневмоприводы, электроприводы)
- Интеграция с 1С (справочник «Номенклатура»)
