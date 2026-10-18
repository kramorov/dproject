"""Переименование БУ 'none' → 'basic' (классификация AOX, 2026-10-18).

'none' был «базовый привод с концевиками»; по AOX-классификации это Basic
(управление подачей напряжения на мотор). «Нет управления» — концепция без
записей (моделей пока нет). FK матрицы/Allowed не меняются (переименование
кода, id тот же).
"""
from django.db import migrations


def forwards(apps, schema_editor):
    CU = apps.get_model('params', 'ControlUnitInstalledOption')
    cu = CU.objects.filter(code='none').first()
    if cu is not None:
        cu.code = 'basic'
        cu.kind = 'BASIC'
        cu.name = 'Basic (без БУ, управление подачей напряжения на мотор)'
        cu.save(update_fields=['code', 'kind', 'name'])


def backwards(apps, schema_editor):
    CU = apps.get_model('params', 'ControlUnitInstalledOption')
    cu = CU.objects.filter(code='basic').first()
    if cu is not None:
        cu.code = 'none'
        cu.kind = 'NONE'
        cu.name = 'нет'
        cu.save(update_fields=['code', 'kind', 'name'])


class Migration(migrations.Migration):

    dependencies = [
        ('electric_actuators', '0061_alter_allowedcontrolunitoption_unique_together_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
