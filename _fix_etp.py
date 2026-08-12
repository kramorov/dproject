"""Fix ETP data: source ← PropagationRule, field_path ← FilterDefinition."""
import os;os.environ.setdefault('DJANGO_SETTINGS_MODULE','djangoProject1.settings')
import django;django.setup()

from configurator.models import (
    EquipmentTypeParameter as ETP,
    PropagationRule,
    ParameterSource,
)

# 1. Заполняем source из PropagationRule
rules = PropagationRule.objects.filter(is_active=True)
source_map = {s.code: s for s in ParameterSource.objects.all()}
source_filled = 0
field_filled = 0

for rule in rules:
    etp = ETP.objects.filter(
        equipment_type=rule.equipment_type,
        param_name=rule.param_name,
        is_active=True,
    ).first()
    if not etp:
        continue
    if etp.source is None and rule.source in source_map:
        etp.source = source_map[rule.source]
        etp.source_param = rule.source_param
        etp.is_required = rule.is_mandatory
        etp.allow_override = rule.allow_override
        etp.required_condition = rule.mandatory_condition
        etp.priority = rule.priority
        etp.save()
        source_filled += 1

print(f"Source заполнен из PropagationRule: {source_filled}")

# 2. Заполняем field_path из FilterDefinition продукт-моделей
from configurator.services.registry import get_product_model_class

for etp in ETP.objects.filter(is_active=True, field_path=''):
    try:
        model_class = get_product_model_class(etp.equipment_type)
    except KeyError:
        continue

    for fd in getattr(model_class, 'FILTER_DEFINITIONS', []):
        if getattr(fd, 'param_name', None) == etp.param_name:
            etp.field_path = getattr(fd, 'model_field', '')
            etp.save()
            field_filled += 1
            break

print(f"field_path заполнен из FilterDefinition: {field_filled}")

# Итог
no_src = ETP.objects.filter(is_active=True, source__isnull=True).count()
no_field = ETP.objects.filter(is_active=True, field_path='').count()
print(f"\nОсталось без source: {no_src}")
print(f"Осталось без field_path: {no_field}")
print(f"Всего ETP: {ETP.objects.filter(is_active=True).count()}")
