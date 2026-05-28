# Состояние проекта на 2026-05-28

## Сегодня (2026-05-28)

### ⚡ Оптимизация каталогов
- **Cloud.ru**: `url()` больше не делает `head_object` — только `_normalize()` (было 120+ сетевых запросов на 24 карточки, стало 0)
- **`to_values_dict()`**: больше не вызывает `_get_template_vars()` — лёгкий `tv = {code, name}`
- **`_get_first_image()`**: 1 фото вместо 3-5 (вынесен в `CatalogDictMixin`, переиспользуется всеми каталогами)
- **`_ml_img_cache`**: фолбэк-изображения серий кэшируются вьюхой — 1 раз на серию вместо N раз на товар
- **`useCatalog.js`**: `unref(fixedParams)` — чинит фильтр по серии/бренду (был сломан для всех каталогов)
- **`CatalogBrand.vue`**: `onFilterChange` при старте — фильтр в сайдбаре подсвечивается
- **`ProductCard.vue`**: `ProgressiveImage` — сначала превью, потом full фоном
- **`ProductGallery.vue`**: превью → фоновая загрузка full + preload всей галереи
- **`SELECT_RELATED`**: дополнен `ip`, `body_material`, `body_material_specified`, `model_line__brand`
- **`prefetch_related`**: добавлен для `images`, `tech_docs`, `additional_sensor`, `model_line__images/tech_docs`
- **`/sections/`**: новый эндпоинт — 1 запрос с `annotate(Count)` вместо 1000 записей
- **Gearbox + FilterRegulator**: унифицированы — `to_values_dict()` лёгкий, `_get_first_image()` из mixin
- **`CATALOG_PATTERN.md`**: инструкция для новых каталогов + чек-лист производительности

### Починка LimitSwitchBox API
- **Корень проблемы**: `LimitSwitchBox` был закомментирован в `pa_controls/models/__init__.py` → Django не регистрировал модель → миграции `SeparateDatabaseAndState` ломали through-таблицы (`exd`, `images`, `tech_docs`)
- **Решение**: раскомментирован импорт, исправлен циклический импорт (прямые импорты из подмодулей вместо `pa_controls.models`)
- **M2M-поля**: `related_name='+'` на `exd`, `images`, `tech_docs` — как у gearbox/filter_regulator
- Заменены FK-стиль методы на M2M: `exd_display` итерация, `_copy_custom_relations` через `.set()`

### Shared-компоненты фронтенда
- `M2MDualList.vue` — filter_horizontal стиль (две панели + поиск + стрелки)
- `JsonFieldsEditor.vue` — редактор extra_params (таблица + raw JSON ▲▼)
- `MediaUploadModal.vue` — загрузка в медиатеку (IMAGE/TECH_DOC)

### Формы LimitSwitchBox (табы)
- **ModelLineForm**: Основное | Изображения | Техдокументация | Сертификаты | Дополнительно
- **LimitSwitchForm**: Основное | Изображения | Техдокументация | Дополнительно
- Кнопки «+ Новый» на вкладках медиа для загрузки в медиатеку
- Кнопка «+ Новый» на сертификатах → CertEdit с пресетом equipment_type и brand

### CertEdit
- `isNew`: `!props.item || !props.item.id` — поддержка пресетов без id
- Копирование `name` из формы в новый сертификат
 
## Ключевые архитектурные решения
 
1. CatalogDictMixin в core/models/mixins.py — единый to_dict() для всех каталогов
2. to_dict() → sections (gallery/specs/docs/certs/description) + template_vars
3. _get_template_vars() — единый источник значений. _get_data_dict() — для TemplateMixin
4. Цены вшиты в ответ API, конвертация через ExchangeRate, валюта из CustomerSettings
5. CSS Custom Properties — default/dark/minimal темы, компоненты ссылаются на переменные
6. Виджет widget/ — клиентский hash-роутер (#/gearbox/detail/123), F5 работает
7. Shared-компоненты — переиспользуются для всех типов каталогов
8. Фильтры списка: scope=used (только существующие), формы создания: scope=all (полные справочники)

## ⚠️ Облачное хранилище Cloud.ru (2026-05-27)

Медиабиблиотека перенесена в Cloud.ru Evolution Object Storage.
- Бакет: media-storage, эндпоинт: https://s3.cloud.ru, регион: ru-central-1
- Ключи: в settings.py (CLOUDRU_ADMIN_*, CLOUDRU_READER_*)
- Бэкенд: storage_manager/storage_backends/cloudru.py (CloudRuStorage)
- Нормализация путей: python manage.py normalize_media_paths (\\ → /)
- Бэкап: media_backup_20260526/ + db_backup_20260526.sqlite3
 
### Режимы раздачи (MEDIA_SERVE_MODE)
| Режим | Статус | Описание |
|-------|--------|----------|
| `redirect` | ✅ РАБОТАЕТ | Django → 302 на presigned URL (boto3, tenant_id в X-Amz-Credential) |
| `direct` | ❌ НЕ РАБОТАЕТ | Прямые ссылки на Cloud.ru. Проблема: Cloud.ru требует X-Project-Id, браузер не может передать заголовок через `<img src>`. Публичная политика бакета не помогает — аутентификация всё равно требуется. |
| `proxy` | ⚠️ Для отладки | Django стримит файлы через себя. Медленно, нагружает сервер. |

### История попыток прямого доступа (direct mode)
1. `MEDIA_PUBLIC_BASE_URL = 'https://s3.cloud.ru/media-storage'` — ошибка `missing tenant id`
2. CORS-правила на бакете — не помогли (проблема в аутентификации, не в CORS)
3. `?tenant_id=...` в URL — ошибка `SignatureDoesNotMatch` (boto3 не включает tenant_id в подпись)
4. `X-Project-Id` через заголовок — невозможно для `<img src="...">` (браузер не шлёт кастомные заголовки)
5. `https://media-storage.hb.bizmrg.com` — `NoSuchBucket` (неверный формат endpoint)
6. **Решение**: `MEDIA_SERVE_MODE = 'redirect'` — presigned URL через boto3 с tenant_id в `X-Amz-Credential`

### Проблема обратных слешей (Windows)
- `os.path.join` на Windows → `\` вместо `/`
- Старые файлы в S3: `media_library\medialibraryitem\...`
- Новые файлы: `media_library/medialibraryitem/...`
- **Решение**: `CloudRuStorage._normalize()` + `_resolve_name()` — ищет оба варианта
- **Ускорение**: `python manage.py normalize_media_paths` — обновляет пути в БД

## Админ-панель фронтенда (2026-05-27)

Добавлены страницы в «Администрирование» (только для admin):
- `/admin/cert-docs` — сертификаты (CertDocsPage)
- `/admin/media` — медиабиблиотека (было)
- `/admin/price` — цены (PriceCatalogPage)
- `/admin/sku` — номенклатура (SkuAdminPage)
- `/admin/widgets` — виджеты (было)

Меню: `TopMenu.vue` → выпадающий список «⚙️ Администрирование».
Роуты: `router/index.js` → meta.role = 'admin'.
Изображения: все через Django API → storage backend. Хардкода S3 URL нет.

## Правила работы
- Не писать в существующие файлы без разрешения
- Шаг за шагом
- При смене машины читать SESSION.md (в git)

## Рефакторинг (2026-05-27)

### Унификация каталогов
- **BaseFilterOptionsView** — общий View для /filters/ (core/views.py)
- **BaseQuickSelectView** — общий View для быстрого подбора (core/views.py), заменил EngineerCatalog
- **QuickSelect.vue** — универсальный чипсовый подбор (shared/components/catalog/)
- **Generic-компоненты**: CatalogSection/List/Brand/Detail (shared/components/catalog/)
- **Composables**: useCatalog.js, useCatalogRouter.js
- **API-слой**: все api.js → @/shared/api + shared/endpoints.js
- **Удалено**: 13 старых компонентов + EngineerCatalog.vue, ~2400 строк копипасты

### Медиатека
- **Пагинация**: MediaGrid (limit/offset, селект 20/50)
- **MediaLibraryItem.get_serve_url()** — единый метод для URL файлов
- **CatalogDictMixin._get_image_url()** / **_get_doc_url()** → делегируют get_serve_url()
- **MediaPreviewView** — try/except защита от PyMuPDF-крашей

## Реализованные каталоги

### Редукторы (gearbox)
- **Бэкенд**: GearBox(CatalogDictMixin, SKUMixin, ...), to_dict() + to_values_dict(), фильтры, цены
- **Фронтенд**: frontend/src/apps/gearbox-catalog/ (4 страницы)
- **API**: /api/gearbox/catalog/, /<id>/, /filters/, /meta/

### Фильтр-регуляторы (filter_regulator)
- **Бэкенд**: FilterRegulator(CatalogDictMixin, TemplateMixin, ...)
  - FilterRegulatorModelLine(CertDocMixin, ...) — сертификаты через model_line
  - to_dict(): 5 секций (Images, Specs 4 группы, Docs, Certs, Description)
  - Фильтры: model_line_id, filtration_rating_min, body_material_id, flow_rate_min, thread_id, work_temp_min/max, brand_id
  - Инженерный каталог: /api/filter-regulator/engineer/
- **Фронтенд**: frontend/src/apps/filter-regulator-catalog/ (5 страниц + EngineerCatalog)
- **Инженерный каталог**: чипсы серий и фильтров, авто-дефолты, одна карточка через ProductDetail
- **API**: /api/filter-regulator/catalog/, /<id>/, /filters/, /meta/, /engineer/
- **Виджет**: CatalogIndex «Фильтр-регуляторы», маршруты #/filter_regulator/*
- **Меню**: TopMenu «⚙️ Настройки» → «🔧 Фильтр-регуляторы», «🔬 Инженерный каталог»

### Блоки концевых выключателей (pa_controls)
- **Бэкенд**: LimitSwitchBox(CatalogDictMixin, TemplateMixin, SKUMixin, ...)
  - _get_template_vars(): 25 строковых значений
  - to_dict(): 5 секций (Images, Specs 4 группы, Docs, Certs, Description)
  - to_values_dict(): облегчённая для списков
  - Секции specs: Основные (9 полей), Корпус (5), Датчики (4), Условия эксплуатации (1)
  - Фильтры: model_line_id, sensor_variety_id, points, ip_id, work_temp_min/max, body_material_id, model_line_brand_id, signal_type_id, exd_id
  - M2M images/tech_docs: переопределены (related_name='lsb_images'/'lsb_tech_docs'), чтение через raw SQL
  - Документация: сбор из товара + серии (model_line), без дубликатов
- **Фронтенд**: frontend/src/apps/limit-switch-catalog/ (4 страницы: LsbSection/LsbList/LsbDetail/LsbBrand)
  - Стилизация: CSS-переменные --cat-* (тема default.css)
  - Детали: через shared ProductDetail
- **API**: /api/pa-controls/catalog/, /<id>/, /filters/, /meta/
- **Виджет**: CatalogIndex «Блоки концевых выключателей»
- **Меню**: TopMenu «⚙️ Настройки» → «🔌 Блоки концевых выключателей»
- **Админка**: exd/images/tech_docs — патч get_form/save_related (raw SQL), raw_id_fields

## Фильтрация: scope=used / scope=all
- Медиатека: MediaFilterOptionsView — ?scope=used / ?scope=all
- Сертификаты: CertFilterOptionsView — ?scope=used / ?scope=all

## Исправления
- [x] Замена файла в медиатеке — мгновенное обновление DOM (без location.reload)
- [x] Копирование в медиатеке — логика в модели MediaLibraryItem.copy()
- [x] Сертификаты в filter-regulator — _get_certs_section()
- [x] Фильтр по серии (model_line_id) вместо brand_id в filter-regulator
- [x] Инженерный каталог фильтр-регуляторов
- [x] LimitSwitchBox — переписан на CatalogDictMixin

## Рефакторинг (2026-05-27)

Унификация фронтенда и бэкенда трёх каталогов (gearbox, filter_regulator, limit_switch).

### Бэкенд
- **BaseFilterOptionsView** — общий View для /filters/ (core/views.py). Три FilterOptionsView → подклассы по 5 строк. Формат: `{ param_name: { label, order, options } }`.
- **API-слой фронтенда**: все api.js используют `@/shared/api`. Пути вынесены в `shared/endpoints.js`.

### Фронтенд
- **Generic-компоненты** в `shared/components/catalog/`: CatalogSection/List/Brand/Detail. Параметризуются через `api` + `labels`. Заменили 12 старых компонентов (GearboxSection, FrBrand, LsbList…).
- **Composables**: `useCatalog.js` (fetchData, пагинация, фильтры), `useCatalogRouter.js` (навигация App.vue).
- **Виджет**: добавлен limit_switch (был только в CatalogIndex, без роутов). Все каталоги используют Generic-компоненты.
- **CSS**: все каталоги на CSS-переменных, filter-regulator переведён с hardcoded-цветов.

### Удалено
- **QuickSelect (Быстрый подбор)**: `BaseQuickSelectView` в core/views.py. Заменил EngineerCatalog. Чипсовые фильтры + одна карточка. Подклассы в gearbox/filter_regulator/pa_controls.
- **Spinner.vue**: общий компонент загрузки, заменил «Загрузка...» в 5 компонентах.
- **Breadcrumbs**: родительские уровни с `url: '#'` — кликабельны.

### Удалено
- 13 старых компонентов, ~2400 строк копипасты → ~400 строк конфигов + Generic-компоненты.
- `EngineerCatalog.vue` → `QuickSelect.vue`. `engineer.py` → `quickselect.py`.

## Важные пути

| Ресурс | Путь |
|--------|------|
| CatalogDictMixin | core/models/mixins.py |
| GearBox.to_dict() | gearbox/models/gearbox.py |
| FilterRegulator.to_dict() | filter_regulator/models/fr_model_line_item.py |
| LimitSwitchBox.to_dict() | pa_controls/models/limit_switch.py |
| FilterRegulator фильтры | filter_regulator/services/filters.py |
| QuickSelect (бэкенд, общий) | core/views.py → BaseQuickSelectView |
| QuickSelect (filter_regulator) | filter_regulator/views/quickselect.py |
| QuickSelect (gearbox) | gearbox/views/quickselect.py |
| QuickSelect (limit_switch) | pa_controls/views/quickselect.py |
| QuickSelect (фронтенд) | frontend/src/shared/components/catalog/QuickSelect.vue |
| Shared компоненты | frontend/src/shared/components/ |
| CSS темы | frontend/src/shared/themes/ |
| Виджет | frontend/src/apps/widget/ |
| WordPress плагин | wp-catalog-plugin/catalog.php |
| Vite config | frontend/vite.config.js |
| Главный urls.py | djangoProject1/urls.py |
| Цены / валюта | price/services/currency_converter.py |
| Медиатека (админ) | media_library/admin.py |
| Медиатека (модель) | media_library/models.py |
| Сертификаты (фильтры) | cert_doc/views/filters.py |
| BaseFilterOptionsView | core/views.py |
| FilterOptionsView (gearbox) | gearbox/views/catalog.py |
| FilterOptionsView (filter_regulator) | filter_regulator/views/catalog.py |
| FilterOptionsView (limit_switch) | pa_controls/views/catalog.py |
| Generic-компоненты каталогов | frontend/src/shared/components/catalog/ |
| API эндпоинты (фронтенд) | frontend/src/shared/endpoints.js |
| Composable useCatalog | frontend/src/shared/composables/useCatalog.js |
| Spinner (загрузка) | frontend/src/shared/components/Spinner.vue |

## Админка БКВ (2026-05-27)

Создано приложение `frontend/src/apps/limit-switch-admin/` — CRUD для LimitSwitchModelLine и LimitSwitchBox.

### Бэкенд
- `core/views.py` `_write` — поддержка M2M-полей через `_set_m2m()` (raw-SQL + Django ORM)
- `pa_controls/models/limit_switch.py` — `set_images_ids()`, `set_tech_docs_ids()` (raw SQL)
- `pa_controls/views/m2m_data.py` — batch-эндпоинт `/api/pa-controls/m2m-items/?model=...&ids=1,2,3`
- `pa_controls/models/lsb_model_line.py` — `get_images_data()`, `get_tech_docs_data()`, `get_cert_docs_data()`

### Переиспользуемые компоненты (shared/)
- `BasePicker.vue` — универсальный модальный подбор (fetchFn, filterDefs, columns)
- `ChipList.vue` — таблица code + name с чекбоксами и batch-удалением
- `FkSelect.vue` — выбор ForeignKey с поиском
- `M2MSelect.vue` — выбор ManyToMany с чипсами
- `AdminTable.vue` — таблица с поиском/пагинацией (limit-switch-admin/components/)
- `AdminForm.vue` — модалка CRUD с защитой от несохранённых изменений

### Табы в формах
- ModelLineForm: Основное / Изображения / Техдокументация / Сертификаты
- Подбор через BasePicker, данные загружаются через `/api/pa-controls/m2m-items/`
- M2M-watch с `immediate: true` (props.item установлен до монтирования)

## MediaLibraryItem: title → name (2026-05-27)

Поле `title` переименовано в `name`, добавлено поле `code`.

### Затронутые файлы
- `media_library/models.py` — `__str__`, `to_dict()`, `SEARCH_FIELDS`, `copy()`, `get_absolute_url()`
- `media_library/admin.py` — все `title` → `name` + `code`
- `media_library/views/admin_detail.py`, `admin_upload.py` — `title` → `name`
- `media_library/urls.py` — `app_name = 'media_library'`
- `cert_doc/models.py` — `media_item.title` → `.name` + `.code`, fix None-check
- `cert_doc/views/admin_media_upload.py` — `title` → `name`
- `core/models/image_gallery_mixin.py`, `tech_doc_mixin.py` — `.title` → `.name`
- `gearbox/models/gearbox.py`, `filter_regulator/...`, `pa_controls/...` — унификация: `{id, name, code, url}`
- Весь фронтенд: `item.title` → `item.name`, `file.title` → `file.name`
- `pages/gearbox_catalog.py`, `pages_finished/media_library_editor.py`

### Стандарт сериализации
Изображения: `{id, name, code, url, preview_url, is_default}`
Документы: `{id, name, code, url, file_name}`

## ⚠️ ЗАДАНИЕ: CATALOG_PATTERN.md

При каждом добавлении или изменении общих компонентов каталогов:
1. Прочитай `CATALOG_PATTERN.md`
2. Обнови его — добавь новые паттерны, исправь устаревшее
3. Убедись, что чек-лист производительности актуален