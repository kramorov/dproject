# gearbox/models/gb_item_fields.py
"""Реестр полей GearBox — единый источник правды.

Каждый вариант значения — отдельная запись. ``path`` даёт отображаемое значение
(для `template_vars`/`specs`, включая ``@property`` и пути ``__name`` через FK);
``name_path`` — отдельный путь для подстановки в имя/описание (если отличается
от display-пути: шаблоны подставляют ``str(obj)`` FK, а VARS/specs — имя).
``code_path``/``CODE_FIELD_KEYS`` не используются: у GearBoxModelLine нет
``model_item_code_template`` (артикул не генерируется).

Составы словарей задаются в модели списками ключей:
``NAME_FIELD_KEYS`` / ``VARS_FIELD_KEYS`` / ``SPEC_FIELD_KEYS``;
метаданные ``label``/``unit``/``type``/``order``/``group`` использует
``_get_spec_sections()``.
"""

GB_ITEM_TEMPLATE_FIELDS = (
    # ── Общие / template_vars ──
    {'key': 'code', 'placeholder': '{model_code}', 'path': 'code'},
    {'key': 'name', 'path': 'name'},
    {'key': 'model_line_name', 'path': 'model_line__name', 'label': 'Серия', 'group': 'general', 'order': 1},
    {'key': 'brand_name', 'placeholder': '{brand}', 'path': 'model_line__brand__name',
     'name_path': 'model_line__brand', 'label': 'Бренд', 'group': 'general', 'order': 2},

    # ── Основные ──
    {'key': 'body_material', 'placeholder': '{body_material_text}', 'path': 'body_material_text',
     'label': 'Материал корпуса', 'group': 'general', 'order': 3},
    {'key': 'ip', 'placeholder': '{ip}', 'path': 'ip__name', 'name_path': 'ip',
     'label': 'IP', 'group': 'general', 'order': 4},
    {'key': 'override_mechanism', 'placeholder': '{override_mechanism}', 'path': 'override_mechanism__name',
     'name_path': 'override_mechanism', 'label': 'Механизм отключения', 'group': 'general', 'order': 5},
    {'key': 'locking_mechanism', 'placeholder': '{locking_mechanism}', 'path': 'locking_mechanism__name',
     'name_path': 'locking_mechanism', 'label': 'Механизм блокировки', 'group': 'general', 'order': 6},
    {'key': 'is_declutchable', 'placeholder': '{is_declutchable}', 'path': 'is_declutchable_display',
     'label': 'Расцепляемый', 'group': 'general', 'order': 7},

    # ── Корпус ──
    {'key': 'transmission_variety', 'placeholder': '{transmission_variety}',
     'path': 'body__transmission_variety__name', 'name_path': 'body__transmission_variety',
     'label': 'Тип передачи', 'group': 'body', 'order': 1},
    {'key': 'reduction_ratio', 'placeholder': '{reduction_ratio_text}', 'path': 'body__reduction_ratio_text',
     'label': 'Передаточное число', 'group': 'body', 'order': 2},
    {'key': 'max_output_torque', 'placeholder': '{max_output_torque}', 'path': 'body__max_output_torque',
     'label': 'Макс. момент на выходе', 'unit': 'Нм', 'type': 'number', 'group': 'body', 'order': 3},
    {'key': 'max_input_torque', 'placeholder': '{max_input_torque}', 'path': 'body__max_input_torque',
     'label': 'Макс. входной момент', 'unit': 'Нм', 'type': 'number', 'group': 'body', 'order': 4},
    {'key': 'weight', 'placeholder': '{weight}', 'path': 'body__weight',
     'label': 'Вес', 'unit': 'кг', 'type': 'number', 'group': 'body', 'order': 5},
    {'key': 'handwheel_diameter', 'placeholder': '{handwheel_diameter}', 'path': 'body__handwheel_diameter',
     'label': 'Диаметр штурвала', 'unit': 'мм', 'type': 'number', 'group': 'body', 'order': 6},

    # ── Условия эксплуатации ──
    {'key': 'work_temp', 'path': 'work_temp_display',
     'label': 'Рабочая температура', 'group': 'conditions', 'order': 1},

    # ── VARS без секций ──
    {'key': 'handwheel_force_nominal', 'placeholder': '{handwheel_force_nominal}',
     'path': 'body__handwheel_force_nominal'},
    {'key': 'interlock', 'placeholder': '{interlock}', 'path': 'interlock__name', 'name_path': 'interlock'},
    {'key': 'work_temp_min', 'placeholder': '{work_temp_min}', 'path': 'work_temp_min'},
    {'key': 'work_temp_max', 'placeholder': '{work_temp_max}', 'path': 'work_temp_max'},

    # ── Только имя/описание ──
    {'key': 'gearbox_output_variety', 'placeholder': '{gearbox_output_variety}',
     'path': 'model_line__gearbox_output_variety'},
    {'key': 'gearbox_variety', 'placeholder': '{gearbox_variety}', 'path': 'model_line__gearbox_variety'},
    {'key': 'turn_angle', 'placeholder': '{turn_angle}', 'path': 'model_line__turn_angle'},
    {'key': 'turn_tuning_limit', 'placeholder': '{turn_tuning_limit}', 'path': 'model_line__turn_tuning_limit'},
    {'key': 'mechanical_advantage', 'placeholder': '{mechanical_advantage}', 'path': 'body__mechanical_advantage'},
    {'key': 'max_stem_diameter_bottom', 'placeholder': '{max_stem_diameter_bottom}',
     'path': 'body__max_stem_diameter_bottom'},
    {'key': 'stem_height_bottom', 'placeholder': '{stem_height_bottom}', 'path': 'body__stem_height_bottom'},
    {'key': 'stem_size_bottom', 'placeholder': '{stem_size_bottom}', 'path': 'body__stem_size_bottom'},
    {'key': 'stem_shape_bottom', 'placeholder': '{stem_shape_bottom}', 'path': 'body__stem_shape_bottom'},
    {'key': 'mounting_plate_bottom_list_text', 'placeholder': '{mounting_plate_bottom_list_text}',
     'path': 'body__mounting_plate_bottom_list_text'},
    {'key': 'stem_height_top', 'placeholder': '{stem_height_top}', 'path': 'body__stem_height_top'},
    {'key': 'stem_size_top', 'placeholder': '{stem_size_top}', 'path': 'body__stem_size_top'},
    {'key': 'stem_shape_top', 'placeholder': '{stem_shape_top}', 'path': 'body__stem_shape_top'},
    {'key': 'mounting_plate_top_list_text', 'placeholder': '{mounting_plate_top_list_text}',
     'path': 'body__mounting_plate_top_list_text'},
    {'key': 'efficiency', 'placeholder': '{efficiency}', 'path': 'body__efficiency'},
    {'key': 'amplification_factor', 'placeholder': '{amplification_factor}', 'path': 'body__amplification_factor'},
)
