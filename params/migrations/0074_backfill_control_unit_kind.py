# params/migrations/0074_backfill_control_unit_kind.py
"""
Backfill поля kind у существующих записей ControlUnitInstalledOption (фаза 3,
пункт F7 ревью №2).

Маппинг по кодам текущих 12 записей:
    none        → NONE         (без БУ)
    pote        → NONE         (потенциометр — устройство ОС, не БУ)
    tr-4-20, tr10 → NONE       (трансмиттеры — устройства ОС, не БУ)
    posi10, posi-4-20 → POSITIONER
    int-o/int-l/int-n (+hr/mb/pb) → INTEGRATED
Неизвестные коды — NONE (безопасный фолбэк).
"""
from django.db import migrations

KIND_BY_CODE = {
    'none': 'NONE',
    'pote': 'NONE',
    'tr-4-20': 'NONE',
    'tr10': 'NONE',
    'posi10': 'POSITIONER',
    'posi-4-20': 'POSITIONER',
    'int-o': 'INTEGRATED',
    'int-l': 'INTEGRATED',
    'int-n': 'INTEGRATED',
    'int-n-hr': 'INTEGRATED',
    'int-n-mb': 'INTEGRATED',
    'int-n-pb': 'INTEGRATED',
}


def backfill_kind(apps, schema_editor):
    ControlUnit = apps.get_model('params', 'ControlUnitInstalledOption')
    for obj in ControlUnit.objects.all():
        kind = KIND_BY_CODE.get(obj.code, 'NONE')
        if obj.kind != kind:
            obj.kind = kind
            obj.save(update_fields=['kind'])


def reverse_backfill(apps, schema_editor):
    ControlUnit = apps.get_model('params', 'ControlUnitInstalledOption')
    ControlUnit.objects.update(kind='NONE')


class Migration(migrations.Migration):

    dependencies = [
        ('params', '0073_controlunitinstalledoption_accepts_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_kind, reverse_backfill),
    ]
