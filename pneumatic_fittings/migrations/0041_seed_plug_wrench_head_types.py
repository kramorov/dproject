# Seed справочник «Тип головки под ключ» (заглушки).
from django.db import migrations


def seed_plug_wrench_head_types(apps, schema_editor):
    PlugWrenchHeadType = apps.get_model('pneumatic_fittings', 'PlugWrenchHeadType')
    rows = [
        {
            'name': 'Внутренний шестигранник',
            'code': 'internal_hex',
            'name_i18n': {'ru': 'Внутренний шестигранник', 'en': 'Internal hex', 'cn': '内六角'},
            'description': 'Под внутренний шестигранник',
            'sorting_order': 1,
            'is_active': True,
        },
        {
            'name': 'Внешний шестигранник',
            'code': 'external_hex',
            'name_i18n': {'ru': 'Внешний шестигранник', 'en': 'External hex', 'cn': '外六角'},
            'description': 'Под обычный гаечный ключ (монтажная гайка / внешний шестигранник)',
            'sorting_order': 2,
            'is_active': True,
        },
    ]
    for row in rows:
        PlugWrenchHeadType.objects.get_or_create(code=row['code'], defaults=row)


def reverse_seed(apps, schema_editor):
    PlugWrenchHeadType = apps.get_model('pneumatic_fittings', 'PlugWrenchHeadType')
    PlugWrenchHeadType.objects.filter(code__in=['internal_hex', 'external_hex']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pneumatic_fittings', '0040_plugwrenchheadtype_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_plug_wrench_head_types, reverse_seed),
    ]
