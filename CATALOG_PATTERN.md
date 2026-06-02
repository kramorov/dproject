# Шаблон нового каталога (Catalog Pattern)

## Архитектура: CatalogConfig

Вся конфигурация каталога — в одном месте. Три слоя фильтрации, позитивное определение фильтров на страницу.

Подробнее: `catalog_concept.md`.

### Ключевые компоненты

| Компонент | Где | Назначение |
|-----------|-----|-----------|
| `FilterDefinition` | `core/models/filter_definition.py` | Одно поле фильтра: тип, источник, label |
| `FilterSet` | `core/models/catalog_config.py` | Набор фильтров для страницы (+ scoped, show_compatible) |
| `CatalogConfig` | `core/models/catalog_config.py` | Вся конфигурация: FilterSet'ы, ORM, метки |
| `SmartCatalogMixin.apply_filters_and_split()` | `core/models/smart_catalog_mixin.py` | Фильтрация + exact/compatible split |
| `BaseFilterOptionsView` | `core/views.py` | API опций фильтров (через CatalogConfig) |

---

## Бэкенд

### 1. Пакет `catalog/` внутри приложения

```
my_equipment/
├── catalog/
│   ├── __init__.py          # реэкспорт
│   ├── filter_defs.py       # именованные FilterDefinition (fd_ip, fd_temp_min, ...)
│   ├── config.py            # MY_CONFIG = CatalogConfig(...) с тремя FilterSet
│   ├── views_filters.py     # class MyFilterOptionsView(BaseFilterOptionsView): catalog_config = MY_CONFIG
│   ├── views_list.py        # CatalogView с apply_filters_and_split
│   ├── views_detail.py      # DetailView
│   └── views_sections.py    # SectionView
├── models/
├── services/
└── admin/
```

### 2. `filter_defs.py` — именованные FilterDefinition

```python
from core.models.filter_definition import FilterDefinition, FilterType, DataSourceType

fd_ip = FilterDefinition(
    param_name='ip_id',
    model_field='ip',
    filter_type=FilterType.IP_RANK,
    data_source_type=DataSourceType.GLOBAL_MODEL,
    source_model=IpOption,
    label='IP',
    order=4,
)

fd_temp_min = FilterDefinition(
    param_name='work_temp_min',
    model_field='work_temp_min',
    filter_type=FilterType.TEMP_MIN,
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Температура от, °С',
    order=5,
)

# ... остальные fd_*

# Legacy-список для обратной совместимости
MY_FILTER_DEFINITIONS = [fd_ip, fd_temp_min, ...]
```

### 3. `config.py` — CatalogConfig

```python
from core.models.catalog_config import CatalogConfig, FilterSet
from my_equipment.models import MyModel, MyModelLine
from my_equipment.catalog.filter_defs import fd_ip, fd_temp_min, fd_brand, ...

MY_CONFIG = CatalogConfig(
    model_class=MyModel,
    model_line_class=MyModelLine,

    filter_sets={
        'list': FilterSet(           # Инженерный подбор
            definitions=[fd_ip, fd_temp_min, fd_temp_max, fd_brand, ...],
            scoped=False,
            show_compatible=True,
        ),
        'model_line': FilterSet(     # Страница серии
            definitions=[fd_ip, fd_temp_min, fd_temp_max, ...],  # без model_line_id, brand_id
            scoped=True,
            show_compatible=True,
        ),
        'quickselect': FilterSet(    # Быстрый подбор
            definitions=[fd_material, fd_torque, ...],
            scoped=True,
            show_compatible=False,
        ),
    },

    select_related=['model_line', 'model_line__brand', ...],
    prefetch_fields=['image_gallery__items__image', ...],
    search_fields=['code', 'name', 'description'],

    labels={
        'title': 'Моё оборудование',
        'breadcrumbName': 'Оборудование',
        'countLabel': 'Товаров:',
        'searchPlaceholder': 'Поиск...',
        'emptyLabel': 'Ничего не найдено',
    },
)
```

### 4. `views_filters.py` — 3 строки

```python
from rest_framework.permissions import AllowAny
from core.views import BaseFilterOptionsView
from my_equipment.catalog.config import MY_CONFIG

class MyFilterOptionsView(BaseFilterOptionsView):
    permission_classes = [AllowAny]
    catalog_config = MY_CONFIG
```

### 5. `views_list.py` — список с фильтрацией

```python
class MyCatalogView(APIView):
    permission_classes = [AllowAny]
    config = MY_CONFIG

    def get(self, request):
        params = request.query_params
        scope = params.get('scope', 'list')
        filter_set = self.config.get_filter_set(scope)

        # Layer 0: visibility
        qs = self.config.get_scoped_queryset()
        qs = self.config.apply_visibility_scope(qs, request)
        qs = qs.select_related(*self.config.select_related)
        qs = qs.prefetch_related(*self.config.prefetch_fields)

        # Layer 1+2: filters + split
        result = self.config.model_class.apply_filters_and_split(
            params,
            filter_definitions=filter_set.definitions,
            base_queryset=qs,
        )
        return Response(result)
```

### 6. URLs

```python
path('filters/', MyFilterOptionsView.as_view()),
path('catalog/', MyCatalogView.as_view()),
path('catalog/<int:pk>/', MyDetailView.as_view()),
path('quickselect/', MyQuickSelectView.as_view()),
```

---

## Фронтенд

### 1. `api.js` — ⚠️ getFilters ДОЛЖЕН принимать params

```javascript
export default {
  list(params)      { return api.get(E.catalog, { params }) },
  getDetail(id)     { return api.get(E.detail(id)) },
  getFilters(params) { return api.get(E.filters, { params }) },  // ← params обязателен!
  getQuickSelect(mlId, filters = {}) {
    return api.get(E.quickselect, { params: { model_line_id: mlId, ...filters } })
  },
}
```

### 2. `App.vue`

Использовать Generic-компоненты из `shared/components/catalog/`:
- `CatalogSection` — сетка серий + CatalogActions
- `CatalogList` — инженерный подбор (фильтры + поиск + exact/compatible)
- `CatalogModelLine` — товары серии (fixedParams + `?scope=model_line` + exact/compatible)
- `CatalogDetail` — карточка товара
- `QuickSelect` — быстрый подбор (чипсы → карточка)

### 3. Shared-компоненты UI

- `PageTitle` — заголовок страницы (title + subtitle + context-чип)
- `CatalogActions` — кнопки «Инженерный подбор» / «Быстрый подбор»
- `Breadcrumbs` — все непоследние крошки кликабельны, emit `navigate`
- `FilterSidebar` — сайдбар фильтров + чекбокс «Показывать совместимые»
- `ProductCard` — карточка товара с ProgressiveImage
- `ProductGallery` — галерея с лайтбоксом

### 4. `useCatalog.js` — общий composable

```javascript
const {
  items, compatibleData, total, exactTotal, compatibleTotal,
  splitFilter, loading, limit, offset,
  filterData, filtersLoaded, showCompatibleAvailable, showCompatible,
  activeFilters, search,
  loadFilters, fetchData,
  onFilterChange, toggleCompatible, resetFilters,
  onSearchInput, goPage,
} = useCatalog(api, {
  fixedParams,
  filterScope: 'model_line',   // для страницы серии
  withSearch: true,
})
```

---

## Чек-лист

- [ ] `catalog/filter_defs.py` — именованные `fd_*` + legacy-список
- [ ] `catalog/config.py` — `MY_CONFIG` с тремя FilterSet (`list`, `model_line`, `quickselect`)
- [ ] `model_line` FilterSet: без `model_line_id` и `brand_id`, `scoped=True`
- [ ] `catalog/views_filters.py` — `catalog_config = MY_CONFIG`
- [ ] `api.js`: `getFilters(params)` — принимает и передаёт params
- [ ] CatalogList: `useCatalog(api, { withSearch:true })` — без filterScope
- [ ] CatalogModelLine: `useCatalog(api, { fixedParams, filterScope:'model_line' })`
- [ ] `SELECT_RELATED` покрывает все FK, включая `image_gallery`, `model_line__image_gallery`
- [ ] `prefetch_related('image_gallery__items__image', 'model_line__image_gallery__items__image')`
- [ ] `apply_filters_and_split` с serializer=`to_values_dict` (лёгкий)
- [ ] Крошки трёхуровневые: Каталог / Оборудование / Страница
- [ ] `url()` хранилища (Cloud.ru) **не делает HEAD-запросов** — только `_normalize()`
- [ ] Удаление вызывает `MediaLibraryItem.delete()` → `file_service.delete_file()` для облака

---

## Фильтр взрывозащиты (Exd) — 2026-06-02

### FilterDefinition

```python
fd_exd = FilterDefinition(
    param_name='exd_id',
    model_field='exd',
    filter_type=FilterType.EXD_COMPATIBLE,
    data_source_type=DataSourceType.CUSTOM,
    label='Взрывозащита',
    order=10,
)
```

### API

| Эндпоинт | Назначение |
|----------|-----------|
| `GET /api/core/exd/structure/` | Иерархия: methods, gas_groups, dust_groups, temperature_classes |
| `GET /api/core/exd/compatible/?method_id=&type_id=&group_id=&temp_id=` | Совместимые ExdOption ID |

### Sentinel'ы

| Значение `exd_id` | Фильтр | Описание |
|-------------------|--------|----------|
| `_none_` | `exd__isnull=True` | Общепромышленное (без Ex) |
| `_empty_` | `exd__in=[]` | Ex-метод без совместимых → пустой результат |
| `5,7,10` | `exd__in=[5,7,10]` | Конкретные совместимые ID |

### Фронтенд

`ExdFilter.vue` — переиспользуемый каскадный компонент. `FilterSidebar.vue` рендерит его при `filter_type === 'exd_compatible'`. Селекты: Метод → Тип → Группа (газ/пыль) → Темп.класс (только газ). Первый пункт методов — «Общепромышленное».
