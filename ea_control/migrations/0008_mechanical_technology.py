# ea_control/migrations/0008_mechanical_technology.py
"""Технология датчика «Механический» (концевые датчики БУ INT/O)."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ea_control', '0007_unit_power_cable_glands'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cufeedbackdevice',
            name='technology',
            field=models.CharField(choices=[('POTENTIOMETER', 'Потенциометрический'), ('MWG', 'Магнитно-волновой (MWG)'), ('ELECTRONIC', 'Электронный'), ('MECHANICAL', 'Механический')], help_text='Потенциометрический / магнитно-волновой / электронный', max_length=20, verbose_name='Технология'),
        ),
    ]
