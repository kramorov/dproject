# Модуль `filter_regulator` — каталог фильтр-регуляторов

## Модели

| Модель | Файл | Описание |
|---|---|---|
| `FilterRegulator` | `models/fr_model_line_item.py` | Фильтр-регулятор: серия, корпус, IP, материал, температуры, расход |
| `FilterRegulatorModelLine` | `models/fr_model_line.py` | Серия: бренд, тип, материал корпуса/стакана, давления |
| `FilterRegulatorBody` | `models/fr_body.py` | Корпус: резьба портов, манометра, слива, вес |
| `FilterRegulatorVariety` | `models/fr_options.py` | Тип фильтр-регулятора |
| `DrainVariety` | `models/fr_options.py` | Тип слива |

## Наследование FilterRegulator

```
CatalogDictMixin  — to_dict(), to_values_dict(), build_schema()
SmartCatalogMixin — фильтрация и поиск (FILTER_DEFINITIONS в services/filters.py)
CopyMixin         — копирование
TemplateMixin     — генерация названия/описания по шаблону model_line
ImageGalleryMixin — галерея изображений (images M2M)
TechDocMixin      — техническая документация (tech_docs M2M)
```

> SKUMixin закомментирован — требуется makemigrations + migrate для добавления колонки sku_id.

## Наследование FilterRegulatorModelLine

```
ImageGalleryMixin — галерея
TechDocMixin      — техдокументация
CertDocMixin      — сертификаты (cert_docs M2M)
SmartCatalogMixin — фильтрация
```

## API

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/filter-regulator/meta/` | Метаданные полей |
| `GET` | `/api/filter-regulator/catalog/` | Список с фильтрами + цена |
| `GET` | `/api/filter-regulator/catalog/<id>/` | Детальная модель + Schema.org + цена |
| `GET` | `/api/filter-regulator/filters/` | Опции фильтров |
| `GET` | `/api/filter-regulator/engineer/` | Инженерный каталог (визуальный подбор) |

### Параметры каталога

| Параметр | Тип | Описание |
|---|---|---|
| `model_line_id` | int | Серия (главный фильтр) |
| `filtration_rating_min` | number | Тонкость фильтрации не менее, мкм |
| `body_material_id` | int | Материал корпуса |
| `flow_rate_min` | number | Расход не менее, л/мин |
| `thread_id` | int | Резьба портов |
| `work_temp_min` | int | Температура от, °С |
| `work_temp_max` | int | Температура до, °С |
| `brand_id` | int | Бренд (только используемые) |
| `search` | string | Поиск по code, name, description |
| `is_active` | bool | Только активные (по умолчанию true) |
| `limit` | int | Размер страницы (по умолчанию 24, макс 100) |
| `offset` | int | Смещение |
| `lang` | string | Язык (ru, en, zh) |

## Инженерный каталог

`GET /api/filter-regulator/engineer/?model_line_id=X`

**Параметры**: те же, что в каталоге (подфильтры опциональны).

**Ответ**:
```json
{
    "model_line": {"id": 1, "name": "BPFR", "code": ""},
    "total": 3,
    "items": [{...to_dict()...}],
    "filters": {
        "filtration_rating_min": [{"value": 25.0, "label": "25.0", "count": 3}],
        "body_material_id": [{"id": 1, "name": "Алюминий", "count": 3}],
        "flow_rate_min": [{"value": 2000.0, "label": "2000.00", "count": 3}],
        "thread_id": [{"id": 18, "name": "G 1/8\"", "count": 3}]
    }
}
```

**ENGINEER_FILTERS** (в `services/filters.py`): filtration_rating_min, body_material_id, flow_rate_min, thread_id

## Структура to_dict() — детальная страница

```python
{
    "id": 7, "code": "BPAFR15S02.25RM", "name": "...",
    "model_line": {"id": 3, "name": "BPAFR", "brand": {...}},
    "sku": None,  # будет заполнено после миграции SKU
    "template_vars": {
        "code": "BPAFR15S02.25RM",
        "brand_name": "Архимед",
        "filter_variety": "...",
        "body_material": "...",
        "ip": "...",
        "filtration_rating": "25.0",
        "flow_rate": "4430.00",
        "thread": "NPT 1/2\"",
        ...
    },
    "sections": [
        {"key": "images", "type": "gallery", "data": [...]},
        {"key": "specs", "type": "specs", "groups": [
            {"key": "general", "title": "Основные", "fields": [...]},
            {"key": "pressure", "title": "Давление", "fields": [...]},
            {"key": "body_specs", "title": "Корпус", "fields": [...]},
            {"key": "conditions", "title": "Условия эксплуатации", "fields": [...]},
        ]},
        {"key": "docs", "type": "files", "data": [...]},
        {"key": "certs", "type": "files", "data": [...]},
        {"key": "description", "type": "text", "data": "..."},
    ],
}
```

## Фронтенд

**Страницы** (`frontend/src/apps/filter-regulator-catalog/`):
- `GearboxSection` — сетка серий + кнопка «Инженерный каталог»
- `GearboxList` — подбор + фильтры
- `GearboxDetail` — карточка товара
- `GearboxBrand` — витрина серии (фильтр по model_line_id)
- `EngineerCatalog` — визуальный подбор (чипсы, авто-дефолты, одна карточка)

**Виджет**: `widget/App.vue` — маршруты `#/filter_regulator/{lines,list,detail,brand,engineer}`

**Меню**: TopMenu «⚙️ Настройки» → «🔧 Фильтр-регуляторы», «🔬 Инженерный каталог»
