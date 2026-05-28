# Шаблон нового каталога (Catalog Pattern)

## Три уровня API

| Страница | Эндпоинт | Сериализатор | Что внутри |
|----------|----------|-------------|------------|
| **Серии** | `GET /sections/` | Отдельный View с `annotate(Count)` | `id, name, code, count, image, brand` |
| **Список** | `GET /catalog/` | `to_values_dict()` — лёгкий | `id, name, code, 1 фото, model_line, sku` |
| **Карточка** | `GET /catalog/<id>/` | `to_dict()` — полный | Всё: sections, specs, gallery, docs, certs |

## Бэкенд

### 1. Модель (`models/`)

Наследовать от `CatalogDictMixin` (core/models/mixins.py):

```python
class MyModel(CatalogDictMixin, ImageGalleryMixin, TechDocMixin,
              SmartCatalogMixin, TemplateMixin, SKUMixin, CopyMixin,
              models.Model):
    ...
```

Обязательные методы:
- `_get_template_vars()` → `dict` — плоский словарь значений (для `to_dict()`)
- `_get_images_section()` → `list` — все фото (для `to_dict()`)
- `_get_docs_section()` → `list` — документация
- `_get_certs_section()` → `list` — сертификаты
- `_get_model_line_summary()` → `dict` — `{id, name, code, brand}`
- `_get_sku_summary()` → `dict` — `{id, code, name}`
- `to_dict()` → `dict` — полная структура с sections
- `_get_image_alt()` → `str` — alt-текст

❗ `_get_first_image()` уже есть в `CatalogDictMixin` — возвращает первое фото.
   Если модель использует `get_images()` (активные + сортировка) вместо `self.images.all()`,
   **переопределить** `_get_first_image()` (см. gearbox/models/gearbox.py).

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

### 2. View (`views/catalog.py`)

```python
SELECT_RELATED = [
    'model_line', 'model_line__brand',
    # ВСЕ ForeignKey, к которым обращается _get_template_vars()
]
```

```python
class MyCatalogView(APIView):
    def get(self, request):
        qs = MyModel.objects.select_related(*SELECT_RELATED).prefetch_related(
            'images', 'model_line__images',  # для _get_first_image
        )
        # ... filters, search, pagination ...
        data = [item.to_values_dict() for item in qs]
        return Response({'data': data, 'total': total, ...})


class MyDetailView(APIView):
    def get(self, request, pk):
        item = get_object_or_404(
            MyModel.objects.select_related(*SELECT_RELATED).prefetch_related(
                'images', 'tech_docs',
                'model_line__images', 'model_line__tech_docs',
            ),
            pk=pk,
        )
        return Response(item.to_dict())


class MySectionView(APIView):
    """Серии со счётчиками — 1 запрос."""
    def get(self, request):
        qs = ModelLine.objects.filter(
            related_name__is_active=True
        ).annotate(count=Count('related_name')).prefetch_related('images').order_by('name').distinct()
        ...
```

### 3. URLs

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

Использовать Generic-компоненты из `shared/components/catalog/`:
- `CatalogSection` — страница серий (автоматически использует `getSections()` если есть)
- `CatalogList` — список с фильтрами
- `CatalogDetail` — карточка товара
- `CatalogBrand` — товары серии/бренда
- `QuickSelect` — быстрый подбор

```html
<CatalogSection v-if="page === 'section'" :api="api" :labels="labels.section" ... />
<CatalogList v-else-if="page === 'list'" :api="api" :labels="labels.list" ... />
<CatalogDetail v-else-if="page === 'detail'" :api="api" :labels="labels.detail" :id="selectedId" ... />
<CatalogBrand v-else-if="page === 'brand'" :api="api" :labels="labels.brand" id-prop="model_line_id" :id-value="idValue" ... />
```

## Чек-лист производительности

- [ ] `SELECT_RELATED` покрывает **все** FK, к которым обращается `_get_template_vars()`
- [ ] `prefetch_related('images', 'model_line__images')` в list view
- [ ] `to_values_dict()` **не вызывает** `_get_template_vars()` (только лёгкий `tv`)
- [ ] `to_values_dict()` использует `_get_first_image()` (1 фото, не все)
- [ ] Для M2M-полей в `_get_template_vars()` — правильный доступ (`.all()` + цикл), не `.name` как у FK
- [ ] `_get_model_line_summary()` покрыто `select_related('model_line__brand')`
- [ ] `url()` хранилища (Cloud.ru) **не делает HEAD-запросов** — только `_normalize()`
