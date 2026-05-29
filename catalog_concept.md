# Catalog Concept — концепция и архитектура каталогов

> Дата: 2026-05-29
> Статус: бэкенд реализован, фронтенд реализован, ожидает обкатки

---

## 1. Общая идея

Каждый каталог оборудования (редукторы, фильтр-регуляторы, БКВ) строится по единому шаблону. Вся конфигурация — фильтры, scope, ORM-оптимизации, метки — собрана в одном месте: `CatalogConfig`. Это устраняет дублирование кода, размазанную конфигурацию и негативную логику `scope_exclude`.

### Три слоя фильтрации

```
Запрос: GET /api/gearbox/catalog/?ip_id=5&work_temp_min=-42&show_compatible=true

┌──────────────────────────────────────────────┐
│ Слой 0: VISIBILITY SCOPE                    │
│  apply_visibility_scope(queryset, request)   │
│  → отсечение по партнёру/сайту (TODO)       │
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

### 2.1 `FilterDefinition` (`core/models/smart_catalog_mixin.py`)

Описывает один фильтр: имя параметра, поле модели, тип фильтрации, источник данных.

**Новые методы:**

| Метод | Назначение |
|-------|-----------|
| `supports_split()` | Может ли этот фильтр различать exact/compatible |
| `classify_match(obj, value)` | Классифицирует ОДИН объект: `'exact'`, `'compatible'` или `None` |
| `get_options(model_class, queryset=None)` | Опции фильтра. Если `queryset` передан — значения ограничены им (scoped mode) |

**Логика classify_match:**

```
FK-based (EXD_COMPATIBLE, THREAD_COMPATIBLE, FUNCTION_COMPATIBLE, IP_RANK):
    exact   = obj.{field}_id == requested_id
    compatible = obj.{field}_id != requested_id (но прошёл фильтр)

Value-based (TEMP_MIN, MIN):
    exact   = obj.{field} == requested_value
    compatible = obj.{field} < requested_value (с запасом)

Value-based (TEMP_MAX, MAX):
    exact   = obj.{field} == requested_value
    compatible = obj.{field} > requested_value (с запасом)
```

### 2.2 `FilterSet` + `CatalogConfig` (`core/models/catalog_config.py`)

```python
@dataclass
class FilterSet:
    definitions: List[FilterDefinition]  # какие фильтры на этой странице
    scoped: bool                          # True = значения ограничены model_line
    show_compatible: bool                 # доступен ли exact/compatible split

@dataclass
class CatalogConfig:
    model_class: type                     # Модель Django
    model_line_class: type                # Модель серии
    filter_sets: Dict[str, FilterSet]     # 'list', 'model_line', 'quickselect'
    select_related: List[str]             # ORM-оптимизация
    prefetch_fields: List[str]
    search_fields: List[str]
    labels: Dict[str, str]                # Метки для фронтенда

    def apply_visibility_scope(self, queryset, request) -> QuerySet:
        """Слой 0: ограничение по партнёру/сайту. Пока заглушка (TODO)."""
        return queryset

    def get_filter_set(self, scope: str) -> FilterSet: ...
    def get_scoped_queryset(self, model_line_id=None) -> QuerySet: ...
```

### 2.3 `SmartCatalogMixin.apply_filters_and_split()` (`core/models/smart_catalog_mixin.py`)

Единый метод фильтрации + опционального разделения exact/compatible.

```python
@classmethod
def apply_filters_and_split(cls, params, filter_definitions,
                             base_queryset=None, split_mode='auto') -> Dict:
    """
    params:          Request query params
    filter_definitions: FilterDefinition-ы из FilterSet
    base_queryset:   Пре-фильтрованный queryset (после слоя 0)
    split_mode:      'auto' — разделять если show_compatible=true
                     'off'  — никогда не разделять

    Returns:
        {
            data: [...], total, filters_applied,
            # При split:
            compatible_data: [...], exact_total, compatible_total,
            split_filter: 'param_name', split_value: value,
        }
    """
```

### 2.4 `BaseFilterOptionsView` (`core/views.py`)

Обновлён для поддержки `CatalogConfig` (с обратной совместимостью).

**Новый путь:** `catalog_config = SomeCatalog` → возвращает `{ filters: {...}, show_compatible: bool }`
**Старый путь:** `filter_definitions + model_class + scope_exclude` → возвращает `{ param_name: {...} }`

---

## 3. Как это работает для каждого типа страницы

### 3.1 Инженерный подбор (`CatalogList`)

```
Scope: 'list'
Фильтры: все (включая model_line_id, brand_id)
Scoped: нет (глобальные значения из всей таблицы)
Split:  да (show_compatible=true)

GET /api/gearbox/catalog/?ip_id=5&work_temp_min=-42&show_compatible=true

Ответ:
{
  data: [           // exact: work_temp_min == -42
    { id:1, name:"РД-10", ... }
  ],
  compatible_data: [ // compatible: work_temp_min < -42 (с запасом)
    { id:5, name:"РД-20", work_temp_min:-60, ... }
  ],
  total: 150,
  exact_total: 42,
  compatible_total: 108,
  split_filter: "work_temp_min",
  split_value: -42
}
```

### 3.2 Страница серии (`CatalogModelLine`)

```
Scope: 'model_line'
Фильтры: без model_line_id и brand_id
Scoped: да (значения только из товаров этой серии)
Split:  да (show_compatible=true)

GET /api/gearbox/catalog/?model_line_id=10&ip_id=5&show_compatible=true&scope=model_line

Фильтр «Материал корпуса» покажет 3 варианта (только те, что есть в серии 10),
а не все 15 из глобальной таблицы.
```

### 3.3 Быстрый подбор (`QuickSelect`)

```
Scope: 'quickselect'
Фильтры: только чипсовые (быстрые)
Scoped: да
Split:  нет (show_compatible=false — чекбокс скрыт)

GET /api/gearbox/quickselect/?model_line_id=10&body_material_id=3
```

---

## 4. Файловая структура каталога (на примере gearbox)

```
gearbox/
├── catalog/                     ← новый пакет конфигурации
│   ├── __init__.py              ← реэкспорт
│   ├── filter_defs.py           ← именованные FilterDefinition (fd_ip, fd_temp_min, ...)
│   ├── config.py                ← GEARBOX_CONFIG (FilterSets, select_related, labels)
│   ├── views_filters.py         ← GearboxFilterOptionsView (1 строка)
│   ├── views_list.py            ← GearboxCatalogView (с apply_filters_and_split)
│   ├── views_detail.py          ← GearboxDetailView
│   └── views_sections.py        ← GearboxSectionView (будет)
│
├── models/                      ← модели Django
├── services/                    ← бизнес-логика (старые фильтры оставлены для совместимости)
├── views/                       ← старые view (постепенно мигрируют в catalog/)
└── admin/
```

---

## 5. Фронтенд

### 5.1 `FilterSidebar.vue`

Добавлен чекбокс «Показывать совместимые». Виден только когда API возвращает `show_compatible: true`.

```html
<FilterSidebar
  :filters="filterData"
  :show-compatible="showCompatible"
  :show-compatible-toggle="showCompatibleAvailable"
  @change="onFilterChange"
  @reset="resetFilters"
  @toggle-compatible="toggleCompatible"
/>
```

### 5.2 `useCatalog.js`

Новые поля:
- `showCompatible` / `showCompatibleAvailable` — состояние чекбокса
- `compatibleData` — совместимые результаты
- `exactTotal` / `compatibleTotal` — счётчики
- `splitFilter` — по какому фильтру произошло разделение
- `toggleCompatible(val)` — переключение чекбокса → перезапрос

### 5.3 `CatalogList.vue` / `CatalogModelLine.vue`

Результаты рендерятся двумя секциями:

```
🎯 Точно подходят (42)
┌──────┐ ┌──────┐ ┌──────┐
│ -42  │ │ -42  │ │ -40  │
└──────┘ └──────┘ └──────┘

🔗 Выполняют условия (108)
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│ -60  │ │ -55  │ │ -60  │ │ -55  │  ...
└──────┘ └──────┘ └──────┘ └──────┘
```

Когда `showCompatible=false` — секция «Выполняют условия» скрыта, всё в одном списке.

---

## 6. Конфигурация фильтров по каталогам

### 6.1 Gearbox (редукторы)

| Фильтр | List | ModelLine | QuickSelect | Тип split |
|--------|------|-----------|-------------|-----------|
| IP | ✅ | ✅ | — | IP_RANK |
| Темп. от | ✅ | ✅ | — | TEMP_MIN |
| Темп. до | ✅ | ✅ | — | TEMP_MAX |
| Момент | ✅ | ✅ | ✅ | MIN |
| Материал | ✅ | ✅ | ✅ | — |
| Бренд | ✅ | — | — | — |
| Монтаж. пл. | ✅ | ✅ | ✅ | — |

### 6.2 Filter-regulator

| Фильтр | List | ModelLine | QuickSelect | Тип split |
|--------|------|-----------|-------------|-----------|
| Серия | ✅ | — | — | — |
| Фильтрация | ✅ | ✅ | ✅ | MIN |
| Материал | ✅ | ✅ | ✅ | — |
| Расход | ✅ | ✅ | ✅ | MIN |
| Резьба | ✅ | ✅ | ✅ | — |
| Темп. от | ✅ | ✅ | — | TEMP_MIN |
| Темп. до | ✅ | ✅ | — | TEMP_MAX |
| Бренд | ✅ | — | — | — |

### 6.3 Limit Switch Box (БКВ)

| Фильтр | List | ModelLine | QuickSelect | Тип split |
|--------|------|-----------|-------------|-----------|
| Серия | ✅ | — | — | — |
| Тип сенсора | ✅ | ✅ | ✅ | — |
| Датчики | ✅ | ✅ | ✅ | — |
| IP | ✅ | ✅ | — | IP_RANK |
| Темп. от | ✅ | ✅ | — | TEMP_MIN |
| Темп. до | ✅ | ✅ | — | TEMP_MAX |
| Материал | ✅ | ✅ | ✅ | — |
| Бренд | ✅ | — | — | — |
| Сигнал | ✅ | ✅ | ✅ | — |
| Ex d | ✅ | ✅ | — | EXD_COMPATIBLE |

---

## 7. Будущее: слой visibility и комплексный подбор

### 7.1 Видимость по партнёру/сайту (TODO)

Хук `apply_visibility_scope` в `CatalogConfig` — заглушка. Когда появится `CustomerSettings.catalog_scope`:

```python
def apply_visibility_scope(self, queryset, request):
    partner = get_partner_from_request(request)
    allowed = partner.settings.get('catalog_scope', {})
    scope = allowed.get('gearbox', {})
    if scope.get('brands'):
        queryset = queryset.filter(model_line__brand_id__in=scope['brands'])
    if scope.get('series'):
        queryset = queryset.filter(model_line_id__in=scope['series'])
    return queryset
```

### 7.2 Комплексный подбор оборудования

Те же `FilterDefinition` будут использоваться для:
- Сериализации критериев подбора
- Сохранения/восстановления наборов фильтров
- Пошагового подбора: gearbox → filter_regulator → БКВ → спецификация

---

## 8. Как добавить новый каталог

1. Создать `my_equipment/catalog/filter_defs.py` — именованные `FilterDefinition`
2. Создать `my_equipment/catalog/config.py` — `MY_CONFIG = CatalogConfig(...)` с тремя `FilterSet`
3. Создать `my_equipment/catalog/views_filters.py` — `class MyFilterOptionsView(BaseFilterOptionsView): catalog_config = MY_CONFIG`
4. Подключить URL в `urls.py`
5. Фронтенд: использовать `CatalogList`, `CatalogModelLine`, `QuickSelect` с нужным `api` и `labels`

---

## 9. Известные ограничения

### 9.1 Пагинация при exact/compatible split

`exact_count` и `compatible_count` считаются **по текущей странице**, а не по всему результату. Это связано с тем, что классификация `classify_match()` работает на уровне объектов Python и не может быть эффективно выполнена в SQL.

Для страницы из 24 товаров с `show_compatible=true`:
- `total` = общее количество отфильтрованных (до пагинации)
- `exact_count` = количество exact на этой странице (не во всей выборке)
- `compatible_count` = количество compatible на этой странице

**Следствие:** нельзя независимо пагинировать «только exact» или «только compatible». Пользователь видит смешанную страницу. Для получения полных подсчётов по всей выборке потребуется дополнительный запрос с агрегацией.

### 9.2 Split по последнему splittable-фильтру

Когда активно несколько фильтров с `supports_split()`, разделение производится по **последнему** из них. Приоритет не настраивается.

### 9.3 Scoped-фильтры: N+1 запросов к опциям

Каждый вызов `fd.get_options(model_class, queryset=base_qs)` делает отдельный запрос к БД. Для страницы серии с 6 фильтрами это 6-10 запросов только для сайдбара. Требуется кэширование (см. SESSION.md).

---

## 10. Обратная совместимость

- `BaseFilterOptionsView` поддерживает старый режим (`filter_definitions + model_class + scope_exclude`)
- Старые `FILTER_DEFINITIONS` в `services/filters.py` и `models/limit_switch.py` сохранены
- `SmartCatalogMixin.filter_by_params()` не удалён — используется Streamlit-страницами
- Новый `apply_filters_and_split()` — дополнительный метод, не ломает существующий код
