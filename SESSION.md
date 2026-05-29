# Состояние проекта на 2026-05-29

## ⏳ Задачи на потом

### Кэширование опций фильтров
- **Проблема**: `BaseFilterOptionsView.get()` вызывает `fd.get_options()` для каждого фильтра.
  На странице серии с 6 фильтрами — 6-10 отдельных запросов к БД при каждой загрузке сайдбара.
- **Решение**: кэшировать результат `get_options` в Django cache (memcached/redis) с инвалидацией
  по сигналам модели (post_save/post_delete на связанные модели). Ключ кэша: `catalog:filters:{catalog}:{scope}:{model_line_id}`.
- **Приоритет**: medium, до production-нагрузки.

---

## Сегодня (2026-05-29) — CatalogConfig и Exact/Compatible split

### 🏗️ CatalogConfig — единая конфигурация каталогов
- **`core/models/filter_definition.py`** — `FilterType`, `DataSourceType`, `FilterDefinition` вынесены из `smart_catalog_mixin.py`
  - `supports_split()` — может ли фильтр различать exact/compatible
  - `classify_match(obj, value)` — классификация объекта: 'exact' | 'compatible' | None
  - `get_options(model_class, queryset=None)` — опции фильтра, опционально scoped
  - Float-сравнение с допуском `1e-9`
- **`core/models/catalog_config.py`** — `FilterSet` + `CatalogConfig` dataclasses
  - `FilterSet`: `definitions`, `scoped`, `show_compatible`
  - `CatalogConfig`: `model_class`, `filter_sets`, `select_related`, `prefetch_fields`, `labels`
  - `apply_visibility_scope()` — хук слоя 0 (TODO: партнёрские настройки)
- **`core/utils/catalog_helpers.py`** — `get_currency_code(request)` вынесена из дубликатов

### 🎯 Exact / Compatible split
- **`SmartCatalogMixin.apply_filters_and_split()`** — единый метод фильтрации + разделения
  - Параметр `serializer` (default: `to_values_dict()` — лёгкий)
  - `split_mode='auto'` — разделяет при `show_compatible=true`
  - Ответ: `data`, `compatible_data`, `exact_count`, `compatible_count`, `split_filter`, `split_page_note`
- **Поддерживаемые типы**: TEMP_MIN, TEMP_MAX, MIN, MAX, EXD_COMPATIBLE, THREAD_COMPATIBLE, FUNCTION_COMPATIBLE, IP_RANK
- **Логика classify_match**:
  - FK-based: `obj.{field}_id == requested_id` → exact
  - Value-based: `abs(float(actual) - requested) < 1e-9` → exact

### 📁 Пакеты catalog/ во всех трёх каталогах
- **`gearbox/catalog/`**: `filter_defs.py`, `config.py`, `views_filters.py`, `views_list.py`, `views_detail.py`
- **`filter_regulator/catalog/`**: `filter_defs.py`, `config.py`, `views_filters.py`
- **`pa_controls/catalog/`**: `filter_defs.py`, `config.py`, `views_filters.py`
- Каждый `config.py` определяет 3 FilterSet: `list`, `model_line`, `quickselect`

### 🖥️ BaseFilterOptionsView → CatalogConfig
- Новый путь: `catalog_config = XXX_CONFIG` → возвращает `{ filters, show_compatible }`
- Старый путь (`filter_definitions + scope_exclude`) сохранён для обратной совместимости
- `scope_exclude` по умолчанию исключает `model_line_id` и `brand_id`
- FilterOptionsView всех трёх каталогов переведены на `catalog_config`

### 🎛️ Фронтенд: FilterSidebar + useCatalog
- **FilterSidebar.vue**: чекбокс «Показывать совместимые» (виден при `showCompatibleToggle`)
- **useCatalog.js**:
  - `showCompatible`, `compatibleData`, `exactTotal`, `compatibleTotal`, `splitFilter`
  - `toggleCompatible(val)` — переключение → перезапрос
  - Обработка нового формата `{ filters, show_compatible }`
  - Очистка `filterData` при смене scope (фикс бага с накоплением старых ключей)
- **CatalogList.vue / CatalogModelLine.vue**: секции «🎯 Точно подходят» / «🔗 Выполняют условия»
- **Баг**: `getFilters()` в api.js всех трёх каталогов не принимал параметры → `?scope=model_line` не доходил. Исправлено.

### 📄 Документация
- **`catalog_concept.md`** — полная концепция: 3 слоя, компоненты, постраничная работа, конфигурация, ограничения
- **`CATALOG_PATTERN.md`** — обновлён (CatalogConfig, api.js fix)
- **`frontend/README.md`** — обновлён (новые поля useCatalog, FilterSidebar)

---

## Ранее (2026-05-28 и раньше)

### 🏗️ ImageGallerySet — наборы изображений
- **Модели**: `ImageGallerySet` + `ImageGallerySetItem` (through) в `media_library/models.py`
- **ImageGalleryMixin** переписан: FK `image_gallery` вместо голого M2M `images`
- Удалены дублирующие методы из gearbox, filter_regulator, pa_controls

### 🔗 CertData.media_item: FK → O2O
- `media_item = ForeignKey` → `OneToOneField`, каскадное удаление с очисткой облака

### 🗑️ Каскадное удаление с очисткой Cloud.ru
- `MediaLibraryItem.delete()` удаляет файлы из Cloud.ru через `file_service.delete_file()`

### 🧹 Чистка
- Raw SQL → ORM, удалены мёртвые сигналы, `images` → `image_gallery` в админках

### ⚡ Оптимизация каталогов
- Cloud.ru: `url()` без `head_object` (0 сетевых запросов вместо 120+)
- `to_values_dict()` лёгкий (без `_get_template_vars()`)
- `/sections/` эндпоинт с `annotate(Count)`

## Ключевые архитектурные решения

1. **CatalogConfig** — единая точка конфигурации: фильтры, scope, ORM, метки
2. **FilterSet** — позитивное определение фильтров на страницу (вместо `scope_exclude`)
3. **apply_filters_and_split()** — единый метод фильтрации с exact/compatible
4. **FilterDefinition.classify_match()** — классификация exact/compatible для всех splittable-типов
5. **ImageGalleryMixin** — FK `image_gallery` → `ImageGallerySet`
6. **CertData.media_item** — O2O с каскадным удалением
7. **MediaLibraryItem.delete()** — удаление файлов из Cloud.ru
8. Цены вшиты в ответ API, конвертация через ExchangeRate
9. CSS Custom Properties, виджет с hash-роутером, shared-компоненты
10. `apply_visibility_scope()` — хук для партнёрских ограничений (TODO)

## Файловая карта

| Компонент | Путь |
|---|---|
| FilterDefinition, FilterType, DataSourceType | core/models/filter_definition.py |
| FilterSet, CatalogConfig | core/models/catalog_config.py |
| SmartCatalogMixin (apply_filters_and_split) | core/models/smart_catalog_mixin.py |
| BaseFilterOptionsView | core/views.py |
| get_currency_code (shared) | core/utils/catalog_helpers.py |
| ImageGalleryMixin | core/models/image_gallery_mixin.py |
| CatalogDictMixin | core/models/mixins.py |
| Gearbox config | gearbox/catalog/config.py |
| Gearbox filter defs | gearbox/catalog/filter_defs.py |
| Gearbox views (new) | gearbox/catalog/views_*.py |
| Filter-regulator config | filter_regulator/catalog/config.py |
| Filter-regulator filter defs | filter_regulator/catalog/filter_defs.py |
| Limit-switch config | pa_controls/catalog/config.py |
| Limit-switch filter defs | pa_controls/catalog/filter_defs.py |
| Shared компоненты | frontend/src/shared/components/ |
| Catalog composable | frontend/src/shared/composables/useCatalog.js |
| Catalog API clients | frontend/src/apps/*/api.js |
| Концепция каталогов | catalog_concept.md |
| Паттерн каталога | CATALOG_PATTERN.md |

## ⚠️ Баг codewhale-tui v0.8.47

Паника в `verify.rs:422` на кириллице. `edit_file` — не использовать. `apply_patch` и `write_file` — безопасны.
