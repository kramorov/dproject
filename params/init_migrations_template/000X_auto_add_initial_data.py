# migrations/000X_auto_add_initial_data.py
from django.db import migrations

from .apps import get_this_app_name

#power_supplies_add_initial_data, exd_add_initial_data, ip_add_initial_data, body_coating_add_initial_data, \
#blinker_add_initial_data, switches_add_initial_data, env_temp_add_initial_data, \
#digital_protocol_support_option_add_initial_data, control_unit_installed_option_add_initial_data, \
#actuator_gearbox_types_add_initial_data, actuator_gearbox_combination_types_add_initial_data, \
#valve_types_add_initial_data



def power_supplies_add_initial_data(apps, schema_editor):
    this_model = apps.get_model(get_this_app_name(), 'PowerSupplies')
    this_model.objects.get_or_create(symbolic_code='220/50', voltage_value=220, voltage_type='AC',
                                     text_description='220В/50Гц/1ф')
    this_model.objects.get_or_create(symbolic_code='380/50', voltage_value=380, voltage_type='AC',
                                     text_description='380В/50Гц/3ф')
    this_model.objects.get_or_create(symbolic_code='24DC', voltage_value=24, voltage_type='DC',
                                     text_description='24В пост. Ток')


def exd_add_initial_data(apps, schema_editor):
    this_model = apps.get_model(get_this_app_name(), 'ExdOption')
    this_model.objects.get_or_create(symbolic_code='NONE', exd_full_code='Общепромышленное',
                                     text_description='Общепромышленное')
    this_model.objects.get_or_create(symbolic_code='Exd', exd_full_code='1 Exd IIC T5 Gb X',
                                     text_description='1 Exd IIC T5 Gb X')
    this_model.objects.get_or_create(symbolic_code='Extc', exd_full_code='Ex tc IIIC T95°C  Dc',
                                     text_description='Ex tc IIIC T95°C  Dc')


def ip_add_initial_data(apps, schema_editor):
    this_model = apps.get_model(get_this_app_name(), 'IpOption')
    this_model.objects.get_or_create(symbolic_code='IP54', ip_rank=54,
                                     text_description='IP54')
    this_model.objects.get_or_create(symbolic_code='IP65', ip_rank=65,
                                     text_description='IP65')
    this_model.objects.get_or_create(symbolic_code='IP67', ip_rank=67,
                                     text_description='IP67')
    this_model.objects.get_or_create(symbolic_code='IP68', ip_rank=68,
                                     text_description='IP68 *(до 2м. в течение не более 60 мин.)')


def body_coating_add_initial_data(apps, schema_editor):
    this_model = apps.get_model(get_this_app_name(), 'BodyCoatingOption')
    this_model.objects.get_or_create(symbolic_code='STD',
                                     text_description='Стандарт, аналог AUMA KN')
    this_model.objects.get_or_create(symbolic_code='KS',
                                     text_description='Аналог AUMA KS (агрессивная среда)')
    this_model.objects.get_or_create(symbolic_code='KX',
                                     text_description='Аналог AUMA KX (экстремально агрессивная среда)')


def blinker_add_initial_data(apps, schema_editor):
    this_model = apps.get_model(get_this_app_name(), 'BlinkerOption')
    this_model.objects.get_or_create(symbolic_code='NONE',
                                     text_description='Нет')
    this_model.objects.get_or_create(symbolic_code='blinker_int',
                                     text_description='Блинкер на блоке управления')


def switches_add_initial_data(apps, schema_editor):
    this_model = apps.get_model(get_this_app_name(), 'SwitchesParameters')
    this_model.objects.get_or_create(symbolic_code='NONE',
                                     text_description='нет')
    this_model.objects.get_or_create(symbolic_code='SPDT',
                                     text_description='одиночные (стандарт)')
    this_model.objects.get_or_create(symbolic_code='DPDT',
                                     text_description='сдвоенные')


def env_temp_add_initial_data(apps, schema_editor):
    this_model = apps.get_model(get_this_app_name(), 'EnvTempParameters')
    this_model.objects.get_or_create(symbolic_code='NONE', min_temp=-20, max_temp=70,
                                     text_description='Стандарт (от -20 °C до +70 °C)')
    this_model.objects.get_or_create(symbolic_code='LT', min_temp=-40, max_temp=70,
                                     text_description='LT (от -40 °C до +70 °C)')
    this_model.objects.get_or_create(symbolic_code='VLT', min_temp=-60, max_temp=70,
                                     text_description='VLT (от -60 °C до +70 °C)')


def digital_protocol_support_option_add_initial_data(apps, schema_editor):
    this_model = apps.get_model(get_this_app_name(), 'DigitalProtocolsSupportOption')
    this_model.objects.get_or_create(symbolic_code='NONE',
                                     text_description='без цифровых протоколов')
    this_model.objects.get_or_create(symbolic_code='MB',
                                     text_description='ModBus')
    this_model.objects.get_or_create(symbolic_code='PB',
                                     text_description='ProfiBus')
    this_model.objects.get_or_create(symbolic_code='HART',
                                     text_description='HART')


def control_unit_installed_option_add_initial_data(apps, schema_editor):
    this_model = apps.get_model(get_this_app_name(), 'ControlUnitInstalledOption')
    this_model.objects.get_or_create(symbolic_code='NONE',
                                     text_description='нет')
    this_model.objects.get_or_create(symbolic_code='INT_O',
                                     text_description='INT/O')
    this_model.objects.get_or_create(symbolic_code='INT_L',
                                     text_description='INT/L')
    this_model.objects.get_or_create(symbolic_code='INT_N',
                                     text_description='INT/N')


def actuator_gearbox_types_add_initial_data(apps, schema_editor):
    this_model = apps.get_model(get_this_app_name(), 'ActuatorGearboxOutputType')
    this_model.objects.get_or_create(symbolic_code='Q',
                                     text_description='Четвертьоборотный')
    this_model.objects.get_or_create(symbolic_code='M',
                                     text_description='Многоборотный')
    this_model.objects.get_or_create(symbolic_code='L',
                                     text_description='Линейный')
    this_model.objects.get_or_create(symbolic_code='NO',
                                     text_description='нет')

def actuator_gearbox_combination_types_add_initial_data(apps, schema_editor):
    this_model = apps.get_model(get_this_app_name(), 'ActuatorGearBoxCombinationTypes')
    this_model.objects.get_or_create(
        symbolic_code='Q',
        electric_actuator_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='Q'),
        gearbox_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='NO'),
        pneumatic_actuator_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='NO'),
        text_description='Четвертьоборотный электропривод')
    this_model.objects.get_or_create(
        symbolic_code='Q',
        electric_actuator_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='M'),
        gearbox_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='Q'),
        pneumatic_actuator_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='NO'),
        text_description='Многооборотный электропривод с четвертьоборотным редуктором')
    this_model.objects.get_or_create(
        symbolic_code='Q',
        electric_actuator_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='NO'),
        gearbox_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='NO'),
        pneumatic_actuator_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='Q'),
        text_description='Четвертьоборотный пневмопривод')
    this_model.objects.get_or_create(
        symbolic_code='M',
        electric_actuator_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='M'),
        gearbox_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='NO'),
        pneumatic_actuator_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='NO'),
        text_description='Многооборотный электропривод')
    this_model.objects.get_or_create(
        symbolic_code='M',
        electric_actuator_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='M'),
        gearbox_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='M'),
        pneumatic_actuator_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='NO'),
        text_description='Многооборотный электропривод с многооборотным редуктором')
    this_model.objects.get_or_create(
        symbolic_code='L',
        electric_actuator_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='L'),
        gearbox_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='NO'),
        pneumatic_actuator_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='NO'),
        text_description='Линейный электропривод')
    this_model.objects.get_or_create(
        symbolic_code='L',
        electric_actuator_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='M'),
        gearbox_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='L'),
        pneumatic_actuator_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='NO'),
        text_description='Многооборотный электропривод с линейным модулем')
    this_model.objects.get_or_create(
        symbolic_code='L',
        electric_actuator_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='NO'),
        gearbox_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='NO'),
        pneumatic_actuator_type=ActuatorGearboxOutputType.objects.filter(symbolic_code='L'),
        text_description='Линейный пневмопривод')


def valve_types_add_initial_data(apps, schema_editor):
    this_model = apps.get_model(get_this_app_name(), 'ValveTypes')
    this_model.objects.get_or_create(
        symbolic_code='КШ',
        actuator_gearbox_combinations=ActuatorGearBoxCombinationTypes.objects.filter(symbolic_code='Q'),
        text_description='Кран шаровый')
    this_model.objects.get_or_create(
        symbolic_code='ЗД',
        actuator_gearbox_combinations=ActuatorGearBoxCombinationTypes.objects.filter(symbolic_code='Q'),
        text_description='Затвор дисковый')
    this_model.objects.get_or_create(
        symbolic_code='ЗК',
        actuator_gearbox_combinations=ActuatorGearBoxCombinationTypes.objects.filter(symbolic_code='M')|
                                      ActuatorGearBoxCombinationTypes.objects.filter(symbolic_code='L'),
        text_description='Задвижка клиновая')
    this_model.objects.get_or_create(
        symbolic_code='ЗШ',
        actuator_gearbox_combinations=ActuatorGearBoxCombinationTypes.objects.filter(symbolic_code='M') |
                                      ActuatorGearBoxCombinationTypes.objects.filter(symbolic_code='L'),
        text_description='Задвижка шиберная')
    this_model.objects.get_or_create(
        symbolic_code='КК',
        actuator_gearbox_combinations=ActuatorGearBoxCombinationTypes.objects.filter(symbolic_code='L'),
        text_description='Клапан')

init_data_modules=['power_supplies_add_initial_data', 'exd_add_initial_data', 'ip_add_initial_data', 'body_coating_add_initial_data', \
'blinker_add_initial_data', 'switches_add_initial_data', 'env_temp_add_initial_data', \
'digital_protocol_support_option_add_initial_data', 'control_unit_installed_option_add_initial_data', \
'actuator_gearbox_types_add_initial_data', 'actuator_gearbox_combination_types_add_initial_data', \
'valve_types_add_initial_data']

class Migration(migrations.Migration):
    dependencies = [
        # Укажите зависимости для вашей миграции, например:
        # ('uzra1', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(power_supplies_add_initial_data),
        migrations.RunPython(exd_add_initial_data),
        migrations.RunPython(ip_add_initial_data),
        migrations.RunPython(body_coating_add_initial_data),
        migrations.RunPython(blinker_add_initial_data),
        migrations.RunPython(switches_add_initial_data),
        migrations.RunPython(env_temp_add_initial_data),
        migrations.RunPython(digital_protocol_support_option_add_initial_data),
        migrations.RunPython(control_unit_installed_option_add_initial_data),
        migrations.RunPython(actuator_gearbox_types_add_initial_data),
        migrations.RunPython(actuator_gearbox_combination_types_add_initial_data),
        migrations.RunPython(valve_types_add_initial_data),


    ]
