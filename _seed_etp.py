import os;os.environ.setdefault('DJANGO_SETTINGS_MODULE','djangoProject1.settings')
import django;django.setup()
from core.models import EquipmentType
from configurator.models import EquipmentTypeParameter as ETP, ParameterSource
from configurator.services.registry import get_product_model_class

source_map = {s.code: s for s in ParameterSource.objects.all()}

# For each equipment_type, create ETP from FILTER_DEFINITIONS
for et in EquipmentType.objects.filter(is_active=True).order_by('sorting_order', 'code'):
    try:
        mc = get_product_model_class(et)
    except KeyError:
        continue
    
    fdefs = getattr(mc, 'FILTER_DEFINITIONS', [])
    if not fdefs:
        continue
    
    # Get param_semantics for this type
    sem = getattr(et, 'param_semantics', None) or {}
    
    created = 0
    for fd in fdefs:
        pn = fd.param_name
        if not hasattr(fd, 'param_name'):
            continue
        
        # Check if already exists
        if ETP.objects.filter(equipment_type=et, param_name=pn, is_active=True).exists():
            continue
        
        # Determine compare_direction from param_semantics
        cd = ''
        cl = ''
        sem_entry = sem.get(pn) or sem.get(getattr(fd, 'model_field', pn))
        if sem_entry:
            cd = sem_entry.get('direction', '')
            cl = sem_entry.get('label', '')
        
        ETP.objects.create(
            code=f'{et.code}-{pn}',
            equipment_type=et,
            param_name=pn,
            field_path=getattr(fd, 'model_field', pn),
            field_type=getattr(fd, 'filter_type', None) and str(fd.filter_type) or None,
            label=getattr(fd, 'label', pn),
            product_model=mc._meta.label,
            compare_direction=cd or None,
            compare_label=cl or None,
            is_active=True,
        )
        created += 1
    
    if created:
        print(f'{et.code:25s}: created {created:2d} ETP records')

print(f'\nTotal ETP: {ETP.objects.filter(is_active=True).count()}')
