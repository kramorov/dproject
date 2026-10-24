# ea_control/migrations/0007_unit_power_cable_glands.py
"""Питание БУ (CuUnitPowerSource) и резьба кабельных вводов БУ:
kinds unit_power/cable_gland + типизированные нагрузки опций."""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ea_control', '0006_local_indication'),
        ('params', '0076_remove_safetypositionoption_requires_battery'),
    ]

    operations = [
        migrations.CreateModel(
            name='CuUnitPowerSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_i18n', models.JSONField(blank=True, default=dict, help_text='JSON: {"ru": ..., "en": ..., "cn": ...}. "ru" синхронизируется с названием.', verbose_name='Переводы названия (ru/en/cn)')),
                ('description_i18n', models.JSONField(blank=True, default=dict, help_text='JSON: {"ru": ..., "en": ..., "cn": ...}. "ru" синхронизируется с описанием.', verbose_name='Переводы описания (ru/en/cn)')),
                ('name', models.CharField(help_text='Например: «От цепей питания привода (общий кабель)»', max_length=200, verbose_name='Название')),
                ('code', models.CharField(help_text='Уникальный код, например «SHARED_CABLE», «SEPARATE_CABLE»', max_length=50, unique=True, verbose_name='Код')),
                ('description', models.TextField(blank=True, help_text='Примечания к способу подвода питания БУ', verbose_name='Описание')),
                ('sorting_order', models.IntegerField(default=0, verbose_name='Порядок сортировки')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
            ],
            options={
                'verbose_name': 'Питание БУ',
                'verbose_name_plural': 'Питания БУ',
                'ordering': ['sorting_order', 'code'],
            },
        ),
        migrations.AlterField(
            model_name='cuslotoption',
            name='kind',
            field=models.CharField(choices=[('signal', 'Сигнал'), ('heater', 'Питание обогрева'), ('power', 'Питание цепей управления'), ('logic', 'Логика работы'), ('signal_type', 'Тип управляющего сигнала'), ('unit', 'Блок управления (слот control_unit)'), ('local_control', 'Орган местного управления'), ('display', 'Вид отображения'), ('unit_power', 'Питание БУ'), ('cable_gland', 'Кабельные вводы БУ'), ('none', 'Без сигнала (none-строка)'), ('pair', 'Пара контактов (Откр/Закр)')], default='signal', help_text='signal — сигнал/протокол; heater — обогрев; power — питание цепей; logic — логика работы; signal_type — тип сигнала; unit — БУ (слот control_unit); local_control — орган местного управления; display — вид(ы) отображения; unit_power — питание БУ; cable_gland — резьба кабельных вводов БУ; none — опция без полезной нагрузки; pair — пара контактов Откр/Закр', max_length=20, verbose_name='Тип опции'),
        ),
        migrations.AddField(
            model_name='cuslotoption',
            name='unit_power_source',
            field=models.ForeignKey(blank=True, help_text='Для kind=unit_power: общий кабель с приводом или отдельный кабель (слот CU_POWER_SUPPLY)', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='slot_options', to='ea_control.cuunitpowersource', verbose_name='Питание БУ'),
        ),
        migrations.AddField(
            model_name='cuslotoption',
            name='cable_gland_thread',
            field=models.ForeignKey(blank=True, help_text='Для kind=cable_gland: резьба отверстий ввода кабелей БУ (глобальный справочник params.ThreadSize; слот CU_CABLE_GLANDS)', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='cu_slot_options', to='params.threadsize', verbose_name='Резьба кабельных вводов БУ'),
        ),
    ]
