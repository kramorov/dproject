# pneumatic_actuators/migrations/0077_torque_long_format.py
# Длинный формат таблицы моментов (строка = точка). Три фазы:
#   1) добавляем point/value (nullable);
#   2) копируем данные: воздух bto/rto/eto → BTO/RTO/ETO; пружина (pressure='spring')
#      разворачивается в ориентацию закрытия: BTC=eto, RTC=rto, ETC=bto;
#   3) удаляем старые колонки, делаем новые обязательными, уникальность набора.
import django.db.models.deletion
from django.db import migrations, models


def copy_data(apps, schema_editor):
    TorqueRow = apps.get_model('pneumatic_actuators', 'BodyThrustTorqueTable')
    TorquePoint = apps.get_model('valve_data', 'TorquePoint')

    points = {p.code: p for p in TorquePoint.objects.all()}
    if len(points) < 6:
        raise RuntimeError('TorquePoint справочник не заполнен — сначала примените valve_data 0073.')

    created = 0
    for row in TorqueRow.objects.all().select_related('pressure'):
        is_spring = row.pressure.code == 'spring'
        mapping = (
            [('etc', row.bto), ('rtc', row.rto), ('btc', row.eto)]
            if is_spring
            else [('bto', row.bto), ('rto', row.rto), ('eto', row.eto)]
        )
        for code, value in mapping:
            if value is None:
                continue
            TorqueRow.objects.create(
                body_id=row.body_id, pressure_id=row.pressure_id,
                spring_qty_id=row.spring_qty_id, point=points[code],
                value=value)
            created += 1
        row.delete()
    print(f'torque long-format: created {created} point rows')


def backwards_data(apps, schema_editor):
    TorqueRow = apps.get_model('pneumatic_actuators', 'BodyThrustTorqueTable')
    TorqueRow.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pneumatic_actuators', '0076_pneumaticactuatorspringsqty_uq_pa_springsqty_code'),
        ('valve_data', '0073_seed_torque_points'),
    ]

    operations = [
        migrations.AddField(
            model_name='bodythrusttorquetable',
            name='point',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT,
                                    related_name='pa_torque_rows', to='valve_data.torquepoint',
                                    verbose_name='Точка'),
        ),
        migrations.AddField(
            model_name='bodythrusttorquetable',
            name='value',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=10, null=True,
                                      verbose_name='Момент/усилие'),
        ),
        # Старые колонки делаем nullable, чтобы можно было вставлять строки точек
        # (bto/rto/eto остаются NOT NULL в схеме).
        migrations.AlterField(
            model_name='bodythrusttorquetable',
            name='bto',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=10, null=True,
                                      verbose_name='Момент/усилие BTO'),
        ),
        migrations.AlterField(
            model_name='bodythrusttorquetable',
            name='rto',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=10, null=True,
                                      verbose_name='Момент/усилие RTO'),
        ),
        migrations.AlterField(
            model_name='bodythrusttorquetable',
            name='eto',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=10, null=True,
                                      verbose_name='Момент/усилие ETO'),
        ),
        migrations.RunPython(copy_data, backwards_data),
        migrations.RemoveField(
            model_name='bodythrusttorquetable',
            name='bto',
        ),
        migrations.RemoveField(
            model_name='bodythrusttorquetable',
            name='rto',
        ),
        migrations.RemoveField(
            model_name='bodythrusttorquetable',
            name='eto',
        ),
        migrations.AlterField(
            model_name='bodythrusttorquetable',
            name='point',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                    related_name='pa_torque_rows', to='valve_data.torquepoint',
                                    verbose_name='Точка',
                                    help_text='BTO/RTO/ETO (воздух) или BTC/RTC/ETC (пружина)'),
        ),
        migrations.AlterField(
            model_name='bodythrusttorquetable',
            name='value',
            field=models.DecimalField(decimal_places=1, help_text='Значение момента/усилия в точке',
                                      max_digits=10, verbose_name='Момент/усилие'),
        ),
        migrations.AddConstraint(
            model_name='bodythrusttorquetable',
            constraint=models.UniqueConstraint(fields=('body', 'pressure', 'spring_qty', 'point'),
                                               name='uq_pa_torque_row'),
        ),
    ]
