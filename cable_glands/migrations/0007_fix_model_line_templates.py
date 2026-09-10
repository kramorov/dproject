# Generated manually — data fix: placeholder rename and removal in model line templates.

import re

from django.db import migrations


def fix_model_line_templates(apps, schema_editor):
    """Заменяет {flags} -> {cable_types} и убирает {size} из шаблонов серии."""
    CableGlandModelLine = apps.get_model('cable_glands', 'CableGlandModelLine')
    for ml in CableGlandModelLine.objects.all():
        changed = False
        for field in ('name_template', 'description_template'):
            value = getattr(ml, field)
            if not value:
                continue
            new_value = value.replace('{flags}', '{cable_types}')
            new_value = re.sub(r'\s*\{size\}\s*', ' ', new_value)
            if new_value != value:
                setattr(ml, field, new_value)
                changed = True
        if changed:
            ml.save(update_fields=['name_template', 'description_template'])


class Migration(migrations.Migration):

    dependencies = [
        ('cable_glands', '0006_cableglandmodellineitem_cable_diameter_outer_max_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_model_line_templates, migrations.RunPython.noop),
    ]
