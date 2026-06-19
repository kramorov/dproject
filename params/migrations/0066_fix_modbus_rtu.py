# Generated manually — fix MODBUS_RTU record (manually created before migration 0064)
from django.db import migrations


def fix_modbus_rtu(apps, schema_editor):
    InputSignalSpec = apps.get_model('params', 'InputSignalSpec')
    InputSignalSpec.objects.filter(code='MODBUS_RTU').update(
        signal_category='digital',
        electrical_specs='RS-485, 2-проводный (A/B), полудуплекс, до 115.2 кбит/с',
        sorting_order=110,
    )


def revert(apps, schema_editor):
    InputSignalSpec = apps.get_model('params', 'InputSignalSpec')
    InputSignalSpec.objects.filter(code='MODBUS_RTU').update(
        signal_category='discrete',
        electrical_specs='RS-485, 2-проводный (A/B), терминатор 120 Ом',
        sorting_order=100,
    )


class Migration(migrations.Migration):
    dependencies = [
        ('params', '0065_add_digital_signal_descriptions'),
    ]
    operations = [
        migrations.RunPython(fix_modbus_rtu, revert),
    ]
