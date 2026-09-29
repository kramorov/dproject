# pneumatic_actuators/models/pa_item_fields.py
"""Реестр полей PneumaticActuatorItem — единый источник правды.

Единственная модель каталога с автогенерацией артикула: ``code_path`` даёт
encoding-значение для ``model_line.model_item_code_template`` (из through-опций
серии через ``*_encoding``-свойства), поэтому объявлены ``CODE_FIELD_KEYS``.

``path`` — display-значение (для `template_vars`/`specs`), ``name_path`` — путь
для подстановки в имя/описание (шаблоны подставляют ``str(obj)`` FK), а
VARS/specs — имя. ``{model_code}`` в имени/описании — ``code`` артикула, в
шаблоне артикула — ``base_model_code`` (базовый код без опций).

Составы словарей задаются в модели списками ключей:
``NAME_FIELD_KEYS`` / ``CODE_FIELD_KEYS`` / ``VARS_FIELD_KEYS`` /
``SPEC_FIELD_KEYS``.
"""

PA_ITEM_TEMPLATE_FIELDS = (
    # ── Общие / template_vars ──
    {'key': 'code', 'placeholder': '{model_code}', 'path': 'code', 'code_path': 'base_model_code'},
    {'key': 'name', 'path': 'name'},
    {'key': 'model_line_name', 'path': 'model_line__name', },
    {'key': 'model_line_code', 'path': 'model_line__code'},
    {'key': 'brand_name', 'placeholder': '{brand}', 'path': 'model_line__brand__name',
     'name_path': 'model_line__brand', },

    # ── Вид и корпус ──
    {'key': 'variety_name', 'placeholder': '{variety_name}', 'path': 'pneumatic_actuator_variety__name',
     'name_path': 'pneumatic_actuator_variety', },
    {'key': 'variety_description', 'placeholder': '{variety_description}', 'path': 'pneumatic_actuator_variety__description',
     'name_path': 'pneumatic_actuator_variety', },
    {'key': 'variety_code', 'path': 'pneumatic_actuator_variety__code'},
    {'key': 'body_name', 'placeholder': '{body_name}', 'path': 'body__name',
     },
    {'key': 'body_code', 'placeholder': '{body_code}', 'path': 'body__code'},
    {'key': 'weight', 'placeholder': '{weight}', 'path': 'calculated_weight',
     },

    # ── Опции (шаблоны + артикул) ──
    {'key': 'safety_position', 'placeholder': '{safety_position}', 'path': 'selected_safety_position__name',
     'name_path': 'selected_safety_position', 'code_path': 'safety_position_encoding'},
    {'key': 'safety_position_text_value', 'placeholder': '{safety_position_text_value}', 'path': 'safety_position_text_value',
     'name_path': 'safety_position_text_value'},
    {'key': 'springs_qty', 'placeholder': '{springs_qty}', 'path': 'selected_springs_qty__name',
     'name_path': 'selected_springs_qty', 'code_path': 'springs_qty_encoding'},
    {'key': 'temperature', 'placeholder': '{temperature}', 'path': 'selected_temperature__name',
     'name_path': 'selected_temperature', 'code_path': 'temperature_encoding'},
    {'key': 'ip', 'placeholder': '{ip}', 'path': 'selected_ip__name',
     'name_path': 'selected_ip', 'code_path': 'ip_encoding'},
    {'key': 'exd', 'placeholder': '{exd}', 'path': 'selected_exd__get_exd_list',
     'code_path': 'exd_encoding'},
    {'key': 'exd_short', 'placeholder': '{exd_short}', 'path': 'selected_exd__get_exd_short_list'},
    {'key': 'coating', 'placeholder': '{coating}', 'path': 'selected_body_coating__body_coating',
     'name_path': 'selected_body_coating', 'code_path': 'coating_encoding'},
    {'key': 'body_material', 'placeholder': '{body_material}', 'path': 'selected_body_coating__body_material__name',
     'name_path': 'selected_body_coating__body_material'},
    {'key': 'body_coating', 'placeholder': '{body_coating}', 'path': 'selected_body_coating__body_coating',
     'name_path': 'selected_body_coating__body_coating'},
    {'key': 'body_color_ral', 'placeholder': '{body_color_ral}', 'path': 'selected_body_coating__body_color__ral_code',
     'name_path': 'selected_body_coating__body_color__ral_code'},
    {'key': 'body_color_name', 'placeholder': '{body_color_name}', 'path': 'selected_body_coating__body_color__ral_name_ru',
     'name_path': 'selected_body_coating__body_color__ral_name_ru'},
    {'key': 'hand_wheel', 'placeholder': '{hand_wheel}', 'path': 'selected_hand_wheel__name',
     'name_path': 'selected_hand_wheel', 'code_path': 'hand_wheel_encoding'},

    # ── Технические характеристики корпуса (для spec_template) ──
    {'key': 'construction_name', 'placeholder': '{construction_name}',
     'path': 'model_line__pneumatic_actuator_construction_variety__name',
    'label': 'Конструкция', 'group': 'Корпус'},
    {'key': 'construction_description', 'placeholder': '{construction_description}',
     'path': 'model_line__pneumatic_actuator_construction_variety__description',
     'label': 'Конструкция описание', 'group': 'Корпус'},
    {'key': 'piston_diameter', 'placeholder': '{piston_diameter}',
     'resolver': '_res_piston_diameter', 'label': 'Диаметр поршня', 'unit': 'мм', 'group': 'Корпус'},
    {'key': 'turn_angle', 'placeholder': '{turn_angle}', 'path': 'body__turn_angle',
     'label': 'Угол поворота', 'group': 'Корпус'},
    {'key': 'turn_tuning_limit', 'placeholder': '{turn_tuning_limit}', 'path': 'body__turn_tuning_limit',
     'label': 'Ограничитель поворота', 'group': 'Корпус'},
    {'key': 'weight_spring', 'placeholder': '{weight_spring}',
     'resolver': '_res_weight_spring', 'label': 'Вес пружины', 'unit': 'кг', 'group': 'Корпус'},
    {'key': 'pressure_min', 'placeholder': '{pressure_min}',
     'resolver': '_res_pressure_min', 'label': 'Мин. давление', 'unit': 'бар', 'group': 'Корпус'},
    {'key': 'pressure_max', 'placeholder': '{pressure_max}',
     'resolver': '_res_pressure_max', 'label': 'Макс. давление', 'unit': 'бар', 'group': 'Корпус'},
    {'key': 'pressure', 'placeholder': '{pressure}',
     'resolver': '_res_pressure', 'label': 'Давление', 'unit': 'бар', 'group': 'Корпус'},
    {'key': 'air_usage_open', 'placeholder': '{air_usage_open}',
     'resolver': '_res_air_usage_open', 'label': 'Расход воздуха (открытие)', 'unit': 'л', 'group': 'Корпус'},
    {'key': 'air_usage_close', 'placeholder': '{air_usage_close}',
     'resolver': '_res_air_usage_close', 'label': 'Расход воздуха (закрытие)', 'unit': 'л', 'group': 'Корпус'},
    {'key': 'air_usage', 'placeholder': '{air_usage}',
     'resolver': '_res_air_usage', 'label': 'Расход воздуха', 'unit': 'л', 'group': 'Корпус'},

    # ── Шток ──
    {'key': 'stem_shape', 'placeholder': '{stem_shape}', 'path': 'body__stem_shape__name',
     'label': 'Форма штока', 'group': 'Шток'},
    {'key': 'stem_size', 'placeholder': '{stem_size}', 'path': 'body__stem_size__code',
     'label': 'Размер штока (код)', 'group': 'Шток'},
    {'key': 'stem_size_dim', 'placeholder': '{stem_size_dim}',
     'resolver': '_res_stem_size_dim', 'label': 'Размер штока (габарит)', 'group': 'Шток'},
    {'key': 'max_stem_height', 'placeholder': '{max_stem_height}',
     'resolver': '_res_max_stem_height', 'label': 'Макс. высота штока', 'unit': 'мм', 'group': 'Шток'},
    {'key': 'max_stem_diameter', 'placeholder': '{max_stem_diameter}',
     'resolver': '_res_max_stem_diameter', 'label': 'Макс. диаметр штока', 'unit': 'мм', 'group': 'Шток'},
    {'key': 'stem', 'placeholder': '{stem}', 'path': 'body__stem_info_display',
     'label': 'Шток (сводно)', 'group': 'Шток'},

    # ── Монтаж ──
    {'key': 'mounting', 'placeholder': '{mounting}', 'path': 'body__mounting_plate_display',
     'label': 'Монтажные площадки', 'group': 'Монтаж'},

    # ── Подключения ──
    {'key': 'thread_in', 'placeholder': '{thread_in}', 'path': 'body__thread_in',
     'label': 'Пневмовход (резьба)', 'group': 'Подключения'},
    {'key': 'thread_out', 'placeholder': '{thread_out}', 'path': 'body__thread_out',
     'label': 'Пневмовыход (резьба)', 'group': 'Подключения'},
    {'key': 'pneumatic_conn', 'placeholder': '{pneumatic_conn}',
     'resolver': '_res_pneumatic_conn', 'label': 'Типы пневмоподключений', 'group': 'Подключения'},

    # ── Расчёт ──
    {'key': 'torque_table', 'resolver': '_res_torque_table', 'type': 'html',
     'label': 'Таблица моментов/усилий', 'group': 'Расчёт'},
    {'key': 'time_open', 'placeholder': '{time_open}', 'resolver': '_res_time_open',
     'label': 'Время открытия', 'unit': 'сек', 'group': 'Расчёт'},
    {'key': 'time_close', 'placeholder': '{time_close}', 'resolver': '_res_time_close',
     'label': 'Время закрытия', 'unit': 'сек', 'group': 'Расчёт'},
)
