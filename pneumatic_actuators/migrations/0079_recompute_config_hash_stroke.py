# Пересчёт config_hash всех карточек пневмоприводов: в схему хэша добавлено
# поле stroke (config_hash_fields). Для ротационных карточек stroke=None —
# в каноническую строку добавляется пустой сегмент, поэтому хэш меняется у ВСЕХ
# карточек. Без пересчёта дедуп по config_hash (materialize_configuration,
# generate_pa_cards) перестаёт находить существующие карточки и падает на
# совпадении артикула/SKU.
from django.db import migrations


def recompute_config_hashes(apps, schema_editor):
    from pneumatic_actuators.models.pa_item import PneumaticActuatorCatalogItem

    for item in PneumaticActuatorCatalogItem.objects.exclude(
        config_hash__isnull=True
    ).iterator():
        try:
            new_hash = item.compute_config_hash()
        except Exception:
            new_hash = None
        if new_hash and new_hash != item.config_hash:
            PneumaticActuatorCatalogItem.objects.filter(pk=item.pk).update(
                config_hash=new_hash)


class Migration(migrations.Migration):

    dependencies = [
        ('pneumatic_actuators', '0078_pneumaticactuatorcatalogitem_stroke_and_more'),
    ]

    operations = [
        migrations.RunPython(recompute_config_hashes, migrations.RunPython.noop),
    ]
