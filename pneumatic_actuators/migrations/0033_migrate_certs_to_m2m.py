# Generated migration — fill with data migration code

from django.db import migrations


def migrate_certs(apps, schema_editor):
    """Перенос сертификатов из through-модели в cert_docs M2M (CertDocMixin)."""
    PneumaticActuatorModelLine = apps.get_model('pneumatic_actuators', 'PneumaticActuatorModelLine')
    PneumaticActuatorModelLineCertRelation = apps.get_model('pneumatic_actuators', 'PneumaticActuatorModelLineCertRelation')

    for ml in PneumaticActuatorModelLine.objects.all():
        cert_ids = list(
            PneumaticActuatorModelLineCertRelation.objects
            .filter(model_line=ml)
            .values_list('cert_data_id', flat=True)
        )
        if cert_ids:
            ml.cert_docs.add(*cert_ids)


def reverse_migrate(apps, schema_editor):
    """Откат не нужен — данные остаются в through-модели."""
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('pneumatic_actuators', '0032_remove_cert_docs_from_model_line_item'),
    ]

    operations = [
        migrations.RunPython(migrate_certs, reverse_migrate),
    ]
