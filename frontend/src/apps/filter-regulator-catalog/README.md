# Filter-Regulator Catalog (фронтенд)

Standalone SPA + виджет для каталога фильтр-регуляторов.

## Структура

```
filter-regulator-catalog/
  api.js              — API-клиент (/api/filter-regulator/)
  App.vue             — standalone SPA (страницы: section, list, detail, brand, engineer)
  main.js             — точка входа standalone
  index.html          — HTML для standalone
  components/
    GearboxSection.vue   — сетка серий + кнопка «Инженерный каталог»
    GearboxList.vue      — каталог с фильтрами (FilterSidebar + ProductCard)
    GearboxDetail.vue    — карточка товара (ProductDetail)
    GearboxBrand.vue     — витрина серии (фильтр по model_line_id)
    EngineerCatalog.vue  — инженерный каталог (визуальный подбор)
```

## Страницы

| Страница | Компонент | Описание |
|---|---|---|
| Серии | `GearboxSection` | Сетка карточек серий, кнопки «Инженерный каталог» и «Показать все» |
| Каталог | `GearboxList` | Список с FilterSidebar, поиск, пагинация |
| Карточка | `GearboxDetail` | ProductDetail с вкладками |
| Серия | `GearboxBrand` | Все модели серии (фильтр model_line_id) |
| Инженерный | `EngineerCatalog` | Чипсы серий и фильтров, авто-дефолты, одна карточка |

## Инженерный каталог (EngineerCatalog)

- Выбор серии — чипсы (кнопки)
- Подфильтры: тонкость фильтрации, материал корпуса, расход, резьба портов
- Авто-дефолты при загрузке: первая серия, макс. фильтрация, мин. расход
- При смене фильтра: остальные сохраняются (если совместимы) или сбрасываются
- Все чипсы всегда видны и кликабельны
- Карточка через `ProductDetail` (общий компонент)

## API

| Метод | Эндпоинт |
|---|---|
| `list(params)` | `GET /api/filter-regulator/catalog/` |
| `getDetail(id)` | `GET /api/filter-regulator/catalog/{id}/` |
| `getFilters()` | `GET /api/filter-regulator/filters/` |
| `getMeta()` | `GET /api/filter-regulator/meta/` |
| `getEngineer(mlId, filters)` | `GET /api/filter-regulator/engineer/` |
| `getPrices(codes)` | `GET /api/admin/prices/snapshot/` |

## Виджет

Маршруты в `widget/App.vue`:
- `#/filter_regulator` → серии (FrSection)
- `#/filter_regulator/catalog` → каталог (FrList)
- `#/filter_regulator/detail/{id}` → карточка (FrDetail)
- `#/filter_regulator/brand/{id}` → серия (FrBrand)
- `#/filter_regulator/engineer` → инженерный (FrEngineer)

## Запуск

```bash
npm run dev
# Standalone: http://localhost:5173/src/apps/filter-regulator-catalog/index.html
# Виджет: http://localhost:5173/src/apps/widget/index.html#/filter_regulator
```
