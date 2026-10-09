from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pneumatic_fittings', '0032_populate_pressure_temp_model_lines'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pneumaticfitting',
            name='pressure_max',
        ),
        migrations.RemoveField(
            model_name='pneumaticfitting',
            name='pressure_min',
        ),
        migrations.RemoveField(
            model_name='pneumaticfitting',
            name='temp_max',
        ),
        migrations.RemoveField(
            model_name='pneumaticfitting',
            name='temp_min',
        ),
        migrations.RemoveField(
            model_name='pneumaticplug',
            name='pressure_max',
        ),
        migrations.RemoveField(
            model_name='pneumaticplug',
            name='pressure_min',
        ),
        migrations.RemoveField(
            model_name='pneumaticplug',
            name='temp_max',
        ),
        migrations.RemoveField(
            model_name='pneumaticplug',
            name='temp_min',
        ),
        migrations.RemoveField(
            model_name='pneumaticsilencer',
            name='pressure_min',
        ),
        migrations.RemoveField(
            model_name='pneumaticsilencer',
            name='temp_max',
        ),
        migrations.RemoveField(
            model_name='pneumaticsilencer',
            name='temp_min',
        ),
    ]
