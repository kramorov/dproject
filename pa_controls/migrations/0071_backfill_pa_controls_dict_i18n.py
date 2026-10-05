from django.db import migrations

MODELS = (
    'SignalType', 'ContactState', 'ContactForm', 'PointsOption',
    'LimitSwitchSensorVariety', 'PaControlMountingStandard',
    'LimitSwitchBody', 'VisualIndicatorType',
)
TEXT_FIELDS = ('name', 'description')
# Для variety дополнительно локализуются шаблоны (Фаза 4, Шаг 2-3)
TEMPLATE_FIELDS = ('name_template', 'description_template')


def _backfill_obj(obj, fields, changed):
    for field in fields:
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
    return changed


def backfill_dict_i18n(apps, schema_editor):
    """Заполнить ``*_i18n["ru"]`` из RU-полей справочников БКВ (Фаза 4, Шаг 3)."""
    for model_name in MODELS:
        Model = apps.get_model('pa_controls', model_name)
        for obj in Model.objects.all():
            changed = _backfill_obj(obj, TEXT_FIELDS, False)
            if model_name == 'LimitSwitchSensorVariety':
                changed = _backfill_obj(obj, TEMPLATE_FIELDS, False) or changed
            if changed:
                obj.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('pa_controls', '0070_contactform_description_i18n_contactform_name_i18n_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_dict_i18n, noop),
    ]
