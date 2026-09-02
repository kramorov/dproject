# TemplateMixin — единый контракт генерации названий и описаний каталога

> Файл документации для новых приложений-каталогов проекта.
> Код миксина: `core/models/mixins.py` (класс `TemplateMixin`).
> Эталонные реализации: `DirectionValve` (solenoid_valves), `FilterRegulator`,
> `GearBox`, `PneumaticFitting`, `LimitSwitchBox`, `PosiModelLineItem`,
> `PneumaticActuatorItem` (pneumatic_actuators, включая опции и автогенерацию артикула).

---

## 1. Концепция

Один механизм для всех каталогов:

- **Шаблоны текста живут на серии** (`model_line`): поля `name_template`, `description_template`.
- **Артикул каталога** (item) отвечает только за **словарь подстановок** `_get_data_dict()` — «плейсхолдер → путь к характеристике».
- **Генерация выполняется при сохранении** (`save()` → `TemplateMixin.save()`), результат записывается в поля `name`/`description` и может быть отредактирован шаблоном в любой момент.

Цепочка источника шаблона (приоритет сверху вниз):

```
_get_name_template_source()        ← переопределение модели (обычно model_line)
  → _get_default_name_template()   ← fallback-текст в модели
Для title дополнительно:
  → EquipmentType.title_template   ← глобальная настройка типа оборудования
```

---

## 2. Обязательные паттерны для нового приложения

### 2.1. Модель серии (model_line)

```python
class MyModelLine(ImageGalleryMixin, TechDocMixin, CertDocMixin,
                  EquipmentTypeMixin, StructuredDataMixin, models.Model):
    name = models.CharField(...)
    code = models.CharField(...)
    description = models.TextField(blank=True, ...)

    # ОБЯЗАТЕЛЬНО: шаблоны текста каталога
    name_template = models.TextField(blank=True, null=True,
                                     verbose_name=_("Шаблон названия"))
    description_template = models.TextField(blank=True, null=True,
                                            verbose_name=_("Шаблон описания"))

    brand = models.ForeignKey(Brands, ...)
    # EquipmentTypeMixin даёт поле equipment_type — используется
    # для title-цепочки (EquipmentType.title_template) и для SKU.
```

### 2.2. Модель артикула (item)

Стек миксинов — в этом порядке:

```python
class MyItem(CatalogDictMixin, ImageGalleryMixin, TechDocMixin,
             SKUMixin, CopyMixin, TemplateMixin,
             SmartCatalogMixin, EquipmentTypeMixin, models.Model):
```

Обязательные переопределения item:

```python
    # ── Шаблоны: источник — model_line ──
    def _get_name_template_source(self):
        if not self.model_line:
            return None
        return self.model_line.name_template or None

    def _get_description_template_source(self):
        if not self.model_line:
            return None
        return self.model_line.description_template or None

    # ── Fallback-тексты (используются, если шаблон серии не задан) ──
    def _get_default_name_template(self) -> str:
        return "{model_code} Наименование {brand}; ..."

    def _get_default_description_template(self) -> str:
        return "{model_code} ...полный текст характеристик..."

    # ── СЛОВАРЬ ПОДСТАНОВОК: ОБЯЗАТЕЛЕН ──
    def _get_data_dict(self) -> Dict[str, str]:
        return {
            '{model_code}': 'code',            # ОБЯЗАТЕЛЕН всегда
            '{brand}': 'model_line__brand',
            '{weight}': 'body__weight',        # связь через __
            '{ip}': 'ip',                      # FK (подставится str(obj))
            '{temp_range}': 'temperature_range_display',  # @property
            # '{json_val}': 'extra_params.some_key',      # JSON-поле через .
        }

    # ── SKU: создаётся из этой модели (стандартный путь) ──
    def get_equipment_type_for_sku(self):
        return self.model_line.equipment_type if self.model_line else None

    def get_brand_for_sku(self):
        return self.model_line.brand if self.model_line else None

    # ── Сохранение: генерация + SKU ──
    def save(self, *args, **kwargs):
        # (опционально: автозаполнение equipment_type из model_line,
        #  если поле обязательное)
        super().save(*args, **kwargs)   # цепочка → TemplateMixin.save()
        self.sync_sku()

    # ── Сериализация для фронта ──
    def _get_template_vars(self) -> Dict[str, str]: ...
    def to_dict(self): ...      # 'title': self.generate_title(), ...
    def to_values_dict(self): ...  # 'title': self.generate_title() or self.name or ''
```

### 2.3. Анти-паттерны (ЗАПРЕЩЕНО)

- **Не объявлять на item поля `name_template` / `description_template` / `title_template`** — они затеняют одноимённые property миксина (проверено на реальном баге: поле `DeferredAttribute` перекрывало property, fallback-цепочка молча отключалась). Шаблоны — только на model_line.
- **Не писать собственный рендер строк** (`str.replace`, ручная склейка) — только `_fill_template()` / `_get_value()`.
- **Не наследовать устаревший `TemplateGeneratorMixin`** — он удалён; есть только `TemplateMixin`.
- **Не пропускать `_get_data_dict`** — это обязательный контракт каждой модели.
- Плейсхолдеры: `{model_code}` должен присутствовать всегда; значения — пути (см. 2.4).
- Модели-справочники (body, options, variety) миксин **не наследуют** — он только для артикулов каталога.

### 2.4. Правила путей в `_get_data_dict`

`_get_value(path)` поддерживает:

- поле: `'code'` → `str(self.code)`;
- связь: `'model_line__brand'` → по цепочке FK;
- JSON: `'extra_params.some_key'` → значение из JSONField;
- `@property`-геттер: `'temperature_range_display'` — вычисляется при подстановке;
- комбинации: `'body__extra_params.cable_glands_holes'`.

**Zero-arg методы НЕ вызываются** (нужен именно `@property`).

---

## 3. Как пользоваться

### 3.1. Генерация

- При `save()` артикула name/description пересобираются автоматически (если не передан `skip_auto_generate=True`).
- Программно:

```python
obj.generate_name()              # строка из текущего шаблона
obj.generate_description()
obj.generate_title()             # EquipmentType.title_template → default '{model_code}'
obj.update_from_templates(save=True)     # перезаписать поля и сохранить
obj.update_name_from_template()          # только при заданном шаблоне серии
obj.save(skip_auto_generate=True)        # сохранить БЕЗ перегенерации
```

- Массовая перегенерация по всем каталогам:

```bash
python manage.py regenerate_catalog_descriptions                 # все каталоги
python manage.py regenerate_catalog_descriptions --model gearbox.GearBox
python manage.py regenerate_catalog_descriptions --inactive      # включая неактивные
```

### 3.2. Шаблоны серии

Пример (`description_template`):

```
{model_code} Пневмораспределитель {brand} {function} {operation};
корпус: {body_material}; уплотнение {sealing_material_specified};
P {pressure_range} бар; T {temperature_range}°С; {exd}; {ip}; {power_supply};
```

Правила:

- плейсхолдер, отсутствующий в `_get_data_dict`, заменяется пустой строкой (с warning в консоль);
- текст без плейсхолдеров возвращается как есть;
- в `_get_data_dict` описывайте **все характеристики модели** — это единственный источник правды для шаблонов (недостающее добавить в словарь, а не хардкодить в шаблон).

### 3.3. Артикул с опциями (pattern pneumatic_actuators / позиционеров / электроприводов)

Если артикул собирается из кода модели + encodings опций (как `PneumaticActuatorItem`
и `PosiModelLineItem`):

- шаблон артикула хранится на серии: `model_line.model_item_code_template`
  (например `'MOD.{model_code}.{springs_qty}.{ip}'`);
- рендер — тем же `_fill_template()` с отдельным словарём `_get_code_data_dict()`,
  где значения — encoding опций из through-моделей;
- в `save()` артикул автозаполняется, если `code` пуст;
- дедупликация SKU — по итоговому коду (см. `sku_service.get_or_create_sku`);
- **шаблон артикула обязан различать конфигурации**: если в нём нет плейсхолдеров
  опций, все конфигурации серии получат один код и одну SKU.

### 3.4. SKU

SKU создаётся/обновляется автоматически из item (`SKUMixin.sync_sku()` в `save()`):
code/name/description/equipment_type/brand/привязка `source_*` — всё из модели.
Повторный save той же модели — та же SKU (по коду).

---

## 4. Как применять в админке

### 4.1. Админка серии: поля шаблонов + справочник плейсхолдеров

```python
# my_app/admin.py
from core.admin_template_placeholders import TemplatePlaceholdersAdminMixin

@admin.register(MyModelLine)
class MyModelLineAdmin(TemplatePlaceholdersAdminMixin, admin.ModelAdmin):
    template_item_model = MyItem   # модель-артикул — источник _get_data_dict()

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'code', 'brand', 'equipment_type',
                       ('name_template', 'description_template'), 'description'),
        }),
        ...
    )
```

`TemplatePlaceholdersAdminMixin` автоматически:

- добавляет в форму readonly-блок **«Справочник плейсхолдеров»** — чипы со всеми
  ключами из `_get_data_dict()` модели-артикула;
- клик по чипу **вставляет плейсхолдер в последнее выбранное поле шаблона**
  (Название/Описание) и копирует в буфер обмена;
- кнопка **«Скопировать все»** — весь список в буфер;
- подсказывает: не хватает характеристики — добавить её в `_get_data_dict()`.

Чтобы блок рендерился **внутри** конкретного fieldset'а (например, рядом с
полями шаблонов), задайте его заголовок:

```python
class MyModelLineAdmin(TemplatePlaceholdersAdminMixin, admin.ModelAdmin):
    template_item_model = MyItem
    template_placeholders_fieldset = _('Шаблоны')   # блок — в этот fieldset
```

### 4.2. Админка артикула

```python
from core.models.mixins import AdminCopyMixin

@admin.register(MyItem)
class MyItemAdmin(AdminCopyMixin, admin.ModelAdmin):
    actions = ['copy_selected_objects']   # копирование (CopyMixin сбрасывает sku —
                                          # sync_sku() создаст новую привязку)
    readonly_fields = ('sku',)            # SKU управляется sync_sku()
    fieldsets = (
        (_('Основная информация'), {'fields': ('model_line', 'body', ('code', 'name', 'description'))}),
        (_('Номенклатура и медиа'), {'fields': ('equipment_type', 'sku', 'image_gallery', 'tech_docs')}),
        (_('Настройки'), {'fields': ('sorting_order', 'is_active', 'extra_params')}),
    )
```

---

## 5. Полный минимальный пример

```python
# my_app/models.py
from core.models.mixins import CatalogDictMixin, CopyMixin, TemplateMixin
from core.models import ImageGalleryMixin, TechDocMixin, EquipmentTypeMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin
from sku.models import SKUMixin

class MyModelLine(ImageGalleryMixin, TechDocMixin, EquipmentTypeMixin, models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True)
    name_template = models.TextField(blank=True, null=True)
    description_template = models.TextField(blank=True, null=True)
    brand = models.ForeignKey('producers.Brands', null=True, blank=True, on_delete=models.SET_NULL)

class MyItem(CatalogDictMixin, ImageGalleryMixin, TechDocMixin, SKUMixin,
             CopyMixin, TemplateMixin, SmartCatalogMixin, EquipmentTypeMixin, models.Model):
    name = models.TextField(blank=True)
    code = models.CharField(max_length=150, blank=True, null=True)
    description = models.TextField(blank=True)
    sorting_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    model_line = models.ForeignKey(MyModelLine, null=True, blank=True, on_delete=models.SET_NULL)
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    def _get_name_template_source(self):
        return self.model_line.name_template or None if self.model_line else None

    def _get_description_template_source(self):
        return self.model_line.description_template or None if self.model_line else None

    def _get_default_name_template(self):
        return "{model_code} {brand}"

    def _get_default_description_template(self):
        return "{model_code} {brand}, вес {weight} кг"

    def _get_data_dict(self):
        return {
            '{model_code}': 'code',
            '{brand}': 'model_line__brand',
            '{weight}': 'weight',
        }

    def get_equipment_type_for_sku(self):
        return self.model_line.equipment_type if self.model_line else None

    def get_brand_for_sku(self):
        return self.model_line.brand if self.model_line else None

    def save(self, *args, **kwargs):
        if not self.equipment_type_id and self.model_line and self.model_line.equipment_type_id:
            self.equipment_type = self.model_line.equipment_type
        super().save(*args, **kwargs)
        self.sync_sku()

    def to_values_dict(self):
        return {
            'id': self.id, 'code': self.code or '', 'name': self.name or '',
            'title': self.generate_title() or self.name or '',
            'sku': {'id': self.sku.id, 'code': self.sku.code} if self.sku else None,
        }
```

---

## 6. Справочник методов TemplateMixin

| Метод | Назначение |
|---|---|
| `name_template` / `description_template` / `title_template` | property-цепочка источника шаблона |
| `_get_name_template_source()` и др. | переопределить: вернуть шаблон или `None` |
| `_get_default_name_template()` и др. | fallback-текст модели |
| `_get_data_dict()` | **обязательный** словарь плейсхолдер → путь |
| `_fill_template(template, data_dict)` | рендер (не вызывать вручную без нужды) |
| `_get_value(path)` | чтение значения по пути |
| `generate_name()` / `generate_description()` / `generate_title()` | строки без записи в БД |
| `update_name()` / `update_description()` / `update_from_templates(save=)` | запись в поля |
| `update_name_from_template()` | только при заданном шаблоне model_line |
| `generated_model_name_description('name'/'description')` | генерация напрямую из шаблона model_line |
| `_process_m2m_field(manager, item_template)` | склейка M2M-значений в шаблоне |
| `save(skip_auto_generate=...)` | автогенерация при сохранении |

Связанные механизмы: `SKUMixin` (SKU из модели), `CatalogDictMixin` (`to_dict`/`to_values_dict`), `CopyMixin`/`AdminCopyMixin` (копирование), `EquipmentType.title_template` (глобальный title), management-команда `regenerate_catalog_descriptions`.
