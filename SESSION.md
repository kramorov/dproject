# Состояние проекта на 2026-05-29

## Сегодня (2026-05-29)

### 🏗️ ImageGallerySet — наборы изображений
- **Модели**: `ImageGallerySet` + `ImageGallerySetItem` (through) в `media_library/models.py`
  - `name, code, keywords` — поиск и идентификация
  - M2M `images` через through с полями `sorting_order` и `is_default`
  - `get_images()`, `get_default_image()` — методы доступа
  - Админка с TabularInline (autocomplete на image)
- **ImageGalleryMixin** переписан:
  - Старый голый M2M `images` → FK `image_gallery` на `ImageGallerySet`
  - `@cached_property _gallery` — своя галерея → фолбэк на `model_line.image_gallery`
  - `_get_first_image()`, `_get_images_section()`, `_build_image_dict()` — единые для всех каталогов
- **Удалены дублирующие методы** из gearbox, filter_regulator, pa_controls (4× `_get_first_image`, 4× `_get_images_section`)
- **Удалён `_ml_img_cache`** из pa_controls views — заменён на `prefetch_related('image_gallery__items__image')`
- **Фронтенд каталогов**:
  - Таб «Изображения» → «Галерея», `FkSelect` вместо `ChipList`+`BasePicker`+`MediaUploadModal`
  - `CatalogBrand` → `CatalogModelLine` (переименован, `idProp` по умолчанию `model_line_id`)
  - `useCatalog`: добавлен `filterScope` → `api.getFilters({scope})` для `?scope=model_line`
  - `BaseFilterOptionsView`: `scope_exclude` — при `?scope=model_line` исключает `model_line_id`/`brand_id`
  - gearbox: `scope_exclude = {'model_line': ['brand_id']}` (фильтр по бренду уже зафиксирован)
  - Обновлены все 4 App.vue (gearbox, filter_regulator, limit_switch, widget)
  - `PageTitle` — новый shared-компонент заголовка (title + subtitle + context-чип)
  - `CatalogActions` — кнопки «Инженерный подбор» / «Быстрый подбор» над сеткой серий
  - `Breadcrumbs` — все непоследние крошки кликабельны (`router.push` или `emit('navigate')`)
  - Крошки трёхуровневые: Каталог / БКВ / Серия (или Инженерный/Быстрый подбор)
  - Стили PageTitle вынесены в CSS-переменные (`--cat-page-title-*`)
  - Удалены `extraButtons` из CatalogSection — заменены на CatalogActions
  - Удалён старый `CatalogBrand.vue`

### 🔗 CertData.media_item: FK → O2O
- `media_item = ForeignKey(..., related_name='certificates')` → `OneToOneField(..., related_name='cert_data')`
- Семантика: один сертификат = один PDF, эксклюзивная связь
- `CertData.delete()` — каскадно удаляет `media_item` → `MediaLibraryItem.delete()` → облачные файлы

### 🗑️ Каскадное удаление с очисткой облака
- **`MediaLibraryItem.delete()`** — удаляет `media_file` и `preview_file` из Cloud.ru через `file_service.delete_file()`
- **`media_library/views/admin_detail.py`** DELETE: raw SQL → `item.delete()`
  - O2O `cert_doc_certdata.media_item_id` обнуляется через `on_delete=SET_NULL`
  - Файлы удаляются в модели, не во вьюхе
- **Убран мёртвый `replace_file_view`** из админки (дублировал `replace_file_ajax`)

### 🧹 Чистка
- **Raw SQL → ORM**: `lsb_model_line_item.py` и `limit_switch.py` — `_get_certs_section()`:
  - `cursor.execute(SELECT ... through)` → `self.model_line.cert_docs.filter(is_active=True).values_list('id', flat=True)`
  - Добавлен `select_related('media_item')` для устранения N+1
- **Сигналы**: удалены мёртвые `create_preview_on_save`, `update_media_item_metadata`, закомментированные
  - Оставлен только `prevent_predefined_category_deletion`
  - Убран `print("Сигналы...")` из `apps.py`
- **Админки**: `images` в `filter_horizontal`/`fieldsets` заменён на `image_gallery` во всех admin-классах
- **`exd` в raw_id_fields** (LimitSwitchBoxAdmin) — убран, M2M нельзя в raw_id_fields
- **Баг codewhale-tui v0.8.47** — паника в verify.rs:422 на кириллице

### ⚡ Оптимизация каталогов (2026-05-28)
- **Cloud.ru**: `url()` больше не делает `head_object` — только `_normalize()` (было 120+ сетевых запросов на 24 карточки, стало 0)
- **`to_values_dict()`**: больше не вызывает `_get_template_vars()` — лёгкий `tv = {code, name}`
- **`useCatalog.js`**: `unref(fixedParams)` — чинит фильтр по серии/бренду (был сломан для всех каталогов)
- **`CatalogBrand.vue`**: `onFilterChange` при старте — фильтр в сайдбаре подсвечивается
- **`ProductCard.vue`**: `ProgressiveImage` — сначала превью, потом full фоном
- **`ProductGallery.vue`**: превью → фоновая загрузка full + preload всей галереи
- **`SELECT_RELATED`**: дополнен `ip`, `body_material`, `body_material_specified`, `model_line__brand`
- **`prefetch_related`**: добавлен для `images`, `tech_docs`, `additional_sensor`, `model_line__images/tech_docs`
- **`/sections/`**: новый эндпоинт — 1 запрос с `annotate(Count)` вместо 1000 записей
- **Gearbox + FilterRegulator**: унифицированы — `to_values_dict()` лёгкий, `_get_first_image()` из mixin
- **`CATALOG_PATTERN.md`**: инструкция для новых каталогов + чек-лист производительности

## Ключевые архитектурные решения

1. **ImageGalleryMixin** — FK `image_gallery` → `ImageGallerySet`, кэширование через `@cached_property _gallery`
2. **ImageGallerySet** в `media_library` — контейнер с through-моделью для порядка и default
3. **CatalogDictMixin** — `to_dict()` → sections (gallery/specs/docs/certs/description) + template_vars
4. **CertData.media_item** — O2O вместо FK, каскадное удаление с очисткой облака
5. **MediaLibraryItem.delete()** — удаление файлов из Cloud.ru при удалении записи
6. Цены вшиты в ответ API, конвертация через ExchangeRate, валюта из CustomerSettings
7. CSS Custom Properties — default/dark/minimal темы, компоненты ссылаются на переменные
8. Виджет widget/ — клиентский hash-роутер (#/gearbox/detail/123), F5 работает
9. Shared-компоненты — переиспользуются для всех типов каталогов
10. Фильтры списка: scope=used (только существующие), формы создания: scope=all (полные справочники)

## ⚠️ Облачное хранилище Cloud.ru (2026-05-27)

Медиабиблиотека использует Cloud.ru (S3-совместимое) через `storage_manager`.
- `ManagedFileField` — кастомное поле с авто-категоризацией
- `file_service` — глобальный синглтон для операций с файлами
- `MediaLibraryItem.delete()` вызывает `file_service.delete_file()` для media_file и preview_file

## Структура каталогов

### Редукторы (gearbox)
- **Бэкенд**: GearBox(CatalogDictMixin, ImageGalleryMixin, TemplateMixin, SKUMixin, ...)
- **Фронтенд**: frontend/src/apps/gearbox-catalog/ (5 страниц + gearbox-admin/)
- **API**: /api/gearbox/catalog/, /<id>/, /filters/, /meta/
- **Виджет**: CatalogIndex «Редукторы», маршруты #/gearbox/*

### Фильтр-регуляторы (filter_regulator)
- **Бэкенд**: FilterRegulator(CatalogDictMixin, ImageGalleryMixin, TemplateMixin, SKUMixin, ...)
- **Фронтенд**: frontend/src/apps/filter-regulator-catalog/ (5 страниц + EngineerCatalog)
- **API**: /api/filter-regulator/catalog/, /<id>/, /filters/, /meta/, /engineer/

### Блоки концевых выключателей (pa_controls)
- **Бэкенд**: LimitSwitchBox / LsbModelLineItem (CatalogDictMixin, ImageGalleryMixin, ...)
- **Фронтенд**: frontend/src/apps/limit-switch-catalog/ (4 страницы)
- **Админка**: limit-switch-admin/ — CRUD с табами и shared-компонентами
- **API**: /api/pa-controls/catalog/, /<id>/, /filters/, /meta/

## Файловая карта

| Компонент | Путь |
|---|---|
| ImageGalleryMixin | core/models/image_gallery_mixin.py |
| ImageGallerySet | media_library/models.py |
| CatalogDictMixin | core/models/mixins.py |
| BaseFilterOptionsView | core/views.py |
| FilterOptionsView (gearbox) | gearbox/views/catalog.py |
| FilterOptionsView (filter_regulator) | filter_regulator/views/catalog.py |
| FilterOptionsView (limit_switch) | pa_controls/views/catalog.py |
| Shared компоненты | frontend/src/shared/components/ |
| Generic-компоненты каталогов | frontend/src/shared/components/catalog/ |
| CSS темы | frontend/src/shared/themes/ |
| Виджет | frontend/src/apps/widget/ |
| Vite config | frontend/vite.config.js |
| Цены / валюта | price/services/currency_converter.py |
| Медиатека (админ) | media_library/admin.py |
| Медиатека (модель) | media_library/models.py |

## ⚠️ Баг codewhale-tui v0.8.47 (2026-05-29)

В codewhale-tui v0.8.47 обнаружен баг — паника в `verify.rs:422`:
```
start byte index N is not a char boundary; it is inside 'О' (bytes N..N+2)
```
Возникает при использовании `edit_file` на файлах с кириллицей.

### До исправления:
- **НЕ использовать `edit_file`** на файлах с русским текстом
- **Использовать `write_file`** — перезапись файла целиком
- **Использовать `apply_patch`** — unified diff, безопасный путь
- **`read_file` безопасен** — read-only не вызывает верификатор

### Файлы повышенного риска:
- `media_library/models.py` — много кириллицы в docstrings
- `core/views.py`
- `SESSION.md`
- Все файлы с русскими комментариями/docstrings