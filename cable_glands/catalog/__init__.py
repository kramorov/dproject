# cable_glands/catalog/__init__.py
"""
Каталог кабельных вводов (CableGland) — конфигурация и REST-эндпоинты для фронта.

Реализует паттерн каталога оборудования (см. `CATALOG_PATTERN.md` и эталон
`solenoid_valves/catalog/`): декларативные `FilterDefinition` + `CatalogConfig`
(`filter_sets` по страницам) и тонкие `APIView`, делегирующие фильтрацию в
`SmartCatalogMixin.apply_filters_and_split` и сериализацию в
`CatalogSerializerMixin.to_dict()`.

Состав пакета:

- `filter_defs.py` — определения фильтров (`CABLE_GLAND_FILTER_DEFINITIONS`):
  серия, бренд, резьба (`thread_option__thread_size`), материал корпуса
  (`body_material_option__body_material`), взрывозащита (EXD_COMPATIBLE через
  `exd_option__exd_options`), IP (EXACT-вхождение через M2M `model_line__ip`),
  диаметр кабеля (внутр./внеш. — числовые «от/до»), температура («от/до» +
  климатическое исполнение `CLIMATE_CASCADE`), булевы флаги серии
  (бронированный / металлорукав / трубопровод). Реестр зарегистрирован в
  `core/wizard_filter_registry.py` для мастера подбора (Selection Wizard).

- `config.py` — `CABLE_GLAND_CONFIG` (`CatalogConfig`): наборы фильтров
  `list` / `engineer` / `model_line` / `quickselect`, `select_related` /
  `prefetch_fields`, подписи UI.

- `views_list.py` — `GET /api/cable-glands/catalog/` (список + поиск + цены;
  `?scope=model_line` — просмотр по сериям).

- `views_detail.py` — `GET /api/cable-glands/catalog/<pk>/` (карточка + Schema.org).

- `views_filters.py` — `GET /api/cable-glands/filters/` (опции фильтров списка).

- `views_engineer.py` / `views_engineer_filters.py` — инженерный подбор
  (`/api/cable-glands/engineer/`, `/engineer/filters/`).

- `views_quickselect.py` — `GET /api/cable-glands/quickselect/` (быстрый подбор).

- `views_meta.py` — `GET /api/cable-glands/meta/` (метаданные полей из
  `TEMPLATE_FIELDS` через `CableGland.get_field_meta()`).

- `views_sections.py` — `GET /api/cable-glands/sections/` (серии со счётчиками
  и первым фото). Отдельный эндпоинт нужен, потому что fallback фронта на
  `list({limit: 1000})` серверно режется до 200 записей — при 972 артикулах
  часть серий терялась бы.

Маршруты подключены в `cable_glands/urls.py`; фронт — мини-приложение
`frontend/src/apps/cable-gland-catalog/` + страница
`frontend/src/pages/catalog/CableGlandPage.vue` (маршрут `/catalog/cable-glands`).
"""
