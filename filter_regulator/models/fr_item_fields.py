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
    {'key': 'model_line_name', 'path': 'model_line__name', 'label': 'Серия', 'group': 'general', 'order': 1},
    {'key': 'brand_name', 'placeholder': '{brand}', 'path': 'model_line__brand__name',
     'name_path': 'model_line__brand', 'label': 'Бренд', 'group': 'general', 'order': 2},

    # ── Основные ──
    {'key': 'filter_variety', 'placeholder': '{filter_variety}', 'path': 'model_line__filter_variety__name',
     'name_path': 'model_line__filter_variety', 'label': 'Тип', 'group': 'general', 'order': 3},
    {'key': 'body_material', 'placeholder': '{body_material}', 'path': 'model_line__body_material_text',
     'label': 'Материал корпуса', 'group': 'general', 'order': 4},
    {'key': 'bowl_material', 'placeholder': '{bowl_material}', 'path': 'model_line__bowl_material_text',
     'label': 'Материал стакана', 'group': 'general', 'order': 5},
    {'key': 'protection_material', 'placeholder': '{protection_material}',
     'path': 'model_line__protection_material', 'label': 'Материал кожуха', 'group': 'general', 'order': 6},
    {'key': 'ip', 'path': 'ip__name', 'label': 'IP', 'group': 'general', 'order': 7},
    {'key': 'filtration_rating', 'placeholder': '{filtration_rating}', 'path': 'filtration_rating',
     'label': 'Тонкость фильтрации', 'unit': 'мкм', 'type': 'number', 'group': 'general', 'order': 8},
    {'key': 'flow_rate', 'placeholder': '{flow_rate}', 'path': 'flow_rate',
     'label': 'Расход', 'unit': 'л/мин', 'type': 'number', 'group': 'general', 'order': 9},
    {'key': 'filter_element_material', 'placeholder': '{filter_element_material}',
     'path': 'filter_element_material_display', 'name_path': 'filter_element_material',
     'label': 'Фильтрующий элемент', 'group': 'general', 'order': 10},

    # ── Давление ──
    {'key': 'pressure_range', 'path': 'pressure_range_display',
     'label': 'Диапазон выходного давления', 'unit': 'бар', 'group': 'pressure', 'order': 1},
    {'key': 'pressure_inlet_max', 'placeholder': '{pressure_inlet_max}',
     'path': 'model_line__pressure_inlet_max',
     'label': 'Макс. входное давление', 'unit': 'бар', 'type': 'number', 'group': 'pressure', 'order': 2},

    # ── Корпус ──
    {'key': 'weight', 'placeholder': '{weight}', 'path': 'body__weight',
     'label': 'Вес', 'unit': 'кг', 'type': 'number', 'group': 'body_specs', 'order': 1},
    {'key': 'thread', 'placeholder': '{thread}', 'path': 'body__thread__name', 'name_path': 'body__thread',
     'label': 'Резьба портов', 'group': 'body_specs', 'order': 2},
    {'key': 'gauge_port_size', 'placeholder': '{gauge_port_size}', 'path': 'body__gauge_port_size__name',
     'name_path': 'body__gauge_port_size', 'label': 'Резьба манометра', 'group': 'body_specs', 'order': 3},
    {'key': 'drain_port_size', 'placeholder': '{drain_port_size}', 'path': 'body__drain_port_size__name',
     'name_path': 'body__drain_port_size', 'label': 'Резьба слива', 'group': 'body_specs', 'order': 4},
    {'key': 'wall_mounting_included', 'placeholder': '{wall_mounting_included}',
     'path': 'wall_mounting_included_display', 'label': 'Настенное крепление', 'group': 'body_specs', 'order': 5},
    {'key': 'has_shut_off_valve', 'path': 'has_shut_off_valve_display',
     'label': 'Отсечной клапан', 'group': 'body_specs', 'order': 6},

    # ── Условия эксплуатации ──
    {'key': 'work_temp', 'path': 'work_temp_display',
     'label': 'Рабочая температура', 'group': 'conditions', 'order': 1},

    # ── Только имя/описание ──
    {'key': 'pressure_min', 'placeholder': '{pressure_min}', 'path': 'model_line__pressure_min'},
    {'key': 'pressure_max', 'placeholder': '{pressure_max}', 'path': 'model_line__pressure_max'},
    {'key': 'work_temp_min', 'placeholder': '{work_temp_min}', 'path': 'work_temp_min'},
    {'key': 'work_temp_max', 'placeholder': '{work_temp_max}', 'path': 'work_temp_max'},
    {'key': 'drain_variety', 'placeholder': '{drain_variety}', 'path': 'drain_variety'},
    {'key': 'gauge_quantity', 'placeholder': '{gauge_quantity}', 'path': 'gauge_quantity_display'},
)
