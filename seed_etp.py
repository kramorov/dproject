"""
Миграция: PropagationRule → EquipmentTypeParameter.

Переносит все существующие PropagationRules в новую модель.
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')
import django; django.setup()

from configurator.models import (
    PropagationRule, EquipmentTypeParameter,
    ParameterSource, ParameterRule,
)
from django.contrib.contenttypes.models import ContentType

# 1. Seed ParameterSources
srcs = ParameterSource.seed_defaults()
print(f"ParameterSources: {ParameterSource.objects.count()} total, {srcs} created")

# 2. Build source mapping
source_map = {s.code: s for s in ParameterSource.objects.all()}

# 3. Migrate
rules = PropagationRule.objects.filter(is_active=True).order_by('equipment_type__code', 'priority')
created = 0
skipped = 0

for rule in rules:
    # Check if ETP already exists
    existing = EquipmentTypeParameter.objects.filter(
        equipment_type=rule.equipment_type,
        param_name=rule.param_name,
    ).first()

    if existing:
        skipped += 1
        continue

    # Resolve ParameterRule
    param_rule = None
    if rule.code:
        param_rule = ParameterRule.objects.filter(code=rule.code).first()

    # Resolve ContentType
    from configurator.services.registry import get_product_model_class
    try:
        model_class = get_product_model_class(rule.equipment_type)
        product_ct = ContentType.objects.get_for_model(model_class)
        field_path = None
        for fd in getattr(model_class, 'FILTER_DEFINITIONS', []):
            if hasattr(fd, 'param_name') and fd.param_name == rule.param_name:
                field_path = getattr(fd, 'model_field', rule.param_name)
                break
    except (KeyError, Exception):
        product_ct = None
        field_path = None

    EquipmentTypeParameter.objects.create(
        code=f"{rule.equipment_type.code}-{rule.param_name}"[:128],
        equipment_type=rule.equipment_type,
        product_model=product_ct,
        field_path=field_path or rule.param_name,
        param_name=rule.param_name,
        label=rule.param_name,
        field_type='choice',
        source=source_map.get(rule.source),
        source_param=rule.source_param,
        is_required=rule.is_mandatory,
        allow_override=rule.allow_override,
        required_condition=rule.mandatory_condition,
        priority=rule.priority,
        parameter_rule=param_rule,
        is_active=rule.is_active,
        sorting_order=rule.priority,
    )
    created += 1

print(f"Migrated {created}, skipped (already exist) {skipped}")
print(f"Total EquipmentTypeParameters: {EquipmentTypeParameter.objects.count()}")

# 4. List all
for etp in EquipmentTypeParameter.objects.all().order_by('equipment_type__code', 'param_name')[:20]:
    print(f"  {etp.equipment_type.code:25s} {etp.param_name:20s} src={etp.source.code if etp.source else '?'}")
