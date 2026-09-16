# pa_controls/models/lsb_item_fields.py
"""Реестр полей LimitSwitchBox — единый источник правды.

``path`` — display-путь (для `template_vars`/`specs`), ``name_path`` — отдельный
путь для подстановки в имя/описание (если отличается от display), ``code_path`` —
encoding для артикула, ``resolver`` — callable для нестроковых значений (списки).

Динамические сигналы/датчики — ``type='list'`` и резолвятся в список словарей
(вложенный JSON для MCP вместо плоских ``role_0``/``sensor_0``).
"""

LSB_ITEM_TEMPLATE_FIELDS = (
    # ── Общие / template_vars ──
    {'key': 'code', 'placeholder': '{model_code}', 'path': 'code'},
    {'key': 'name', 'path': 'name'},
    {'key': 'model_line_name', 'path': 'model_line__name', },
    {'key': 'brand_name', 'placeholder': '{brand}', 'path': 'model_line__brand__name',
     },

    # ── Основные ──
    {'key': 'sensor_variety', 'placeholder': '{sensor_variety}', 'path': 'sensor_variety__name',
     },
    {'key': 'points', 'placeholder': '{points}', 'path': 'get_points_display', 'name_path': 'points_option',
     },
    {'key': 'ip', 'placeholder': '{ip}', 'path': 'ip__name', },
    {'key': 'exd', 'placeholder': '{exd}', 'path': 'exd_display', },
    {'key': 'exd_short', 'placeholder': '{exd_short}', 'path': 'get_exd_short_list', },
    {'key': 'work_temp', 'path': 'get_work_temp_display', },
    {'key': 'visual_indicator_type', 'path': 'visual_indicator_type__name', },

    # ── Только template_vars ──
    {'key': 'work_temp_min', 'placeholder': '{work_temp_min}', 'path': 'work_temp_min'},
    {'key': 'work_temp_max', 'placeholder': '{work_temp_max}', 'path': 'work_temp_max'},
    {'key': 'body_material_specified', 'placeholder': '{body_material_specified}', 'path': 'body_material_specified__name'},
    {'key': 'is_pneumatic', 'path': 'get_is_pneumatic_display'},
    {'key': 'has_namur_interface', 'path': 'get_has_namur_interface_display'},
    {'key': 'primary_sensor', 'placeholder': '{primary_sensor}', 'path': 'primary_sensor__name',
     'name_path': 'primary_sensor__description'},
    {'key': 'primary_sensor_signal_type', 'placeholder': '{primary_sensor_signal_type}',
     'path': 'primary_sensor__signal_type__name'},
    {'key': 'primary_sensor_contact_state', 'placeholder': '{primary_sensor_contact_state}',
     'name_path': 'primary_sensor__contact_state'},
    {'key': 'primary_sensor_contact_form', 'placeholder': '{primary_sensor_contact_form}',
     'name_path': 'get_primary_sensor_contact_form'},
    {'key': 'signal_profile_summary', 'placeholder': '{signal_profile_summary}', 'path': 'get_signal_profile_summary'},
    {'key': 'cert_description', 'path': 'get_cert_docs_description_display'},

    # ── Корпус ──
    {'key': 'body_material', 'placeholder': '{body_material}', 'path': 'body_material__name',
     },
    {'key': 'weight', 'placeholder': '{weight}', 'path': 'get_weight_display', 'name_path': 'body__weight',
     },
    {'key': 'cable_glands_holes', 'placeholder': '{cable_glands_holes}', 'path': 'body__cable_glands_holes_list_text',
     },
    {'key': 'mounting', 'placeholder': '{mounting}', 'path': 'body__mounting_list_text',
     },

    # ── Динамические списки (JSON/MCP) ──
    {'key': 'signals', 'resolver': 'get_signals_data', },
    {'key': 'sensors', 'resolver': 'get_sensors_data', },
)
