# Удаление legacy сигнальных через-опций (фаза 7).
# RemoveField на удаляемых моделях опущены (таблица удаляется целиком),
# оставлены только снятия FK у остающихся моделей и DeleteModel.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('electric_actuators', '0059_allowedcontrolunitoption_ext_encoding'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='electricactuatorselected',
            name='selected_blinker_option',
        ),
        migrations.RemoveField(
            model_name='electricactuatorselected',
            name='selected_control_unit_option',
        ),
        migrations.RemoveField(
            model_name='electricactuatorselected',
            name='selected_end_switches_option',
        ),
        migrations.RemoveField(
            model_name='electricactuatorselected',
            name='selected_mechanical_indicator_option',
        ),
        migrations.RemoveField(
            model_name='electricactuatorselected',
            name='selected_torque_switches_option',
        ),
        migrations.RemoveField(
            model_name='electricactuatorselected',
            name='selected_way_switches_option',
        ),
        migrations.RemoveField(
            model_name='electricactuatorconstructor',
            name='selected_blinker_option',
        ),
        migrations.RemoveField(
            model_name='electricactuatorconstructor',
            name='selected_end_switches_option',
        ),
        migrations.RemoveField(
            model_name='electricactuatorconstructor',
            name='selected_mechanical_indicator_option',
        ),
        migrations.RemoveField(
            model_name='electricactuatorconstructor',
            name='selected_torque_switches_option',
        ),
        migrations.RemoveField(
            model_name='electricactuatorconstructor',
            name='selected_way_switches_option',
        ),
        migrations.DeleteModel(
            name='AllowedSignalProfileOption',
        ),
        migrations.DeleteModel(
            name='ControlUnitWiring',
        ),
        migrations.DeleteModel(
            name='ElectricBlinkerOption',
        ),
        migrations.DeleteModel(
            name='ElectricControlUnitInstalledOption',
        ),
        migrations.DeleteModel(
            name='ElectricControlUnitOption',
        ),
        migrations.DeleteModel(
            name='ElectricEndSwitchesOption',
        ),
        migrations.DeleteModel(
            name='ElectricMechanicalIndicatorOption',
        ),
        migrations.DeleteModel(
            name='ElectricOperatingModeOption',
        ),
        migrations.DeleteModel(
            name='ElectricTorqueSwitchesOption',
        ),
        migrations.DeleteModel(
            name='ElectricWaySwitchesOption',
        ),
    ]
