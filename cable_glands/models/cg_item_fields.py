# cable_glands/models/cg_item_fields.py
"""Реестр полей артикула CableGland — единый источник правды.

Паттерн: core TEMPLATE_FIELDS (см. template_mixin.md §7).

- ``path`` — display-значение (для template_vars/specs/`_get_value`);
- ``name_path`` — отдельный путь для подстановки в имя/описание, если display
  отличается (шаблоны подставляют ``str(obj)`` FK, а VARS/specs — имя);
- ``code_path`` — encoding-значение для автогенерации артикула
  (``model_line.model_item_code_template``).

Составы словарей заданы в модели списками ключей:
``NAME_FIELD_KEYS`` / ``CODE_FIELD_KEYS`` / ``VARS_FIELD_KEYS`` / ``SPEC_FIELD_KEYS``;
метаданные ``label``/``unit``/``type``/``order``/``group`` использует
``_get_spec_sections()`` (CatalogSerializerMixin).
"""

CG_ITEM_TEMPLATE_FIELDS = (
    # ── Общие / template_vars ──
    {'key': 'code', 'placeholder': '{model_code}', 'path': 'code',
     'code_path': 'model_line__code', 'label': 'Артикул', 'group': 'general', 'order': 1},
    {'key': 'name', 'path': 'name', 'label': 'Название'},
    {'key': 'model_line_name', 'path': 'model_line__name', 'label': 'Серия', 'group': 'general', 'order': 2},
    {'key': 'brand_name', 'placeholder': '{brand}', 'path': 'model_line__brand__name',
     'name_path': 'model_line__brand', 'label': 'Бренд', 'group': 'general', 'order': 3},
    {'key': 'size', 'placeholder': '{size}', 'path': 'model_line_item__code',
     'code_path': 'model_line_item__code', 'label': 'Размер/исполнение', 'group': 'general', 'order': 4},
    {'key': 'ip', 'placeholder': '{ip}', 'path': 'model_line__ip__name',
     'name_path': 'model_line__ip', 'label': 'IP', 'group': 'general', 'order': 5},
    {'key': 'exd', 'placeholder': '{exd}', 'path': 'get_exd_display',
     'label': 'Взрывозащита', 'group': 'general', 'order': 6},

    # ── Корпус ──
    {'key': 'thread', 'placeholder': '{thread}', 'path': 'thread__name',
     'name_path': 'thread', 'code_path': 'thread__code',
     'label': 'Резьба', 'group': 'body', 'order': 1},
    {'key': 'body_material', 'placeholder': '{body_material}', 'path': 'body_material__name',
     'name_path': 'body_material', 'code_path': 'body_material__code',
     'label': 'Материал корпуса', 'group': 'body', 'order': 2},
    {'key': 'cable_diameter', 'placeholder': '{cable_diameter}', 'path': 'get_cable_diameter_display',
     'label': 'Диаметр кабеля', 'unit': 'мм', 'group': 'body', 'order': 3},
    {'key': 'weight', 'placeholder': '{weight}', 'path': 'model_line_item__weight',
     'label': 'Вес', 'unit': 'кг', 'type': 'number', 'group': 'body', 'order': 4},

    # ── Условия эксплуатации ──
    {'key': 'temp_range', 'placeholder': '{temp_range}', 'path': 'get_temp_range_display',
     'label': 'Температура', 'unit': '°С', 'group': 'conditions', 'order': 1},
    {'key': 'flags', 'placeholder': '{flags}', 'path': 'get_cable_flags_display',
     'label': 'Исполнение', 'group': 'conditions', 'order': 2},
)
