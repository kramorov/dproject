# pneumatic_actuators/migrations/0072_springs_qty_kinds_and_13_16.py
from django.db import migrations

SPRINGS_QTY_KIND_COUNT = 'count'
SPRINGS_QTY_KIND_BLOCK = 'block'


def forwards(apps, schema_editor):
    SpringsQty = apps.get_model('pneumatic_actuators', 'PneumaticActuatorSpringsQty')

    # Пружинные блоки (кулисные): S1..S5 → kind=block.
    SpringsQty.objects.filter(code__in=['S1', 'S2', 'S3', 'S4', 'S5']).update(
        kind=SPRINGS_QTY_KIND_BLOCK)

    # Количества пружин (реечные): 05..12 → kind=count + spring_count.
    for n in range(5, 13):
        code = f'{n:02d}'
        SpringsQty.objects.filter(code=code).update(
            kind=SPRINGS_QTY_KIND_COUNT, spring_count=n)

    # Новые количества пружин 13..16 (NRT400).
    for n in range(13, 17):
        code = f'{n:02d}'
        name = f'{n:02d} пружин'
        SpringsQty.objects.update_or_create(
            code=code,
            defaults={
                'kind': SPRINGS_QTY_KIND_COUNT,
                'spring_count': n,
                'name': name,
                'name_i18n': {'ru': name, 'en': f'{n:02d} springs', 'cn': f'{n:02d}根弹簧'},
                'sorting_order': n,
                'is_active': True,
            })


def backwards(apps, schema_editor):
    SpringsQty = apps.get_model('pneumatic_actuators', 'PneumaticActuatorSpringsQty')
    SpringsQty.objects.filter(code__in=[f'{n:02d}' for n in range(13, 17)]).delete()
    # kind/spring_count остаются (откат схемы снесёт поля).


class Migration(migrations.Migration):

    dependencies = [
        ('pneumatic_actuators', '0071_alter_pneumaticspringsqtyoption_options_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
