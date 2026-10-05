from django.db import migrations


def backfill_lsb_description_i18n(apps, schema_editor):
    """Заполнить description_i18n['ru'] из description серий БКВ (Фаза 4)."""
    LimitSwitchModelLine = apps.get_model('pa_controls', 'LimitSwitchModelLine')
    for ml in LimitSwitchModelLine.objects.all():
        ru_value = ml.description
        if not ru_value:
            continue
        i18n = ml.description_i18n or {}
        if not isinstance(i18n, dict):
            i18n = {}
        if i18n.get('ru') == ru_value:
            continue
        i18n = dict(i18n)
        i18n['ru'] = ru_value
        ml.description_i18n = i18n
        ml.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('pa_controls', '0073_limitswitchmodelline_description_i18n'),
    ]

    operations = [
        migrations.RunPython(backfill_lsb_description_i18n, noop),
    ]
