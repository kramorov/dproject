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
    {'key': 'model_line_name', 'path': 'model_line__name', 'label': 'Серия', 'group': 'general', 'order': 1},
    {'key': 'brand_name', 'placeholder': '{brand}', 'path': 'brand__name', 'name_path': 'model_line__brand',
     'label': 'Бренд', 'group': 'general', 'order': 2},

    # ── Основные ──
    {'key': 'function', 'placeholder': '{function}', 'path': 'function__name', 'name_path': 'function',
     'label': 'Схема', 'group': 'general', 'order': 3},
    {'key': 'actuation', 'placeholder': '{actuation}', 'path': 'actuation__name', 'name_path': 'actuation',
     'label': 'Управление', 'group': 'general', 'order': 4},
    {'key': 'construction', 'placeholder': '{construction}', 'path': 'construction',
     'label': 'Конструкция', 'group': 'general', 'order': 5},
    {'key': 'operation', 'placeholder': '{operation}', 'path': 'operation',
     'label': 'Принцип действия', 'group': 'general', 'order': 6},
    {'key': 'manual_override', 'placeholder': '{manual_override}', 'path': 'manual_override__name',
     'name_path': 'manual_override', 'label': 'Ручной дублер', 'group': 'general', 'order': 7},
    {'key': 'working_medium', 'placeholder': '{working_medium}', 'path': 'working_medium',
     'label': 'Рабочая среда', 'group': 'general', 'order': 8},

    # ── Пропускная способность ──
    {'key': 'kv', 'placeholder': '{kv}', 'path': 'kv',
     'label': 'Kv', 'unit': 'м³/ч', 'type': 'number', 'group': 'flow', 'order': 1},
    {'key': 'dn', 'placeholder': '{dn}', 'path': 'dn',
     'label': 'DN', 'unit': 'мм', 'type': 'number', 'group': 'flow', 'order': 2},

    # ── Давление ──
    {'key': 'pressure_min', 'placeholder': '{pressure_min}', 'path': 'pressure_min',
     'label': 'Мин. давление', 'unit': 'бар', 'type': 'number', 'group': 'pressure', 'order': 1},
    {'key': 'pressure_max', 'placeholder': '{pressure_max}', 'path': 'pressure_max',
     'label': 'Макс. давление', 'unit': 'бар', 'type': 'number', 'group': 'pressure', 'order': 2},
    {'key': 'pressure_range', 'placeholder': '{pressure_range}', 'path': 'pressure_range_display',
     'label': 'Диапазон', 'type': 'text', 'group': 'pressure', 'order': 3},

    # ── Корпус и материалы ──
    {'key': 'body_material', 'placeholder': '{body_material}', 'path': 'body_material__name',
     'name_path': 'body_material', 'label': 'Материал корпуса', 'group': 'body', 'order': 1},
    {'key': 'body_material_specified', 'placeholder': '{body_material_specified}',
     'path': 'body_material_specified__name', 'name_path': 'body_material_specified',
     'label': 'Марка корпуса', 'group': 'body', 'order': 2},
    {'key': 'sealing_material_specified', 'placeholder': '{sealing_material_specified}',
     'path': 'sealing_material_specified__name', 'name_path': 'sealing_material_specified',
     'label': 'Уплотнение', 'group': 'body', 'order': 3},
    {'key': 'solenoid_body_material', 'placeholder': '{solenoid_body_material}',
     'path': 'solenoid_body_material__name', 'name_path': 'solenoid_body_material',
     'label': 'Материал соленоида', 'group': 'body', 'order': 4},
    {'key': 'solenoid_body_material_specified', 'placeholder': '{solenoid_body_material_specified}',
     'path': 'solenoid_body_material_specified__name', 'name_path': 'solenoid_body_material_specified',
     'label': 'Марка соленоида', 'group': 'body', 'order': 5},
    {'key': 'weight', 'placeholder': '{weight}', 'path': 'weight',
     'label': 'Вес', 'unit': 'кг', 'type': 'number', 'group': 'body', 'order': 6},

    # ── Присоединения ──
    {'key': 'pneumatic_connection', 'placeholder': '{pneumatic_connection}',
     'path': 'pneumatic_connection__name', 'name_path': 'pneumatic_connection',
     'label': 'Пневмоприсоединение', 'group': 'connections', 'order': 1},
    {'key': 'pneumatic_connection_thread', 'placeholder': '{pneumatic_connection_thread}',
     'path': 'pneumatic_connection_thread__name', 'name_path': 'pneumatic_connection_thread',
     'label': 'Резьба', 'group': 'connections', 'order': 2},
    {'key': 'cable_glands_holes', 'placeholder': '{cable_glands_holes}', 'path': 'cable_glands_holes',
     'label': 'Отверстия КВ', 'group': 'connections', 'order': 3},

    # ── Электрические параметры ──
    {'key': 'power_supply', 'placeholder': '{power_supply}', 'path': 'power_supply__name',
     'name_path': 'power_supply', 'label': 'Напряжение', 'group': 'electric', 'order': 1},
    {'key': 'power_consumption_start', 'placeholder': '{power_consumption_start}', 'path': 'power_consumption_start',
     'label': 'Мощность пусковая', 'unit': 'Вт', 'type': 'number', 'group': 'electric', 'order': 2},
    {'key': 'power_consumption_hot', 'placeholder': '{power_consumption_hot}', 'path': 'power_consumption_hot',
     'label': 'Мощность номинальная', 'unit': 'Вт', 'type': 'number', 'group': 'electric', 'order': 3},
    {'key': 'power_consumption_hold', 'placeholder': '{power_consumption_hold}', 'path': 'power_consumption_hold',
     'label': 'Мощность удержания', 'unit': 'Вт', 'type': 'number', 'group': 'electric', 'order': 4},
    {'key': 'solenoid_insulation_class', 'placeholder': '{solenoid_insulation_class}',
     'path': 'solenoid_insulation_class', 'label': 'Класс изоляции', 'group': 'electric', 'order': 5},

    # ── Защита ──
    {'key': 'ip', 'placeholder': '{ip}', 'path': 'ip__name', 'name_path': 'ip',
     'label': 'IP', 'group': 'protection', 'order': 1},
    {'key': 'exd', 'placeholder': '{exd}', 'path': 'exd__name', 'name_path': 'exd',
     'label': 'Ex', 'group': 'protection', 'order': 2},

    # ── Условия эксплуатации ──
    {'key': 'temperature_range', 'placeholder': '{temperature_range}', 'path': 'temperature_range_display',
     'label': 'Рабочая температура', 'group': 'conditions', 'order': 1},
    {'key': 'medium_density_max', 'placeholder': '{medium_density_max}', 'path': 'medium_density_max',
     'label': 'Макс. вязкость', 'unit': 'сСт', 'type': 'number', 'group': 'conditions', 'order': 2},

    # ── Только имя/описание и VARS (min/max) ──
    {'key': 'work_temp_min', 'placeholder': '{work_temp_min}', 'path': 'work_temp_min'},
    {'key': 'work_temp_max', 'placeholder': '{work_temp_max}', 'path': 'work_temp_max'},
)
