# pneumatic_fittings/pf_item_fields.py
"""Реестр полей PneumaticFitting — единый источник правды.

Каждый вариант значения — отдельная запись. ``path`` даёт отображаемое значение
(для `template_vars`/`specs`, включая ``@property`` и пути ``__name`` через FK);
``name_path`` — отдельный путь для подстановки в имя/описание (если отличается
от display-пути: шаблоны подставляют ``str(obj)`` FK, а VARS/specs — имя).
``code_path``/``CODE_FIELD_KEYS`` не используются: у PneumaticFittingModelLine
нет ``model_item_code_template`` (артикул не генерируется).

Динамика вида оборудования (фитинг vs глушитель/заглушка) — в
``PneumaticFitting._get_spec_sections()``: группа ``pipe`` показывается только
для фитингов, ``silencer`` — только для глушителей/заглушек.

Составы словарей задаются в модели списками ключей:
``NAME_FIELD_KEYS`` / ``VARS_FIELD_KEYS`` / ``SPEC_FIELD_KEYS``.
"""

PF_ITEM_TEMPLATE_FIELDS = (
    # ── Общие / template_vars ──
    {'key': 'code', 'placeholder': '{model_code}', 'path': 'code'},
    {'key': 'name', 'path': 'name'},
    {'key': 'model_line_name', 'path': 'model_line__name', 'label': 'Серия', 'group': 'general', 'order': 1},
    {'key': 'brand_name', 'placeholder': '{brand}', 'path': 'model_line__brand__name',
     'name_path': 'model_line__brand', 'label': 'Бренд', 'group': 'general', 'order': 2},

    # ── Основные ──
    {'key': 'fitting_variety', 'placeholder': '{fitting_variety}', 'path': 'fitting_variety__name',
     'label': 'Тип фитинга', 'group': 'general', 'order': 3},
    # {shape} и {fixation_method} исторически указывают на один путь (см. старый _get_data_dict)
    {'key': 'shape', 'placeholder': '{shape}', 'path': 'fitting_variety__fixation_method'},
    {'key': 'fixation_method', 'placeholder': '{fixation_method}', 'path': 'fitting_variety__fixation_method'},
    {'key': 'thread', 'placeholder': '{thread}', 'path': 'thread__name', 'name_path': 'thread',
     'label': 'Резьба', 'group': 'general', 'order': 4},
    {'key': 'thread_inner_outer', 'placeholder': '{thread_inner_outer}', 'path': 'thread_inner_outer__name',
     'name_path': 'thread_inner_outer', 'label': 'Резьба нар/внутр', 'group': 'general', 'order': 5},
    {'key': 'body_material', 'placeholder': '{body_material}', 'path': 'body_material__name',
     'name_path': 'body_material', 'label': 'Материал корпуса', 'group': 'general', 'order': 6},
    {'key': 'temperature_range', 'placeholder': '{temperature_range}', 'path': 'temperature_range_display',
     'label': 'Т раб., °С', 'group': 'general', 'order': 7},
    {'key': 'swivel', 'placeholder': '{swivel}', 'path': 'swivel_display'},

    # ── Трубка и давление (только для фитингов) ──
    {'key': 'pipe_diameter', 'placeholder': '{pipe_diameter}', 'path': 'pipe_diameter',
     'label': 'Диаметр трубки, мм', 'type': 'number', 'group': 'pipe', 'order': 1},
    {'key': 'pipe_material', 'placeholder': '{pipe_material}', 'path': 'pipe_material__name',
     'name_path': 'pipe_material', 'label': 'Материал трубки', 'group': 'pipe', 'order': 2},
    {'key': 'pressure_range', 'placeholder': '{pressure_range}', 'path': 'pressure_range_display',
     'label': 'Р раб., бар', 'group': 'pipe', 'order': 3},

    # ── Глушитель/заглушка ──
    {'key': 'flow_rate', 'placeholder': '{flow_rate}', 'path': 'flow_rate',
     'label': 'Пропускная способность, Нл/мин', 'type': 'number', 'group': 'silencer', 'order': 1},
    {'key': 'noise_level', 'placeholder': '{noise_level}', 'path': 'noise_level',
     'label': 'Уровень шума, дБ', 'type': 'number', 'group': 'silencer', 'order': 2},
    {'key': 'operating_pressure', 'placeholder': '{operating_pressure}', 'path': 'operating_pressure',
     'label': 'P раб.макс, бар', 'type': 'number', 'group': 'silencer', 'order': 3},

    # ── Только имя/описание (расширение реестра, backlog SESSION.md п.2) ──
    {'key': 'pressure_min', 'placeholder': '{pressure_min}', 'path': 'pressure_min'},
    {'key': 'pressure_max', 'placeholder': '{pressure_max}', 'path': 'pressure_max'},
    {'key': 'temp_min', 'placeholder': '{temp_min}', 'path': 'temp_min'},
    {'key': 'temp_max', 'placeholder': '{temp_max}', 'path': 'temp_max'},
)
