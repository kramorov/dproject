import os;os.environ.setdefault('DJANGO_SETTINGS_MODULE','djangoProject1.settings')
import django;django.setup()
from core.models import EquipmentType
from configurator.models import EquipmentTypeParameter as ETP

# ── Defaults по имени параметра ──
DEFAULTS = {
    'torque_nm': ('min', 'не менее'),
    'ip': ('min', 'не хуже'),
    'ip_id': ('min', 'не хуже'),
    'exd': ('exact', ''),
    'exd_id': ('exact', ''),
    'work_temp_min': ('max', 'не выше'),
    'work_temp_max': ('min', 'не ниже'),
    'temp_min': ('max', 'не выше'),
    'temp_max': ('min', 'не ниже'),
    'voltage': ('exact', ''),
    'coating': ('exact', ''),
    'coating_id': ('exact', ''),
    'safety_position': ('exact', ''),
    'safety_position_id': ('exact', ''),
    'hand_wheel': ('exact', ''),
    'hand_wheel_id': ('exact', ''),
    'connection_size': ('exact', ''),
    'connection_type': ('exact', ''),
    'body_material': ('exact', ''),
    'body_material_id': ('exact', ''),
    'cable_entry': ('exact', ''),
    'cable_entry_thread_id': ('exact', ''),
    'sensor_type': ('exact', ''),
    'sensor_type_id': ('exact', ''),
    'sensor_variety_code': ('exact', ''),
    'function_type': ('exact', ''),
    'actuator_variety_id': ('exact', ''),
    'air_pressure': ('exact', ''),
    'air_pressure_id': ('exact', ''),
    'model_line_id': ('exact', ''),
    'valve_type_id': ('exact', ''),
    'actuator_switches_limit_max_angle_rotation': ('max', 'не более'),
    'actuator_switches_limit_max_distance_mm': ('max', 'не более'),
    'actuator_switches_limit_max_pressure_bar': ('max', 'не более'),
    'actuator_switches_limit_max_temperature_c': ('max', 'не более'),
    'actuator_switches_limit_max_turns': ('max', 'не более'),
    'certificate_of_conformity_id': ('exact', ''),
    'connection_thread_id': ('exact', ''),
    'equipment_explosion_protection_id': ('exact', ''),
    'explosion_protection_class_id': ('exact', ''),
    'limit_switch_view_id': ('exact', ''),
    'arm_explosion_protection_id': ('exact', ''),
    'armoring_type_id': ('exact', ''),
    'armoring_material_id': ('exact', ''),
    'seal_type_id': ('exact', ''),
    'thread_type_id': ('exact', ''),
    'pressure_max': ('max', 'не более'),
    'temperature_range': ('min', 'не хуже'),
    'flow_capacity': ('min', 'не менее'),
    'nominal_diameter': ('exact', ''),
    'connection_standard': ('exact', ''),
    'media_type': ('exact', ''),
    'ambient_temp_min': ('max', 'не ниже'),
    'ambient_temp_max': ('min', 'не выше'),
    'response_time_ms': ('max', 'не более'),
    'power_consumption': ('max', 'не более'),
    'weight_kg': ('max', 'не более'),
    'length_mm': ('exact', ''),
    'width_mm': ('exact', ''),
    'height_mm': ('exact', ''),
    'mounting_type': ('exact', ''),
}

total = 0
for et in EquipmentType.objects.filter(is_active=True).order_by('code'):
    sem = et.param_semantics or {}
    updated = 0
    for p in ETP.objects.filter(equipment_type=et, is_active=True):
        if p.compare_direction:
            continue  # уже заполнено

        # 1. Ищем в param_semanticsEquipmentType
        sem_entry = sem.get(p.param_name) or sem.get(p.field_path or '')
        if sem_entry:
            p.compare_direction = sem_entry.get('direction', '') or None
            p.compare_label = sem_entry.get('label', '') or None
            p.save()
            updated += 1
            continue

        # 2. Defaults по имени параметра
        default = DEFAULTS.get(p.param_name) or DEFAULTS.get(p.field_path or '')
        if default:
            p.compare_direction = default[0]
            p.compare_label = default[1]
            p.save()
            updated += 1

    if updated:
        total += updated
        print(f'{et.code:25s} updated {updated:2d} params')

print(f'\nTotal updated: {total}')
print(f'Remaining empty: {ETP.objects.filter(is_active=True, compare_direction__isnull=True).count()}')
