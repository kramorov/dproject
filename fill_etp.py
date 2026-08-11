"""Заполнить ETP значениями из FilterDefinition всех каталогов."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')
import django; django.setup()

from configurator.models import EquipmentTypeParameter as ETP, ParameterSource
from configurator.services.registry import get_product_model_class

# Equipment type codes that have FILTER_DEFINITIONS
ET_CODES = [
    'lsb',              # pa_controls → LimitSwitchBox
    'directional-valve', # solenoid_valves → DirectionValve
    'fittings',          # pneumatic_fittings → PneumaticFitting
    'fr',               # filter_regulator → FilterRegulator
    'manual-override',  # gearbox → GearBox
    'pneumatic-actuator', # pneumatic_actuators → PneumaticActuatorModelLineItem
    'cable-gland',      # cable_glands → CableGlandItem
]

# ── Дополнительные FilterDefinitions из catalog-файлов ──
EXTRA_FDS = {
    'directional-valve': ('solenoid_valves.catalog.filter_defs', 'SOLENOID_VALVES_FILTER_DEFINITIONS'),
    'fr':                ('filter_regulator.catalog.filter_defs',   'FILTER_REGULATOR_FILTER_DEFINITIONS'),
    'manual-override':   ('gearbox.catalog.filter_defs',            'GEARBOX_FILTER_DEFINITIONS'),
}

creates = 0
updates = 0

for et_code in ET_CODES:
    try:
        mc = get_product_model_class(et_code)
    except KeyError:
        print(f'  SKIP {et_code}: no model class')
        continue

    filter_defs = getattr(mc, 'FILTER_DEFINITIONS', None)
    if not filter_defs and et_code in EXTRA_FDS:
        import importlib
        mod_path, var_name = EXTRA_FDS[et_code]
        mod = importlib.import_module(mod_path)
        filter_defs = getattr(mod, var_name, None)
    if not filter_defs:
        print(f'  SKIP {et_code}: no FILTER_DEFINITIONS')
        continue

    from core.models import EquipmentType
    et = EquipmentType.objects.get(code=et_code)

    for fd in filter_defs:
        param_name = getattr(fd, 'param_name', '')
        if not param_name:
            continue

        ft = getattr(fd, 'filter_type', None)
        dst = getattr(fd, 'data_source_type', None)
        sm = getattr(fd, 'source_model', None)

        ft_val = ft.value if hasattr(ft, 'value') else str(ft) if ft else None
        dst_val = dst.value if hasattr(dst, 'value') else str(dst) if dst else None

        # Build options_config from source_model
        opts_cfg = None
        if sm:
            opts_cfg = {'model': f'{sm._meta.app_label}.{sm.__name__}'}

        # Find or create ETP
        p = ETP.objects.filter(equipment_type=et, param_name=param_name).first()
        if not p:
            # Create new ETP
            p = ETP.objects.create(
                equipment_type=et,
                param_name=param_name,
                label=getattr(fd, 'label', param_name),
                field_path=getattr(fd, 'model_field', param_name),
                field_type='choice' if dst_val in ('foreign_key','global_model','unique_field_values') else 'decimal',
                filter_type=ft_val,
                data_source_type=dst_val,
                options_config=opts_cfg,
                param_type='choice' if dst_val in ('foreign_key','global_model','unique_field_values') else 'decimal',
                is_active=True,
            )
            creates += 1
        else:
            # Update existing
            changed = False
            if ft_val and p.filter_type != ft_val:
                p.filter_type = ft_val; changed = True
            if dst_val and p.data_source_type != dst_val:
                p.data_source_type = dst_val; changed = True
            if opts_cfg and p.options_config != opts_cfg:
                p.options_config = opts_cfg; changed = True
            if changed:
                p.save(update_fields=['filter_type', 'data_source_type', 'options_config'])
                updates += 1

print(f'\nCreated: {creates}, Updated: {updates}, Total ETP: {ETP.objects.count()}')
print('\nSample:')
for p in ETP.objects.filter(filter_type__isnull=False).exclude(filter_type='').order_by('equipment_type__code', 'param_name')[:20]:
    print(f'  {p.equipment_type.code:25s} {p.param_name:25s} ft={p.filter_type:20s} dst={p.data_source_type:20s} cfg={str(p.options_config)[:50]}')
