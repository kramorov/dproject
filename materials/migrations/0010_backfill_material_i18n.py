from django.db import migrations

FIELDS = ('name', 'description')


def backfill_material_i18n(apps, schema_editor):
    """Заполнить *_i18n['ru'] из RU-полей материалов (Фаза 4)."""
    for model_name in ('MaterialGeneral', 'MaterialSpecified'):
        Model = apps.get_model('materials', model_name)
        for obj in Model.objects.all():
            changed = False
            for field in FIELDS:
                ru_value = getattr(obj, field)
                if not ru_value:
                    continue
                i18n = getattr(obj, f'{field}_i18n') or {}
                if not isinstance(i18n, dict):
                    i18n = {}
                if i18n.get('ru') == ru_value:
                    continue
                i18n = dict(i18n)
                i18n['ru'] = ru_value
                setattr(obj, f'{field}_i18n', i18n)
                changed = True
            if changed:
                obj.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0009_materialgeneral_description_i18n_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_material_i18n, noop),
    ]
