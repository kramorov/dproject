# Состояние проекта на 2026-06-03

## Сегодня (2026-06-03) — EngineerSelection, Exd-каскад, Requirement-модели

### 🏗️ EngineerSelection — выделенный компонент инженерного подбора

- **`EngineerSelection.vue`** — копия `CatalogList.vue`, независимый компонент:
  - `EngineerProductCard.vue` — горизонтальная карточка товара (изображение слева, спеки + цена справа)
  - `EngineerFilterBar.vue` — горизонтальная панель фильтров вместо сайдбара (селекты в строку)
  - CSS `.grid` заменён с `grid repeat(3,1fr)` на `flex column` (карточки в столбец)
  - Пропс `presetFilters` — предзаполнение фильтров (для потока требований)
- **`useCatalog.js`** — `mode: 'engineer'` → вызывает `api.getEngineer()` / `api.getEngineerFilters()`
- **Django API**: `/api/{catalog}/engineer/` + `/api/{catalog}/engineer/filters/`
  - `gearbox/catalog/views_engineer.py` + `views_engineer_filters.py`
  - `filter_regulator/catalog/views_engineer.py` + `views_engineer_filters.py`
  - `pa_controls/catalog/views_engineer.py` + `views_engineer_filters.py`
- **Config**: `'engineer'` FilterSet в `config.py` каждого каталога (пока копия `'list'`)
- **URLs**: `gearbox/urls.py`, `filter_regulator/urls.py`, `pa_controls/urls.py` — engineer endpoints
- **Фронтенд**: `endpoints.js` + `api.js` всех трёх каталогов — `getEngineer()`, `getEngineerFilters()`
- **App.vue**: все 4 App.vue (gearbox, filter-regulator, limit-switch, widget) — `CatalogList` → `EngineerSelection`

### 💥 Exd-фильтр — каскадный редизайн

- **`ExdFilter.vue`** — полный редизайн:
  - Селекты: `Ex d` (код метода), `db` (код типа) — без расшифровок
  - Группа: «Группа среды» (было «Группа опасности среды»)
  - Все селекты в одну строку, метод шире (100–160px), тип/группа/T-класс уже (70–110px)
  - Поле «Описание» всегда видно, `min-height: 42px`:
    - «Все» → «Не указан класс взрывозащиты»
    - «Общепром.» → «Взрывозащита — нет, Общепромышленное исполнение»
    - Выбран тип → `Ex db (описание типа), группа среды IIB (описание), T4 (описание), до 135°C`
  - Тип «перекрывает» метод в описании
  - Пропс `compact` — для горизонтального фильтр-бара
  - Пропс `single` — для формы требований (один ID вместо массива)
- **Текстовое поле парсинга**: ввод строки `Ex db IIC T4` → автозаполнение селектов
  - `POST /api/core/exd/parse/` — парсер строки → `{method_id, type_id, group_id, temp_id}`
  - Ошибки красным шрифтом 11px под полем
- **Фильтрация групп по категории типа**: `GAS` → только газовые группы, `DUST` → только пылевые
  - `category` добавлен в `get_structured_choices()` API
  - `ExplosionProtectionType.category` → `GAS`/`DUST`
- **Баг-фиксы**: `isDustGroup` — сравнение `String(id)` (v-model возвращает строки), все сравнения с `0` → `String(methodId) === '0'`
- **Стиль**: `.filter-group-border` в `default.css` — переиспользуемая рамка (`border: 1px solid var(--cat-border)`)
- **Парсер** (`core/models/exd_parser.py`): переписан на regex, upper-case, уровни (Ga-Gc, Da-Dc) и X/U вырезаются до разбора, поддерживает форматы `Ex d IIC T6 Gb`, `ExdbIICT6`

### 📋 Requirement-модели

- **`BaseRequirement`** (abstract) — общие поля: `request_item` (O2O), `ip_protection` (FK), `temp_min`, `temp_max`
- **`GearboxRequirement`**: + `body_material`, `torque`, `mounting_plate`
- **`FilterRegulatorRequirement`**: + `body_material`, `flow_rate`, `thread`, `filtration`
- **`LimitSwitchRequirement`**: + `body_material`, `sensor_variety`, `points`, `exd_protection`, `signal_type`
- `exd_protection` — только в LimitSwitchRequirement (не в базе)
- **`to_filter_params()`** — метод на каждом требовании, возвращает словарь query-параметров для EngineerSelection API
- **API**:
  - `GET /api/client_requests/requirements/schema/?type=gearbox` — поля + choices
  - `POST /api/client_requests/requirements/preview/` — dry-run → `filter_params`
  - `exd_id_override` — обработка sentinel'а `_none_`
- **`RequirementForm.vue`** — динамическая форма: загружает схему, рендерит поля, для `exd_protection` — каскадный `ExdFilter` в режиме `single`
- **Тестовая страница**: `/tools/requirements`

### 🔧 Прочее

- `db.sqlite3` — git stash/pull main office-work
- `BaseFilterOptionsView` — поддержка `default_scope` (для `views_engineer_filters.py`)

## Ранее (2026-06-02) — Скачивание сертификатов, Exd-фильтр, админка БКВ

### 📥 Имена файлов при скачивании сертификатов и техдокументации

- **Проблема**: при скачивании сертификатов имя файла было хешем из Cloud.ru или «Без названия.pdf». Сжатая версия дублировала суффикс.
- **Решение**:
  - `MediaDownloadView` — принимает `?filename=`, использует в `Content-Disposition`. Фолбэк: `item.name` + расширение.
  - `_get_certs_section()` во всех моделях — формирует `file_name` по шаблону `"{variety} {code} для {model_line}.pdf"` + санитазация (`\ / : * ? " < > |` → `_`).
  - API-ответ: `file_name`, `email_file_name`, `email_url` с `&filename=`.
  - `FileList.vue` — `:download="file.email_file_name"` для сжатой версии.
  - `select_related('cert_variety')`, `str(cert.cert_variety)`, `'id': media.id` для DocViewer.

### 💥 Каскадный Exd-фильтр на фронтенде

- **Проблема**: `fd_exd` с `CUSTOM` пропускался в `BaseFilterOptionsView`, не отображался. При пустом результате фильтра показывались все модели.
- **Решение**:
  - **API**: `GET /api/core/exd/structure/` → иерархия (методы→типы→группы→темп.классы) + `gas_groups`/`dust_groups` раздельно
  - **API**: `GET /api/core/exd/compatible/?method_id=&type_id=&group_id=&temp_id=` → совместимые ExdOption ID
  - **Vue**: `ExdFilter.vue` — каскадные селекты: метод → тип → группа (газ/пыль раздельно) → темп.класс (только для газа)
  - **Sentinel'ы**: `_none_` (общепромышленное → `exd__isnull=True`), `_empty_` (нет совместимых → `exd__in=[]`), иначе comma-separated ID
  - **«Общепромышленное»**: опция `methodId=0` в селекте методов → ищет модели без взрывозащиты
  - `FilterSidebar.vue` — рендерит `ExdFilter` для `filter_type === 'exd_compatible'`, передаёт sentinel'ы как строку
  - `filter_definition.py` — `EXD_COMPATIBLE`: comma-separated ID, список, одиночный ID, или sentinel'ы `_none_`/`_empty_`
  - `exd_models.py` — `get_compatible_ids_by_components`: не фильтрует по `TemperatureClass` для пылевых групп
  - `exd_models.py` — `get_compatible_ids`: `temperature_rating__lte` для пыли (меньше = безопаснее)
  - `BaseFilterOptionsView` — добавлен `filter_type` в ответ API, CUSTOM больше не пропускается

### 🔧 Админка LimitSwitchBox

- Action `regenerate_from_templates` — перегенерация `name`/`description` через `update_from_templates(save=True)`.
- `TemplateMixin`: `generate_title`/`title_template`/`_get_title_template_source` переопределены в `LimitSwitchBox`.

## 2026-06-01 — Бэкап Cloud.ru, анализ хранилища, автоочистка

## Сегодня (2026-06-01) — Бэкап Cloud.ru, анализ хранилища, автоочистка

### Инструменты бэкапа и восстановления (`storage_manager/management/commands/`)

- **`backup_cloudru`** — полный бэкап бакета Cloud.ru на локальный диск. Скачивает все объекты с сохранением S3-структуры путей, создаёт `manifest.json` с метаданными (ETag, размер, дата). Повторный запуск докачивает только недостающие файлы. Флаги: `--prefix`, `--output-dir`, `--dry-run`, `--manifest-only`.
- **`restore_cloudru`** — восстановление из локального бэкапа в Cloud.ru. Читает `manifest.json`, заливает файлы обратно, пропускает существующие того же размера. Флаги: `--overwrite`, `--dry-run`, `--prefix`.
- **`find_orphaned_files`** — поиск файлов в облаке без ссылок в БД. Сравнивает: MediaLibraryItem (media_file + preview_file), MediaVariant (file_path), ImageCropSession (original + results). Поддерживает `--manifest` (офлайн-режим). Флаги: `--delete`, `--save-manifest`, `--output`.
- **`analyze_storage`** — детальная сверка БД и облака: разбивка по категориям, preview_file, элементы без вариантов, топ-15, баланс. Учитывает оба варианта слешей.
- **`list_inactive_media`** — неактивные MediaLibraryItem с размерами.
- **`analyze_tech_doc`** — анализ TECH_DOC на дубликаты (по имени, размеру, семействам).
- Документация: `storage_manager/management/commands/README.md`
- `storage_manager.apps.StorageManagerConfig` добавлен в `INSTALLED_APPS`

### Результаты анализа (бэкап 2026-06-01: 935 объектов, 357.4 МБ)

| Категория | Оригиналы | Варианты | Preview | Всего |
|-----------|----------|---------|---------|-------|
| CERTIFICATE | 56.3 МБ | 9.7 МБ | 0.2 МБ | 66.2 МБ |
| TECH_DOC | 181.2 МБ | 33.0 МБ | 1.6 МБ | 215.8 МБ |
| USER_MANUAL | 22.9 МБ | 10.2 МБ | 0.1 МБ | 33.2 МБ |
| PRODUCT_GALLERY | 6.6 МБ | 1.6 МБ | 0.3 МБ | 8.6 МБ |
| DRAWING + PHOTO | 1.4 МБ | 0.1 МБ | 0.3 МБ | 1.8 МБ |
| **Итого** | **268.4** | **54.6** | **2.5** | **325.5** |

- Орфаны: 123 файла `imagecropsession/` (31.8 МБ) — удалены через `cleanup_crop_sessions`
- Орфанов по БД: 0 (все 935 объектов привязаны)
- TECH_DOC: 63 элемента, 50 из них — техно-листовки ЯМАЛ (156.3 МБ, не дубли)
- `preview_file`: 2.5 МБ, 116 записей с дублирующимися файлами (у всех есть MediaVariant)
- 20 элементов без MediaVariant (7 DRAWING + 13 PHOTO)

### Автоочистка ImageCropSession

- **`ImageCropSession.delete_files()`** — удаление файлов из Cloud.ru
- **`ImageCropSession.delete()`** — переопределён: сначала файлы, потом запись БД
- **`ImageCropView.post()`**: новый режим — сессия удаляется сразу (base64-ответ); старый режим — `original_file` удаляется, results остаются для presigned URL; при ошибке — тоже удаляется
- **`cleanup_crop_sessions`** — команда для зачистки брошенных сессий (`--hours`, `--all`, `--dry-run`)

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
- **Email PDF** — для PDF-категорий (CERTIFICATE, TECH_DOC, USER_MANUAL) генерируется сжатый комбинированный PDF (email_dpi, JPEG quality=60)
  - `generate_variants()` разделяет email от постраничных вариантов
  - Email сохраняется как один `MediaVariant` с `role='email', format='pdf', page_num=1`
  - `get_variants_for_api()` возвращает `email_pdf` отдельным ключом
- **Профили**: добавлен `USER_MANUAL` (как TECH_DOC), `PHOTO` (как PRODUCT_GALLERY)
- **preview_url** — card 400 → thumb 150 → icon 50 → любой
- **`_detect_mime_type`** — добавлен `.webp`
- **Фронтенд медиабиблиотеки**:
  - `MediaEdit` — двухколоночный макет, превью `<iframe>` для PDF, `<img>` для изображений
  - `MediaVariantsPreview` — показ сгенерированных вариантов
  - `ImageCropper` — `initialUrl` prop + авто-загрузка существующего изображения
  - `MediaGrid` — PDF показывают миниатюру (icon 50px) или иконку 📄
  - `MediaPreviewView` — `?proxy=1` для CORS
- **Каталоги (gearbox, filter-regulator, pa_controls)**:
  - `_get_file_info` / `_get_certs_section` — относительные URL, `preview_url`, `email_url`
  - `FileList.vue` — превью, 👁️ Открыть (DocViewer), 📥 Скачать, 📧 Сжат
  - `DocViewer.vue` — попап с постраничным просмотром (◀ ▶, клавиатура)
  - `MediaDownloadView` — поддержка `?variant=email` (прямая отдача PDF)
  - Конфиги: `prefetch_related('...__image__variants')` во всех трёх
  - `FilterSidebar` — `color: var(--cat-text)` для select
  - `CatalogList`/`CatalogModelLine` — `defineEmits(['navigate'])`
  - `gearbox-catalog/App.vue` — `id-prop="model_line_id"` (был `brand_id`)
- **Миграция**: `replace_variants_jsonfield_with_through_model` (сделана)

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