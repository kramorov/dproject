import os;os.environ.setdefault('DJANGO_SETTINGS_MODULE','djangoProject1.settings')
import django;django.setup()
from configurator.models import EquipmentTypeParameter as ETP

rows = ETP.objects.filter(
    equipment_type__code__in=['directional-valve', 'solenoid-valve'],
    is_active=True,
).order_by('sorting_order', 'param_name')

print(f'Total: {len(rows)}')
for r in rows:
    cd = (r.compare_direction or '(empty)').ljust(8)
    cl = (r.compare_label or '(empty)')
    print(f'  {r.param_name:30s} dir={cd} label={cl}')

print()
print('=== compare_direction filled? ===')
filled = [r for r in rows if r.compare_direction]
print(f'  Filled: {len(filled)}/{len(rows)}')
