# core/migrations/0015_cablegland_content_type.py
"""Backfill content_type для EquipmentType 'cable-gland'.

Графовый мастер подбора (QuestionGraph) резолвит модель товара через
equipment_type.content_type — без него опции и результаты пустые.
"""

from django.db import migrations


def set_cablegland_content_type(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    EquipmentType = apps.get_model('core', 'EquipmentType')
    try:
        ct = ContentType.objects.get(app_label='cable_glands', model='cablegland')
    except ContentType.DoesNotExist:
        return
    EquipmentType.objects.filter(code='cable-gland').update(content_type_id=ct.id)


def clear_cablegland_content_type(apps, schema_editor):
    EquipmentType = apps.get_model('core', 'EquipmentType')
    EquipmentType.objects.filter(code='cable-gland').update(content_type_id=None)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_equipmenttype_spec_template'),
        ('cable_glands', '0016_remove_cableglandmodelline_for_armored_cable_and_more'),
    ]

    operations = [
        migrations.RunPython(set_cablegland_content_type, clear_cablegland_content_type),
    ]
