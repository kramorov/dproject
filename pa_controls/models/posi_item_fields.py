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
    {'key': 'model_line_name', 'path': 'model_line__name', 'label': 'Серия', 'group': 'general', 'order': 1},
    {'key': 'brand_name', 'placeholder': '{brand}', 'path': 'model_line__brand__name', 'label': 'Бренд', 'group': 'general', 'order': 2},

    # ── Основные характеристики ──
    {'key': 'acting_type', 'placeholder': '{acting_type}', 'path': 'get_acting_type__name',
     'code_path': 'acting_type_encoding', 'label': 'Тип действия', 'group': 'general', 'order': 3},
    {'key': 'exd', 'placeholder': '{exd}', 'path': 'get_exd_list', 'code_path': 'exd_encoding',
     'label': 'Взрывозащита', 'group': 'general', 'order': 4},
    {'key': 'exd_short', 'placeholder': '{exd_short}', 'path': 'get_exd_short_list'},
    {'key': 'ip', 'placeholder': '{ip}', 'path': 'model_line__ip__name', 'code_path': 'ip_code',
     'label': 'IP', 'group': 'general', 'order': 5},
    {'key': 'work_temp', 'path': 'get_work_temp_display', 'label': 'Рабочая температура',
     'group': 'general', 'order': 6},
    {'key': 'body_material', 'placeholder': '{body_material}', 'path': 'get_body_material__name',
     'label': 'Материал корпуса', 'group': 'general', 'order': 7},
    {'key': 'weight', 'placeholder': '{weight}', 'path': 'get_weight', 'label': 'Вес', 'unit': 'кг',
     'type': 'number', 'group': 'general', 'order': 8},
    {'key': 'actuator_action', 'placeholder': '{actuator_action}', 'path': 'get_actuator_action_display_text',
     'label': 'Пневмопривод', 'group': 'general', 'order': 9},
    {'key': 'smart_capabilities', 'placeholder': '{smart_capabilities}', 'path': 'get_smart_capabilities_display',
     'label': 'Возможности', 'group': 'general', 'order': 10},

    # ── Присоединения ──
    {'key': 'body_connection', 'placeholder': '{body_connection}', 'path': 'body_connection__name',
     'code_path': 'body_connection_encoding'},
    {'key': 'pneumatic_connection', 'placeholder': '{pneumatic_connection}', 'path': 'get_pneumatic_connection',
     'label': 'Пневмоподключение', 'group': 'connections', 'order': 1},
    {'key': 'cable_gland_hole', 'placeholder': '{cable_gland_hole}', 'path': 'get_cable_gland_hole',
     'label': 'Отверстие под кабельный ввод', 'group': 'connections', 'order': 2},
    {'key': 'lever', 'placeholder': '{lever}', 'path': 'lever__name', 'code_path': 'lever_encoding',
     'label': 'Рычаг', 'group': 'connections', 'order': 3},
    {'key': 'supply_pressure', 'placeholder': '{supply_pressure_range}', 'path': 'get_supply_pressure_range',
     'label': 'Давление питания', 'unit': 'бар', 'group': 'connections', 'order': 4},

    # ── Сигналы ──
    {'key': 'signal_profile', 'placeholder': '{signal_profile}', 'path': 'signal_profile__name',
     'code_path': 'signal_profile_encoding', 'label': 'Профиль сигналов', 'group': 'signals', 'order': 1},
    {'key': 'signal_profile_summary', 'placeholder': '{signal_profile_summary}', 'path': 'get_signal_profile_summary',
     'label': 'Сигналы (по ролям)', 'group': 'signals', 'order': 2},
    {'key': 'alarm', 'placeholder': '{alarm}', 'path': 'alarm__name', 'code_path': 'alarm_encoding',
     'label': 'Сигнал тревоги', 'group': 'signals', 'order': 3},
    {'key': 'alarm_signal_profile_summary', 'placeholder': '{alarm_signal_profile_summary}',
     'path': 'get_alarm_signal_profile_summary', 'label': 'Сигнал тревоги (по ролям)', 'group': 'signals', 'order': 4},

    # ── Только имя/описание (min/max) ──
    {'key': 'work_temp_min', 'placeholder': '{work_temp_min}', 'path': 'work_temp_min'},
    {'key': 'work_temp_max', 'placeholder': '{work_temp_max}', 'path': 'work_temp_max'},

    # ── Только артикул ──
    {'key': 'temperature', 'placeholder': '{temperature}', 'code_path': 'temperature_encoding'},
    {'key': 'smart', 'placeholder': '{smart}', 'code_path': 'smart_code'},
)
