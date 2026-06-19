# Generated manually — add 'digital' choice to InputSignalSpec.signal_category

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('params', '0062_signalrole_direction_bidirectional'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inputsignalspec',
            name='signal_category',
            field=models.CharField(
                choices=[
                    ('discrete', 'Дискретный'),
                    ('analog', 'Аналоговый'),
                    ('digital', 'Цифровой'),
                ],
                help_text='Дискретный (вкл/выкл), аналоговый (4-20мА, 0-10В) или цифровой (Modbus RTU, HART)',
                max_length=20,
                verbose_name='Категория сигнала',
            ),
        ),
    ]
