"""Data migration: param_semantics JSON → EquipmentTypeParameter fields."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')
import django; django.setup()

from core.models import EquipmentType
from configurator.models import EquipmentTypeParameter as ETP

# Type heuristics based on param name
TYPE_MAP = {
    'torque': 'decimal',
    'temp': 'decimal',
    'temperature': 'decimal',
    'pressure': 'decimal',
    'diameter': 'decimal',
    'flow': 'decimal',
    'ip': 'choice',
    'exd': 'choice',
    'coating': 'choice',
    'variety': 'choice',
    'voltage': 'choice',
    'function': 'choice',
    'sensor': 'choice',
    'points': 'choice',
    'valve': 'choice',
    'body': 'choice',
    'connection': 'choice',
    'thread': 'choice',
    'armour': 'choice',
    'safety': 'choice',
    'hand': 'choice',
    'model': 'choice',
    'air': 'choice',
}

UNIT_MAP = {
    'torque': '\u041d\u043c',     # Нм
    'temp': '\u00b0C',            # °C
    'temperature': '\u00b0C',     # °C
    'pressure': '\u0431\u0430\u0440',  # бар
    'diameter': '\u043c\u043c',   # мм
    'flow': '\u043b/\u043c\u0438\u043d',  # л/мин
}

updated = 0
skipped = 0

for et in EquipmentType.objects.filter(is_active=True):
    ps = et.param_semantics or {}
    for key, info in ps.items():
        p = ETP.objects.filter(equipment_type=et, param_name=key).first()
        if not p:
            continue

        changed = False

        # Description from label
        if isinstance(info, dict) and info.get('label'):
            p.description = str(info['label'])
            changed = True
        elif isinstance(info, str):
            p.description = info
            changed = True

        # Type heuristic
        for keyword, dtype in TYPE_MAP.items():
            if keyword in key:
                p.param_type = dtype
                changed = True
                break

        # Unit heuristic
        for keyword, unit in UNIT_MAP.items():
            if keyword in key:
                p.unit = unit
                changed = True
                break

        if changed:
            p.save(update_fields=['description', 'param_type', 'unit'])
            updated += 1
        else:
            skipped += 1

print(f'Done: updated {updated}, skipped {skipped}')
print(f'Sample:')
for p in ETP.objects.filter(description__isnull=False).exclude(description='')[:10]:
    print(f'  {p.equipment_type.code:25s} {p.param_name:20s} type={p.param_type} unit={p.unit} desc={p.description}')
