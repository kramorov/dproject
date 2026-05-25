# Состояние проекта на 2026-05-23

## Ключевые архитектурные решения

1. CatalogDictMixin в core/models/mixins.py — единый to_dict() для всех каталогов
2. to_dict() → sections (gallery/specs/docs/certs/description) + template_vars
3. _get_template_vars() — единый источник значений. _get_data_dict() — для TemplateMixin
4. Цены вшиты в ответ API, конвертация через ExchangeRate, валюта из CustomerSettings
5. CSS Custom Properties — default/dark/minimal темы, компоненты ссылаются на переменные
6. Виджет widget/ — клиентский hash-роутер (#/gearbox/detail/123), F5 работает
7. Shared-компоненты — 11 штук, переиспользуются для всех типов каталогов

## Правила работы
- Не писать в существующие файлы без разрешения
- Шаг за шагом
- При смене машины читать SESSION.md (в git)

## Реализованные каталоги

### Редукторы (gearbox)
- **Бэкенд**: `GearBox(CatalogDictMixin, ...)`, to_dict() + to_values_dict(), фильтры, цены
- **Фронтенд**: `frontend/src/apps/gearbox-catalog/` (4 страницы: секции, каталог, деталка, бренд)
- **API**: `/api/gearbox/catalog/`, `/api/gearbox/catalog/<id>/`, `/api/gearbox/filters/`, `/api/gearbox/meta/`
- **Документация**: `gearbox/README.md`

### Фильтр-регуляторы (filter_regulator) — 2026-05-23
- **Бэкенд**:
  - `FilterRegulator(CatalogDictMixin, ImageGalleryMixin, TechDocMixin, ...)`
  - to_dict(): 5 секций (Images, Specs с 4 группами, Docs, Description)
  - to_values_dict(): облегчённый для списков
  - _get_template_vars(): 21 значение
  - Фильтры: IP (с ранжированием), температура мин/макс, бренд
  - Цены вшиты (через get_bulk_prices/get_display_price)
- **Фронтенд**: `frontend/src/apps/filter-regulator-catalog/` (полный SPA, копия gearbox)
- **API**: `/api/filter-regulator/catalog/`, `/api/filter-regulator/catalog/<id>/`, `/api/filter-regulator/filters/`, `/api/filter-regulator/meta/`
- **Виджет**: добавлен в CatalogIndex как «Фильтр-регуляторы» (icon: 🔧)
- **URL**: `djangoProject1/urls.py` → `path('api/filter-regulator/', include('filter_regulator.urls'))`

## Текущие задачи
- [X] WordPress — просмотр документов
  - [X] FileList — прямая ссылка в новой вкладке (вместо iframe)
  - [X] FileViewerModal — удалён из FileList, остался для галереи
- [ ] npm run build — исправить баг в client_request (незакрытый тег)
- [X] Фильтры редукторов — model_line_id и body_id убраны, body_material → UNIQUE_FIELD_VALUES
- [X] Frontend фильтров — v-model="activeFilters[f.key]" вместо activeFilters[key]
- [X] Каталог фильтр-регуляторов — модель, API, фронтенд, виджет

## Важные пути

| Ресурс | Путь |
|--------|------|
| CatalogDictMixin | `core/models/mixins.py` (+161 строк в конце файла) |
| GearBox.to_dict() | `gearbox/models/gearbox.py` |
| FilterRegulator.to_dict() | `filter_regulator/models/fr_model_line_item.py` |
| API meta (gearbox) | `gearbox/views/meta.py` |
| API meta (filter) | `filter_regulator/views/meta.py` |
| API catalog (общий шаблон) | `gearbox/views/catalog.py`, `filter_regulator/views/catalog.py` |
| Фильтры (gearbox) | `gearbox/services/filters.py` |
| Фильтры (filter_regulator) | `filter_regulator/services/filters.py` |
| Shared компоненты | `frontend/src/shared/components/` (11 шт.) |
| CSS темы | `frontend/src/shared/themes/` (default, dark, minimal) |
| CatalogMeta store | `frontend/src/shared/stores/catalogMeta.js` |
| Gearbox pages | `frontend/src/apps/gearbox-catalog/` (4 компонента) |
| Filter-regulator pages | `frontend/src/apps/filter-regulator-catalog/` (4 компонента) |
| Widget (встраиваемый) | `frontend/src/apps/widget/` (router.js + CatalogIndex) |
| WordPress плагин | `wp-catalog-plugin/catalog.php` |
| Vite config | `frontend/vite.config.js` (gearbox + filter-regulator + widget) |
| Главный urls.py | `djangoProject1/urls.py` |
| Цены / валюта | `price/services/currency_converter.py`, `project_customers/models/customer_settings.py` |
| Утилита получения клиента | `project_customers/utils.py` |

## CSS-темы

Три схемы в `frontend/src/shared/themes/`:
- `default.css` — светлая (60+ токенов)
- `dark.css` — тёмная (17 переопределений)
- `minimal.css` — минималистичная (острые углы, без теней)

Партнёр подключает: `<link rel="stylesheet" href="themes/partner.css">`
и переопределяет `--cat-*` переменные. Компоненты ссылаются на переменные.

## Виджет для WordPress

`frontend/src/apps/widget/` — standalone SPA:
- `router.js` — клиентский hash-роутер (читает/пишет location.hash)
- `App.vue` — слушает hashchange, рендерит каталог по URL
- `CatalogIndex.vue` — сетка каталогов (gearbox, filter_regulator, pneumatic_actuators, ...)
- `main.js` — монтируется в `#widget-root`

Подключение: `<script src="...widget.js" data-key="gearbox"></script>`
URL-схема: `#/gearbox/catalog`, `#/gearbox/detail/123`, `#/gearbox/brand/5`

## Цены

- Модель: `CustomerSettings.default_currency` (FK Currency)
- Конвертер: `price/services/currency_converter.py`
  - convert_price(price, from_cur_code, to_cur_code, date)
  - get_bulk_prices(sku_codes, currency_code)
  - get_display_price(sku_obj, currency_code)
- Вьюха: `gearbox/views/catalog.py` — вшивает цены в ответ:
  - list: `item.price = {...}` для каждого товара
  - detail: `data.price = {...}`
- Отладка: `get_current_customer_user()` ищет клиента «Архимед»
- Курсы валют: `price.models.ExchangeRate` (from_currency, to_currency, rate, date)

## Docker

`docker-compose.yml` — WordPress + MySQL:
- WordPress: порт 8080
- MySQL: порт 3306
- Плагин: `wp-catalog-plugin/catalog.php` (шорткод [catalog])

## Типовой шаблон — как добавить новый каталог

1. **Модель**: наследовать `CatalogDictMixin`, реализовать:
   - `_get_template_vars()` → {key: "строка"}
   - `to_dict()` → `{template_vars: tv, sections: [...]}`
   - `to_values_dict()` → лёгкая версия для списков
2. **Фильтры**: `services/filters.py` с FilterDefinition
3. **Вьюхи**: `catalog.py` (CatalogView, DetailView, FilterOptionsView) + `meta.py`
4. **URL**: `urls.py` + запись в `djangoProject1/urls.py`
5. **Фронтенд**: `frontend/src/apps/{name}-catalog/` — api.js + App.vue + 4 компонента-обёртки
6. **Vite**: entry в `vite.config.js`
7. **Виджет**: запись в `CatalogIndex.vue` CATALOG_INFO
