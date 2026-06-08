# Шаблон конструктора оборудования (Actuator Constructor Pattern)

> Обновлено 2026-06-08: создан на основе конструктора пневмоприводов.  
> Применим для электроприводов, редукторов и другого конфигурируемого оборудования.

## Концепция

Конструктор — это пошаговый wizard для сборки конфигурации оборудования.  
Пользователь выбирает серию → вид → модель → опции. Каждый шаг фильтрует следующий.  
Опции автозаполняются дефолтными значениями, код и описание генерируются автоматически.

В отличие от каталога (Catalog Pattern), здесь нет фильтрации по параметрам — есть **ограниченный набор опций**,
заданный через through-модели в админке. Пользователь не «ищет», а «собирает».

---

## Архитектура данных

### Модель конструктора — прямые FK на реальные опции

```python
class PneumaticActuatorConstructor(models.Model):
    selected_model_line = FK(PneumaticActuatorModelLine)       # шаг 1
    selected_model_line_item = FK(PneumaticActuatorModelLineItem)  # шаг 3
    selected_safety_position = FK(params.SafetyPositionOption)     # прямые FK
    selected_ip = FK(params.IpOption)
    selected_exd = FK(params.ExdOption)
    ...
```

### Through-модели — источник доступных опций и encoding

Through-модели (в `pa_options.py`) связывают `model_line` / `model_line_item` с реальными опциями:

| Through-модель | Родитель | Реальная опция |
|---|---|---|
| `PneumaticSafetyPositionOption` | `model_line_item` | `.safety_position` → `params.SafetyPositionOption` |
| `PneumaticIpOption` | `model_line` | `.ip_option` → `params.IpOption` |
| `PneumaticTemperatureOption` | `model_line` | сама опция (нет отдельной модели) |

**Важно**: encoding для генерации кода хранится в through-моделях (поле `encoding`), а не в `code` реальных опций.  
Например: `PneumaticSafetyPositionOption.encoding = "NO"`, но `SafetyPositionOption.code = "no"`.

### `_OPTION_CONFIG` — маппинг полей на through-модели

```python
_OPTION_CONFIG = {
    'selected_safety_position': {
        'through_model_path': 'pneumatic_actuators.models.pa_options.PneumaticSafetyPositionOption',
        'through_attr': 'safety_position',   # атрибут through-модели → реальная опция
        'parent_field': 'model_line_item',    # по кому фильтруем доступность
    },
    'selected_temperature': {
        'through_model_path': '...PneumaticTemperatureOption',
        'through_attr': None,                 # through-модель САМА опция
        'parent_field': 'model_line',
    },
    ...
}
```

---

## Бэкенд

### 1. Модель (`models/pa_actuator_constructor.py`)

**Обязательные методы:**

| Метод | Назначение |
|---|---|
| `get_available_options()` | Список доступных опций для модели (через through) |
| `_get_option_encoding(field)` | encoding из through-модели для генерации кода |
| `generated_model_item_code` (property) | Генерация артикула по шаблону model_line |
| `_generate_short_description()` | Краткое описание (в поле description) |
| `_generate_tech_description()` | Полное техописание с таблицей моментов |
| `get_description_data()` | Плоский словарь всех данных для описаний |
| `save()` | Валидация → дефолты → генерация → дубликаты |
| `_ensure_valid_options()` | Автозаполнение дефолтов + проверка валидности |
| `_set_default_option()` | Поиск through-записи с is_default=True → реальная опция |
| `_validate_option()` | Проверка через through-модель, замена на дефолт при невалидности |

### 2. API ViewSet (`api/views_constructor.py`)

```python
class ConstructorViewSet(viewsets.ModelViewSet):
    # CRUD: list, create, retrieve, update, destroy
    
    @action(detail=True, methods=['get'])
    def options(self, request, pk=None):
        """GET /constructor/{id}/options/ — доступные опции"""
        return Response(obj.get_available_options())

    @action(detail=False, methods=['post'])
    def preview(self, request):
        """POST /constructor/preview/ — код и описание без сохранения"""
        obj = PneumaticActuatorConstructor(...)  # временный инстанс
        obj._ensure_valid_options()
        return Response({'name': ..., 'code': ..., 'description': ..., 'tech_description': ...})

    @action(detail=False, methods=['get'])
    def model_lines(self, request):
        """GET /constructor/model_lines/ — список серий"""

    @action(detail=False, methods=['get'], url_path='model-lines/(?P<ml_id>[^/.]+)/items')
    def model_line_items(self, request, ml_id=None):
        """GET /constructor/model-lines/{id}/items/?variety=DA — модели серии"""
```

### 3. URLs (`urls.py`)

```python
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'constructor', ConstructorViewSet, basename='constructor')
urlpatterns = [path('', include(router.urls))]
```

### 4. Админка (`admin/pa_constructor_admin.py`)

```python
@admin.register(PneumaticActuatorConstructor)
class PneumaticActuatorConstructorAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', ...все опции..., 'description_preview']
    list_filter = ['is_active', 'selected_model_line', 'selected_model_line_item']
    autocomplete_fields = ['selected_model_line_item', 'selected_model_line']
    readonly_fields = ['name', 'code', 'is_unique']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'selected_model_line', 'selected_model_line_item',
            'selected_safety_position', 'selected_springs_qty',
            'selected_temperature', 'selected_ip', 'selected_exd',
            'selected_body_coating', 'selected_hand_wheel',
        )
```

---

## Фронтенд

### Структура мини-приложения

```
frontend/src/apps/actuator-constructor/
├── index.html          # точка входа
├── main.js             # монтирование Vue
├── api.js              # API-клиент
└── App.vue             # главный компонент-конструктор
```

### `api.js` — эндпоинты

```javascript
export default {
  list(params)           { return api.get(E.list, { params }) },
  getDetail(id)          { return api.get(E.detail(id)) },
  create(data)           { return api.post(E.list, data) },
  update(id, data)       { return api.put(E.detail(id), data) },
  delete(id)             { return api.delete(E.detail(id)) },
  getOptions(id)         { return api.get(E.options(id)) },
  preview(data)          { return api.post(E.preview, data) },
  getModelLines()        { return api.get(E.modelLines) },
  getModelLineItems(mlId, variety) { return api.get(E.modelLineItems(mlId, variety)) },
}
```

### `endpoints.js` — централизованные URL

```javascript
actuatorConstructor: {
    list:       '/pneumatic_actuators/constructor/',
    detail:     (id) => `/pneumatic_actuators/constructor/${id}/`,
    options:    (id) => `/pneumatic_actuators/constructor/${id}/options/`,
    preview:    '/pneumatic_actuators/constructor/preview/',
    modelLines: '/pneumatic_actuators/constructor/model_lines/',
    modelLineItems: (mlId, variety) => {
        let url = `/pneumatic_actuators/constructor/model-lines/${mlId}/items/`
        if (variety) url += `?variety=${variety}`
        return url
    },
},
```

### `App.vue` — поток конструктора

```
┌─ Шаг 1: Серия ───────────────────────────┐
│  <select v-model="form.selected_model_line">  │
└────────────────────────────────────────────┘
┌─ Шаг 2: DA/SR (появляется после серии) ──┐
│  <select v-model="form.selected_variety">     │
└────────────────────────────────────────────┘
┌─ Шаг 3: Модель (фильтруется) ────────────┐
│  <select v-model="form.selected_model_line_item">  │
└────────────────────────────────────────────┘
┌─ Шаг 4: Опции (автозаполнены дефолтами) ─┐
│  Селекты disabled если 1 опция            │
│  optionFields: computed из get_available_options() │
└────────────────────────────────────────────┘
┌─ Превью (live, через watch + /preview/) ──┐
│  Код: PA220SR.LT.NO.PTFE                  │
│  Описание: ...                             │
│  [📄 Просмотр] → модалка с полным техописанием │
└────────────────────────────────────────────┘
┌─ Кнопки ──────────────────────────────────┐
│  [Сохранить] [Сбросить]                    │
└────────────────────────────────────────────┘
┌─ Сохранённые конфигурации ────────────────┐
│  Карточки: клик → загрузка, × → удаление   │
└────────────────────────────────────────────┘
```

**Ключевые моменты фронтенда:**

1. **Каскад**: `onModelLineChange` → `onVarietyChange` → `onModelLineItemChange` → `onOptionsChange`
2. **Черновик**: при выборе модели создаётся POST (без опций), чтобы получить id для `/options/`
3. **Автозаполнение**: `autoFillDefaults()` — `is_default` или единственная опция
4. **Live preview**: `watch(form, {deep:true})` с дебаунсом 300мс → `POST /preview/`
5. **Опции — computed**: `optionFields` — маппинг из `options` в селекты, `disabled: items.length <= 1`
6. **Модалка**: `<Teleport>` с `v-html` для полного техописания (HTML-таблица моментов)

### Интеграция в SPA

```javascript
// pages/admin/ActuatorConstructorPage.vue — страница-обёртка
import ActuatorConstructorApp from '@/apps/actuator-constructor/App.vue'

// router/index.js — маршрут
{ path: '/admin/actuator-constructor', component: ..., meta: { role: 'admin' } }

// TopMenu.vue — пункт меню
{ to:'/admin/actuator-constructor', label:'🔧 Конструктор приводов' }
```

---

## Особенности, важные для повторения

### 1. encoding vs code

**Проблема**: реальные опции (`params.SafetyPositionOption.code = "no"`) содержат не те значения, что нужны для артикула.  
**Решение**: encoding хранится в through-моделях (`PneumaticSafetyPositionOption.encoding = "NO"`).  
**Метод**: `_get_option_encoding(field_name)` — по ID опции + родителю находит through-запись, возвращает `.encoding`.

### 2. Превью без сохранения

`POST /preview/` создаёт **временный** инстанс модели, заполняет дефолты, генерирует код/описание — и **не сохраняет** в базу.  
Фронтенд вызывает preview при каждом изменении (debounce 300ms).

### 3. Дефолты и единственная опция

- Если опция помечена `is_default=True` в through-модели → авто-выбрана
- Если для модели доступна только 1 опция → авто-выбрана + селект заблокирован (`disabled`)
- «Не указано» в селектах опций не показывается — конструктор всегда имеет выбранную опцию

### 4. Оптимизация загрузки

- `getDetail` НЕ включает `get_structured_data()` (тяжёлые расчёты) — они только в `/preview/`
- `select_related` на все FK опций в ViewSet и админке
- Дебаунс на preview (300ms) чтобы не спамить при быстрой смене опций

### 5. Чек-лист для нового конструктора

- [ ] Модель: прямые FK на реальные опции + `selected_model_line` + `selected_model_line_item`
- [ ] `_OPTION_CONFIG` с `through_model_path`, `through_attr`, `parent_field`
- [ ] `get_available_options()` через through-модели с `option_id`
- [ ] `_get_option_encoding()` для генерации кода
- [ ] `generated_model_item_code` (property) + `_generate_fallback_code()`
- [ ] `_generate_short_description()` + `_generate_tech_description()`
- [ ] `save()`: валидация → дефолты → генерация → дубликаты
- [ ] ViewSet: CRUD + `options` + `preview` + `model_lines` + `model_line_items`
- [ ] URLs через DRF router
- [ ] Admin: list_display с опциями, select_related, autocomplete_fields
- [ ] Фронтенд App.vue: каскад серия→вид→модель→опции
- [ ] `autoFillDefaults()` + disabled при 1 опции
- [ ] Live preview через `watch` + `/preview/`
- [ ] Модалка с полным техописанием
- [ ] Сохранённые конфигурации (лента слева/сверху)
- [ ] Интеграция в SPA: page-wrapper + router + TopMenu
- [ ] Vite config: точка входа для standalone-сборки
