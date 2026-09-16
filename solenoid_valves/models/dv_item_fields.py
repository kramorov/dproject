# solenoid_valves/models/dv_item_fields.py
"""Реестр полей DirectionValve — единый источник правды.

Каждый вариант значения — отдельная запись. ``path`` даёт отображаемое значение
(для `template_vars`/`specs`, включая ``@property`` и пути ``__name`` через FK);
``name_path`` — отдельный путь для подстановки в имя/описание (если отличается
от display-пути: у DV шаблоны подставляют ``str(obj)`` FK, а VARS/specs — имя).
``code_path``/``CODE_FIELD_KEYS`` не используются: у DirectionalValveModelLine
нет ``model_item_code_template`` (артикул не генерируется).

Составы словарей задаются в модели списками ключей:
``NAME_FIELD_KEYS`` / ``VARS_FIELD_KEYS`` / ``SPEC_FIELD_KEYS``;
метаданные ``label``/``unit``/``type``/``order``/``group`` использует
``_get_spec_sections()``.
"""

DV_ITEM_TEMPLATE_FIELDS = (
    # ── Общие / template_vars ──
    {'key': 'code', 'placeholder': '{model_code}', 'path': 'code'},
    {'key': 'name', 'path': 'name'},
    {'key': 'model_line_name', 'path': 'model_line__name', },
    {'key': 'brand_name', 'placeholder': '{brand}', 'path': 'brand__name', 'name_path': 'model_line__brand',
     },

    # ── Основные ──
    {'key': 'function', 'placeholder': '{function}', 'path': 'function__name', 'name_path': 'function',
     },
    {'key': 'actuation', 'placeholder': '{actuation}', 'path': 'actuation__name', 'name_path': 'actuation',
     },
    {'key': 'construction', 'placeholder': '{construction}', 'path': 'construction',
     },
    {'key': 'operation', 'placeholder': '{operation}', 'path': 'operation',
     },
    {'key': 'manual_override', 'placeholder': '{manual_override}', 'path': 'manual_override__name',
     'name_path': 'manual_override', },
    {'key': 'working_medium', 'placeholder': '{working_medium}', 'path': 'working_medium',
     },

    # ── Пропускная способность ──
    {'key': 'kv', 'placeholder': '{kv}', 'path': 'kv',
     },
    {'key': 'dn', 'placeholder': '{dn}', 'path': 'dn',
     },

    # ── Давление ──
    {'key': 'pressure_min', 'placeholder': '{pressure_min}', 'path': 'pressure_min',
     },
    {'key': 'pressure_max', 'placeholder': '{pressure_max}', 'path': 'pressure_max',
     },
    {'key': 'pressure_range', 'placeholder': '{pressure_range}', 'path': 'pressure_range_display',
     },

    # ── Корпус и материалы ──
    {'key': 'body_material', 'placeholder': '{body_material}', 'path': 'body_material__name',
     'name_path': 'body_material', },
    {'key': 'body_material_specified', 'placeholder': '{body_material_specified}',
     'path': 'body_material_specified__name', 'name_path': 'body_material_specified',
     },
    {'key': 'sealing_material_specified', 'placeholder': '{sealing_material_specified}',
     'path': 'sealing_material_specified__name', 'name_path': 'sealing_material_specified',
     },
    {'key': 'solenoid_body_material', 'placeholder': '{solenoid_body_material}',
     'path': 'solenoid_body_material__name', 'name_path': 'solenoid_body_material',
     },
    {'key': 'solenoid_body_material_specified', 'placeholder': '{solenoid_body_material_specified}',
     'path': 'solenoid_body_material_specified__name', 'name_path': 'solenoid_body_material_specified',
     },
    {'key': 'weight', 'placeholder': '{weight}', 'path': 'weight',
     },

    # ── Присоединения ──
    {'key': 'pneumatic_connection', 'placeholder': '{pneumatic_connection}',
     'path': 'pneumatic_connection__name', 'name_path': 'pneumatic_connection',
     },
    {'key': 'pneumatic_connection_thread', 'placeholder': '{pneumatic_connection_thread}',
     'path': 'pneumatic_connection_thread__name', 'name_path': 'pneumatic_connection_thread',
     },
    {'key': 'cable_glands_holes', 'placeholder': '{cable_glands_holes}', 'path': 'cable_glands_holes',
     },

    # ── Электрические параметры ──
    {'key': 'power_supply', 'placeholder': '{power_supply}', 'path': 'power_supply__name',
     'name_path': 'power_supply', },
    {'key': 'power_consumption_start', 'placeholder': '{power_consumption_start}', 'path': 'power_consumption_start',
     },
    {'key': 'power_consumption_hot', 'placeholder': '{power_consumption_hot}', 'path': 'power_consumption_hot',
     },
    {'key': 'power_consumption_hold', 'placeholder': '{power_consumption_hold}', 'path': 'power_consumption_hold',
     },
    {'key': 'solenoid_insulation_class', 'placeholder': '{solenoid_insulation_class}',
     'path': 'solenoid_insulation_class', },

    # ── Защита ──
    {'key': 'ip', 'placeholder': '{ip}', 'path': 'ip__name', 'name_path': 'ip',
     },
    {'key': 'exd', 'placeholder': '{exd}', 'path': 'get_exd_display',
     'code_path': 'exd_encoding',
     },
    {'key': 'exd_short', 'placeholder': '{exd_short}', 'path': 'get_exd_short_list',
     },

    # ── Условия эксплуатации ──
    {'key': 'temperature_range', 'placeholder': '{temperature_range}', 'path': 'temperature_range_display',
     },
    {'key': 'medium_density_max', 'placeholder': '{medium_density_max}', 'path': 'medium_density_max',
     },

    # ── Только имя/описание и VARS (min/max) ──
    {'key': 'work_temp_min', 'placeholder': '{work_temp_min}', 'path': 'work_temp_min'},
    {'key': 'work_temp_max', 'placeholder': '{work_temp_max}', 'path': 'work_temp_max'},
)
