# SESSION.md — обновлён 2026-05-22

## Правила
- Не пиши в существующие файлы без разрешения. Спроси: «Я планирую изменить X в Y, можно?»
- Шаг за шагом, не забегай вперёд
- При смене машины — читай этот файл

---

## Сделано 2026-05-22

### Цены — переход на SKU
- **PriceHistory.sku** — FK на SKU (миграции 0007 схема, 0008 данные)
- 47 записей PriceHistory привязаны к SKU по коду, 35 новых SKU создано
- `get_current_price_by_sku(sku, variety)` — поиск цены через номенклатуру
- `get_compact_data()` — sku_id, sku_code, sku_name
- **Каскад:** удаление SKU → удаление всех связанных PriceHistory

### PriceDocument — убран item_content_type
- **Миграция 0009:** PriceDocument − `item_content_type`, PriceDocumentItem: GFK → `sku` FK
- `apply_prices()` / `unapply_prices()` — через SKU, не GFK
- Админка: inline позиций через `sku`, убран тип оборудования из фильтров
- Фронтенд: поиск товара через `/api/admin/sku/?search=`, создание без типа оборудования

### PriceSnapshotView — поиск по коду
- Режим GFK: `?content_type_id=X&object_ids=1,2,3`
- Режим code: `?code=RD7,RD7.LT` — для номенклатуры без сущности
- Ошибка 400 если не указан ни один режим

### UniversalAPIView — search, limit, post/put/delete
- `search` — фильтр по name/code/title (подстрока)
- `limit`/`offset` — пагинация с `total`
- `post` — создание объекта (`{model, ...fields}`)
- `put` — обновление (`{model, id, ...fields}`)
- `delete` — удаление (`?model=X&id=Y`)
- **CSRF fix:** `csrf_exempt` в `core/urls.py` + `authentication_classes = []` в классе
  Причина 403: DRF включает SessionAuthentication по умолчанию → требует CSRF-токен

### Админка цен
- PriceHistory: `search_fields` = name, code, sku__code, sku__name
- PriceDocumentAdmin: inline-позиции, статус-бейджи, фильтры

### SKU — фронтенд-приложение
- **sku-admin** (`frontend/src/apps/sku-admin/`):
  - `SkuList.vue` — таблица с поиском, фильтры (тип, бренд)
  - `SkuForm.vue` — модалка CRUD (код, название, описание, тип, бренд)
  - `BatchProcessing.vue` — групповая обработка: фильтры с «не указано», чекбоксы, кнопки
- **API:** `sku/views.py` — SkuListView, SkuBatchUpdateView
- **URL:** `/api/admin/sku/` + `/api/admin/sku/batch/`
- Меню: раздел Настройки → Номенклатура (SKU)

### SKUMixin — подхват существующей SKU
- `sync_sku()`: если SKU с таким кодом уже есть → обогатить полями из модели
- source_content_type / source_object_id — заполняются при первом связывании

### Документ цен — инлайн-редактирование
- Цена — клик для редактирования, Enter/blur для сохранения
- Кнопка 📝 — модалка редактирования SKU
- Кнопка «+ Создать и добавить» — создание SKU и сразу в документ

### Каталог цен — фильтры
- Выпадающие списки: тип оборудования, бренд
- Бэкенд: фильтрация через `sku__equipment_type_id`, `sku__brand_id`

### apply_prices — name/code из SKU
- При проведении документа PriceHistory получает name и code из SKU (было пусто)
- unapply_prices корректно удаляет записи и восстанавливает is_current у предыдущих

### Документ цен — «Заполнить по фильтрам»
- Кнопка открывает модалку с фильтрацией SKU (код, тип, бренд)
- Чекбоксы, «Выделить всё», «Отобрать»
- «Перенести в документ» — добавляет выделенные SKU в документ

### Попутные исправления
- Закомментирован `from django.contrib.postgres.fields import JSONField` в 3 файлах (проект на SQLite)
- Убран `description` из search_fields PriceHistoryAdmin
- Установлены пакеты: django-import-export, django-filter, streamlit, tabulate, docxtpl, Markdown

---

## Архитектура цен

```
PriceHistory ──FK(CASCADE)──> SKU <──OneToOne── GearBox (SKUMixin)
     ↑                              ↑
     │                    code (уникальный ключ)
     │                              │
PriceDocumentItem ──FK──>  standalone SKU (счета/КП)
```

- PriceHistory привязана к SKU (GFK для совместимости)
- PriceDocumentItem привязан к SKU (GFK убран)
- Номенклатура создаётся раньше модели, модель подхватывает по коду
- Каскад: удаление SKU → удаление цен

---

## Права доступа (важно на будущее)

| Что | Кому | Как |
|---|---|---|
| `/api/core/` (UniversalAPIView) | Все методы — без аутентификации | `csrf_exempt` + `authentication_classes = []` |
| `/api/admin/*/` (цены, SKU, медиатека) | Без аутентификации | `AllowAny` |
| Админка Django `/admin/` | Только staff | Стандартная Django-аутентификация |

**При добавлении аутентификации:**
- `core/urls.py` — убрать `csrf_exempt`
- `core/views.py` — заменить `authentication_classes = []` на `[TokenAuthentication]`
- DRF-вьюхи — заменить `AllowAny` на `IsAuthenticated`

---

## Стек
Django 5.2 + SQLite + DRF (UniversalAPIView) | Vue 3 + Vite 6

---

## Важные пути

| Что | Где |
|---|---|
| Медиатека | `media_library/` + `frontend/src/apps/media-library/` |
| Сертификаты | `cert_doc/` + `frontend/src/apps/cert-docs/` |
| Цены | `price/` + `frontend/src/apps/price-catalog/` |
| SKU | `sku/` + `frontend/src/apps/sku-admin/` |
| UniversalAPIView | `core/views.py` (GET/POST/PUT/DELETE + search + limit) |
| Меню | `frontend/src/components/header/TopMenu.vue` |
| Vite | `frontend/vite.config.js` |

---

### Каталог редукторов — приложение для фронта
- **gearbox/services/filters.py** — FILTER_DEFINITIONS вынесены из модели GearBox
- **gearbox/views/catalog.py** — GearboxCatalogView (список+фильтры), GearboxDetailView, GearboxFilterOptionsView
- **gearbox/urls.py** — /api/gearbox/catalog/, /api/gearbox/catalog/<id>/, /api/gearbox/filters/
- **djangoProject1/urls.py** — добавлен `path('api/gearbox/', include('gearbox.urls'))`
- **frontend/src/apps/gearbox-catalog/** — Vue 3 приложение:
  - `GearboxList.vue` — сетка карточек + поиск + фильтры
  - `GearboxCard.vue` — прямоугольная карточка (изображение→model_line, alt, цена из snapshot)
  - `GearboxDetail.vue` — страница товара (галерея + вкладки: Характеристики/Документы/Сертификаты/Краткое описание)
- **vite.config.js** — добавлен entry `gearbox-catalog`
- **Цены** — через `/api/admin/prices/snapshot/?code=...` (в долларах)
- **Меню** — пункт «🔧 Каталог редукторов» в выпадающем меню ⚙️ Настройки (TopMenu.vue)
- **Изображения** — URL через API медиабиблиотеки `/api/media/<id>/view/` (проксируется Vite)
  - `_get_image_url()` → `/api/media/{id}/view/` (было `img.media_file.url` → `/media/...` — не работало)
  - `_get_file_info()` → `/api/media/{id}/download/` (было `doc.media_file.url`)
  - `vite.config.js`: прокси для `/media` и `/static`
  - Исправлено через `apply_patch` (write_file/edit_file не применялись)
  - 16 редукторов с изображениями через model_line (img id=35), собственных нет
  - Для применения нужен перезапуск Django

### Документация gearbox
- **gearbox/README.md** — полная документация модуля: модели, связи, API, админка, шаблоны, фронтенд
- **Докстринги обновлены/добавлены** во всех моделях gearbox:
  - `GearBox` — класс, save(), SKUMixin-методы, copy(), _get_data_dict(), шаблонные методы, to_dict()
  - `GearBoxBody` — класс, mounting_plate_*_list_text, _get_mounting_plate_list_text, api_dict(), api_short_dict()
  - `GearBoxInterlock` — класс
  - `OverrideMechanism` — класс (варианты в формате RST)
  - `TransmissionVariety` — класс
  - `GearboxVariety` — класс

### Напоминание: конвертер валют
Цены в каталоге редукторов в долларах. Нужно сделать конвертер в рубли.

---

## Следующие шаги
- Импорт цен из Excel в PriceDocument
- ImageGalleryMixin к model_line (PA, EA, фитинги)
- Массовое создание SKU для всех моделей с code
- Аутентификация (API Key / token)
