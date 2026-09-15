# cable_glands/migrations/0014_populate_cableglandmodelline_ip_m2m.py
"""Заполнить M2M ip у всех серий кабельных вводов значениями IP66 / IP67 / IP68."""

from django.db import migrations


def populate_ip(apps, schema_editor):
    CableGlandModelLine = apps.get_model('cable_glands', 'CableGlandModelLine')
    IpOption = apps.get_model('params', 'IpOption')

    codes = ('IP66', 'IP67', 'IP68')
    ips = list(IpOption.objects.filter(code__in=codes).order_by('ip_rank'))
    if not ips:
        return

    for ml in CableGlandModelLine.objects.all():
        ml.ip.set(ips)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cable_glands', '0013_remove_cableglandmodelline_ip_cableglandmodelline_ip'),
    ]

    operations = [
        migrations.RunPython(populate_ip, noop),
    ]
