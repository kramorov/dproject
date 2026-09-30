# PA Card Pattern — виртуальная карточка товара (ПП и сборки)

> Создано 2026-09-30.
> Описывает контракт «карточка товара» для конфигурируемого оборудования,
> у которого нет готового конечного списка артикулов (пневмоприводы, сборки).
> Связано: [`actuator_constructor_pattern.md`](actuator_constructor_pattern.md),
> [`CATALOG_PATTERN.md`](CATALOG_PATTERN.md), [`assy.md`](assy.md).

## Проблема

У готовых каталогов (фитинг, БКВ, редуктор…) карточка поиска — это существующий
артикул (`SKU`), и «открыть карточку» = открыть сохранённую деталку.

У ПП артикул появляется только после конфигурации (`серия × корпус × DA/SR × опции`),
а число комбинаций — произведение мощностей опций. Генерировать карточки на все
комбинации невозможно (комбинаторный взрыв), а для сборок из нескольких типов
оборудования — тем более (`N₁×N₂×…×Nₖ`).

## Решение

Не генерировать все карточки. **Карточка = payload `to_dict()`, который строится
на лету из конфигурации.** SKU материализуется только на commit (корзина/сборка).

- **`to_dict()`** — единый контракт карточки: подходит и сохранённому SKU,
  и виртуальному item.
- **`preview`** — собрать item в памяти без сохранения и вернуть `to_dict()`.
- **`commit`** — материализовать SKU в момент принятия решения.

## Контракт

### 1. `to_dict()` — единый payload карточки

`CatalogDictMixin.to_dict()` отдаёт `{id, code, name, model_line, sku, template_vars, sections}`;
`to_values_dict()` — обёртка для списков. Фронт рендерит **один** компонент карточки,
которому безразлично, персистентный это SKU или виртуальный item.

### 2. `preview` — виртуальная карточка (без сохранения)

Уже реализовано в `pneumatic_actuators/api/views_constructor.py`:

```python
item = PneumaticActuatorItem.from_constructor(obj)   # item в памяти, без save()
item.code = item.generated_model_item_code
item.name = item.generate_name()
item.description = item.generate_description()
data = item.to_dict()                                # карточка
data['tech_description'] = item.render_spec_html()
```

### 3. `commit` — материализация SKU

Только здесь происходит запись в БД:

```python
# create-sku / add-to-cart
sku = get_or_create_sku(mli, resolved_options)
```

## Применение

### Пневмопривод

```
мастер/селектор → model_line_item (корпус+DA/SR) → конфигуратор → preview → commit
```

- Результат подбора — `model_line_item` (не SKU). Клик по нему открывает
  конфигуратор с предвыбором.
- «Открыть карточку» для ПП = открыть конфигуратор (это действие, а не деталка);
  сама карточка отображается через `preview` → `to_dict()`.

### Сборки

- Базовый тип → `ComponentRequirement.selected_sku = FK(SKU)`.
- Составной тип → `selected_sku = null`; его «продукт» — разрешённое поддерево.
- `MBOM` — материализация `fixed`-сборки через SKU (обход `selected_sku`).
- Суб-SKU материализуются лениво в момент конфигурации/фиксации сборки.

## Чего НЕ делаем

- Не генерируем карточки на все комбинации (взрыв + сборки).
- Не создаём временный список карточек под «текущий товар» (плохая связка фронт↔бэк).

## Статус

- [x] `PneumaticActuatorItem.from_constructor()` + `to_dict()` + `render_spec_html()`
- [x] `preview` (без сохранения)
- [x] `create-sku` / `get_or_create_sku` (материализация на commit)
- [x] `SKU` — единый реестр номенклатуры; `MBOM` — производная `fixed`-сборки
- [ ] единый frontend-рендер карточки по `to_dict()` (persisted + virtual)
- [ ] результат мастера ПП = `model_line_item` → конфигуратор (кастомный results resolver)
