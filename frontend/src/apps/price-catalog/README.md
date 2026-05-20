# Цены — мини-приложение (Vue 3)

Каталог цен и журнал документов формирования цен.

**Дата:** 2026-05-20  
**Стек:** Vue 3 `<script setup>`, Vite 6, axios

---

## Файлы

| Файл | Назначение |
|------|-----------|
| `index.html` | Точка входа Vite |
| `main.js` | `createApp(App).mount('#price-app')` |
| `App.vue` | Две вкладки: Каталог цен + Документы |
| `api.js` | API-вызовы к `/api/admin/prices/` |

---

## API

```
GET /api/admin/prices/                      список цен с фильтрацией
GET /api/admin/prices/filters/              опции фильтров
GET /api/admin/prices/documents/            список документов
POST /api/admin/prices/documents/           создать документ
PUT /api/admin/prices/documents/<id>/       обновить (черновик)
DELETE /api/admin/prices/documents/<id>/    удалить
POST /api/admin/prices/documents/<id>/apply/ применить → PriceHistory
GET /api/admin/prices/documents/<id>/items/ строки документа
POST /api/admin/prices/documents/<id>/items/ добавить строку
```

---

## Вкладки

### Каталог цен
- Таблица: название, код, вид цены, валюта, цена, дата, актуальность
- Фильтры: поиск, вид цены, валюта, даты «с/по», чекбокс «только актуальные»

### Документы
- Таблица: название, тип товаров, дата, кол-во позиций, статус
- Кнопки: «Применить» (→ PriceHistory), «Удалить»
- Создание: название + выбор типа товаров (ContentType)

---

## Что не доделано

- [ ] Редактор документа — страница с таблицей строк (добавление товаров, цены)
- [ ] Импорт из Excel
- [ ] Выбор товаров через поиск (сейчас только object_id вручную)
- [ ] Пагинация
