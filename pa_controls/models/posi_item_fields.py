# pa_controls/models/posi_item_fields.py
"""Реестр полей PosiModelLineItem — единый источник правды.

Каждый вариант значения — отдельная запись. ``path`` даёт отображаемое значение
(скаляр, включая ``@property``); ``code_path`` — encoding для артикула;
``resolver`` — только для нестроковых значений (list/json). Метаданные
``label``/``unit``/``type``/``order``/``group`` используются ``_get_spec_sections()``.

Составы словарей задаются в модели списками ключей:
``NAME_FIELD_KEYS`` / ``CODE_FIELD_KEYS`` / ``VARS_FIELD_KEYS`` / ``SPEC_FIELD_KEYS``.
"""

POSI_ITEM_TEMPLATE_FIELDS = (
    # ── Общие / template_vars ──
    {'key': 'code', 'placeholder': '{model_code}', 'path': 'code', 'code_path': 'model_line__code'},
    {'key': 'name', 'path': 'name'},
    {'key': 'model_line_name', 'path': 'model_line__name', },
    {'key': 'brand_name', 'placeholder': '{brand}', 'path': 'model_line__brand__name', },

    # ── Основные характеристики ──
    {'key': 'acting_type', 'placeholder': '{acting_type}', 'path': 'get_acting_type__name',
     'code_path': 'acting_type_encoding', },
    {'key': 'exd', 'placeholder': '{exd}', 'path': 'get_exd_list', 'code_path': 'exd_encoding',
     },
    {'key': 'exd_short', 'placeholder': '{exd_short}', 'path': 'get_exd_short_list'},
    {'key': 'ip', 'placeholder': '{ip}', 'path': 'model_line__ip__name', 'code_path': 'ip_code',
     },
    {'key': 'work_temp', 'path': 'get_work_temp_display', },
    {'key': 'body_material', 'placeholder': '{body_material}', 'path': 'get_body_material__name',
     },
    {'key': 'weight', 'placeholder': '{weight}', 'path': 'get_weight', },
    {'key': 'actuator_action', 'placeholder': '{actuator_action}', 'path': 'get_actuator_action_display_text',
     },
    {'key': 'smart_capabilities', 'placeholder': '{smart_capabilities}', 'path': 'get_smart_capabilities_display',
     },

    # ── Присоединения ──
    {'key': 'body_connection', 'placeholder': '{body_connection}', 'path': 'body_connection__name',
     'code_path': 'body_connection_encoding'},
    {'key': 'pneumatic_connection', 'placeholder': '{pneumatic_connection}', 'path': 'get_pneumatic_connection',
     },
    {'key': 'cable_gland_hole', 'placeholder': '{cable_gland_hole}', 'path': 'get_cable_gland_hole',
     },
    {'key': 'lever', 'placeholder': '{lever}', 'path': 'lever__name', 'code_path': 'lever_encoding',
     },
    {'key': 'supply_pressure', 'placeholder': '{supply_pressure_range}', 'path': 'get_supply_pressure_range',
     },

    # ── Сигналы ──
    {'key': 'signal_profile', 'placeholder': '{signal_profile}', 'path': 'signal_profile__name',
     'code_path': 'signal_profile_encoding', },
    {'key': 'signal_profile_summary', 'placeholder': '{signal_profile_summary}', 'path': 'get_signal_profile_summary',
     },
    {'key': 'alarm', 'placeholder': '{alarm}', 'path': 'alarm__name', 'code_path': 'alarm_encoding',
     },
    {'key': 'alarm_signal_profile_summary', 'placeholder': '{alarm_signal_profile_summary}',
     'path': 'get_alarm_signal_profile_summary', },

    # ── Только имя/описание (min/max) ──
    {'key': 'work_temp_min', 'placeholder': '{work_temp_min}', 'path': 'work_temp_min'},
    {'key': 'work_temp_max', 'placeholder': '{work_temp_max}', 'path': 'work_temp_max'},

    # ── Только артикул ──
    {'key': 'temperature', 'placeholder': '{temperature}', 'code_path': 'temperature_encoding'},
    {'key': 'smart', 'placeholder': '{smart}', 'code_path': 'smart_code'},
)
