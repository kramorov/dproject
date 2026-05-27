# Состояние проекта на 2026-05-25

## ⚠️ НАПОМИНАНИЕ: установить PyMuPDF на домашней машине

При смене машины выполни:
```
pip install PyMuPDF
```
Без него PDF-превью в медиатеке не создаются (молча пропускаются).
Добавлен в requirements.txt (2026-05-26).

## Ключевые архитектурные решения

1. CatalogDictMixin в core/models/mixins.py — единый to_dict() для всех каталогов
2. to_dict() → sections (gallery/specs/docs/certs/description) + template_vars
3. _get_template_vars() — единый источник значений. _get_data_dict() — для TemplateMixin
4. Цены вшиты в ответ API, конвертация через ExchangeRate, валюта из CustomerSettings
5. CSS Custom Properties — default/dark/minimal темы, компоненты ссылаются на переменные
6. Виджет widget/ — клиентский hash-роутер (#/gearbox/detail/123), F5 работает
7. Shared-компоненты — переиспользуются для всех типов каталогов
8. Фильтры списка: scope=used (только существующие), формы создания: scope=all (полные справочники)

## ⚠️ Облачное хранилище cloud.ru (2026-05-26)

Медиабиблиотека перенесена в Cloud.ru Evolution Object Storage.
- Бакет: media-storage, эндпоинт: https://s3.cloud.ru, регион: ru-central-1
- Ключи: в settings.py (CLOUDRU_ADMIN_*, CLOUDRU_READER_*)
- Режим раздачи: MEDIA_SERVE_MODE = 'redirect' — клиент качает напрямую из S3 через presigned URL.
  'proxy' — Django стримит через себя (медленно). Переключать в settings.py.
- Бэкенд: storage_manager/storage_backends/cloudru.py (CloudRuStorage)
- Миграция: python manage.py migrate_media_to_cloudru
- Бэкап: media_backup_20260526/ + db_backup_20260526.sqlite3
- Для домашней машины: установить boto3 и PyMuPDF, вписать ключи в settings.py

## Правила работы
- Не писать в существующие файлы без разрешения
- Шаг за шагом
- При смене машины читать SESSION.md (в git)

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