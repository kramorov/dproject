# Медиабиблиотека — мини-приложение (Vue 3)

Автономное приложение для управления медиафайлами. Работает через REST API, не зависит от роутера и других частей SPA.

**Дата:** 2026-05-19  
**Стек:** Vue 3 `<script setup>`, Vite 6, axios, без Pinia/роутера

---

## Файлы

| Файл | Назначение |
|------|-----------|
| `index.html` | Точка входа для Vite (multi-page build) |
| `main.js` | `createApp(App).mount('#media-app')` |
| `App.vue` | Корень: хедер, переключение грид/загрузка, модалки |
| `api.js` | Все API-вызовы к `/api/admin/media/` и `/api/core/` |
| `components/MediaGrid.vue` | Сетка карточек (2 в ряд) + 5 фильтров + debounce |
| `components/MediaUpload.vue` | Drag&drop загрузка файла с формой |
| `components/MediaEdit.vue` | Модалка: редактирование, удаление, копирование, замена файла |

---

## Используемые shared-компоненты

| Компонент | Откуда | Назначение |
|-----------|--------|-----------|
| `BaseButton` | `@/shared/components/BaseButton.vue` | Пока не используется (кнопки inline) |
| `BaseModal` | `@/shared/components/BaseModal.vue` | Модальное окно (closable=false в MediaEdit) |
| `MediaViewer` | `@/shared/components/MediaViewer.vue` | Fullscreen просмотр изображений и PDF |

---

## API (REST)

### Админские (все AllowAny, TODO: IsAdminUser)
```
POST   /api/admin/media/upload/       загрузка
PUT    /api/admin/media/<id>/         полное обновление
PATCH  /api/admin/media/<id>/         частичное обновление
DELETE /api/admin/media/<id>/         удаление
POST   /api/admin/media/<id>/copy/    копия (без файла)
```

### Публичные
```
GET /api/media/<id>/download/         скачивание
GET /api/media/<id>/view/             просмотр (inline)
```

### Список и фильтрация (через UniversalAPIView)
```
GET /api/core/?model=media_library.MediaLibraryItem&fmt=compact
    &category_id=X&equipment_type_id=Y&brand_id=Z&search=...&keyword=...
```

`fmt=compact` включает `get_compact_data()` → `to_dict()` с вложенными объектами.

---

## Поток данных

```
MediaGrid        → App.vue → MediaEdit   (клик по карточке → редактирование)
MediaGrid        → App.vue → MediaViewer (клик по картинке → просмотр)
MediaEdit.preview → App.vue → MediaViewer (клик в модалке → просмотр)
MediaUpload      → App.vue → MediaGrid   (загрузка → обновить список)
MediaEdit.save   → App.vue → MediaGrid   (сохранение → обновить)
MediaEdit.copy   → App.vue → MediaEdit   (копия → открыть карточку)
MediaEdit.delete → App.vue → MediaGrid   (удаление → обновить)
```

Фильтры в MediaGrid — локальные, запрос уходит сразу при изменении (debounce 200ms).

---

## Сборка

**Dev:** `npm run dev` → `http://localhost:5173/src/apps/media-library/index.html`  
**Prod:** `npm run build` → `dist/media-library.html` + js/css  
**Vite config:** multi-page `rollupOptions.input` в `frontend/vite.config.js`

---

## Что не доделано

- [ ] Аутентификация — все админские endpoint'ы на `AllowAny`, нужно вернуть `IsAdminUser` + API Key
- [ ] Загрузка файла при редактировании — работает через PATCH с FormData, но UX можно улучшить (прогресс-бар)
- [ ] Графический drag&drop в гриде — сейчас загрузка отдельной формой
- [ ] Пагинация — список без лимита, при 100+ элементах тормозит
- [ ] Сортировка в гриде — только как приходит от API

## Примечания

1. **Preview URL для карточек** — `MediaGrid` использует `previewUrl(id)` → `/api/media/<id>/view/`. Для PDF возвращает JPEG первой страницы (PyMuPDF).
2. **PDF в просмотрщике** — `MediaViewer` для PDF использует `downloadUrl` (теперь inline), для картинок — `viewUrl`.
3. **Копирование** — создаёт полную копию без файла, title + «(копия)», сразу открывает карточку копии.
4. **Закрытие модалки** — только по кнопкам (✕, Отмена, Сохранить). Клик вне формы не закрывает.
5. **Удаление через raw SQL** — бэкенд делает `DELETE FROM media_library_medialibraryitem WHERE id = %s` в обход каскадного коллектора Django.
