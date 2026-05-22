# price — Цены и ценообразование

Управление ценами, документами формирования цен и правилами скидок/наценок.

**Дата:** 2026-05-22

---

## Модели

```
price/models/
├── currency.py          ← Currency (RUB, USD, EUR...)
├── price_variety.py     ← PriceVariety (РРЦ, опт, дилерская...)
├── price_history.py     ← PriceHistory (FK на SKU, быстрый поиск)
├── price_document.py    ← PriceDocument + PriceDocumentItem (документ цен, привязка к SKU)
├── pricing_rule.py      ← PricingRule (скидки/наценки)
└── exchange_rate.py     ← ExchangeRate (курсы валют ЦБ)
```

### PriceHistory
- **Основная связь** — `sku` (FK → SKU, CASCADE). При удалении SKU — каскад.
- GFK для обратной совместимости
- `get_current_price_by_sku(sku, variety)` — основной поиск
- `get_current_price(instance, variety)` — через GFK
- `get_compact_data()` включает sku_id, sku_code, sku_name

### PriceDocument + PriceDocumentItem
Документ формирования цен. **Все позиции привязаны к SKU**.
- **Статусы:** draft → on_approval → posted
- `apply_prices()`: создаёт PriceHistory с name/code из SKU, переводит в posted
- `unapply_prices()`: удаляет PriceHistory по source_document, восстанавливает is_current у предыдущих, возвращает в draft

---

## API

```
GET    /api/admin/prices/               каталог цен (фильтры: equipment_type_id, brand_id через SKU)
GET    /api/admin/prices/filters/       опции (varieties, currencies, equipment_types, brands)
GET    /api/admin/prices/snapshot/      срез цен (mode: gfk или code)
GET    /api/admin/prices/documents/     журнал
POST   /api/admin/prices/documents/     создать
GET    /.../<id>/                       детали + строки
PUT    /.../<id>/                       редактировать реквизиты / статус
DELETE /.../<id>/                       удалить
POST   /.../<id>/apply/                провести → PriceHistory
POST   /.../<id>/unapply/              отмена (удаление History + возврат в draft)
GET    /.../<id>/items/                строки
POST   /.../<id>/items/                добавить ({sku_id, price})
DELETE /.../<id>/items/?id=X           удалить
```

### Срез цен
- **GFK:** `?content_type_id=X&object_ids=1,2,3`
- **Code:** `?code=RD7,RD7.LT`
- Общие: `price_variety_id`, `currency_id`, `as_of_date`

---

## Views

| Файл | Класс | Методы |
|------|-------|--------|
| `views/price_catalog.py` | `PriceCatalogView` | GET (equipment_type_id, brand_id) |
| `views/price_filters.py` | `PriceFilterOptionsView` | GET (varieties, currencies, types, brands) |
| `views/price_snapshot.py` | `PriceSnapshotView` | GET (gfk / code modes) |
| `views/document_journal.py` | `PriceDocumentListView` | GET, POST |
| `views/document_detail.py` | `PriceDocumentDetailView` | GET, PUT, DELETE, POST (apply/unapply) |
| `views/document_detail.py` | `PriceDocumentItemView` | GET, POST (sku_id), DELETE |

---

## Админка

| Модель | Особенности |
|--------|-------------|
| Currency | Импорт/экспорт |
| PriceVariety | Счётчик цен |
| PriceHistory | Импорт Excel, поиск по SKU, sku_link |
| PriceDocument | Inline-позиции, статус-бейджи |
| ExchangeRate | Обновление из ЦБ |

---

## Фронтенд

`frontend/src/apps/price-catalog/`
- **Каталог цен** — фильтры (тип, бренд, вид, валюта, дата)
- **Документы** — журнал с созданием
- **Редактор документа:**
  - Инлайн-редактирование цены (клик → ввод → Enter)
  - Поиск товара через `/api/admin/sku/`
  - Кнопка «Заполнить по фильтрам» — подбор SKU с переносом в документ
  - Кнопка «+ Создать и добавить» — создать SKU и сразу в документ
  - Кнопка 📝 — редактирование SKU в модалке

---

## Что дальше

- Импорт цен из Excel в PriceDocument
- Автоматический расчёт цены для партнёра
- Конструктор цен для сложного оборудования
