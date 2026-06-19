# Generated manually — add heater_supply FK to ControlUnitWiring

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('electric_actuators', '0040_control_unit_wiring'),
        ('params', '0068_actuator_heater_supply'),
    ]

    operations = [
        migrations.AddField(
            model_name='controlunitwiring',
            name='heater_supply',
            field=models.ForeignKey(
                blank=True,
                help_text='Вариант питания антиконденсатного обогрева привода',
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name='control_unit_wirings',
                to='params.actuatorheatersupply',
                verbose_name='Питание обогрева',
            ),
        ),
    ]
