# price — Цены и ценообразование

Управление ценами, документами формирования цен, правилами скидок/наценок и конфигуратором цен ЭП.

**Дата:** 2026-06-16

---

## Модели

```
price/models/
├── currency.py              ← Currency (RUB, USD, EUR...)
├── price_variety.py         ← PriceVariety (РРЦ, опт, дилерская...)
├── price_history.py         ← PriceHistory (FK на SKU, быстрый поиск)
├── price_document.py        ← PriceDocument + PriceDocumentItem (документ цен, привязка к SKU)
├── pricing_rule.py          ← PricingRule (скидки/наценки)
├── exchange_rate.py         ← ExchangeRate (курсы валют ЦБ)
├── ea_price_constructor.py  ← EAPriceConstructor (конфигуратор цен ЭП: model × option → surcharge)
└── ea_price_document.py     ← EAPriceDocument (заголовок документа конфигуратора цен ЭП)
```

### EAPriceConstructor

Строка конфигуратора цен. Одна запись = model_line_item + power_supply + option_field + option_id → цена/надбавка.

- `document` — FK на EAPriceDocument (в UniqueConstraint)
- `model_line_item` — FK на ElectricActuatorModelLineItem
- `power_supply` — FK на ElectricPowerSupplyOption
- `option_field` — имя поля (`base`, `ip`, `exd`, `temperature`, `control_unit`, `way_switches`, ...)
- `option_id` — ID опции (NULL для base)
- `surcharge` — базовая цена или надбавка
- `currency` — FK на Currency
- `price_variety` — FK на PriceVariety
- `is_active` — активна ли для расчёта цены (True после проведения)

**UniqueConstraint:** `(document, model_line_item, power_supply, option_field, option_id, price_variety)` — разные документы могут иметь одинаковые строки.

`calculate_price(cls, constructor, price_variety_id)` — один запрос с Q-фильтром по `is_active=True`, возвращает `{total, currency, base, surcharges}`.

### EAPriceDocument

Заголовок документа конфигуратора цен. Наследует AbstractDocument.

- `name` — название
- `price_variety` — FK на PriceVariety
- `currency` — FK на Currency
- `model_line` — FK на ElectricActuatorModelLine
- `power_supply` — FK на ElectricPowerSupplyOption

**`register_changes()` (post):**
1. Собирает уникальные комбинации строк документа
2. Одним batch-update деактивирует (`is_active=False`) конкурирующие строки из других документов
3. Активирует (`is_active=True`) строки этого документа

**`unregister_changes()` (unpost):**
1. Удаляет строки документа (`EAPriceConstructor.delete()`)
2. Статус → DRAFT

### PriceHistory
- **Основная связь** — `sku` (FK → SKU, CASCADE). При удалении SKU — каскад.
- GFK для обратной совместимости
- `get_current_price_by_sku(sku, variety)` — основной поиск

### PriceDocument + PriceDocumentItem
Документ формирования цен. Все позиции привязаны к SKU.
- **Статусы:** draft → on_approval → posted
- `apply_prices()`: создаёт PriceHistory, переводит в posted
- `unapply_prices()`: удаляет PriceHistory по source_document, возвращает в draft

---

## API

### Общие цены
```
GET    /api/admin/prices/                      каталог цен
GET    /api/admin/prices/filters/              опции (varieties, currencies, equipment_types, brands)
GET    /api/admin/prices/snapshot/             срез цен
GET    /api/admin/prices/documents/            журнал документов
POST   /api/admin/prices/documents/            создать
GET    /api/admin/prices/documents/<id>/       детали + строки
PUT    /api/admin/prices/documents/<id>/       редактировать
DELETE /api/admin/prices/documents/<id>/       удалить
POST   /api/admin/prices/documents/<id>/apply/    провести → PriceHistory
POST   /api/admin/prices/documents/<id>/unapply/  отмена проведения
```

### EA Price Configurator
```
GET    /ea-configurator/power-supplies/            список напряжений ЭП
GET    /ea-configurator/options/?power_supply_id=X  модели + опции (включая WaySwitches)
POST   /ea-configurator/create/                     создать документ + авто-строки
GET    /ea-configurator/documents/                  журнал документов ЭП
GET    /ea-configurator/documents/<id>/             детали + строки
POST   /ea-configurator/documents/<id>/             обновить (сохранить) — @transaction.atomic
POST   /ea-configurator/documents/<id>/post/        провести (отправляет rows + currency_id + price_variety_id)
POST   /ea-configurator/documents/<id>/unpost/      отменить проведение → удаление строк
POST   /ea-configurator/documents/<id>/export/      Excel (Pandas) — принимает {rows} или читает БД
POST   /ea-configurator/documents/<id>/import/      импорт Excel (парсинг на бэкенде)
POST   /ea-configurator/documents/<id>/print/       HTML для печати — принимает {rows} или читает БД
GET    /ea-configurator/documents/<id>/fill/        действующие цены (is_active=True, exclude текущий документ)
DELETE /ea-configurator/documents/<id>/             мягкое удаление (mark_deleted)
```

### Особенности

- **options/** — возвращает модели серии с выбранным напряжением, включая WaySwitches как отдельную группу опций
- **create/** — если нет `rows`, авто-генерирует base-строки для всех моделей серии с этим напряжением
- **post/** (провести) — требует `currency_id` и `price_variety_id` в теле; если DRAFT — удаляет старые строки и создаёт новые
- **export/print** — принимают `{rows}` от фронтенда (текущая матрица), иначе fallback на БД
- **import** — парсит Excel на бэкенде (label→mli_id, label→key), возвращает готовые `{model_line_item_id, base_price, options}`
- **fill** — читает активные строки (`is_active=True`) для той же серии/напряжения/типа/валюты, исключая текущий документ
- Все методы используют `logger.debug/warning` вместо `print`

---

## Views

| Файл | Класс | Методы |
|------|-------|--------|
| `views/price_catalog.py` | `PriceCatalogView` | GET |
| `views/price_filters.py` | `PriceFilterOptionsView` | GET |
| `views/price_snapshot.py` | `PriceSnapshotView` | GET |
| `views/document_journal.py` | `PriceDocumentListView` | GET, POST |
| `views/document_detail.py` | `PriceDocumentDetailView` | GET, PUT, DELETE, POST |
| `views/document_detail.py` | `PriceDocumentItemView` | GET, POST, DELETE |
| `views/ea_configurator.py` | `EaPowerSuppliesView` | GET |
| `views/ea_configurator.py` | `EaConfiguratorOptionsView` | GET |
| `views/ea_configurator.py` | `EaConfiguratorDocumentView` | GET (list/detail/fill), POST (create/update/post/unpost/export/import/print) |

---

## Админка

| Модель | Особенности |
|--------|-------------|
| Currency | Импорт/экспорт |
| PriceVariety | Счётчик цен |
| PriceHistory | Импорт Excel, поиск по SKU |
| PriceDocument | Inline-позиции, статус-бейджи |
| ExchangeRate | Обновление из ЦБ |
| EAPriceConstructor | list_display: model_line_item, power_supply, option_field, option_id, surcharge, price_variety, is_active |
| EAPriceDocument | list_display: name, date, price_variety, currency, model_line, power_supply, status |

---

## Фронтенд

`frontend/src/apps/price-catalog/`

- **Каталог цен** — фильтры (тип, бренд, вид, валюта, дата)
- **Документы** — журнал + редактор с инлайн-редактированием цены
- **Конфигуратор цен ЭП:**
  - `EaPriceJournal.vue` — `SharedDocumentJournal`, каскад серия→напряжение
  - `EaPriceCard.vue` — `SharedDocumentCard`, матрица с WaySwitches, недоступные опции = `—`
  - `buildRows()` — единая функция сборки строк матрицы
  - `DEFAULT_NAME` — константа вместо хардкода
  - Импорт/Заполнить — автосохранение в документ
  - Экспорт/Печать — отправляют текущую матрицу, не читают БД
  - `AppButton.vue` — поддержка `as="span"` для кнопки Импорт

---

## Что дальше

- Автоматический расчёт цены через `EAPriceConstructor.calculate_price()`
- Добавление EndSwitches и TorqueSwitches в конфигуратор (аналогично WaySwitches)
