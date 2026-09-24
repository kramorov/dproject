# Generated manually 2026-09-24
"""Переносит хардкод-заголовки (title_template) трёх каталогов в EquipmentType.

Раньше ``_get_title_template_source()`` у DirectionValve / LimitSwitchBox /
PosiModelLineItem возвращал захардкоженную строку; теперь заголовок идёт по
общей цепочке model_line → EquipmentType.title_template → {model_code}.
"""

from django.db import migrations


EQUIPMENT_TYPE_TITLE_TEMPLATES = {
    'directional-valve': '{model_code} {function}; {temperature_range}°С; {exd}; {ip}; {power_supply}; {operation}; {construction}',
    'lsb': '{model_code} {points}, {sensor_variety}; {ip}, В/з: {exd}; {work_temp_min}..{work_temp_max} °С, корпус: {body_material}',
    'pa-posi': '{model_code} Позиционер {brand}, {acting_type}; {exd}; {ip}',
}


def populate_equipment_type_title_templates(apps, schema_editor):
    EquipmentType = apps.get_model('core', 'EquipmentType')
    for code, title_template in EQUIPMENT_TYPE_TITLE_TEMPLATES.items():
        EquipmentType.objects.filter(code=code).update(title_template=title_template)


def clear_equipment_type_title_templates(apps, schema_editor):
    EquipmentType = apps.get_model('core', 'EquipmentType')
    EquipmentType.objects.filter(
        code__in=list(EQUIPMENT_TYPE_TITLE_TEMPLATES.keys())
    ).update(title_template=None)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_populate_equipment_type_templates'),
    ]

    operations = [
        migrations.RunPython(
            populate_equipment_type_title_templates,
            clear_equipment_type_title_templates,
        ),
    ]
