# filter_regulator/models/fr_item_fields.py
"""Реестр полей FilterRegulator — единый источник правды.

Каждый вариант значения — отдельная запись. ``path`` даёт отображаемое значение
(для `template_vars`/`specs`, включая ``@property`` и пути ``__name`` через FK);
``name_path`` — отдельный путь для подстановки в имя/описание (если отличается
от display-пути: шаблоны подставляют ``str(obj)`` FK, а VARS/specs — имя).
``code_path``/``CODE_FIELD_KEYS`` не используются: у FilterRegulatorModelLine
нет ``model_item_code_template`` (артикул не генерируется).

Составы словарей задаются в модели списками ключей:
``NAME_FIELD_KEYS`` / ``VARS_FIELD_KEYS`` / ``SPEC_FIELD_KEYS``;
метаданные ``label``/``unit``/``type``/``order``/``group`` использует
``_get_spec_sections()``.
"""

FR_ITEM_TEMPLATE_FIELDS = (
    # ── Общие / template_vars ──
    {'key': 'code', 'placeholder': '{model_code}', 'path': 'code'},
    {'key': 'name', 'path': 'name'},
    {'key': 'model_line_name', 'path': 'model_line__name', },
    {'key': 'brand_name', 'placeholder': '{brand}', 'path': 'model_line__brand__name',
     'name_path': 'model_line__brand', },

    # ── Основные ──
    {'key': 'filter_variety', 'placeholder': '{filter_variety}', 'path': 'model_line__filter_variety__name',
     'name_path': 'model_line__filter_variety', },
    {'key': 'body_material', 'placeholder': '{body_material}', 'path': 'model_line__body_material_text',
     },
    {'key': 'bowl_material', 'placeholder': '{bowl_material}', 'path': 'model_line__bowl_material_text',
     },
    {'key': 'protection_material', 'placeholder': '{protection_material}',
     'path': 'model_line__protection_material', },
    {'key': 'ip', 'path': 'ip__name', },
    {'key': 'filtration_rating', 'placeholder': '{filtration_rating}', 'path': 'filtration_rating',
     },
    {'key': 'flow_rate', 'placeholder': '{flow_rate}', 'path': 'flow_rate',
     },
    {'key': 'filter_element_material', 'placeholder': '{filter_element_material}',
     'path': 'filter_element_material_display', 'name_path': 'filter_element_material',
     },

    # ── Давление ──
    {'key': 'pressure_range', 'path': 'pressure_range_display',
     },
    {'key': 'pressure_inlet_max', 'placeholder': '{pressure_inlet_max}',
     'path': 'model_line__pressure_inlet_max',
     },

    # ── Корпус ──
    {'key': 'weight', 'placeholder': '{weight}', 'path': 'body__weight',
     },
    {'key': 'thread', 'placeholder': '{thread}', 'path': 'body__thread__name', 'name_path': 'body__thread',
     },
    {'key': 'gauge_port_size', 'placeholder': '{gauge_port_size}', 'path': 'body__gauge_port_size__name',
     'name_path': 'body__gauge_port_size', },
    {'key': 'drain_port_size', 'placeholder': '{drain_port_size}', 'path': 'body__drain_port_size__name',
     'name_path': 'body__drain_port_size', },
    {'key': 'wall_mounting_included', 'placeholder': '{wall_mounting_included}',
     'path': 'wall_mounting_included_display', },
    {'key': 'has_shut_off_valve', 'path': 'has_shut_off_valve_display',
     },

    # ── Условия эксплуатации ──
    {'key': 'work_temp', 'path': 'work_temp_display',
     },

    # ── Только имя/описание ──
    {'key': 'pressure_min', 'placeholder': '{pressure_min}', 'path': 'model_line__pressure_min'},
    {'key': 'pressure_max', 'placeholder': '{pressure_max}', 'path': 'model_line__pressure_max'},
    {'key': 'work_temp_min', 'placeholder': '{work_temp_min}', 'path': 'work_temp_min'},
    {'key': 'work_temp_max', 'placeholder': '{work_temp_max}', 'path': 'work_temp_max'},
    {'key': 'drain_variety', 'placeholder': '{drain_variety}', 'path': 'drain_variety'},
    {'key': 'gauge_quantity', 'placeholder': '{gauge_quantity}', 'path': 'gauge_quantity_display'},
)
