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
     'code_path': 'model_line_item__code', 'label': 'Артикул', 'group': 'general', 'order': 1},
    {'key': 'name', 'path': 'name', 'label': 'Название'},
    {'key': 'model_line_name', 'path': 'model_line__name', 'label': 'Серия', 'group': 'general', 'order': 2},
    {'key': 'brand_name', 'placeholder': '{brand}', 'path': 'model_line__brand__name',
     'name_path': 'model_line__brand', 'label': 'Бренд', 'group': 'general', 'order': 3},
    {'key': 'ip', 'placeholder': '{ip}', 'path': 'model_line__ip__name',
     'name_path': 'model_line__ip', 'label': 'IP', 'group': 'general', 'order': 5},
    {'key': 'exd', 'placeholder': '{exd}', 'path': 'get_exd_display',
     'code_path': 'exd_encoding',
     'label': 'Взрывозащита', 'group': 'general', 'order': 6},
    {'key': 'exd_short', 'placeholder': '{exd_short}', 'path': 'get_exd_short_list',
     'label': 'Взрывозащита (кратко)', 'group': 'general', 'order': 7},

    # ── Корпус ──
    {'key': 'thread', 'placeholder': '{thread}', 'path': 'thread_option__thread_size__name',
     'name_path': 'thread_option__thread_size', 'code_path': 'thread_encoding',
     'label': 'Резьба', 'group': 'body', 'order': 1},
    {'key': 'body_material', 'placeholder': '{body_material}', 'path': 'body_material_option__body_material__name',
     'name_path': 'body_material_option__body_material', 'code_path': 'body_material_encoding',
     'label': 'Материал корпуса', 'group': 'body', 'order': 2},
    {'key': 'cable_diameter', 'placeholder': '{cable_diameter}', 'path': 'get_cable_diameter_display',
     'label': 'Диаметр кабеля', 'unit': 'мм', 'group': 'body', 'order': 3},
    {'key': 'cable_diameter_outer', 'placeholder': '{cable_diameter_outer}', 'path': 'get_outer_cable_diameter_display',
     'label': 'Диаметр кабеля', 'unit': 'мм', 'group': 'body', 'order': 4},
    {'key': 'weight', 'placeholder': '{weight}', 'path': 'model_line_item__weight',
     'label': 'Вес', 'unit': 'кг', 'type': 'number', 'group': 'body', 'order': 5},

    # ── Крепление металлорукава / корпус (из «модели в серии») ──
    {'key': 'metal_sleeve_body_code', 'placeholder': '{metal_sleeve_body_code}',
     'path': 'model_line_item__metal_sleeve_body__code',
     'label': 'Крепление МР (код)', 'group': 'body', 'order': 6},
    {'key': 'metal_sleeve_inner', 'placeholder': '{metal_sleeve_inner}',
     'path': 'model_line_item__metal_sleeve_body__metal_sleeve_inner',
     'label': 'МР внутр. ⌀', 'unit': 'мм', 'group': 'body', 'order': 7},
    {'key': 'metal_sleeve_outer', 'placeholder': '{metal_sleeve_outer}',
     'path': 'model_line_item__metal_sleeve_body__metal_sleeve_outer',
     'label': 'МР внеш. ⌀', 'unit': 'мм', 'group': 'body', 'order': 8},
    {'key': 'metal_sleeve_range', 'placeholder': '{metal_sleeve_range}', 'path': 'get_metal_sleeve_range_display',
     'label': 'МР внутр./внеш. ⌀', 'unit': 'мм', 'group': 'body', 'order': 9},
    {'key': 'metal_sleeve', 'placeholder': '{metal_sleeve}', 'path': 'get_metal_sleeve_display',
     'label': 'Металлорукав', 'group': 'body', 'order': 10},
    {'key': 'body_code', 'placeholder': '{body_code}', 'path': 'model_line_item__body__code',
     'label': 'Корпус (код)', 'group': 'body', 'order': 11},

    # ── Условия эксплуатации ──
    {'key': 'temp_range', 'placeholder': '{temp_range}', 'path': 'get_temp_range_display',
     'label': 'Температура', 'unit': '°С', 'group': 'conditions', 'order': 1},
    {'key': 'cable_types', 'placeholder': '{cable_types}', 'path': 'get_applicable_cable_types_display',
     'label': 'Исполнение', 'group': 'conditions', 'order': 2},

    # ── Дополнительно ──
    {'key': 'extra_params', 'placeholder': '{extra_params}', 'path': 'get_extra_params',
     'label': 'Дополнительные параметры', 'group': 'extra', 'order': 1},

)
