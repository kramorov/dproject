"""
Seed PropagationRules for pa-kit equipment types.

Запуск: python configurator/management/commands/seed_propagation_rules.py
Или через Django management command позже.
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')
import django
django.setup()

from core.models import EquipmentType
from configurator.models import PropagationRule

RULES = [
    # ── pneumatic-actuator ──
    # Пользовательские (обязательные)
    ('pa-torque', 'pneumatic-actuator', 'torque_nm', 'user', None, True, True, None, 100),
    ('pa-variety', 'pneumatic-actuator', 'actuator_variety_id', 'user', None, True, True, None, 90),
    ('pa-air-pressure', 'pneumatic-actuator', 'air_pressure_id', 'user', None, True, True, None, 80),

    # Глобальные
    ('pa-temp-min', 'pneumatic-actuator', 'temp_min', 'global', 'temp_min', True, False, None, 50),
    ('pa-temp-max', 'pneumatic-actuator', 'temp_max', 'global', 'temp_max', True, False, None, 50),
    ('pa-exd', 'pneumatic-actuator', 'exd', 'global', 'exd', True, False, None, 60),
    ('pa-ip', 'pneumatic-actuator', 'ip_id', 'global', 'ip', True, False, None, 40),
    # Индивидуальные (пользовательские, необязательные)
    ('pa-coating', 'pneumatic-actuator', 'coating_id', 'user', None, True, False, None, 70),
    ('pa-safety-pos', 'pneumatic-actuator', 'safety_position_id', 'user', None, True, False,
     {'param': 'actuator_variety_code', 'value': 'SR'}, 85),  # только для SR
    ('pa-hand-wheel', 'pneumatic-actuator', 'hand_wheel_id', 'user', None, True, False, None, 60),

    # ── directional-valve ──
    ('dv-voltage', 'directional-valve', 'voltage_id', 'user', None, True, True, None, 100),
    ('dv-function', 'directional-valve', 'valve_function_id', 'user', None, True, False, None, 90),
    ('dv-temp-min', 'directional-valve', 'temp_min', 'global', 'temp_min', True, False, None, 50),
    ('dv-temp-max', 'directional-valve', 'temp_max', 'global', 'temp_max', True, False, None, 50),
    ('dv-exd', 'directional-valve', 'exd', 'global', 'exd', True, False, None, 60),
    ('dv-ip', 'directional-valve', 'ip_id', 'global', 'ip', True, False, None, 40),
    # connection_size — от DerivationRule
    ('dv-connection', 'directional-valve', 'connection_size', 'derived', None, False, False, None, 30),

    # ── cable-gland ──
    ('cg-exd', 'cable-gland', 'exd', 'global', 'exd', True, False, None, 60),
    ('cg-ip', 'cable-gland', 'ip_id', 'global', 'ip', True, False, None, 40),
    ('cg-temp-min', 'cable-gland', 'temp_min', 'global', 'temp_min', True, False, None, 50),
    ('cg-temp-max', 'cable-gland', 'temp_max', 'global', 'temp_max', True, False, None, 50),
    ('cg-thread', 'cable-gland', 'thread_size', 'derived', None, False, False, None, 30),

    # ── lsb (БКВ) ──
    ('lsb-sensor', 'lsb', 'sensor_variety_id', 'user', None, True, True, None, 100),
    ('lsb-points', 'lsb', 'points_option_id', 'user', None, True, False, None, 90),
    ('lsb-exd', 'lsb', 'exd', 'global', 'exd', True, False, None, 60),
    ('lsb-ip', 'lsb', 'ip_id', 'global', 'ip', True, False, None, 40),
    ('lsb-temp-min', 'lsb', 'temp_min', 'global', 'temp_min', True, False, None, 50),
    ('lsb-temp-max', 'lsb', 'temp_max', 'global', 'temp_max', True, False, None, 50),

    # ── fr (фильтр-регулятор) ──
    ('fr-body-material', 'fr', 'body_material_id', 'user', None, True, False, None, 90),
    ('fr-flow', 'fr', 'flow_rate_min', 'user', None, True, False, None, 80),
    ('fr-temp-min', 'fr', 'temp_min', 'global', 'temp_min', True, False, None, 50),
    ('fr-temp-max', 'fr', 'temp_max', 'global', 'temp_max', True, False, None, 50),

    # ── mk-iso (монтажный комплект) ──
    ('mk-flange', 'mk-iso', 'flange_size', 'derived', None, False, False, None, 30),
    ('mk-temp-min', 'mk-iso', 'temp_min', 'global', 'temp_min', True, False, None, 50),
]

created = 0
updated = 0
for code, et_code, param, source, src_param, allow_over, mandatory, mand_cond, priority in RULES:
    et = EquipmentType.objects.get(code=et_code)
    rule, is_new = PropagationRule.objects.update_or_create(
        code=code,
        defaults={
            'equipment_type': et,
            'param_name': param,
            'source': source,
            'source_param': src_param,
            'allow_override': allow_over,
            'is_mandatory': mandatory,
            'mandatory_condition': mand_cond,
            'priority': priority,
            'is_active': True,
        },
    )
    if is_new:
        created += 1
    else:
        updated += 1

print(f"PropagationRules: {created} created, {updated} updated")
print(f"Total active: {PropagationRule.objects.filter(is_active=True).count()}")
