# Шаблон нового каталога (Catalog Pattern)

## Три уровня API

| Страница | Эндпоинт | Сериализатор | Что внутри |
|----------|----------|-------------|------------|
| **Серии** | `GET /sections/` | Отдельный View с `annotate(Count)` | `id, name, code, count, image, brand` |
| **Список** | `GET /catalog/` | `to_values_dict()` — лёгкий | `id, name, code, 1 фото, model_line, sku` |
| **Карточка** | `GET /catalog/<id>/` | `to_dict()` — полный | Всё: sections, specs, gallery, docs, certs |

## Бэкенд

### 1. Модель (`models/`)

Наследовать от `CatalogDictMixin` + `ImageGalleryMixin` (core/models/):

```python
class MyModel(CatalogDictMixin, ImageGalleryMixin, TechDocMixin,
              SmartCatalogMixin, TemplateMixin, SKUMixin, CopyMixin,
              models.Model):
    ...
```

Обязательные методы:
- `_get_template_vars()` → `dict` — плоский словарь значений
- `_get_docs_section()` → `list` — документация
- `_get_certs_section()` → `list` — сертификаты
- `_get_model_line_summary()` → `dict` — `{id, name, code, brand}`
- `_get_sku_summary()` → `dict` — `{id, code, name}`
- `to_dict()` → `dict` — полная структура с sections
- `_get_image_alt()` → `str` — alt-текст

❗ `_get_first_image()` и `_get_images_section()` — теперь в `ImageGalleryMixin`,
   **не нужно** переопределять в модели. Миксин сам делает фолбэк
   `item.image_gallery → model_line.image_gallery`.

❗ `to_values_dict()` — переопределить для скорости:
```python
def to_values_dict(self) -> dict:
    first_img = self._get_first_image()
    tv = {'code': self.code or '', 'name': self.name or ''}
    return {
        'id': self.id, 'code': self.code or '', 'name': self.name or '',
        'image_alt': self._get_image_alt(),
        'template_vars': tv, 'values': tv,
        'images': [first_img] if first_img else [],
        'model_line': self._get_model_line_summary(),
        'sku': self._get_sku_summary(),
    }
```

### 2. ImageGallerySet — наборы изображений

Модели в `media_library/models.py`:
- `ImageGallerySet` — контейнер (name, code, keywords)
- `ImageGallerySetItem` — через through: `gallery_set`, `image`, `sorting_order`, `is_default`

`ImageGalleryMixin` добавляет FK `image_gallery` → `ImageGallerySet`.
Фолбэк: если у товара нет своей галереи → берётся из `model_line.image_gallery`.

### 3. View (`views/catalog.py`)

```python
SELECT_RELATED = [
    'model_line', 'model_line__brand',
    'image_gallery', 'model_line__image_gallery',
    # ВСЕ ForeignKey, к которым обращается _get_template_vars()
]
```

```python
class MyCatalogView(APIView):
    def get(self, request):
        qs = MyModel.objects.select_related(*SELECT_RELATED).prefetch_related(
            'image_gallery__items__image',
            'model_line__image_gallery__items__image',
        )
        # ... filters, search, pagination ...
        data = [item.to_values_dict() for item in qs]
        return Response({'data': data, 'total': total, ...})


class MyDetailView(APIView):
    def get(self, request, pk):
        item = get_object_or_404(
            MyModel.objects.select_related(*SELECT_RELATED).prefetch_related(
                'image_gallery__items__image',
                'tech_docs',
                'model_line__image_gallery__items__image',
                'model_line__tech_docs',
            ),
            pk=pk,
        )
        return Response(item.to_dict())


class MySectionView(APIView):
    """Серии со счётчиками — 1 запрос."""
    def get(self, request):
        qs = ModelLine.objects.filter(
            related_name__is_active=True
        ).annotate(count=Count('related_name')).prefetch_related(
            'image_gallery__items__image'
        ).select_related('brand').order_by('name').distinct()
        for ml in qs:
            img = ml.image_gallery.get_default_image() if ml.image_gallery else None
            ...
```

### 4. URLs

```python
path('sections/', MySectionView.as_view()),
path('catalog/', MyCatalogView.as_view()),
path('catalog/<int:pk>/', MyDetailView.as_view()),
path('filters/', MyFilterOptionsView.as_view()),
path('quickselect/', MyQuickSelectView.as_view()),
```

## Фронтенд

### 1. endpoints.js

```javascript
myCatalog: {
    sections: '/my-catalog/sections/',
    catalog: '/my-catalog/catalog/',
    detail: (id) => `/my-catalog/catalog/${id}/`,
    filters: '/my-catalog/filters/',
    quickselect: '/my-catalog/quickselect/',
}
```

### 2. api.js

```javascript
import api from '@/shared/api'
import { ENDPOINTS } from '@/shared/endpoints'
const E = ENDPOINTS.myCatalog

export default {
  getSections()  { return api.get(E.sections) },
  list(params)   { return api.get(E.catalog, { params }) },
  getDetail(id)  { return api.get(E.detail(id)) },
  getFilters()   { return api.get(E.filters) },
  getQuickSelect(mlId, filters = {}) {
    return api.get(E.quickselect, { params: { model_line_id: mlId, ...filters } })
  },
}
```

### 3. App.vue

### 4. Shared-компоненты UI

- `PageTitle` — заголовок страницы (title + subtitle + context-чип «Серия XXX»)
- `CatalogActions` — кнопки «Инженерный подбор» / «Быстрый подбор»
- `Breadcrumbs` — все непоследние крошки кликабельны, emit `navigate`

Использовать Generic-компоненты из `shared/components/catalog/`:
- `CatalogSection` — сетка серий + CatalogActions
- `CatalogList` — инженерный подбор (фильтры + поиск)
- `CatalogModelLine` — товары серии (fixedParams + ?scope=model_line)
- `CatalogDetail` — карточка товара
- `QuickSelect` — быстрый подбор (чипсы → карточка)

## Чек-лист производительности

- [ ] `SELECT_RELATED` покрывает **все** FK, включая `image_gallery`, `model_line__image_gallery`
- [ ] `prefetch_related('image_gallery__items__image', 'model_line__image_gallery__items__image')` в list view
- [ ] `to_values_dict()` **не вызывает** `_get_template_vars()` (только лёгкий `tv`)
- [ ] `to_values_dict()` использует `_get_first_image()` из микcина (1 фото)
- [ ] `_gallery` — `@cached_property` в `ImageGalleryMixin`, не требует ручного кэша
- [ ] Section View: `image_gallery__items__image` в prefetch, не `images`
- [ ] Крошки трёхуровневые: Каталог / Оборудование / Страница
- [ ] `url()` хранилища (Cloud.ru) **не делает HEAD-запросов** — только `_normalize()`
- [ ] Удаление вызывает `MediaLibraryItem.delete()` → `file_service.delete_file()` для облака