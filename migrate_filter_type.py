"""Перенос filter_type + data_source_type из FilterDefinition в ETP."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')
import django; django.setup()

from configurator.models import EquipmentTypeParameter as ETP
from configurator.services.registry import get_product_model_class

updated = 0
for p in ETP.objects.filter(is_active=True).select_related('equipment_type'):
    try:
        mc = get_product_model_class(p.equipment_type)
    except Exception:
        continue

    for fd in getattr(mc, 'FILTER_DEFINITIONS', []):
        if getattr(fd, 'param_name', '') != p.param_name:
            continue

        changed = False
        ft = getattr(fd, 'filter_type', None)
        dst = getattr(fd, 'data_source_type', None)

        if ft and p.filter_type is None:
            p.filter_type = ft.value if hasattr(ft, 'value') else str(ft)
            changed = True
        if dst and p.data_source_type is None:
            p.data_source_type = dst.value if hasattr(dst, 'value') else str(dst)
            changed = True

        if changed:
            p.save(update_fields=['filter_type', 'data_source_type'])
            updated += 1
        break

print(f'Updated: {updated}')
for p in ETP.objects.filter(filter_type__isnull=False)[:10]:
    print(f'  {p.equipment_type.code:25s} {p.param_name:20s} ft={p.filter_type} dst={p.data_source_type}')
