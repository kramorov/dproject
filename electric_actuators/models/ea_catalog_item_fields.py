# electric_actuators/models/ea_catalog_item_fields.py
"""Реестр полей ElectricActuatorCatalogItem — единый источник правды.

Паттерн TemplateMixin (§7 template_mixin.md): плейсхолдеры шаблонов имени/
описания берутся из ``NAME_FIELD_KEYS``; encoding-значения для
``model_line.model_item_code_template`` — из ``code_path`` (``CODE_FIELD_KEYS``);
``template_vars`` — из ``VARS_FIELD_KEYS``.

Номенклатура плейсхолдеров (группировка):
- ``{cu_*}``   — блок управления (имя, питание, режим, обогрев БУ);
- ``{ctl_*}``  — сигналы управления (команды, уставка, шина, органы МУ);
- ``{fb_*}``   — обратная связь (концевые/путевые/моментные, позиция, HART,
  теплозащита, индикация, счётчик);
- прочие — серия/модель/корпус/опции корпуса/артикул/ext-код.

Суффиксы кодировок (номенклатура 2026-10-19):
- ``{..._enc}``    — ``encoding`` through-опции (основной артикул);
- ``{..._e_enc}``  — ``ext_encoding`` through-опции (ext-часть артикула).

Сложные значения (сигналы матрицы) — resolver-методы ``_res_*`` модели
(принимают ``locale=None`` → локализация через ``localized_name``).
"""
from core.models.template_fields import TemplateFieldSpec

EA_CATALOG_ITEM_TEMPLATE_FIELDS = (
    # ── Серия / модель / корпус ──
    TemplateFieldSpec(key='code', placeholder='{model_code}',
                      path='model_line_item__code',
                      code_path='model_line_item__code'),
    TemplateFieldSpec(key='series_code', placeholder='{series_code}',
                      path='model_line__code'),
    TemplateFieldSpec(key='body_code', placeholder='{body_code}',
                      path='body__code'),
    TemplateFieldSpec(key='torque', placeholder='{torque}',
                      resolver='_res_torque'),
    TemplateFieldSpec(key='time_to_close', placeholder='{time_to_close}',
                      resolver='_res_time_to_close'),

    # ── Питание ──
    TemplateFieldSpec(key='power_supply', placeholder='{power_supply}',
                      path='power_supply',
                      name_path='power_supply',
                      code_path='power_supply__encoding',
                      enc_placeholder='{power_supply_enc}',
                      ext_code_path='power_supply__ext_encoding',
                      ext_enc_placeholder='{power_supply_e_enc}'),
    TemplateFieldSpec(key='voltage', placeholder='{voltage}',
                      path='power_supply__power_supply',
                      name_path='power_supply__power_supply',
                      code_path='power_supply__encoding',
                      enc_placeholder='{voltage_enc}',
                      ext_code_path='power_supply__ext_encoding',
                      ext_enc_placeholder='{voltage_e_enc}'),

    # ── Блок управления (cu_*) ──
    TemplateFieldSpec(key='cu_name', placeholder='{cu_name}',
                      path='control_unit__name',
                      name_path='control_unit',
                      code_path='control_unit__encoding',
                      enc_placeholder='{cu_name_enc}'),
    TemplateFieldSpec(key='cu_power_supply', placeholder='{cu_power_supply}',
                      path='cu_power_supply',
                      name_path='cu_power_supply'),
    TemplateFieldSpec(key='cu_mode', placeholder='{cu_mode}',
                      resolver='_res_mode'),
    TemplateFieldSpec(key='cu_heater', placeholder='{cu_heater}',
                      resolver='_res_cu_heater'),

    # ── Сигналы управления (ctl_*) ──
    TemplateFieldSpec(key='ctl_protocol', placeholder='{ctl_protocol}',
                      resolver='_res_protocol'),
    TemplateFieldSpec(key='ctl_commands', placeholder='{ctl_commands}',
                      resolver='_res_commands'),
    TemplateFieldSpec(key='ctl_setpoint', placeholder='{ctl_setpoint}',
                      resolver='_res_setpoint'),
    TemplateFieldSpec(key='ctl_local_controls',
                      placeholder='{ctl_local_controls}',
                      resolver='_res_local_controls'),

    # ── Обратная связь (fb_*) ──
    TemplateFieldSpec(key='fb_end_switches', placeholder='{fb_end_switches}',
                      resolver='_res_end_switches'),
    TemplateFieldSpec(key='fb_way_switches', placeholder='{fb_way_switches}',
                      resolver='_res_way_switches'),
    TemplateFieldSpec(key='fb_torque_switches',
                      placeholder='{fb_torque_switches}',
                      resolver='_res_torque_switches'),
    TemplateFieldSpec(key='fb_position_feedback',
                      placeholder='{fb_position_feedback}',
                      resolver='_res_position_feedback'),
    TemplateFieldSpec(key='fb_hart', placeholder='{fb_hart}',
                      resolver='_res_hart'),
    TemplateFieldSpec(key='fb_thermal_sensor',
                      placeholder='{fb_thermal_sensor}',
                      resolver='_res_thermal_sensor'),
    TemplateFieldSpec(key='fb_indicator', placeholder='{fb_indicator}',
                      resolver='_res_indicator'),
    TemplateFieldSpec(key='fb_turn_counter', placeholder='{fb_turn_counter}',
                      resolver='_res_turn_counter'),

    # ── Опции корпуса / исполнения ──
    TemplateFieldSpec(key='temperature', placeholder='{temperature}',
                      path='temperature', name_path='temperature',
                      code_path='temperature__encoding',
                      enc_placeholder='{temperature_enc}',
                      ext_code_path='temperature__ext_encoding',
                      ext_enc_placeholder='{temperature_e_enc}'),
    TemplateFieldSpec(key='ip', placeholder='{ip}',
                      path='ip', name_path='ip',
                      code_path='ip__encoding',
                      enc_placeholder='{ip_enc}',
                      ext_code_path='ip__ext_encoding',
                      ext_enc_placeholder='{ip_e_enc}'),
    TemplateFieldSpec(key='exd', placeholder='{exd}',
                      path='get_exd_display',
                      code_path='exd_encoding',
                      enc_placeholder='{exd_enc}',
                      ext_code_path='exd__ext_encoding',
                      ext_enc_placeholder='{exd_e_enc}'),
    TemplateFieldSpec(key='exd_short', placeholder='{exd_short}',
                      path='get_exd_short_list'),
    TemplateFieldSpec(key='coating', placeholder='{coating}',
                      path='coating', name_path='coating',
                      code_path='coating__encoding',
                      enc_placeholder='{coating_enc}',
                      ext_code_path='coating__ext_encoding',
                      ext_enc_placeholder='{coating_e_enc}'),
    TemplateFieldSpec(key='color', placeholder='{color}',
                      path='color', name_path='color',
                      code_path='color__encoding',
                      enc_placeholder='{color_enc}',
                      ext_code_path='color__ext_encoding',
                      ext_enc_placeholder='{color_e_enc}'),
    TemplateFieldSpec(key='hand_wheel', placeholder='{hand_wheel}',
                      path='hand_wheel', name_path='hand_wheel',
                      code_path='hand_wheel__encoding',
                      enc_placeholder='{hand_wheel_enc}',
                      ext_code_path='hand_wheel__ext_encoding',
                      ext_enc_placeholder='{hand_wheel_e_enc}'),
    TemplateFieldSpec(key='turn_angle', placeholder='{turn_angle}',
                      path='turn_angle', name_path='turn_angle',
                      code_path='turn_angle__encoding',
                      enc_placeholder='{turn_angle_enc}',
                      ext_code_path='turn_angle__ext_encoding',
                      ext_enc_placeholder='{turn_angle_e_enc}'),
    TemplateFieldSpec(key='cable_glands', placeholder='{cable_glands}',
                      path='cable_glands', name_path='cable_glands',
                      code_path='cable_glands__encoding',
                      enc_placeholder='{cable_glands_enc}',
                      ext_code_path='cable_glands__ext_encoding',
                      ext_enc_placeholder='{cable_glands_e_enc}'),
    TemplateFieldSpec(key='access_device', placeholder='{access_device}',
                      path='access_device__name',
                      name_path='access_device'),
    TemplateFieldSpec(key='safety_position', placeholder='{safety_position}',
                      path='safety_position',
                      name_path='safety_position',
                      code_path='safety_position__encoding',
                      enc_placeholder='{safety_position_enc}',
                      ext_code_path='safety_position__ext_encoding',
                      ext_enc_placeholder='{safety_position_e_enc}'),

    # ── Артикул / ext-код ──
    TemplateFieldSpec(key='article', placeholder='{article}',
                      resolver='_res_article'),
    TemplateFieldSpec(key='ext_code', placeholder='{ext_code}',
                      resolver='_res_ext_code'),
)
