# media_library — Медиабиблиотека

Централизованное хранилище файлов (изображения, PDF, чертежи, техдокументация). Используется как служебный инструмент — другие сущности (модельные линейки, сертификаты) ссылаются на файлы отсюда.

**Дата актуализации:** 2026-05-18

---

## Файлы и зоны ответственности

| Файл | Назначение | Статус |
|------|-----------|--------|
| `models.py` | MediaCategory + MediaLibraryItem (SmartCatalogMixin, to_dict, get_compact_data) | ✅ |
| `views/__init__.py` | Реэкспорт 4 view-классов | ✅ |
| `views/admin_upload.py` | POST `/api/admin/media/upload/` — загрузка файла (IsAdminUser) | ✅ |
| `views/admin_detail.py` | PUT/PATCH/DELETE `/api/admin/media/<id>/` — CRUD (IsAdminUser) | ✅ |
| `views/download.py` | GET `/api/media/<id>/download/` — скачивание (AllowAny, проверка is_public) | ✅ |
| `views/preview.py` | GET `/api/media/<id>/view/` — просмотр в браузере (AllowAny) | ✅ |
| `urls.py` | `urlpatterns_admin` + `urlpatterns_public` — два входа | ✅ |
| `admin.py` | Django-админка (MediaCategory + MediaLibraryItem) | Старый, HTML, не трогался |
| `signals.py` | Сигналы (удалены: post_migrate, pre_delete MediaLibraryItem) | ⚠️ Проверить — возможно остался мусор |
| `graphql/` | GraphQL-схема (mutations, queries, types, schema) | ⚠️ Не рабочий, нужно переписать под новые модели |
| `templates/` | HTML-шаблоны для старых views | ⚠️ Можно удалить — старые view удалены |
| `apps.py` | AppConfig, импортирует signals | ⚠️ Убрать импорт signals |

---

## API — два входа

### Публичный (раздача файлов)
```
GET  /api/media/<id>/download/   → MediaDownloadView   (AllowAny)
GET  /api/media/<id>/view/       → MediaPreviewView    (AllowAny)
```

### Админский (редактирование)
```
POST   /api/admin/media/upload/  → MediaAdminUploadView   (IsAdminUser)
PUT    /api/admin/media/<id>/    → MediaAdminDetailView   (IsAdminUser)
PATCH  /api/admin/media/<id>/    → MediaAdminDetailView   (IsAdminUser)
DELETE /api/admin/media/<id>/    → MediaAdminDetailView   (IsAdminUser)
```

Список и фильтрация — через `UniversalAPIView`:
```
GET /api/core/?model=media_library.MediaLibraryItem&fmt=compact&category_id=X&brand_id=Y&search=...
```

---

## Модель: MediaLibraryItem

```
MediaLibraryItem (SmartCatalogMixin)
├── media_file        — ManagedFileField (файл)
├── preview_file      — ManagedFileField (авто-JPEG превью 400×300)
├── category          — FK → MediaCategory
├── brand             — FK → Brands (nullable)
├── equipment_type    — FK → EquipmentType (nullable)
├── keywords          — строка через запятую (поиск)
├── is_public         — доступ всем / только авторизованным
├── is_active         — мягкое удаление
├── sorting_order     — порядок в списках
├── is_default        — изображение по умолчанию
├── created_by        — FK → User
├── mime_type         — автоопределение в save()
└── to_dict()         — JSON с вложенными объектами category/brand/equipment_type
    get_compact_data() — делегирует to_dict() (для UniversalAPIView)
```

### Особенности save()
- Автоопределение `mime_type` по расширению
- Автосоздание `preview_file` (JPEG, 400×300) — изображения (Pillow) + PDF (PyMuPDF, первая страница)

### Особенности удаления
- Физические файлы чистятся вручную через `file_service.delete_file()`
- M2M-связи (ImageGalleryMixin.images) очищаются через `.clear()`
- FK-связи (CertData.media_item) обнуляются сырым SQL
- Сама запись удаляется сырым SQL (обход бага каскадного коллектора Django)

---

## Фильтрация (SmartCatalogMixin)

```python
FILTER_DEFINITIONS:
  category_id       — EXACT, FK
  brand_id          — EXACT, FK
  equipment_type_id — EXACT, FK
  keyword           — CONTAINS (icontains по keywords)

SEARCH_FIELDS = ['title', 'description', 'keywords']
SELECT_RELATED_FIELDS = ['category', 'equipment_type', 'created_by', 'brand']
```

---

## Что нужно доделать

### Высокий приоритет
- [ ] **GraphQL-схема** — файлы в `graphql/` не актуальны. Нужно переписать под MediaLibraryItem + MediaCategory с учётом вложенных объектов (category{id,name,icon}, brand, equipment_type)
- [ ] **Файловая загрузка через GraphQL** — GraphQL не поддерживает multipart из коробки. Нужен либо graphene-file-upload, либо оставить REST для upload
- [ ] **apps.py** — убрать `from . import signals`, если signals.py удалён
- [ ] **templates/** — удалить `media_library/media_detail.html` (старый view удалён)
- [ ] **signals.py** — проверить, удалён ли файл полностью или там остался мусор

### Средний приоритет
- [ ] **Контроль доступа** — сейчас `IsAdminUser` на админских эндпоинтах, `AllowAny` на раздаче. Для партнёров нужен API Key / token auth. В модели уже есть `is_public` — используется в download/preview
- [ ] **Пагинация в list** — UniversalAPIView не пагинирует. При сотнях файлов будет тормозить. Добавить `?limit=50&offset=100` или DRF PageNumberPagination
- [ ] **Загрузка от партнёров** — partner upload endpoint с привязкой к partner_id + квоты

### Низкий приоритет
- [ ] **Тесты** — нет ни одного теста на views
- [x] **preview для PDF** — реализовано через PyMuPDF (2026-05-19)
- [ ] **preview для Word/Excel** — не реализовано, показ generic-иконки
- [ ] **Автоопределение equipment_type** — по имени файла или ключевым словам

---

## Зависимости

- `core.models.EquipmentType` — тип оборудования (фильтр)
- `producers.models.Brands` — бренд (фильтр)
- `storage_manager.fields.ManagedFileField` — файловое поле с кастомным generate_filename
- `storage_manager.services.file_service` — сервис удаления/проверки файлов
- `core.models.smart_catalog_mixin.SmartCatalogMixin` — фильтрация и поиск
- `core.views.UniversalAPIView` — list/detail через `/api/core/`

## Frontend

Vue-мини-приложение: `frontend/src/apps/media-library/`
- `MediaGrid.vue` — сетка + 5 фильтров (поиск, категория, тип, бренд, keyword)
- `MediaUpload.vue` — drag&drop загрузка с формой
- `MediaEdit.vue` — модалка редактирования/удаления/замены файла
- `api.js` — вызовы к `/api/admin/media/` + `/api/core/`

---

## Примечания для следующей сессии

1. **`get_compact_data()`** — критично: UniversalAPIView использует его вместо сериализатора, если передан `fmt=compact`. Возвращает `to_dict()` с вложенными объектами. Без этого list отдаёт голые FK-ID.
2. **`fmt` в exclude_filters** — я чинил баг в `core/views.py`: добавил `'fmt'` в `exclude_filters`. Если кто-то перепишет UniversalAPIView — может вернуться.
3. **Удаление через raw SQL** — баг каскадного коллектора Django (ValueError: Cannot query str()). При любом удалении MediaLibraryItem использовать raw SQL, а не `instance.delete()`.
4. **Старый `views.py`** — удалён и заменён на `views/` (пакет). Если видишь `media_library/views.py` и `media_library/views/` одновременно — удали файл.
5. **Approval mode** — у меня были проблемы с записью в режиме Never. Для правки файлов в этой сессии использовался SUGGEST.
6. **Слеши в URL** — все эндпоинты требуют завершающий `/`. Без него Django не резолвит.
