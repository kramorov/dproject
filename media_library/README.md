# Медиабиблиотека (media_library)

Хранение и раздача медиафайлов (изображения, PDF, документы) через Cloud.ru Evolution Object Storage.

## Как работает раздача файлов

### Текущее решение: MEDIA_SERVE_MODE = 'redirect'

```
Браузер → <img src="/api/media/{id}/view/">
  → Vite proxy → Django MediaPreviewView
    → boto3 generate_presigned_url (SigV4, tenant_id в X-Amz-Credential)
      → 302 Redirect на presigned URL Cloud.ru
        → Браузер качает напрямую с Cloud.ru
```

**Плюсы**: Django не нагружается (только 302), браузер качает быстро.
**Минусы**: presigned URL живёт 1 час, нужен boto3 с ключами.

### Режимы (MEDIA_SERVE_MODE)

| Режим | Статус | Описание |
|-------|--------|----------|
| `redirect` | ✅ работает | 302 на presigned URL через boto3 |
| `direct` | ❌ не работает | Прямые ссылки на Cloud.ru |
| `proxy` | ⚠️ отладка | Django стримит файлы через себя |

## Проблема прямого доступа (direct mode) и история попыток

Cloud.ru Evolution Object Storage **не поддерживает анонимный доступ** к объектам,
даже при публичной политике бакета. Каждый запрос требует tenant ID.

### Попытка 1: прямые ссылки
```
MEDIA_PUBLIC_BASE_URL = 'https://s3.cloud.ru/media-storage'
```
**Ошибка**: `AuthorizationQueryParametersError — missing tenant id`

### Попытка 2: CORS-правила
CORS не имеет отношения — проблема в аутентификации, не в кросс-доменных запросах.

### Попытка 3: tenant_id в query string
```
https://s3.cloud.ru/media-storage/.../file.png?tenant_id=...
```
**Ошибка**: `SignatureDoesNotMatch` — boto3 не включает tenant_id в подпись,
добавление параметра извне ломает подпись.

### Попытка 4: заголовок X-Project-Id
Cloud.ru требует `X-Project-Id: <tenant_id>` в HTTP-заголовке.
**Проблема**: браузер не может передать кастомный заголовок через `<img src="...">`.
Это фундаментальное ограничение HTML.

### Попытка 5: альтернативные endpoint'ы
- `https://media-storage.hb.bizmrg.com` — `NoSuchBucket`
- `https://media-storage.s3.cloud.ru` — DNS не резолвится
- `https://hb.bizmrg.com/media-storage` — `NoSuchBucket`

### Вывод
Cloud.ru Evolution требует аутентификацию для **всех** запросов к S3 API.
Прямой доступ через `<img src="...">` невозможен без прокси.

## Текущая архитектура

### CloudRuStorage (storage_manager/storage_backends/cloudru.py)
- Два boto3-клиента: админ (upload/delete) и читатель (get_object/presigned URL)
- Аутентификация: `tenant_id:key_id` в качестве Access Key (документация Cloud.ru)
- `_normalize(name)` — замена `\` → `/` (Windows → S3)
- `_resolve_name(name)` — поиск файла с прямыми и обратными слешами (старые файлы)
- `url(name)` — presigned URL через boto3 (1 час)

### MediaLibraryItem (media_library/models.py)
- `public_url` — `MEDIA_PUBLIC_BASE_URL + '/' + media_file.name` (для справки)
- `get_serve_url(mode=None)` — единый метод: direct → public_url, иначе → /api/media/{id}/view/

### CatalogDictMixin (core/models/mixins.py)
- `_get_image_url(img)` → `img.get_serve_url()`
- `_get_doc_url(doc)` → `doc.get_serve_url()`
- Все каталоги (gearbox, filter_regulator, pa_controls) используют эти методы

### MediaPreviewView (media_library/views/preview.py)
- Проверка доступа: is_active, is_public
- `redirect` → 302 на presigned URL
- `proxy` → стриминг через Django с try/except защитой

## Проблема обратных слешей (Windows)

`os.path.join` на Windows использует `\`, S3 требует `/`.

- **Старые файлы**: загружены с `\` в пути
- **Новые файлы**: `_normalize()` исправляет при сохранении
- **Поиск**: `_resolve_name()` проверяет оба варианта (замедляет)

### Исправление
```bash
python manage.py normalize_media_paths   # обновить пути в БД
```

## Настройки (settings.py)

```python
MEDIA_SERVE_MODE = 'redirect'
MEDIA_API_BASE = 'http://localhost:8000'
MEDIA_PUBLIC_BASE_URL = 'https://s3.cloud.ru/media-storage'

CLOUDRU_BUCKET_NAME = 'media-storage'
CLOUDRU_ENDPOINT_URL = 'https://s3.cloud.ru'
CLOUDRU_REGION = 'ru-central-1'
```

## Требования

```
boto3          # S3-клиент для Cloud.ru
PyMuPDF        # PDF-превью (pip install PyMuPDF)
```

## Модель MediaLibraryItem (2026-05-27)

Поля: `id`, `name`, `code`, `description`, `media_file`, `preview_file`, `mime_type`,
`category` (FK), `equipment_type` (FK), `brand` (FK),
`keywords`, `is_active`, `is_public`, `is_default`, `sorting_order`.

- `name` — основное название (ранее `title`, переименовано)
- `code` — строковый код элемента
- `to_dict()` — `id, name, code, description, category, brand, ...`
- `get_absolute_url()` — fallback: `media_library:media_view` → `/api/media/{pk}/view/`
- `SEARCH_FIELDS = ['name', 'code', 'description', 'keywords']`

### Сериализация в каталогах

Изображения: `{id, name, code, url, preview_url, is_default}`
Документы: `{id, name, code, url, file_name}`
Унифицировано: gearbox, filter_regulator, pa_controls.

## Профили отображения (2026-05-30)

`MediaCategory.PRESENTATION_PROFILES` — хардкод-словарь, определяющий какие варианты
генерировать для каждой категории при загрузке файла.

| Категория | Роли (ширины) | multi_page | dpi |
|-----------|---------------|------------|-----|
| PRODUCT_GALLERY | icon(50), thumb(80,150), card(400,800) | нет | 72 |
| CERTIFICATE | icon(50), page(600), email→PDF(100dpi) | да | 150 |
| TECH_DOC | icon(50), page(800), email→PDF(100dpi) | да | 150 |
| BANNER | full(1200,1920) | нет | 72 |
| SCHEMA/DRAWING/DIAGRAM | icon + card/full | нет | 150 |

Профиль читается через `item.category.profile` или `MediaCategory.get_profile(code)`.

## Генерация вариантов

`media_library/services.py` — оркестратор:
- `generate_variants(item)` — читает `item.category.profile`, вызывает `image_processor`,
  сохраняет файлы в Cloud.ru, создаёт строки `MediaVariant` в БД
- `delete_variants(item)` — удаляет варианты из облака и БД
- `get_variants_for_api(item)` — строит словарь {role: {width: url}} из через through-модели

Генерация запускается автоматически при `MediaLibraryItem.save()` для изображений и PDF.

## Модель MediaVariant (2026-06-01) — through-модель

Заменила `MediaLibraryItem.variants` (JSONField). Поля:
- `media_item` (FK → MediaLibraryItem, related_name='variants', CASCADE)
- `role` (icon/thumb/card/page/full/email), `width`, `height`, `format`
- `file_path`, `file_size`, `page_num` (nullable, для PDF), `created_at`
- `unique_together`: (media_item, role, width, page_num)

Email-вариант для PDF: один `MediaVariant` с `role='email', format='pdf', page_num=1` —
комбинированный сжатый PDF (email_dpi, JPEG quality=60).

`preview_url` property: card 400 → thumb 150 → icon 50 → preview_file (фолбэк) → оригинал.

Старые поля (deprecated):
- `preview_file` — заменён на `MediaVariant`; оставлен для обратной совместимости

## Бэкап и анализ хранилища

Полный набор команд для работы с Cloud.ru — в `storage_manager/management/commands/` (см. `README.md` там же).

```bash
python manage.py backup_cloudru              # бэкап всего бакета на диск
python manage.py find_orphaned_files          # поиск файлов без ссылок в БД
python manage.py analyze_storage              # сверка БД и облака по категориям
python manage.py cleanup_crop_sessions        # очистка брошенных crop-сессий
```

Типичный workflow: `backup_cloudru` → `find_orphaned_files --manifest ...` → при необходимости `--delete`.

Состояние на 2026-06-01: 935 объектов, 357.4 МБ. Орфанов нет, 31.8 МБ crop-сессий удалены.