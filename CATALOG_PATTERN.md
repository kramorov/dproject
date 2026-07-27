# Catalog Pattern — архитектура и шаблон каталога оборудования

> Обновлено 2026-07-27: breadcrumbs с режимами, CatalogActions-табы, parentMode, core/access.py, engineer AllowAny
> Обновлено 2026-07-23: SectionAccessPermission → catalog_permission_classes(), новый HomePage
> Обновлено 2026-06-10: PriceDocument/EAPriceDocument → shared DocumentJournal/DocumentCard

---

## 1. Концепция

Каждый каталог оборудования (редукторы, фильтр-регуляторы, БКВ, клапаны, фитинги) строится по единому шаблону. Вся конфигурация — фильтры, scope, ORM-оптимизации, метки, права доступа — собрана в одном месте.

### Три слоя фильтрации

```
GET /api/gearbox/catalog/?ip_id=5&work_temp_min=-42&show_compatible=true

┌──────────────────────────────────────────────┐
│ Слой 0: VISIBILITY SCOPE                    │
│  apply_visibility_scope(queryset, request)   │
│  → core.access.apply_catalog_visibility()    │
│  → фильтрация по брендам/сериям (заглушка)   │
├──────────────────────────────────────────────┤
│ Слой 1: USER FILTERS                        │
│  FilterSet.definitions                      │
│  → итерация FilterDefinition, build_filter_lookup, .filter() │
├──────────────────────────────────────────────┤
│ Слой 2: EXACT / COMPATIBLE SPLIT            │
│  apply_filters_and_split(..., split_mode='auto')            │
│  → classify_match(obj, requested_value)                     │
│  → data (точные) + compatible_data (совместимые)            │
└──────────────────────────────────────────────┘
```

---

## 2. Ключевые компоненты

| Компонент | Где | Назначение |
|-----------|-----|-----------|
| `FilterDefinition` | `core/models/filter_definition.py` | Одно поле фильтра: тип, источник, label |
| `FilterSet` | `core/models/catalog_config.py` | Набор фильтров для страницы (+ scoped, show_compatible) |
| `CatalogConfig` | `core/models/catalog_config.py` | Вся конфигурация: FilterSet'ы, ORM, метки, visibility |
| `catalog_permission_classes()` | `core/access.py` | Централизованные права доступа для catalog API |
| `apply_catalog_visibility()` | `core/access.py` | Централизованная фильтрация queryset по правам |
| `SmartCatalogMixin` | `core/models/smart_catalog_mixin.py` | `apply_filters_and_split()` + `to_dict()` |
| `BaseFilterOptionsView` | `core/views.py` | API опций фильтров (через CatalogConfig) |

### 2.1 FilterDefinition

```python
fd_ip = FilterDefinition(
    param_name='ip_id',
    model_field='ip',
    filter_type=FilterType.IP_RANK,
    data_source_type=DataSourceType.GLOBAL_MODEL,
    source_model=IpOption,
    label='IP',
    order=4,
)
```

Методы:
- `supports_split()` — может ли фильтр различать exact/compatible
- `classify_match(obj, value)` — `'exact'`, `'compatible'` или `None`
- `get_options(model_class, queryset=None)` — опции (scoped если передан queryset)

### 2.2 FilterSet + CatalogConfig

```python
@dataclass
class FilterSet:
    definitions: List[FilterDefinition]
    scoped: bool            # True = опции ограничены model_line
    show_compatible: bool   # доступен exact/compatible split

@dataclass
class CatalogConfig:
    model_class: type
    model_line_class: type
    filter_sets: Dict[str, FilterSet]  # 'list', 'engineer', 'model_line', 'quickselect'
    select_related: List[str]
    prefetch_fields: List[str]
    search_fields: List[str]
    labels: Dict[str, str]

    def apply_visibility_scope(self, queryset, request) -> QuerySet: ...
    def get_filter_set(self, scope: str) -> FilterSet: ...
    def get_scoped_queryset(self, model_line_id=None) -> QuerySet: ...
```

### 2.3 Access control (`core/access.py`)

Централизованный модуль доступа для всех catalog API. Единая точка входа:

```python
from core.access import catalog_permission_classes, apply_catalog_visibility

class MyCatalogView(APIView):
    permission_classes = catalog_permission_classes()  # [AllowAny] — заглушка

    def get(self, request):
        qs = config.get_scoped_queryset()
        qs = apply_catalog_visibility(request, qs)     # фильтрация — заглушка
        ...
```

`CatalogConfig.apply_visibility_scope()` делегирует в `apply_catalog_visibility()`.

Будущее (access.md §7): фильтрация по `request.customer.visible_brands`, `CustomerApiKey.brand_filters`, `CustomerAppAccess`.

---

## 3. Типы страниц каталога

| Страница | Scope FilterSet | Scoped | Split | Компонент |
|----------|----------------|--------|-------|-----------|
| Просмотр по сериям | — | — | — | `CatalogSection` |
| Инженерный подбор | `'list'` | нет | да | `EngineerSelection` |
| Страница серии | `'model_line'` | да | да | `CatalogModelLine` |
| Быстрый подбор | `'quickselect'` | да | нет | `QuickSelect` |
| Мастер подбора | — | — | — | `WizardPlaceholder` (заглушка) |
| AI подбор | — | — | — | `AiPlaceholder` (заглушка) |
| Карточка товара | — | — | — | `CatalogDetail` |

---

## 4. Бэкенд

### 4.1 Пакет `catalog/` внутри приложения

```
my_equipment/
├── catalog/
│   ├── __init__.py          # реэкспорт
│   ├── filter_defs.py       # именованные FilterDefinition
│   ├── config.py            # MY_CONFIG = CatalogConfig(...) с FilterSet'ами
│   ├── views_filters.py     # class MyFilterOptionsView(BaseFilterOptionsView)
│   ├── views_list.py        # CatalogView с apply_filters_and_split
│   ├── views_detail.py      # DetailView
│   ├── views_engineer.py    # EngineerView (mode='engineer')
│   ├── views_engineer_filters.py  # EngineerFilterOptionsView
│   └── views_sections.py    # SectionView
├── models/
├── services/
└── admin/
```

### 4.2 config.py — пример

```python
MY_CONFIG = CatalogConfig(
    model_class=MyModel,
    model_line_class=MyModelLine,

    filter_sets={
        'list': FilterSet(
            definitions=[fd_ip, fd_temp_min, fd_temp_max, fd_brand, ...],
            scoped=False, show_compatible=True,
        ),
        'engineer': FilterSet(
            definitions=[...],  # обычно копия 'list'
            scoped=False, show_compatible=True,
        ),
        'model_line': FilterSet(
            definitions=[fd_ip, fd_temp_min, ...],  # без model_line_id, brand_id
            scoped=True, show_compatible=True,
        ),
        'quickselect': FilterSet(
            definitions=[fd_material, fd_torque, ...],
            scoped=True, show_compatible=False,
        ),
    },

    select_related=['model_line', 'model_line__brand', 'image_gallery', ...],
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

### 4.3 views_list.py

```python
from core.access import catalog_permission_classes

class MyCatalogView(APIView):
    permission_classes = catalog_permission_classes()
    config = MY_CONFIG

    def get(self, request):
        params = request.query_params
        scope = params.get('scope', 'list')
        filter_set = self.config.get_filter_set(scope)

        qs = self.config.get_scoped_queryset()
        qs = self.config.apply_visibility_scope(qs, request)  # → core.access
        qs = qs.select_related(*self.config.select_related)
        qs = qs.prefetch_related(*self.config.prefetch_fields)

        result = self.config.model_class.apply_filters_and_split(
            params, filter_definitions=filter_set.definitions, base_queryset=qs,
        )
        # Добавить цены (get_bulk_prices)
        return Response(result)
```

### 4.4 views_filters.py

```python
class MyFilterOptionsView(BaseFilterOptionsView):
    permission_classes = catalog_permission_classes()
    catalog_config = MY_CONFIG
```

### 4.5 URLs

```python
path('sections/', MySectionView.as_view()),
path('catalog/', MyCatalogView.as_view()),
path('catalog/<int:pk>/', MyDetailView.as_view()),
path('filters/', MyFilterOptionsView.as_view()),
path('engineer/', MyEngineerView.as_view()),
path('engineer/filters/', MyEngineerFilterOptionsView.as_view()),
path('quickselect/', MyQuickSelectView.as_view()),
path('meta/', MyMetaView.as_view()),
```

### 4.6 apply_filters_and_split — формат ответа

```json
{
    "data": [...],
    "total": 42,
    "filters_applied": {"ip_id": "5"},
    "limit": 24, "offset": 0,
    "compatible_data": [...],
    "exact_count": 12,
    "compatible_count": 30,
    "split_filter": "work_temp_min",
    "split_value": "-42"
}
```

---

## 5. Фронтенд

### 5.1 api.js

```javascript
import api from '@/shared/api'
import { ENDPOINTS } from '@/shared/endpoints'
const E = ENDPOINTS.limitSwitch

export default {
  getSections()  { return api.get(E.sections) },
  list(params)   { return api.get(E.catalog, { params }) },
  getDetail(id)  { return api.get(E.detail(id)) },
  getFilters(params) { return api.get(E.filters, { params }) },
  getEngineer(params) { return api.get(E.engineer, { params }) },
  getEngineerFilters(params) { return api.get(E.engineerFilters, { params }) },
  getQuickSelect(mlId, filters = {}) {
    return api.get(E.quickselect, { params: { model_line_id: mlId, ...filters } })
  },
}
```

### 5.2 App.vue — структура

```vue
<template>
  <div class="app">
    <CatalogSection v-if="page === 'section'" :api="api" :labels="labels.section"
      @select-series="goToBrand" @select="goToList" @quickselect="goToQuickSelect"
      @wizard="goToWizard" @ai="goToAi" @navigate="goToSection" />
    <EngineerSelection v-else-if="page === 'list'" ... @navigate="goToSection" />
    <CatalogDetail v-else-if="page === 'detail'" :parent-mode="parentModeName" ... />
    <CatalogModelLine v-else-if="page === 'brand'" :parent-mode="parentModeName" ... />
    <QuickSelect v-else-if="page === 'quickselect'" ... />
    <WizardPlaceholder v-else-if="page === 'wizard'" ... />
    <AiPlaceholder v-else-if="page === 'ai'" ... />
  </div>
</template>
```

Все 7 состояний страницы. `parentModeName` — computed, отслеживает текущий/предыдущий режим для хлебных крошек.

### 5.3 Shared-компоненты каталога

| Компонент | Назначение |
|-----------|-----------|
| `CatalogSection` | Сетка серий + `CatalogActions` (табы режимов) + `Breadcrumbs` |
| `CatalogActions` | Табы-переключатели: Просмотр по сериям / Инженерный / Быстрый / Мастер / AI |
| `EngineerSelection` | Инженерный подбор с `EngineerFilterBar` + `EngineerProductCard` |
| `CatalogModelLine` | Товары серии (fixedParams + exact/compatible split) |
| `QuickSelect` | Быстрый подбор (чипсы → карточка) |
| `CatalogDetail` | Карточка товара через `ProductDetail` |
| `WizardPlaceholder` | Заглушка «Мастер подбора» |
| `AiPlaceholder` | Заглушка «AI подбор» |
| `Breadcrumbs` | Хлебные крошки (3–4 уровня), `to`/`url`/`emit('navigate')` |
| `PageTitle` | Заголовок (title + subtitle + context-чип) |
| `ProductDetail` | Оркестратор карточки: `Breadcrumbs` + `ProductGallery` + `ProductHeader` + `ProductTabs` |

### 5.4 Хлебные крошки — структура

| Страница | Крошки |
|----------|--------|
| Просмотр по сериям | `🏠 Каталог` → `БКВ` → `Просмотр по сериям` |
| Серия УРАЛ | `🏠 Каталог` → `БКВ` → `Просмотр по сериям` → `УРАЛ` |
| Инженерный подбор | `🏠 Каталог` → `БКВ` → `Инженерный подбор` |
| Быстрый подбор | `🏠 Каталог` → `БКВ` → `Быстрый подбор` |
| Мастер подбора | `🏠 Каталог` → `БКВ` → `Мастер подбора` |
| AI подбор | `🏠 Каталог` → `БКВ` → `AI подбор` |
| Карточка товара | `🏠 Каталог` → `БКВ` → `{откуда пришли}` → `товар` |

- `🏠` = `{ to: '/' }` → router.push (главная)
- Средние крошки без `to` → `emit('navigate')` → `goToSection()`
- `ProductDetail` пробрасывает `@navigate` наружу
- `parentMode` прокидывается в `CatalogModelLine` и `CatalogDetail`

### 5.5 useCatalog.js

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
  mode: 'engineer',            // для инженерного подбора
  withSearch: true,
})
```

---

## 6. Exd-фильтр (взрывозащита)

```python
fd_exd = FilterDefinition(
    param_name='exd_id', model_field='exd',
    filter_type=FilterType.EXD_COMPATIBLE,
    data_source_type=DataSourceType.CUSTOM,
    label='Взрывозащита', order=10,
)
```

API:
- `GET /api/core/exd/structure/` — иерархия: methods, gas_groups, dust_groups, temp_classes
- `GET /api/core/exd/compatible/?method_id=&type_id=&group_id=&temp_id=` — совместимые ID

Фронтенд: `ExdFilter.vue` — каскадный компонент. Рендерится в `FilterSidebar` при `filter_type === 'exd_compatible'`.

---

## 7. ClimateFilter (климатическое исполнение)

```python
fd_climate = FilterDefinition(
    param_name='climate', model_field='work_temp_min',
    filter_type=FilterType.CLIMATE_CASCADE,
    data_source_type=DataSourceType.CUSTOM,
    label='Клим. исполнение',
)
```

Фронтенд: `ClimateFilter.vue` — каскад (зона → размещение), `compact`-режим, парсинг «УХЛ4».

---

## 8. Чек-лист нового каталога

- [ ] `catalog/filter_defs.py` — именованные `fd_*` + legacy-список
- [ ] `catalog/config.py` — `MY_CONFIG` с FilterSet'ами (`list`, `engineer`, `model_line`, `quickselect`)
- [ ] `model_line` FilterSet: без `model_line_id` и `brand_id`, `scoped=True`
- [ ] `catalog/views_*.py` — все view с `permission_classes = catalog_permission_classes()`
- [ ] `app/urls.py` — все 8 маршрутов (sections, catalog, detail, filters, engineer, engineer/filters, quickselect, meta)
- [ ] `djangoProject1/urls.py` — `path('api/my-equipment/', include(...))`
- [ ] `api.js`: `getFilters(params)` — принимает и передаёт params
- [ ] `App.vue`: все 7 состояний страницы, `@wizard`/`@ai` → `goToSection()`
- [ ] `labels`: `breadcrumbName` во всех секциях, `wizardTitle`/`aiTitle` для заглушек
- [ ] `SELECT_RELATED` покрывает все FK, включая `image_gallery`, `model_line__image_gallery`
- [ ] `prefetch_related('image_gallery__items__image', 'model_line__image_gallery__items__image')`
- [ ] Крошки 3–4 уровневые с `parentMode`
- [ ] `endpoints.js` — запись в `ENDPOINTS`
- [ ] `vite.config.js` — входная точка мини-аппа в `rollupOptions.input`
