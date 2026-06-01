# Состояние проекта на 2026-06-01

## 🔧 В работе: MediaVariant — through-модель вместо JSONField

- **Удалён** `variants = models.JSONField` из `MediaLibraryItem`
- **Добавлена** `MediaVariant` — through-модель с полями: `media_item` (FK), `role`, `width`, `height`, `format`, `file_path`, `file_size`, `page_num`, `created_at`
- `unique_together`: `(media_item, role, width, page_num)`
- **`services.py`** переписан:
  - `_save_to_storage()` → возвращает `(path, size)`
  - `_compute_height()` — вычисление высоты по пропорции
  - `generate_variants()` → создаёт `MediaVariant` через `apps.get_model`
  - `delete_variants()` → удаляет файлы из Cloud.ru + строки БД
  - `get_variants_for_api()` → строит словарь из through-строк
- **`models.py`**:
  - `save()` → `self.variants.exists()` / `self.variants.all().delete()` + CASCADE
  - `delete()` → `self.variants.all()` для сбора путей
  - `get_variants_for_api()` — метод модели, делегирует в `services`
- ⚠️ **Нужно создать миграцию вручную**: `python manage.py makemigrations media_library --name replace_variants_jsonfield_with_through_model`
- **`preview_file` — deprecated**: поле оставлено в БД, но код переведён на `MediaVariant`
  - `preview_url` property → MediaVariant (thumb/card) → preview_file (фолбэк)
  - `MediaPreviewView` → отдаёт variant из MediaVariant
  - `admin_recreate_preview` → `delete_variants()` + `generate_variants()`
  - `admin_detail.py` PUT/PATCH → `delete_variants()` перед заменой файла
  - `to_dict()` → включает `variants` (get_variants_for_api)
  - `ImageGalleryMixin._build_image_dict()` → `img.preview_url`
  - Внешние ссылки (gearbox_catalog, pa_controls, valve_data) → `preview_url`
- ⚠️ **После проверки — удалить preview_file файлы из Cloud.ru, затем дропнуть поле из БД**

## ⏳ Задачи на потом

### Кэширование опций фильтров
- **Проблема**: `BaseFilterOptionsView.get()` вызывает `fd.get_options()` для каждого фильтра.
  На странице серии с 6 фильтрами — 6-10 отдельных запросов к БД при каждой загрузке сайдбара.
- **Решение**: кэшировать результат `get_options` в Django cache (memcached/redis) с инвалидацией
  по сигналам модели (post_save/post_delete на связанные модели). Ключ кэша: `catalog:filters:{catalog}:{scope}:{model_line_id}`.
- **Приоритет**: medium, до production-нагрузки.

### 🛡️ Защита от парсеров и скрапинга
- **Источник**: анализ защиты на vseinstrumenti.ru (ServicePipe) и market.yandex.ru
- **Уровень 1 — минимальный (сейчас нет ничего)**:
  - Rate limiting на `/api/` через `django-ratelimit` или nginx `limit_req`
  - Лимит: 60 запросов/мин с IP на `/api/catalog/`, 30/мин на `/api/media/`
  - Блокировка пустых/подозрительных User-Agent на уровне nginx
  - `X-Robots-Tag: noindex, nofollow` на API-эндпоинтах (не индексировать поисковиками)
- **Уровень 2 — средний**:
  - Проверка `Referer` на `/api/media/*/download/` — только с нашего домена
  - CSRF-токены уже есть (axios interceptors), но проверить на всех эндпоинтах
  - Throttling на Django REST Framework (встроенный `UserRateThrottle`/`AnonRateThrottle`)
  - Логирование подозрительной активности: >100 запросов с одного IP за минуту → alert
- **Уровень 3 — высокий (перед production)**:
  - SRI (Subresource Integrity) на критических JS-бандлах: `integrity="sha256-..."`
  - Cloudflare/аналог как reverse proxy с Bot Fight Mode
  - Защита от копирования изображений: `user-select: none` + `pointer-events: none` на оверлеях
  - Watermark на full-size изображениях (накладывать при отдаче, не хранить)
- **Приоритет**: уровень 1 — high (до публичного доступа), уровень 2 — medium, уровень 3 — low

### 🖼️ Оптимизация изображений: WebP + ресайз + кроп (план)
- **WebP-варианты** для каждого изображения: `webp_sm` (150w), `webp_md` (400w), `webp_lg` (800w), `webp_xl` (1600w)
- **center_crop** для sm/md (квадратные карточки), **thumbnail** для lg/xl (пропорции)
- **`remove_background`** флаг в модели — нейросеть `rembg` (ONNX/U2Net) для удаления фона
- **Конвертация при загрузке** (save) — новые файлы сразу получают WebP-варианты
- **Management command** `generate_webp_variants` — добить существующие (пакетами по 50)
- **Fallback**: `get_image_urls()` отдаёт WebP если есть, иначе оригинал
- **Frontend**: `<img srcset="...">` — браузер сам выбирает размер
- **Экономия**: карточка ~12 KB WebP вместо ~200 KB JPEG
- **Поля**: `webp_sm/md/lg/xl` (ManagedFileField), `remove_background` (BooleanField)

### ✂️ Image Cropper — интерактивная обрезка (готово)
- **Приложение** `image_processor/` — модели, API, сервисы, README
- **API**: `/api/image-processor/` → `upload/`, `preview/`, `crop/`
- **Pipeline**: загрузка → [rembg] → crop_and_pad → WebP sm/md/lg (lossy, с альфа-каналом)
- **Модель**: `ImageCropSession` — ManagedFileField (Cloud.ru), координаты, bgColor, флаг rembg
- **Фронтенд**: `ImageCropper.vue` — canvas, drag/зум, color picker, лог-панель
  - Рамка фиксирована, изображение двигается
  - Колёсико — зум
  - Чекбокс «Убрать фон» → rembg (U2Net, ~170 MB модель)
  - Превью на шахматном фоне
  - Лог с таймстемпами и диагностикой прозрачности
- **Тестовая страница**: `/tools/image-processor`
- **Результат**: WebP с прозрачностью (RGBA, lossy quality=80)
- **Известно**: RGBA на 30-50% больше RGB; U2Net лучше на однородном фоне

### 🔄 Миграция фронтенда на новую структуру вариантов
- **Контекст**: `MediaLibraryItem.variants` (JSONField) заменил старые `preview_file` + `media_file.url`
- **Что нужно обновить**:
  - `ProgressiveImage.vue` — `preview`/`full` пропсы → `variants[role][width]`
  - `ProductCard.vue` — `imagePreview`/`imageFull` → `get_variant('card', 400)`
  - `ProductGallery.vue` — миниатюры (`thumb/80`), главное фото (`card/800`)
  - `CatalogSection.vue` — баннер серии (`card/400`)
  - `_build_image_dict()` в `image_gallery_mixin.py` — отдавать `variants` вместо `preview_url`
  - API: эндпоинт `/api/media/{id}/` должен возвращать `variants` с URL (через `get_variants_for_api`)
  - `srcset` на всех `<img>` — чтобы браузер сам выбирал размер
- **Приоритет**: high (старая структура `preview_file` отключена, всё сломается)

### 📁 TECH_DOC — через-модель для техдокументации
- **Проблема**: техническая документация может быть PDF, PDF с 3D, изображение, .STP
- **Нужна through-модель** (как `ImageGallerySetItem` для изображений, `CertData` для сертификатов)
- **Поля**: `media_item` (FK), `doc_type` (PDF/IMAGE/STP/DWG), `sorting_order`
- **Профиль**: `TECH_DOC` в `PRESENTATION_PROFILES` уже есть (пустой — только скачивание)
- **Приоритет**: medium (пока нет техдокументации в базе)

---

## Сегодня (2026-05-30) — Профили отображения и PDF-обработка

### 🏗️ PRESENTATION_PROFILES в MediaCategory
- Хардкод-словарь профилей по коду категории
- Категории: PRODUCT_GALLERY, BANNER, CERTIFICATE, TECH_DOC, SCHEMA, DRAWING, DIAGRAM
- PHOTO переименован в PRODUCT_GALLERY, добавлен BANNER (1200/1920)
- CERTIFICATE и TECH_DOC: page(600/800), email→сборный PDF(100dpi)

### 📄 PDF-обработка в image_processor
- `render_pdf_page()` — рендер страницы через PyMuPDF
- `_process_pdf_with_profile()` — постраничный рендер + профильные варианты
- `process_with_profile()` — единый вход: детектит PDF по расширению
- Email PDF: все страницы → один файл, JPEG quality=60, deflate-сжатие, исходные размеры A4
- `/crop/` принимает `category_code`, crop-параметры опциональны для PDF
- `/upload/` детектит PDF и пропускает PIL.open()

### 🖼️ Доработки ImageCropper
- Селектор «Убрать фон» / «Наложить фон» вместо чекбокса (по умолчанию «Убрать»)
- Альфа-канал автоопределяется (бейдж), но режим не меняет
- При «Наложить фон» — альфа всегда заливается bgColor
- Пропс `categoryCode` — передаётся в `/crop/`
- Таймаут превью увеличен до 120с (rembg на больших фото)

### 🧪 Тестовая страница `/tools/image-processor`
- Выбор категории → показ профиля → обработка
- PDF-категории: загрузка PDF → автообработка → страницы + email PDF
- Фото-категории: интерактивная обрезка → профильные варианты
- Сравнение исходного/сжатого размера для PDF
- Blob URL для открытия PDF (Chrome блокирует data: URI)

### 📝 Документация обновлена
- `image_processor/README.md` — полностью переписан
- `media_library/README.md` — добавлены профили + variants
- `frontend/README.md` — ImageCropper + тестовая страница
- `CATALOG_PATTERN.md` — без изменений (актуален)
- Анализ защиты Яндекс.Маркета и ВсеИнструменты.ру в SESSION.md

---

## Ранее (2026-05-29) — CatalogConfig и Exact/Compatible split

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