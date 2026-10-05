from django.db import migrations

FIELDS = (
    'name_template', 'description_template', 'title_template',
    'spec_title_template', 'list_title_template', 'spec_template',
)


def backfill_template_i18n(apps, schema_editor):
    """Заполнить ``*_i18n["ru"]`` из существующих RU-полей (Фаза 4, Шаг 2)."""
    EquipmentType = apps.get_model('core', 'EquipmentType')
    for et in EquipmentType.objects.all():
        changed = False
        for field in FIELDS:
            ru_value = getattr(et, field)
            if not ru_value:
                continue
            i18n = getattr(et, f'{field}_i18n') or {}
            if not isinstance(i18n, dict):
                i18n = {}
            if i18n.get('ru') == ru_value:
                continue
            i18n = dict(i18n)
            i18n['ru'] = ru_value
            setattr(et, f'{field}_i18n', i18n)
            changed = True
        if changed:
            et.save(update_fields=[f'{f}_i18n' for f in FIELDS])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_equipmenttype_description_template_i18n_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_template_i18n, noop),
    ]
