# Каталог редукторов — мини-приложение (Vue 3)

Просмотр каталога редукторов с фильтрами, поиском, карточками товаров и детальной страницей.

**Дата:** 2026-05-22
**Стек:** Vue 3 `<script setup>`, Vite 6, axios

---

## Файлы

| Файл | Назначение |
|------|-----------|
| `index.html` | Точка входа Vite |
| `main.js` | `createApp(App).mount('#gearbox-app')` |
| `App.vue` | Переключение список/детальная, загрузка фильтров |
| `api.js` | Вызовы к `/api/gearbox/catalog/`, `/api/gearbox/filters/`, prices |
| `components/GearboxList.vue` | Сетка карточек + поиск + боковая панель фильтров |
| `components/GearboxCard.vue` | Карточка товара (изображение, название, мета, цена) |
| `components/GearboxDetail.vue` | Страница товара (галерея, вкладки, характеристики) |

---

## Структура страницы

### Каталог (GearboxList)
- Поисковая строка (поиск по code, name, description)
- Боковая панель: выпадающие фильтры (серия, бренд, IP, температура, материал корпуса, монтажная площадка...)
- Сетка карточек 3 колонки (адаптивная: 2 → 1 на мобильных)
- Пагинация

### Карточка (GearboxCard)
- Изображение: `images` модели → `images` model_line → заглушка «Нет фото»
- `alt` = `"Изображение " + gearbox_output_variety + " " + gearbox_variety + " " + code`
- Название, бренд, тип редуктора
- Цена из price/snapshot (в долларах) или «Цена по запросу»

### Детальная страница (GearboxDetail)
- Заголовок (name)
- Фотогалерея с миниатюрами
- Правая колонка: цена + краткие характеристики
- Вкладки:
  - **Характеристики** — полная таблица параметров (бренд, IP, тип передачи, моменты, вес, присоединения...)
  - **Документы** — ссылки на скачивание tech_docs (модель + model_line)
  - **Сертификаты** — ссылки на скачивание cert_docs (model_line)
  - **Краткое описание** — name + description (кликабельные для копирования)

---

## API (бэкенд)

| Метод | URL | Описание |
|-------|-----|---------|
| GET | `/api/gearbox/catalog/` | Список с фильтрами + sku_codes для цен |
| GET | `/api/gearbox/catalog/<id>/` | Детальная модель |
| GET | `/api/gearbox/filters/` | Опции фильтров |
| GET | `/api/admin/prices/snapshot/?code=...` | Цены (через общий снэпшот) |

---

## Конвертер валют

Цены в каталоге — в долларах. Нужен конвертер в рубли (курс ЦБ или фиксированный).

---

## Подключение

1. `gearbox/urls.py` → `djangoProject1/urls.py`: `path('api/gearbox/', include('gearbox.urls'))`
2. `frontend/vite.config.js`: `'gearbox-catalog': resolve(__dirname, 'src/apps/gearbox-catalog/index.html')`
3. Фильтры вынесены из `gearbox/models/gearbox.py` в `gearbox/services/filters.py`
