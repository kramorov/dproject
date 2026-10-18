# electric_actuators/migrations/0070_migrate_certs_to_m2m.py
"""Перенос сертификатов серий ЭП из через-модели в cert_docs M2M (CertDocMixin).

Паттерн — pneumatic_actuators 0033-0034 (переход на общий M2M; через-модель
AbstractCertRelation — устаревший подход). Откат не нужен: данные остаются
в через-модели до её удаления следующей миграцией.
"""
from django.db import migrations


def migrate_certs(apps, schema_editor):
    ModelLine = apps.get_model(
        'electric_actuators', 'ElectricActuatorModelLine')
    CertRelation = apps.get_model(
        'electric_actuators', 'ElectricActuatorModelLineCertRelation')

    for ml in ModelLine.objects.all():
        cert_ids = list(
            CertRelation.objects
            .filter(model_line=ml, is_active=True)
            .order_by('sorting_order')
            .values_list('cert_data_id', flat=True)
        )
        if cert_ids:
            ml.cert_docs.add(*cert_ids)


def reverse_migrate(apps, schema_editor):
    # Откат не нужен — данные остаются в through-модели.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('electric_actuators', '0069_electricactuatormodelline_cert_docs'),
    ]

    operations = [
        migrations.RunPython(migrate_certs, reverse_migrate),
    ]
