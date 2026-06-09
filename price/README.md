# price — Цены и ценообразование

Управление ценами, документами формирования цен, правилами скидок/наценок и конфигуратором цен ЭП.

**Дата:** 2026-06-09

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

- `document` — FK на EAPriceDocument (nullable, для привязки к документу)
- `model_line_item` — FK на ElectricActuatorModelLineItem
- `power_supply` — FK на ElectricPowerSupplyOption
- `option_field` — имя поля в конструкторе (`ip`, `exd`, `temperature`, ... или `base`)
- `option_id` — ID опции (NULL для base)
- `surcharge` — базовая цена или надбавка
- `currency` — FK на Currency
- `price_variety` — FK на PriceVariety
- `is_active` — учитывать при расчёте (True после проведения документа)

`calculate_price(cls, constructor, price_variety_id)` — рассчитать цену для конструктора: один запрос с Q-фильтром, возвращает `{total, currency, base, surcharges}`.

### EAPriceDocument

Заголовок документа конфигуратора цен. Задаёт контекст: тип цены, валюту, серию, напряжение.

- `name` — название документа
- `document_date` — дата
- `price_variety` — FK на PriceVariety (РРЦ, опт, ...)
- `currency` — FK на Currency
- `model_line` — FK на ElectricActuatorModelLine (серия)
- `power_supply` — FK на ElectricPowerSupplyOption (напряжение)
- `status` — draft / on_approval / posted

`post()` — провести: активирует все строки EAPriceConstructor.
`unpost()` — отменить: деактивирует строки.

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
GET    /api/admin/prices/                            каталог цен
GET    /api/admin/prices/filters/                    опции (varieties, currencies, equipment_types, brands)
GET    /api/admin/prices/snapshot/                   срез цен
GET    /api/admin/prices/documents/                  журнал документов
POST   /api/admin/prices/documents/                  создать
GET    /.../<id>/                                    детали + строки
PUT    /.../<id>/                                    редактировать
DELETE /.../<id>/                                    удалить
POST   /.../<id>/apply/                             провести → PriceHistory
POST   /.../<id>/unapply/                           отмена проведения

GET    /api/admin/prices/ea-configurator/power-supplies/   список напряжений ЭП
GET    /api/admin/prices/ea-configurator/options/           опции моделей (?power_supply_id=X)
GET    /api/admin/prices/ea-configurator/documents/         журнал документов ЭП
POST   /api/admin/prices/ea-configurator/create/            создать документ + строки
GET    /api/admin/prices/ea-configurator/documents/<id>/    детали документа ЭП
DELETE /api/admin/prices/ea-configurator/documents/<id>/    удалить
```

### EA Configurator

**options/** — возвращает model_line_item + доступные опции (encoding из through-моделей) для выбранного напряжения.

**create/** — создаёт EAPriceDocument + EAPriceConstructor строки из матрицы:
```json
{
  "name": "...", "price_variety_id": 1, "currency_id": 1,
  "model_line_id": 5, "power_supply_id": 12,
  "rows": [{"model_line_item_id": 42, "base_price": 45000, "options": {"ip_5": 2000, "exd_3": 5000}}]
}
```

### Срез цен
- **GFK:** `?content_type_id=X&object_ids=1,2,3`
- **Code:** `?code=RD7,RD7.LT`
- Общие: `price_variety_id`, `currency_id`, `as_of_date`

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
| `views/ea_configurator.py` | `EaConfiguratorOptionsView` | GET (?power_supply_id=) |
| `views/ea_configurator.py` | `EaConfiguratorDocumentView` | GET, POST, DELETE |

---

## Админка

| Модель | Особенности |
|--------|-------------|
| Currency | Импорт/экспорт |
| PriceVariety | Счётчик цен |
| PriceHistory | Импорт Excel, поиск по SKU, sku_link |
| PriceDocument | Inline-позиции, статус-бейджи |
| ExchangeRate | Обновление из ЦБ |
| EAPriceConstructor | list_display: model_line_item, power_supply, option_field, option_id, surcharge, price_variety, is_active |
| EAPriceDocument | list_display: name, date, price_variety, currency, model_line, power_supply, status |

---

## Фронтенд

`frontend/src/apps/price-catalog/`
- **Каталог цен** — фильтры (тип, бренд, вид, валюта, дата)
- **Документы** — журнал с созданием, редактор с инлайн-редактированием цены
- **Конфигуратор ЭП** — журнал + редактор:
  - `EaPriceJournal.vue` — список документов + форма создания (название, тип цены, валюта, серия, напряжение)
    - Каскад: выбор серии → `GET /electric_actuators/constructor/model-lines/{id}/items/` → `GET /options/` → автозаполнение напряжений
    - Кнопка «Создать и заполнить» → `POST /create/` → открывается редактор
    - Клик по строке документа → открывается редактор
    - Кнопки «Провести»/«Отмена» → `POST /documents/{id}/post/` / `unpost/`
  - `EaPriceCard.vue` — матрица model_line_item × опции:
    - Загрузка по `power_supply_id` → `GET /options/?power_supply_id=X`
    - Колонки: encoding из through-моделей, дефолтные опции скрыты
    - Сохранение → `POST /create/` (перезаписывает строки EAPriceConstructor)
    - При открытии существующего документа — восстанавливает сохранённые значения
  - `api.js` — методы для конфигуратора: `getEaConfigDocs`, `getEaConfigDoc`, `createEaConfigDoc`, `deleteEaConfigDoc`, `postEaConfigDoc`, `unpostEaConfigDoc`
  - Загрузка model_lines/options через `fetch()` напрямую (минуя `priceApi` с baseURL)

---

## Что дальше

- Импорт цен из Excel в EAPriceDocument
- Автоматический расчёт цены через `EAPriceConstructor.calculate_price()`
