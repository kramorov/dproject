# Data migration: add scotch-yoke spring-block codes S1/S2/S3 and re-point
# the SY through-options (and their weight params) from the numeric '10'/'11'/'12'
# to the block codes, so rack-and-pinion keeps numeric counts while scotch-yoke
# uses named blocks uniformly.

from django.db import migrations


MAPPING = {'10': 'S1', '11': 'S2', '12': 'S3'}


def add_scotch_yoke_spring_blocks(apps, schema_editor):
    SpringQty = apps.get_model('pneumatic_actuators', 'PneumaticActuatorSpringsQty')
    SpringOption = apps.get_model('pneumatic_actuators', 'PneumaticSpringsQtyOption')
    WeightParam = apps.get_model('pneumatic_actuators', 'PneumaticWeightParameter')
    ConstructionVariety = apps.get_model('pneumatic_actuators', 'PneumaticActuatorConstructionVariety')
    ModelLine = apps.get_model('pneumatic_actuators', 'PneumaticActuatorModelLine')
    ModelLineItem = apps.get_model('pneumatic_actuators', 'PneumaticActuatorModelLineItem')

    # 1) Create the block codes in the spring-qty reference.
    blocks = {}
    for code, sorting in (('S1', 13), ('S2', 14), ('S3', 15)):
        obj, _ = SpringQty.objects.get_or_create(
            code=code,
            defaults={
                'name': code,
                'description': 'Пружинный блок %s' % code,
                'sorting_order': sorting,
                'is_active': True,
            },
        )
        blocks[code] = obj

    # 2) Scope to scotch-yoke model lines.
    sy = ConstructionVariety.objects.filter(code='SY').first()
    if not sy:
        return
    sy_ml_ids = list(ModelLine.objects.filter(
        pneumatic_actuator_construction_variety=sy,
    ).values_list('id', flat=True))
    sy_mli_ids = list(ModelLineItem.objects.filter(
        model_line_id__in=sy_ml_ids,
    ).values_list('id', flat=True))

    # 3) Re-point SY through-options: numeric 10/11/12 -> S1/S2/S3 (+ encoding).
    for option in SpringOption.objects.filter(
        model_line_item_id__in=sy_mli_ids,
    ).select_related('springs_qty'):
        if not option.springs_qty:
            continue
        new_code = MAPPING.get(option.springs_qty.code)
        if not new_code:
            continue
        option.springs_qty = blocks[new_code]
        option.encoding = new_code
        option.save(update_fields=['springs_qty', 'encoding'])

    # 4) Re-point SY weight params keyed by '12' -> 'S3' (keeps weight lookup consistent).
    sy_body_ids = list(ModelLineItem.objects.filter(
        model_line_id__in=sy_ml_ids,
    ).values_list('body_id', flat=True).distinct())
    for wp in WeightParam.objects.filter(body_id__in=sy_body_ids).select_related('spring_qty'):
        if wp.spring_qty and wp.spring_qty.code in MAPPING:
            wp.spring_qty = blocks[MAPPING[wp.spring_qty.code]]
            wp.save(update_fields=['spring_qty'])


class Migration(migrations.Migration):

    dependencies = [
        ('pneumatic_actuators', '0043_alter_pneumaticbodydesignoption_body_color'),
    ]

    operations = [
        migrations.RunPython(add_scotch_yoke_spring_blocks, migrations.RunPython.noop),
    ]
