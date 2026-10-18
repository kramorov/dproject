# Перенос значений «разрешённый БУ × напряжение» из старой схемы
# (ElectricPowerSupplyOption×ElectricControlUnitOption) в новую
# (AllowedControlUnitOption). Однократный переезд; старые таблицы
# удаляются в фазе 7 — обратная поддержка не предусмотрена.
from django.db import migrations


def backfill(apps, schema_editor):
    Allowed = apps.get_model('electric_actuators', 'AllowedControlUnitOption')
    CUOpt = apps.get_model('electric_actuators', 'ElectricControlUnitOption')
    created = 0
    for cu_opt in CUOpt.objects.filter(is_active=True).select_related(
            'power_supply_option__power_supply',
            'power_supply_option__model_line_item__model_line',
            'control_unit'):
        line = cu_opt.power_supply_option.model_line_item.model_line
        ps = cu_opt.power_supply_option.power_supply
        cu = cu_opt.control_unit
        if Allowed.objects.filter(model_line=line, control_unit=cu,
                                 power_supply=ps).exists():
            continue
        Allowed.objects.create(
            model_line=line, control_unit=cu, power_supply=ps,
            encoding=cu_opt.encoding or '', is_active=True)
        created += 1
    print(f'backfill AllowedControlUnitOption: создано {created}')


class Migration(migrations.Migration):

    dependencies = [
        ('electric_actuators', '0057_alter_allowedcontrolunitoption_unique_together_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
