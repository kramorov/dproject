# valve_data/migrations/0071_torquepoint_coefficient_long_format.py
# Ручная миграция: ValveTorqueCoefficient переводится в длинный формат
# (строка = точка). Таблица пустая, поэтому удаляем старую модель и
# создаём новую заново.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('valve_data', '0070_seed_torque_references'),
        ('pa_controls', '__first__'),
        ('params', '__first__'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ValveTorqueCoefficient',
        ),
        migrations.CreateModel(
            name='TorquePoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_i18n', models.JSONField(blank=True, default=dict, verbose_name='Переводы имени (ru/en/cn)')),
                ('description_i18n', models.JSONField(blank=True, default=dict, verbose_name='Переводы описания (ru/en/cn)')),
                ('code', models.CharField(max_length=10, unique=True, verbose_name='Код')),
                ('name', models.CharField(help_text='Краткое имя точки, например BTO', max_length=20, verbose_name='Название')),
                ('direction', models.CharField(choices=[('open', 'Открытие'), ('close', 'Закрытие')], max_length=10, verbose_name='Направление')),
                ('position', models.CharField(choices=[('start', 'Начало хода'), ('mid', 'Середина хода'), ('end', 'Конец хода')], max_length=10, verbose_name='Позиция хода')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('sorting_order', models.IntegerField(default=0, verbose_name='Порядок сортировки')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
            ],
            options={
                'verbose_name': 'Точка момента/усилия',
                'verbose_name_plural': 'Точки момента/усилия',
                'ordering': ['sorting_order', 'id'],
            },
        ),
        migrations.AddField(
            model_name='torquethrustcharacteristics',
            name='points',
            field=models.ManyToManyField(blank=True, related_name='characteristics_sets',
                                         to='valve_data.torquepoint',
                                         verbose_name='Точки набора'),
        ),
        migrations.CreateModel(
            name='ValveTorqueCoefficient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('factor', models.DecimalField(decimal_places=3, help_text='Рабочий коэффициент (умножается на базовый момент)', max_digits=6, verbose_name='Коэффициент')),
                ('min_factor', models.DecimalField(blank=True, decimal_places=3, default=0, max_digits=6, null=True, verbose_name='Минимальный коэффициент')),
                ('display', models.CharField(blank=True, help_text='Число или диапазон вида «90%~80%»', max_length=30, verbose_name='Отображаемое значение')),
                ('source', models.CharField(blank=True, max_length=200, verbose_name='Источник')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
                ('sorting_order', models.IntegerField(default=0, verbose_name='Порядок сортировки')),
                ('characteristics', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='valve_coefficients', to='valve_data.torquethrustcharacteristics', verbose_name='Характеристики')),
                ('point', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='valve_coefficients', to='valve_data.torquepoint', verbose_name='Точка')),
                ('seal_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='torque_coefficients', to='valve_data.sealtype', verbose_name='Тип уплотнения')),
                ('support', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='torque_coefficients', to='valve_data.valvesupporttype', verbose_name='Тип опоры пробки')),
                ('valve_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='torque_coefficients', to='params.valvetypes', verbose_name='Тип арматуры')),
            ],
            options={
                'verbose_name': 'Коэффициент момента арматуры',
                'verbose_name_plural': 'Коэффициенты момента арматуры',
                'ordering': ['characteristics', 'sorting_order', 'id'],
                'unique_together': {('characteristics', 'valve_type', 'support', 'seal_type', 'point')},
            },
        ),
    ]
