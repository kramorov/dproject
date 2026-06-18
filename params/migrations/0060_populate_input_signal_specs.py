# Generated migration — populate InputSignalSpec
from django.db import migrations


def create_input_signal_specs(apps, schema_editor):
    InputSignalSpec = apps.get_model('params', 'InputSignalSpec')

    specs = [
        {
            'name': 'Дискретный вход БУ, 24В DC, «сухой контакт»',
            'code': 'CU_DI_24V_DC',
            'signal_category': 'discrete',
            'electrical_specs': '24В DC, внешний источник, ~10мА',
            'wires_count': 2,
            'sorting_order': 10,
            'is_active': True,
        },
        {
            'name': 'Дискретный вход БУ, ~220В AC',
            'code': 'CU_DI_220V_AC',
            'signal_category': 'discrete',
            'electrical_specs': '~220В AC, через промежуточное реле',
            'wires_count': 2,
            'sorting_order': 20,
            'is_active': True,
        },
        {
            'name': 'Дискретный вход ESD, 24В DC, нормально-замкнутый',
            'code': 'CU_DI_ESD_NC',
            'signal_category': 'discrete',
            'electrical_specs': '24В DC, НЗ, контроль обрыва цепи',
            'wires_count': 2,
            'sorting_order': 30,
            'is_active': True,
        },
        {
            'name': 'Аналоговый вход 4-20мА, пассивный',
            'code': 'CU_AI_4_20MA_PASSIVE',
            'signal_category': 'analog',
            'electrical_specs': '4-20мА, внешний источник петли, 250 Ом',
            'wires_count': 2,
            'sorting_order': 40,
            'is_active': True,
        },
        {
            'name': 'Аналоговый вход 4-20мА, активный (питание от БУ)',
            'code': 'CU_AI_4_20MA_ACTIVE',
            'signal_category': 'analog',
            'electrical_specs': '4-20мА, питание петли от БУ, 250 Ом',
            'wires_count': 2,
            'sorting_order': 50,
            'is_active': True,
        },
    ]

    for spec in specs:
        InputSignalSpec.objects.get_or_create(
            code=spec['code'],
            defaults=spec,
        )


def remove_input_signal_specs(apps, schema_editor):
    InputSignalSpec = apps.get_model('params', 'InputSignalSpec')
    InputSignalSpec.objects.filter(code__startswith='CU_').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('params', '0059_inputsignalspec_signalrole_direction_and_more'),
    ]
    operations = [
        migrations.RunPython(create_input_signal_specs, remove_input_signal_specs),
    ]
