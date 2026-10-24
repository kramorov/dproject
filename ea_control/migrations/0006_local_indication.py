# ea_control/migrations/0006_local_indication.py
"""Местная индикация: справочники CuLocalControlType/CuDisplayType и
типизированные нагрузки опций (local_control_type FK, display_types M2M)."""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ea_control', '0005_cusignaltype_voltage_fk'),
    ]

    operations = [
        migrations.CreateModel(
            name='CuDisplayType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_i18n', models.JSONField(blank=True, default=dict, help_text='JSON: {"ru": ..., "en": ..., "cn": ...}. "ru" синхронизируется с названием.', verbose_name='Переводы названия (ru/en/cn)')),
                ('description_i18n', models.JSONField(blank=True, default=dict, help_text='JSON: {"ru": ..., "en": ..., "cn": ...}. "ru" синхронизируется с описанием.', verbose_name='Переводы описания (ru/en/cn)')),
                ('name', models.CharField(help_text='Например: «Светодиод», «Мигающий светодиод», «На LCD-экране»', max_length=200, verbose_name='Название')),
                ('code', models.CharField(help_text='Уникальный код, например «LED», «LED_BLINK», «LCD»', max_length=50, unique=True, verbose_name='Код')),
                ('description', models.TextField(blank=True, help_text='Примечания к виду отображения', verbose_name='Описание')),
                ('sorting_order', models.IntegerField(default=0, verbose_name='Порядок сортировки')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
            ],
            options={
                'verbose_name': 'Вид отображения',
                'verbose_name_plural': 'Виды отображения',
                'ordering': ['sorting_order', 'code'],
            },
        ),
        migrations.CreateModel(
            name='CuLocalControlType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_i18n', models.JSONField(blank=True, default=dict, help_text='JSON: {"ru": ..., "en": ..., "cn": ...}. "ru" синхронизируется с названием.', verbose_name='Переводы названия (ru/en/cn)')),
                ('description_i18n', models.JSONField(blank=True, default=dict, help_text='JSON: {"ru": ..., "en": ..., "cn": ...}. "ru" синхронизируется с описанием.', verbose_name='Переводы описания (ru/en/cn)')),
                ('name', models.CharField(help_text='Например: «Кнопки», «Селекторы»', max_length=200, verbose_name='Название')),
                ('code', models.CharField(help_text='Уникальный код, например «BUTTONS», «SELECTOR»', max_length=50, unique=True, verbose_name='Код')),
                ('description', models.TextField(blank=True, help_text='Примечания к виду органов управления', verbose_name='Описание')),
                ('sorting_order', models.IntegerField(default=0, verbose_name='Порядок сортировки')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
            ],
            options={
                'verbose_name': 'Орган местного управления',
                'verbose_name_plural': 'Органы местного управления',
                'ordering': ['sorting_order', 'code'],
            },
        ),
        migrations.AlterField(
            model_name='cuslotoption',
            name='kind',
            field=models.CharField(choices=[('signal', 'Сигнал'), ('heater', 'Питание обогрева'), ('power', 'Питание цепей управления'), ('logic', 'Логика работы'), ('signal_type', 'Тип управляющего сигнала'), ('unit', 'Блок управления (слот control_unit)'), ('local_control', 'Орган местного управления'), ('display', 'Вид отображения'), ('none', 'Без сигнала (none-строка)'), ('pair', 'Пара контактов (Откр/Закр)')], default='signal', help_text='signal — сигнал/протокол; heater — обогрев; power — питание цепей; logic — логика работы; signal_type — тип сигнала; unit — БУ (слот control_unit); local_control — орган местного управления; display — вид(ы) отображения; none — опция без полезной нагрузки; pair — пара контактов Откр/Закр', max_length=20, verbose_name='Тип опции'),
        ),
        migrations.AddField(
            model_name='cuslotoption',
            name='local_control_type',
            field=models.ForeignKey(blank=True, help_text='Для kind=local_control: кнопки/селекторы (слот LOCAL_CONTROL_DESIGN узла «Местная индикация»)', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='slot_options', to='ea_control.culocalcontroltype', verbose_name='Орган местного управления'),
        ),
        migrations.AddField(
            model_name='cuslotoption',
            name='display_types',
            field=models.ManyToManyField(blank=True, help_text='Для kind=display: один или несколько видов отображения (слоты сигналов индикации; комбинация — например, «на LCD + мигающий светодиод»)', related_name='slot_options', to='ea_control.cudisplaytype', verbose_name='Виды отображения'),
        ),
    ]
