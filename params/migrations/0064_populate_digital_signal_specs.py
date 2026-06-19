# Generated manually — populate digital InputSignalSpec entries
from django.db import migrations


def create_digital_signal_specs(apps, schema_editor):
    InputSignalSpec = apps.get_model('params', 'InputSignalSpec')

    specs = [
        {
            'name': 'Modbus RTU (RS-485)',
            'code': 'MODBUS_RTU',
            'signal_category': 'digital',
            'electrical_specs': 'RS-485, 2-проводный (A/B), полудуплекс, до 115.2 кбит/с',
            'wires_count': 2,
            'sorting_order': 110,
            'is_active': True,
        },
        {
            'name': 'Modbus TCP (Ethernet)',
            'code': 'MODBUS_TCP',
            'signal_category': 'digital',
            'electrical_specs': 'Ethernet 10/100 Мбит/с, TCP/IP, Modbus Application Protocol',
            'wires_count': 4,
            'sorting_order': 120,
            'is_active': True,
        },
        {
            'name': 'Profibus DP (RS-485)',
            'code': 'PROFIBUS_DP',
            'signal_category': 'digital',
            'electrical_specs': 'RS-485, 2-проводный, до 12 Мбит/с, циклический обмен',
            'wires_count': 2,
            'sorting_order': 130,
            'is_active': True,
        },
        {
            'name': 'Profinet (Ethernet)',
            'code': 'PROFINET',
            'signal_category': 'digital',
            'electrical_specs': 'Ethernet 100 Мбит/с, Profinet RT/IRT, полный дуплекс',
            'wires_count': 4,
            'sorting_order': 140,
            'is_active': True,
        },
        {
            'name': 'HART (поверх 4-20мА)',
            'code': 'HART',
            'signal_category': 'digital',
            'electrical_specs': 'Bell 202 FSK поверх 4-20мА, 1.2/2.2 кГц, 1.2 кбит/с, двунаправленный',
            'wires_count': 2,
            'sorting_order': 150,
            'is_active': True,
        },
        {
            'name': 'Foundation Fieldbus H1',
            'code': 'FOUNDATION_FIELDBUS',
            'signal_category': 'digital',
            'electrical_specs': '31.25 кбит/с, питание по сигнальной линии, Manchester-кодирование',
            'wires_count': 2,
            'sorting_order': 160,
            'is_active': True,
        },
    ]

    for spec in specs:
        InputSignalSpec.objects.get_or_create(
            code=spec['code'],
            defaults=spec,
        )


def remove_digital_signal_specs(apps, schema_editor):
    InputSignalSpec = apps.get_model('params', 'InputSignalSpec')
    codes = [
        'MODBUS_RTU', 'MODBUS_TCP', 'PROFIBUS_DP', 'PROFINET',
        'HART', 'FOUNDATION_FIELDBUS',
    ]
    InputSignalSpec.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('params', '0063_inputsignalspec_digital_category'),
    ]
    operations = [
        migrations.RunPython(create_digital_signal_specs, remove_digital_signal_specs),
    ]
