# pneumatic_fittings — Пневматические фитинги

Каталог пневматических фитингов (штуцера, переходники, цанговые соединения).

**Дата:** 2026-05-20

---

## Модели

### FittingShape
Форма фитинга: прямой, угловой, тройник, угловой 45°...  
Поля: `name`, `code`, `is_swivel` (поворотный).

### FittingFixationMethod
Способ фиксации: цанговый (push-in), обжимной (компрессионный)...  
Поля: `name`, `code`.

### PneumaticFittingVariety
Разновидность конструкции — комбинация формы и способа фиксации.  
Поля: `name`, `code`, `shape` (FK → FittingShape), `fixation_method` (FK → FittingFixationMethod).

> **TODO:** Рассмотреть перенос FK на shape и fixation_method напрямую в PneumaticFitting.

### PneumaticFittingModelLine
Серия фитингов (напр. «Серия QS» от Festo).  
Поля: `name`, `brand`, `work_temp_min/max`, `pressure_min/max`, `body_material`, `pipe_material`.

### PneumaticFitting
Конкретный артикул фитинга.  
Наследует: `SmartCatalogMixin`, `StructuredDataMixin`, `TemplateMixin`, `CopyMixin`.

```
PneumaticFitting
├── name, code, description
├── model_line (FK)      → PneumaticFittingModelLine
├── fitting_variety (FK) → PneumaticFittingVariety
├── brand (FK)           → Brands
├── pipe_diameter        — диаметр трубки
├── body_material (FK)   → MaterialGeneral
├── pipe_material (FK)   → MaterialGeneral
├── thread (FK)          → ThreadSize
├── thread_inner_outer(FK) → ThreadInnerOuter
├── temp_min / temp_max  — ⚠️ дублирует model_line (см. TODO)
└── is_active
```

---

## TODO

### Разбить fitting_variety
`PneumaticFittingVariety` — комбинированный справочник (форма + фиксация).  
Правильнее: FK на `FittingShape` и `FittingFixationMethod` напрямую в `PneumaticFitting`.

**Плюсы:** атомарная фильтрация, не надо плодить комбинации.  
**Минусы:** миграция данных, три дропдауна вместо одного.

### temp_min / temp_max
Дублируют `model_line.work_temp_min/max`. Идея: если поля пустые — брать из model_line.  
Сейчас заполнены вручную (shell: update из model_line). Нужно автоматизировать при импорте.

---

## Фильтрация (SmartCatalogMixin)

```
FILTER_DEFINITIONS:
  brand_id, fitting_model_line_id, fitting_variety_id,
  body_material_id, pipe_material_id, pipe_diameter,
  thread_id, thread_type_id, thread_inner_outer_id,
  temp_min (TEMP_MIN → __lte)
```

Поиск: `code`.

---

## API

Список через UniversalAPIView:
```
GET /api/core/?model=pneumatic_fittings.PneumaticFitting&fmt=compact
```

Streamlit-каталог: `pages/fittings_catalog.py`

---

## Streamlit-каталог (fittings_catalog.py)

Фильтры: поиск, бренд, серия, разновидность, материал, диаметр, резьба, температура.  
Использует `PneumaticFitting.filter_by_params()`.
