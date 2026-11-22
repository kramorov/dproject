# Бэкфилл: существующим карточкам присваивается стандартная строка материала
# штока серии + пересчитывается config_hash.
#
# Карточки генерировались до появления PneumaticShaftMaterialOption — их хэш
# не содержит опции. Стандартная строка (is_default=True, encoding='')
# кодируется в артикуле так же, как «без опции», поэтому это ТОТ ЖЕ продукт:
# бэкфилл сохраняет соответствие карточка↔хэш для конфигураций со стандартным
# материалом штока (иначе дедуп в materialize_configuration промахивается и
# создание карточки падает на UNIQUE constraint sku_id из-за совпадения кода).

from django.db import migrations


def backfill_default_shaft_material(apps, schema_editor):
    from pneumatic_actuators.models.pa_item import PneumaticActuatorCatalogItem
    from pneumatic_actuators.models.pa_options import PneumaticShaftMaterialOption

    defaults = {}
    for row in PneumaticShaftMaterialOption.objects.filter(
        is_active=True, is_default=True
    ).order_by('model_line_id', 'sorting_order'):
        # на случай нескольких стандартных строк — берём первую
        defaults.setdefault(row.model_line_id, row.id)

    if not defaults:
        return

    for item in PneumaticActuatorCatalogItem.objects.filter(
        selected_shaft_material__isnull=True
    ).iterator():
        row_id = defaults.get(item.model_line_id)
        if not row_id:
            continue
        item.selected_shaft_material_id = row_id
        try:
            new_hash = item.compute_config_hash()
        except Exception:
            new_hash = None
        update_fields = {'selected_shaft_material_id': row_id}
        if new_hash and new_hash != item.config_hash:
            update_fields['config_hash'] = new_hash
        PneumaticActuatorCatalogItem.objects.filter(pk=item.pk).update(**update_fields)


class Migration(migrations.Migration):

    dependencies = [
        ('pneumatic_actuators', '0069_alter_pneumaticshaftmaterialoption_shaft_material_description'),
    ]

    operations = [
        migrations.RunPython(backfill_default_shaft_material, migrations.RunPython.noop),
    ]
