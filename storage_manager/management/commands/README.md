# Storage Manager — Management Commands

Инструменты для работы с Cloud.ru Evolution Object Storage: бэкап, восстановление, анализ и очистка.

## Команды

| Команда | Назначение |
|---------|-----------|
| `backup_cloudru` | Скачать все объекты из Cloud.ru на локальный диск |
| `restore_cloudru` | Восстановить файлы из локального бэкапа в Cloud.ru |
| `find_orphaned_files` | Найти файлы в облаке без ссылок в БД (орфаны) |
| `analyze_storage` | Сверка БД и облака: что сколько занимает, где мусор |
| `list_inactive_media` | Показать неактивные MediaLibraryItem с размерами |
| `cleanup_crop_sessions` | Удалить старые временные сессии ImageCropSession |

---

### `backup_cloudru`

Полный бэкап бакета. Скачивает все объекты, сохраняя S3-структуру путей. Создаёт `manifest.json` с метаданными каждого файла (размер, ETag, дата). Повторный запуск докачивает только недостающие/изменившиеся файлы.

```bash
python manage.py backup_cloudru                           # полный бэкап в backups/cloudru/YYYY-MM-DD/
python manage.py backup_cloudru --dry-run                  # только листинг, без скачивания
python manage.py backup_cloudru --manifest-only            # только manifest.json
python manage.py backup_cloudru --prefix media_library/    # только файлы media_library/
python manage.py backup_cloudru --output-dir D:\backups    # кастомная папка
```

**Манифест** (`manifest.json`):
```json
{
  "backup_date": "2026-06-01T17:46:17+00:00",
  "bucket": "media-storage",
  "total_objects": 935,
  "total_size_bytes": 374812345,
  "files": [
    {"key": "media_library/file.pdf", "size": 12345, "etag": "\"abc...\"", "last_modified": "..."}
  ]
}
```

---

### `restore_cloudru`

Восстановление из локального бэкапа. Читает `manifest.json` и заливает файлы обратно. По умолчанию пропускает существующие файлы того же размера.

```bash
python manage.py restore_cloudru backups/cloudru/2026-06-01/manifest.json
python manage.py restore_cloudru --manifest ... --dry-run      # только проверка
python manage.py restore_cloudru --manifest ... --overwrite    # перезаписать существующие
python manage.py restore_cloudru --manifest ... --prefix media_library/
```

---

### `find_orphaned_files`

Сравнивает все объекты в бакете с записями в БД:
- `MediaLibraryItem`: media_file, preview_file
- `MediaVariant`: file_path
- `ImageCropSession`: original_file, result_sm/md/lg

Выводит файлы, которые есть в облаке, но не привязаны ни к одной записи.

```bash
python manage.py find_orphaned_files                                      # листинг Cloud.ru
python manage.py find_orphaned_files --manifest manifest.json             # по манифесту (без запросов к облаку)
python manage.py find_orphaned_files --delete                            # удалить орфанов
python manage.py find_orphaned_files --save-manifest                     # сохранить орфанов как manifest (можно restore)
python manage.py find_orphaned_files --output orphans.json               # сохранить список в JSON
```

**Типичный workflow:**
```bash
python manage.py backup_cloudru && \
python manage.py find_orphaned_files --manifest backups/cloudru/$(date +%Y-%m-%d)/manifest.json
```

---

### `analyze_storage`

Детальная сверка БД и облака. Показывает разбивку по категориям (CERTIFICATE, TECH_DOC, PRODUCT_GALLERY...), элементы с устаревшим preview_file, элементы без вариантов, топ по размеру, и баланс (что учтено, что нет).

```bash
python manage.py analyze_storage
python manage.py analyze_storage --manifest backups/cloudru/2026-06-01/manifest.json
```

**Вывод:**
```
=== АНАЛИЗ ПО КАТЕГОРИЯМ ===
Категория                 Элементов    Оригиналы     Варианты      Preview        Всего
-------------------------------------------------------------------------------------
CERTIFICATE                     12      56.3 МБ       9.7 МБ       0.2 МБ      66.2 МБ
TECH_DOC                        63     181.2 МБ      33.0 МБ       1.6 МБ     215.8 МБ
...
=== БАЛАНС: сверка облака и БД ===
  Всего в облаке:           357.4 МБ
  Привязано к БД:           325.5 МБ
  НЕ привязано (орфаны):     31.8 МБ
```

---

### `cleanup_crop_sessions`

Удаляет старые временные сессии `ImageCropSession` и их файлы из Cloud.ru. Сессии создаются при загрузке изображения в ImageCropper, но после `/crop/` удаляются автоматически. Эта команда — для зачистки брошенных сессий (пользователь загрузил, но не обрезал).

```bash
python manage.py cleanup_crop_sessions --dry-run     # посмотреть сколько
python manage.py cleanup_crop_sessions               # старше 1 часа
python manage.py cleanup_crop_sessions --hours 24    # старше 24 часов
python manage.py cleanup_crop_sessions --all          # все
```

---

### `list_inactive_media`

Показывает неактивные (`is_active=False`) элементы медиабиблиотеки с размерами файлов.

```bash
python manage.py list_inactive_media
python manage.py list_inactive_media --manifest manifest.json    # с размерами из облака
python manage.py list_inactive_media --delete                   # удалить неактивные
```

---

## Зависимости

Все команды требуют:
- Django settings с настроенным Cloud.ru (`CLOUDRU_BUCKET_NAME`, `CLOUDRU_ENDPOINT_URL`, ...)
- `boto3` в окружении
- `storage_manager` в `INSTALLED_APPS`

## Примечания

- **Слеши**: Windows использует `\`, S3 требует `/`. Все команды нормализуют пути и проверяют оба варианта.
- **Повторный бэкап**: `backup_cloudru` пропускает файлы, уже существующие локально с тем же размером — можно прерывать и продолжать.
- **Манифест vs лайв**: `find_orphaned_files --manifest` не делает запросов к Cloud.ru — работает офлайн по снапшоту.
- **Безопасность**: `--delete` всегда требует явного подтверждения через аргумент командной строки. `--dry-run` показывает что будет сделано без действий.
