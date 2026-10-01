# SKU, MBOM, Assembly — структура и связи

> Снапшот: 2026-10-01. Актуализировано под текущий код (`sku/models/*`) и план §14 SESSION.md.
> Ранее (2026-07-29) документ описывал концепцию с моделью `Nomenclature`; реализовано как `SKU`.
> Связано: `assy.md` (сборки/заказы), `pa_card_pattern.md`, `CATALOG_PATTERN.md`.

## Уровни

Уровень 1: SKU               Атомарная номенклатура (артикул)
Уровень 2: EquipmentType      Классификатор типа оборудования
Уровень 3: MBOM               Конкретный подбор (материализация fixed-сборки)
Уровень 4: MBOMItem           Строка MBOM (иерархическая)
Уровень 5: Document/Item      КП, счёт — ссылаются на SKU (FK), код читается из `sku.code`

---

## Реализованные модели (код)

### SKU (`sku/models/sku.py`)

Единый реестр номенклатуры. Поля:

- `code` — `CharField(255)`, **сейчас `unique=True`** → план: перевести на `(code, brand)`.
- `name` / `description` — текстовые.
- `equipment_type` — FK → `core.EquipmentType` (`PROTECT`).
- `brand` — FK → `producers.Brands` (`SET_NULL`, nullable).
- `source_content_type` / `source_object_id` — GFK на модель-источник (каталожный item).
- `extra` — `JSONField` произвольных параметров.
- `is_active`, `created_at`, `updated_at`.

Факты текущего кода:

- Ссылки на SKU везде — **FK на `sku_id`**, не по строке кода:
  `cart.CartItem.sku`, `assemblies.ComponentRequirement.selected_sku`,
  `sku.MBOMItem.sku`, `price.PriceHistory.sku`, `price.PriceDocumentItem.sku`.
- `SKUMixin.sync_sku()` (`sku/models/mixins.py`) создаёт/обновляет SKU из модели-источника
  (OneToOne `sku` на item); сейчас `get_or_create(code=...)`, conflict-guard по `code`.

### SKUMixin (`sku/models/mixins.py`)

Абстрактный миксин: поле `sku` (OneToOne → SKU) + `sync_sku()`. Каталожный item вызывает
`sync_sku()` в `save()`. Хуки: `get_sku_code/name/description/equipment_type/brand`.

### MBOM / MBOMItem (`sku/models/mbom.py`)

- `MBOM`: `name`, `code` (unique), `conversation`, `customer`, `user`, `is_active`.
- `MBOMItem`: `mbom` FK, `parent` self-FK (иерархия), `equipment_type`, `composition_group`,
  `sku` FK (`PROTECT`), `quantity`, `quantity_unit`, `position`.

MBOM — **материализация `fixed`-сборки через SKU** (обход `selected_sku`), производная от fixed.

---

## План изменений (2026-10-01, §14 SESSION.md)

### 1. Идентичность SKU = `(code, brand)` (решено)

Артикулы у разных производителей совпадают; уникальность — внутри бренда.

- Убрать `unique=True` у `SKU.code`.
- Частичные ограничения (в SQLite/PG `NULL != NULL`, поэтому один общий
  `UniqueConstraint(code, brand)` не подходит):
  - `UniqueConstraint(code, condition=Q(brand__isnull=True))` — безбрендовые уникальны глобально;
  - `UniqueConstraint(code, brand, condition=Q(brand__isnull=False))` — внутри бренда.
- `SKUMixin.sync_sku()`: `get_or_create` и conflict-guard → `(code, brand)`.

### 2. Цены и документы — перевод с «по коду» на «по sku_id»

- `get_display_price(sku_code)` / `get_bulk_prices(sku_codes)`
  (`price/services/currency_converter.py`) ищут цену по `sku__code` → перевести на `sku_id`
  (фильтр по `PriceHistory.sku_id`, а не `sku__code`).
- Ревизия прочих code-keyed lookup'ов SKU: `price/views/price_filters.py`,
  `price/views/price_snapshot.py`, генератор `cable_glands`, `configurator`,
  `pa_controls/services/posi_sku_service.py`, `pneumatic_actuators/services/sku_service.py`,
  `sync_*_sku` команды.
- Снэпшот документа (решено): при переходе документа в статус `POSTED` (проведён) фиксировать
  все параметры и опции строк, включая `code` и `description` — полный снимок. До `POSTED`
  строки читают `sku.code` live; после — заморожены. `PriceHistory.code` — отдельный снэпшот из GFK.

### 3. Карточки конфигурируемого оборудования — семантическая идентичность

Для ПП (позже ЭП) — материализация карточек (~8к), скрытых из каталога:

- `config_hash` — хэш конфигурации (типоразмер + опции) на карточке; ключ дедупа и диффа.
- `code` — производное, пере-выводится из encoding; смена кодировки = тот же `config_hash`,
  пересчитанный код. Опция/значение добавилось → новый `config_hash` → новая карточка;
  хэш исчез → `is_active=False`.

---

## ER-диаграмма (реализовано)

```
EquipmentType ──< SKU (equipment_type)
     │
     └──< MBOM ──< MBOMItem >── SKU (sku, PROTECT)
CartItem ──> SKU (sku, PROTECT)
ComponentRequirement ──> SKU (selected_sku)
PriceHistory ──> SKU (sku)             (code — денормализованный снэпшот)
PriceDocumentItem ──> SKU (sku, PROTECT) (кода нет — читает sku.code live)
```

---

## Правила

1. Номенклатура — атомарные SKU; ссылки на SKU — только FK на `sku_id`.
2. `PriceHistory.code` — денормализованный снэпшот. Документ замораживается целиком
   (код + описание + параметры + опции) при переходе в статус `POSTED`.
3. MBOM — производная `fixed`-сборки, не вторая правда.
4. Документ — строка ссылается на SKU (FK) или MBOM.
5. Уникальность кода — внутри бренда; безбрендовые — глобально по коду (частичные unique).
6. Никогда не hard-delete SKU, участвующее в корзине/заказе/сборке/КП.
