# Модуль `gearbox` — каталог редукторов

## Модели

| Модель | Файл | Описание |
|---|---|---|
| `GearBox` | `models/gearbox.py` | Редуктор: серия, корпус, IP, материал, температуры, цена |
| `GearBoxModelLine` | `models/gb_model_line.py` | Серия: бренд, тип выхода, шаблоны названия/описания |
| `GearBoxBody` | `models/gb_body.py` | Корпус: передаточное число, моменты, монтажные площадки, вес |
| `GearBoxInterlock` | `models/interlock.py` | Модель интерлока |
| `OverrideMechanism` | `models/gb_options.py` | Механизм отключения |
| `TransmissionVariety` | `models/gb_options.py` | Тип передачи |
| `GearboxVariety` | `models/gb_options.py` | Разновидность редуктора |

## Наследование GearBox

```
CatalogDictMixin  — to_dict(), get_field_meta(), to_values_dict(), build_schema()
SmartCatalogMixin — фильтрация и поиск (FILTER_DEFINITIONS в services/filters.py)
CopyMixin         — копирование через админку
TemplateMixin     — генерация названия/описания по шаблону model_line
ImageGalleryMixin — галерея изображений (images M2M)
TechDocMixin      — техническая документация (tech_docs M2M)
SKUMixin          — привязка к номенклатуре (SKU)
```

## API

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/gearbox/meta/` | Метаданные полей: `{field_key: {label, group, unit, type}}` |
| `GET` | `/api/gearbox/catalog/` | Список с фильтрами + **цена в валюте клиента** |
| `GET` | `/api/gearbox/catalog/<id>/` | Детальная модель + **Schema.org Product** + **цена** |
| `GET` | `/api/gearbox/filters/` | Опции фильтров |

### Параметры каталога

| Параметр | Тип | Описание |
|---|---|---|
| `search` | string | Поиск по code, name, description |
| `ip_id` | int | IP (с ранжированием: >= выбранного) |
| `work_temp_min` | int | Температура от, °С |
| `work_temp_max` | int | Температура до, °С |
| `min_work_torque` | number | Рабочий момент не менее, Нм |
| `body_material_id` | int | Материал корпуса (только используемые) |
| `brand_id` | int | Бренд (только используемые) |
| `mounting_plate_top_id` | int | Монтажная площадка (только используемые) |
| `is_active` | bool | Только активные (по умолчанию true) |
| `limit` | int | Размер страницы (по умолчанию 24, макс 100) |
| `offset` | int | Смещение |
| `lang` | string | Язык (ru, en, zh) |

## Структура to_dict() — детальная страница

```python
{
    "id": 1, "code": "RD-1", "name": "...",
    "image_alt": "Четвертьоборотный Ручной дублер RD-1",

    "model_line": {"id": 1, "name": "RD - Artorq", "brand": {...}},
    "sku": {"id": 1, "code": "RD-1", "name": "..."},

    "template_vars": {  # плоский словарь для шаблонов
        "code": "RD-1",
        "brand_name": "Artorq",
        "reduction_ratio": "26:1",
        "max_output_torque": "100.00",
        "weight": "2.62",
        "work_temp": "-40...+100 °С",
        ...
    },

    "sections": [
        {"key": "images", "type": "gallery", "data": [...]},
        {"key": "specs",  "type": "specs",   "groups": [
            {"key": "general",    "title": "Основные",               "fields": [...]},
            {"key": "body",       "title": "Корпус",                 "fields": [...]},
            {"key": "conditions", "title": "Условия эксплуатации",    "fields": [...]},
        ]},
        {"key": "docs",        "type": "files", "data": [...]},
        {"key": "certs",       "type": "files", "data": [...]},
        {"key": "description", "type": "text",  "data": "..."},
    ],

    "price": {"price": "7814.12", "currency": "RUB", "symbol": "₽"},
    "schema": {"@context": "https://schema.org", "@type": "Product", ...},
}
```

## Структура to_values_dict() — список (облегчённая)

```python
{
    "id": 1, "code": "RD-1", "name": "...",
    "template_vars": {...},       # 19 полей
    "values": {...},              # те же ключи (совместимость)
    "images": [{url, ...}],       # первое изображение
    "model_line": {...},          # сводка
    "sku": {...},                 # для цен
    "price": {"price": "7814.12", "currency": "RUB", "symbol": "₽"},
}
```

## Три метода — три роли

| Метод | Возвращает | Для кого |
|---|---|---|
| `_get_data_dict()` | `{'{brand}': 'model_line__brand'}` — пути | `TemplateMixin` (админка) |
| `_get_template_vars()` | `{'brand_name': 'Artorq'}` — строки | `to_dict()`, Jinja2 |
| `to_dict()` | Полная структура с sections | API деталки |

## Цены

Цены вшиты сервером в ответ каталога. Фронт не делает второй запрос.

```
GearboxCatalogView
  → _get_currency_code(request)
    → get_current_customer_user() → CustomerSettings.default_currency = RUB
  → get_bulk_prices(sku_codes, 'RUB')
    → PriceHistory (is_current) → convert_price(USD→RUB через ExchangeRate)
```

Курсы валют: `ExchangeRate` — к RUB на дату. Загрузка с ЦБ через `CBRExchangeService`.

## Фильтры

`services/filters.py`. Все кроме IP используют `UNIQUE_FIELD_VALUES` — только реально используемые значения.

## Фронтенд

**Виджет** (`frontend/src/apps/widget/`):
- `router.js` — hash-роутер: `#/gearbox/detail/123`
- `App.vue` — оркестратор, рендерит каталог по URL
- `CatalogIndex.vue` — стартовая: сетка «Редукторы», «Приводы»...

**Страницы** (`frontend/src/apps/gearbox-catalog/`):
- `GearboxSection` — сетка серий
- `GearboxList` — подбор + фильтры
- `GearboxDetail` — карточка товара
- `GearboxBrand` — витрина бренда

**Shared-компоненты** (`frontend/src/shared/components/`):
`ProductDetail`, `ProductHeader`, `ProductTabs`, `ProductGallery`, `ProductCard`, `TabSpecs`, `FileList`, `FileViewerModal`, `FilterSidebar`, `Breadcrumbs`, `JsonLd`

**CSS-темы** (`frontend/src/shared/themes/`):
`default.css`, `dark.css`, `minimal.css` — 50+ custom properties. Партнёр переопределяет `:root` — весь каталог перекрашивается.

## Типовой шаблон для других каталогов

```python
# 1. Модель
class PneumaticActuator(CatalogDictMixin, ...):
    def _get_template_vars(self): return {...}
    def to_dict(self):
        tv = self._get_template_vars()
        return {"template_vars": tv, "sections": [...]}

# 2. Вьюхи: meta.py + catalog.py (копия gearbox)
# 3. URL: добавить в widget/App.vue новый блок v-else-if
# 4. CatalogIndex: добавить запись в CATALOG_INFO
```
