# cert_doc — Сертификаты и декларации соответствия

Приложение Django для управления сертификатами. REST API + Vue-фронтенд.

**Дата:** 2026-05-20

---

## Модели

### CertVariety
Тип сертификата: ТР ТС 012, Декларация, ISO...  
Наследует `BaseAbstractModel` → `is_active`, `sorting_order`, `SoftDeleteMixin`.

### CertData
Основная модель. Наследует:
- `SmartCatalogMixin` — фильтрация, `to_dict()`
- `BaseAbstractModel` — `is_active`, `sorting_order`, `SoftDeleteMixin`
- `StructuredDataMixin` — `get_compact_data()`, `get_display_data()`
- `CopyMixin` — `copy()` с суффиксом «(копия)»

```
CertData
├── name, code, description
├── cert_variety (FK)    → CertVariety
├── brand (FK)           → Brands
├── equipment_types (M2M) → EquipmentType
├── issued_by            — кем выдан
├── valid_from / valid_until — даты
├── public_url           — внешняя ссылка
├── media_item (FK)      → MediaLibraryItem (PDF)
└── is_active
```

---

## API

```
POST   /api/admin/certs/                создание
PUT    /api/admin/certs/<id>/           полное обновление
PATCH  /api/admin/certs/<id>/           частичное обновление
DELETE /api/admin/certs/<id>/           физическое удаление (soft=False)
POST   /api/admin/certs/<id>/copy/      копия (CopyMixin, без media_item)
POST   /api/admin/certs/upload-media/   загрузка PDF → медиатека
GET    /api/admin/certs/filters/        опции фильтров (CertFilterOptionsView)
```

Список и детали:
```
GET /api/core/?model=cert_doc.CertData&fmt=compact&cert_variety_id=X&...
GET /api/core/?model=cert_doc.CertData&id=1
```

---

## Views

| Файл | Класс | Методы |
|------|-------|--------|
| `views/admin_create.py` | `CertAdminCreateView` | POST |
| `views/admin_detail.py` | `CertAdminDetailView` | PUT, PATCH, DELETE |
| `views/admin_copy.py` | `CertAdminCopyView` | POST (copy) |
| `views/admin_media_upload.py` | `CertMediaUploadView` | POST (upload PDF to media library) |
| `views/filters.py` | `CertFilterOptionsView` | GET (filter options) |

Все: `AllowAny` (TODO: IsAdminUser + API Key).

---

## Фильтрация

Фильтры определяются в `CertFilterOptionsView`, **не** в модели.  
View сам опрашивает: какие типы/бренды/оборудование используются в CertData.

```
cert_variety_id   — SELECT DISTINCT cert_variety_id FROM cert_doc_certdata
brand_id          — SELECT DISTINCT brand_id WHERE brand_id IS NOT NULL
equipment_type_id — через through-таблицу M2M
```

---

## Копирование

`CertData.copy()` (CopyMixin):
- Копирует все поля + M2M `equipment_types`
- `code` и `name` + « (копия)»
- `media_item` → None (копия без файла)
- `sorting_order` → 0

---

## Удаление

`cert.delete(soft=False)` — физическое удаление.  
Без `soft=False` срабатывает `SoftDeleteMixin` (is_deleted=True) — объект остаётся в базе.

---

## Загрузка PDF в медиатеку

`CertMediaUploadView` (multipart):
1. Принимает `file` (PDF) + опциональные `title`, `equipment_type_id`, `brand_id`
2. Создаёт `MediaLibraryItem` с `category=CERTIFICATE`
3. Возвращает `{id, title, ...to_dict()}`
4. Фронтенд проставляет `media_item_id` в сертификат

---

## Фронтенд

Мини-приложение: `frontend/src/apps/cert-docs/`
- `CertGrid.vue` — таблица с цветовыми индикаторами срока
- `CertEdit.vue` — модалка (BaseModal 800px): форма + загрузка/выбор/замена PDF

---

## Что дальше

- Привязка model_line к сертификату (M2M cert_docs)
- Аутентификация (API Key)
- Тесты
