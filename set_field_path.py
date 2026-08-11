"""Установить field_path у EquipmentTypeParameter из FilterDefinition."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')
import django; django.setup()

from configurator.models import EquipmentTypeParameter as ETP
from configurator.services.registry import get_product_model_class

updated = 0
skipped = 0

for p in ETP.objects.filter(is_active=True).select_related('equipment_type'):
    try:
        mc = get_product_model_class(p.equipment_type)
    except Exception:
        mc = None

    if mc is None:
        skipped += 1
        continue

    fd_found = None
    for fd in getattr(mc, 'FILTER_DEFINITIONS', []):
        if hasattr(fd, 'param_name') and fd.param_name == p.param_name:
            fd_found = fd
            break

    if fd_found and hasattr(fd_found, 'model_field'):
        model_field = fd_found.model_field
        if model_field and model_field != p.field_path:
            p.field_path = model_field
            p.save(update_fields=['field_path'])
            updated += 1
        else:
            skipped += 1
    else:
        skipped += 1

print(f'Updated: {updated}, Skipped: {skipped}')
print('Sample with correct field_path:')
for p in ETP.objects.filter(is_active=True).exclude(param_name='')[:8]:
    print(f'  {p.equipment_type.code:25s} {p.param_name:20s} → {p.field_path}')
