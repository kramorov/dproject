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
