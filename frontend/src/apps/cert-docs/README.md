# Сертификаты — мини-приложение (Vue 3)

Автономное приложение для управления сертификатами и декларациями соответствия.

**Дата:** 2026-05-19  
**Стек:** Vue 3 `<script setup>`, Vite 6, axios, BaseModal, MediaViewer

---

## Файлы

| Файл | Назначение |
|------|-----------|
| `index.html` | Точка входа Vite (multi-page build) |
| `main.js` | `createApp(App).mount('#cert-app')` |
| `App.vue` | Корень: грид, модалка create/edit, MediaViewer |
| `api.js` | API-вызовы к `/api/admin/certs/` + `/api/core/` |
| `components/CertGrid.vue` | Таблица: название+код, тип, бренд, срок (зелёный/красный), файл |
| `components/CertEdit.vue` | Модалка (BaseModal): форма сертификата + загрузка PDF в медиатеку |

---

## Используемые shared-компоненты

| Компонент | Назначение |
|-----------|-----------|
| `BaseModal` | Модальное окно (closable=false, width=800px) |
| `MediaViewer` | Fullscreen просмотр PDF сертификата |

---

## API

### Админские
```
POST   /api/admin/certs/              создание
PUT    /api/admin/certs/<id>/         полное обновление
PATCH  /api/admin/certs/<id>/         частичное обновление
DELETE /api/admin/certs/<id>/         жёсткое удаление (soft=False)
POST   /api/admin/certs/<id>/copy/    копия (CopyMixin)
POST   /api/admin/certs/upload-media/ загрузка PDF в медиатеку
GET    /api/admin/certs/filters/      опции фильтров (только используемые)
```

### Список и фильтрация (UniversalAPIView)
```
GET /api/core/?model=cert_doc.CertData&fmt=compact
    &cert_variety_id=X&brand_id=Y&equipment_type_id=Z&search=...
```

`fmt=compact` → `get_compact_data()` → `to_dict()` с вложенными объектами.

---

## Поток данных

```
CertGrid          → App.vue → CertEdit     (клик по строке → редактирование)
CertEdit.save     → App.vue → CertGrid     (сохранение → обновить список)
CertEdit.copy     → App.vue → CertEdit     (копия → открыть карточку)
CertEdit.delete   → App.vue → CertGrid     (удаление → обновить)
CertEdit.upload   → POST upload-media → media_item_id проставляется
CertGrid 📎 click → App.vue → MediaViewer  (просмотр PDF)
CertEdit 👁 click → App.vue → MediaViewer  (просмотр PDF)
```

---

## Модель сертификата (бэкенд)

```
CertData (SmartCatalogMixin, BaseAbstractModel, StructuredDataMixin, CopyMixin)
├── name, code, description
├── cert_variety    — FK → CertVariety (ТР ТС 012, декларация...)
├── brand           — FK → Brands
├── equipment_types — M2M → EquipmentType
├── issued_by       — кем выдан
├── valid_from/until — даты
├── public_url      — ссылка
├── media_item      — FK → MediaLibraryItem (файл PDF)
└── is_active       — активно / скрыто
```

### CopyMixin
- `copy()` копирует все поля + M2M equipment_types
- `code` + `name` получают суффикс «(копия)»
- `media_item` сбрасывается в None (копия без файла)
- `sorting_order` сбрасывается в 0

### Фильтрация
```
FILTER_DEFINITIONS: cert_variety_id, brand_id, equipment_type_id
SEARCH_FIELDS: name, code, description, issued_by
```
`CertFilterOptionsView` возвращает только те опции, для которых есть сертификаты.

---

## Загрузка файла сертификата в медиатеку

`CertMediaUploadView` (`POST /api/admin/certs/upload-media/`):
- Принимает `file` (multipart PDF) + опциональные `title`, `equipment_type_id`, `brand_id`
- Создаёт `MediaLibraryItem` с категорией `CERTIFICATE`
- Название формируется: «Тип сертификата — Тип оборудования — Название сертификата»
- Возвращает `{id, title, ...to_dict()}`
- `media_item_id` автоматически проставляется в сертификат при сохранении

---

## Что нужно продумать

### Привязка model_line к сертификату

Сейчас связь строится через M2M `EquipmentTypeMixin.cert_docs` на стороне модельных линеек. Идея: в карточке сертификата можно выбирать конкретные model_line, к которым он относится.

**Варианты реализации:**
1. **Через M2M cert_docs** — добавить в CertEdit multiselect модельных линеек, сгруппированных по типу оборудования
2. **Через equipment_types** — оставить текущую связь через типы оборудования, model_line автоматически подхватывают сертификаты по своему equipment_type
3. **Гибрид** — equipment_types как фильтр + возможность вручную привязать/отвязать model_line

**Сложность:** model_line разных сущностей (PA, EA, фитинги, редукторы, соленоиды) лежат в разных моделях → нужен GenericForeignKey или отдельная through-таблица.

### Сценарий: файл уже в медиатеке

Если PDF сертификата уже загружен в медиатеку:
1. Открыть карточку сертификата
2. В блоке «Файл сертификата» вместо drag&drop — кнопка «Выбрать из медиатеки»
3. Открывается мини-грид медиатеки (или select с поиском)
4. Выбранный `media_item_id` проставляется в сертификат

### Сценарий: замена файла сертификата

Если нужно заменить PDF (новая версия сертификата):
1. В карточке сертификата — кнопка «Заменить файл»
2. Drag&drop нового PDF → вызов `POST /api/admin/certs/upload-media/`
3. Новый `MediaLibraryItem` создаётся, `media_item_id` обновляется
4. Старый `MediaLibraryItem` остаётся в медиатеке (можно удалить вручную)

**Альтернатива:** использовать фичу замены файла из медиатеки — оставить тот же `MediaLibraryItem`, но заменить в нём файл (`PATCH /api/admin/media/<id>/` с file в FormData). Это сохранит связи, если на этот media_item ссылаются другие сущности.

---

## Сборка

**Dev:** `npm run dev` → `http://localhost:5173/src/apps/cert-docs/index.html`  
**Prod:** `npm run build` → `dist/cert-docs.html`

---

## Что не доделано

- [ ] Привязка model_line к сертификату (см. выше)
- [ ] Выбор существующего файла из медиатеки при создании сертификата
- [ ] Замена файла сертификата (через механизм замены в медиатеке)
- [ ] Аутентификация (все AllowAny)
- [ ] Пагинация
- [ ] Тесты
