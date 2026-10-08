# Generated manually — обновляет EquipmentType.content_type для разделённых видов
# фитингов (после раскола PneumaticFitting на три модели).
from django.db import migrations


def fix_content_types(apps, schema_editor):
    EquipmentType = apps.get_model('core', 'EquipmentType')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    ct_sil = ContentType.objects.get(app_label='pneumatic_fittings', model='pneumaticsilencer')
    ct_plug = ContentType.objects.get(app_label='pneumatic_fittings', model='pneumaticplug')

    EquipmentType.objects.filter(code='fitting-silencer').update(content_type=ct_sil)
    EquipmentType.objects.filter(code='fitting-plug').update(content_type=ct_plug)


def reverse_content_types(apps, schema_editor):
    EquipmentType = apps.get_model('core', 'EquipmentType')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    ct_fitting = ContentType.objects.get(app_label='pneumatic_fittings', model='pneumaticfitting')
    EquipmentType.objects.filter(code__in=['fitting-silencer', 'fitting-plug']).update(content_type=ct_fitting)


class Migration(migrations.Migration):

    dependencies = [
        ('pneumatic_fittings', '0025_remove_pneumaticfitting_flow_rate_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_content_types, reverse_content_types),
    ]
