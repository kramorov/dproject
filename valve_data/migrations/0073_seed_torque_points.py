# valve_data/migrations/0073_seed_torque_points.py
from django.db import migrations

POINT_SEED = [
    ('bto', 'open', 'start', 10),
    ('rto', 'open', 'mid', 20),
    ('eto', 'open', 'end', 30),
    ('btc', 'close', 'end', 40),
    ('rtc', 'close', 'mid', 50),
    ('etc', 'close', 'start', 60),
]


def forwards(apps, schema_editor):
    TorquePoint = apps.get_model('valve_data', 'TorquePoint')
    for code, direction, position, order in POINT_SEED:
        TorquePoint.objects.update_or_create(
            code=code,
            defaults=dict(name=code.upper(), direction=direction, position=position,
                          sorting_order=order, is_active=True))


def backwards(apps, schema_editor):
    TorquePoint = apps.get_model('valve_data', 'TorquePoint')
    TorquePoint.objects.filter(code__in=[p[0] for p in POINT_SEED]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('valve_data', '0072_alter_torquepoint_description_i18n_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
