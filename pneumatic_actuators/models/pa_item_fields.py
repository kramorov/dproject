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
    {'key': 'variety_name', 'placeholder': '{variety}', 'path': 'pneumatic_actuator_variety__name',
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
    {'key': 'springs_qty', 'placeholder': '{springs_qty}', 'path': 'selected_springs_qty__name',
     'name_path': 'selected_springs_qty', 'code_path': 'springs_qty_encoding'},
    {'key': 'temperature', 'placeholder': '{temperature}', 'path': 'selected_temperature__name',
     'name_path': 'selected_temperature', 'code_path': 'temperature_encoding'},
    {'key': 'ip', 'placeholder': '{ip}', 'path': 'selected_ip__name',
     'name_path': 'selected_ip', 'code_path': 'ip_encoding'},
    {'key': 'exd', 'placeholder': '{exd}', 'path': 'selected_exd__get_exd_list',
     'code_path': 'exd_encoding'},
    {'key': 'exd_short', 'placeholder': '{exd_short}', 'path': 'selected_exd__get_exd_short_list'},
    {'key': 'coating', 'placeholder': '{coating}', 'path': 'selected_body_coating__name',
     'name_path': 'selected_body_coating', 'code_path': 'coating_encoding'},
    {'key': 'hand_wheel', 'placeholder': '{hand_wheel}', 'path': 'selected_hand_wheel__name',
     'name_path': 'selected_hand_wheel', 'code_path': 'hand_wheel_encoding'},
)
