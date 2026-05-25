# Модуль `filter_regulator` — каталог фильтр-регуляторов

Реализован по типовому шаблону `gearbox` (см. `gearbox/README.md`).

## Модели

| Модель | Файл | Описание |
|---|---|---|
| `FilterRegulator` | `models/fr_model_line_item.py` | Фильтр-регулятор: серия, корпус, IP, фильтрация, давление |
| `FilterRegulatorModelLine` | `models/fr_model_line.py` | Серия: бренд, тип, материалы, шаблоны названия/описания |
| `FilterRegulatorBody` | `models/fr_body.py` | Корпус: резьбы, вес |
| `FilterRegulatorVariety` | `models/fr_options.py` | Тип фильтр-регулятора |
| `DrainVariety` | `models/fr_options.py` | Тип слива |

## Наследование FilterRegulator

```
CatalogDictMixin    — to_dict(), get_field_meta(), to_values_dict(), build_schema()
ImageGalleryMixin   — галерея изображений (images M2M)
TechDocMixin        — техническая документация (tech_docs M2M)
SmartCatalogMixin   — фильтрация и поиск (FILTER_DEFINITIONS в services/filters.py)
CopyMixin           — копирование через админку
TemplateMixin       — генерация названия/описания по шаблону model_line
```

## API

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/filter-regulator/meta/` | Метаданные полей |
| `GET` | `/api/filter-regulator/catalog/` | Список с фильтрами + цена |
| `GET` | `/api/filter-regulator/catalog/<id>/` | Детальная модель + Schema.org + цена |
| `GET` | `/api/filter-regulator/filters/` | Опции фильтров |

## Структура to_dict()

```python
{
    "id": 1, "code": "FR-1", "name": "...",
    "model_line": {"id": 1, "name": "FR Series", "brand": {...}},
    "sku": {"id": 1, "code": "FR-1"},

    "template_vars": {  # 21 значение
        "code", "name", "model_line_name", "brand_name",
        "filter_variety", "body_material", "bowl_material",
        "protection_material", "ip", "work_temp",
        "pressure_range", "pressure_inlet_max", "weight",
        "thread", "gauge_port_size", "drain_port_size",
        "filtration_rating", "flow_rate",
        "filter_element_material", "wall_mounting_included",
        "has_shut_off_valve"
    },

    "sections": [
        {"key": "images", "type": "gallery"},
        {"key": "specs",  "type": "specs", "groups": [
            {"key": "general",    "title": "Основные",         "fields": [...]},  # 10 полей
            {"key": "pressure",   "title": "Давление",         "fields": [...]},  # 2 поля
            {"key": "body_specs", "title": "Корпус",           "fields": [...]},  # 6 полей
            {"key": "conditions", "title": "Условия эксплуатации", "fields": [...]},  # 1 поле
        ]},
        {"key": "docs",        "type": "files"},
        {"key": "description", "type": "text"},
    ],

    "price": {"price": "...", "currency": "RUB", "symbol": "₽"},
    "schema": {"@context": "https://schema.org", "@type": "Product", ...},
}
```

## Фильтры

`services/filters.py`: IP (с ранжированием), температура мин/макс, бренд. Все кроме IP — `UNIQUE_FIELD_VALUES`.

## Фронтенд

`frontend/src/apps/filter-regulator-catalog/` — полный SPA (копия gearbox):
- `api.js` — `/api/filter-regulator/`
- `App.vue` — standalone SPA (страницы: секции, каталог, деталка, бренд)
- `GearboxSection.vue` — сетка серий
- `GearboxList.vue` — подбор + фильтры (FilterSidebar + ProductCard)
- `GearboxDetail.vue` — карточка товара (ProductDetail)
- `GearboxBrand.vue` — витрина бренда

Использует те же shared-компоненты, что и gearbox (`ProductCard`, `ProductDetail`, `TabSpecs`, etc.).

**Запуск**: `npm run dev` → `http://localhost:5173/src/apps/filter-regulator-catalog/index.html`
