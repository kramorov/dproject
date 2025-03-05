# migrations/000X_auto_add_initial_data.py
from django.db import migrations


def model_line_create_initial_data(apps, schema_editor):
    print('model_line_create_initial_data')
    Brands = apps.get_model('producers', 'Brands')
    Producer = apps.get_model('producers', 'Producer')
    ModelLine = apps.get_model('electric_actuators', 'ModelLine')

    IpOption = apps.get_model('params', 'IpOption')
    ip67 = IpOption.objects.filter(symbolic_code='IP67').first()

    BodyCoatingOption = apps.get_model('params', 'BodyCoatingOption')
    body_std = BodyCoatingOption.objects.filter(symbolic_code='STD').first()

    ExdOption = apps.get_model('params', 'ExdOption')
    no_exd = ExdOption.objects.filter(symbolic_code='NONE').first()

    ActuatorGearboxOutputType = apps.get_model('params', 'ActuatorGearboxOutputType')
    default_motion_type_M = ActuatorGearboxOutputType.objects.filter(symbolic_code='M').first()
    default_motion_type_Q = ActuatorGearboxOutputType.objects.filter(symbolic_code='Q').first()
    default_motion_type_L = ActuatorGearboxOutputType.objects.filter(symbolic_code='L').first()

    BlinkerOption = apps.get_model('params', 'BlinkerOption')
    default_blinker_std = BlinkerOption.objects.filter(symbolic_code='NONE').first()

    SwitchesParameters = apps.get_model('params', 'SwitchesParameters')
    default_switches_spdt = SwitchesParameters.objects.filter(symbolic_code='SPDT').first()
    default_switches_none = SwitchesParameters.objects.filter(symbolic_code='NONE').first()

    EnvTempParameters = apps.get_model('params', 'EnvTempParameters')
    default_temperature_std = EnvTempParameters.objects.filter(symbolic_code='STD').first()

    DigitalProtocolsSupportOption = apps.get_model('params', 'DigitalProtocolsSupportOption')
    default_digital_protocol_support_std = DigitalProtocolsSupportOption.objects.filter(symbolic_code='NONE').first()

    ControlUnitInstalledOption = apps.get_model('params', 'ControlUnitInstalledOption')
    default_control_unit_installed_std = ControlUnitInstalledOption.objects.filter(symbolic_code='NONE').first()

    HandWheelInstalledOption = apps.get_model('params', 'HandWheelInstalledOption')
    default_hand_wheel_hex = HandWheelInstalledOption.objects.filter(symbolic_code='NONE').first()
    default_hand_wheel_wheel = HandWheelInstalledOption.objects.filter(symbolic_code='HW').first()

    OperatingModeOption = apps.get_model('params', 'OperatingModeOption')
    default_operating_mode_std = OperatingModeOption.objects.filter(symbolic_code='S2-15мин/S4-25%').first()


    Brands = apps.get_model('producers', 'Brands')
    brand_ARH = Brands.objects.filter(name='Архимед').first()
    brand_Artorq = Brands.objects.filter(name='Artorq').first()


    # Создаем начальные модельные линии
    ar01e = ModelLine.objects.create(name='AR01E', brand=brand_ARH,
                                     default_output_type=default_motion_type_Q,
                                     default_ip=ip67,
                                     default_body_coating=body_std,
                                     default_exd=no_exd,
                                     default_blinker=default_blinker_std,
                                     default_end_switches=default_switches_spdt,
                                     default_way_switches=default_switches_none,
                                     default_torque_switches=default_switches_none,
                                     default_temperature=default_temperature_std,
                                     default_digital_protocol_support=default_digital_protocol_support_std,
                                     default_control_unit_installed=default_control_unit_installed_std,
                                     default_hand_wheel=default_hand_wheel_hex,
                                     default_operating_mode=default_operating_mode_std)

    ar11e = ModelLine.objects.create(name='AR11E', brand=brand_ARH,
                                     default_output_type=default_motion_type_Q,
                                     default_ip=ip67,
                                     default_body_coating=body_std,
                                     default_exd=no_exd,
                                     default_blinker=default_blinker_std,
                                     default_end_switches=default_switches_spdt,
                                     default_way_switches=default_switches_none,
                                     default_torque_switches=default_switches_spdt,
                                     default_temperature=default_temperature_std,
                                     default_digital_protocol_support=default_digital_protocol_support_std,
                                     default_control_unit_installed=default_control_unit_installed_std,
                                     default_hand_wheel=default_hand_wheel_wheel,
                                     default_operating_mode=default_operating_mode_std)

    ar21e = ModelLine.objects.create(name='AR21E', brand=brand_ARH,
                                     default_output_type=default_motion_type_M,
                                     default_ip=ip67,
                                     default_body_coating=body_std,
                                     default_exd=no_exd,
                                     default_blinker=default_blinker_std,
                                     default_end_switches=default_switches_spdt,
                                     default_way_switches=default_switches_none,
                                     default_torque_switches=default_switches_spdt,
                                     default_temperature=default_temperature_std,
                                     default_digital_protocol_support=default_digital_protocol_support_std,
                                     default_control_unit_installed=default_control_unit_installed_std,
                                     default_hand_wheel=default_hand_wheel_wheel,
                                     default_operating_mode=default_operating_mode_std)

    ar11el = ModelLine.objects.create(name='AR11EL', brand=brand_ARH,
                                      default_output_type=default_motion_type_L,
                                      default_ip=ip67,
                                      default_body_coating=body_std,
                                      default_exd=no_exd,
                                      default_blinker=default_blinker_std,
                                      default_end_switches=default_switches_spdt,
                                      default_way_switches=default_switches_none,
                                      default_torque_switches=default_switches_spdt,
                                      default_temperature=default_temperature_std,
                                      default_digital_protocol_support=default_digital_protocol_support_std,
                                      default_control_unit_installed=default_control_unit_installed_std,
                                      default_hand_wheel=default_hand_wheel_wheel,
                                      default_operating_mode=default_operating_mode_std)

    ar19e = ModelLine.objects.create(name='AR19E', brand=brand_ARH,
                                     default_output_type=default_motion_type_M,
                                     default_ip=ip67,
                                     default_body_coating=body_std,
                                     default_exd=no_exd,
                                     default_blinker=default_blinker_std,
                                     default_end_switches=default_switches_spdt,
                                     default_way_switches=default_switches_none,
                                     default_torque_switches=default_switches_spdt,
                                     default_temperature=default_temperature_std,
                                     default_digital_protocol_support=default_digital_protocol_support_std,
                                     default_control_unit_installed=default_control_unit_installed_std,
                                     default_hand_wheel=default_hand_wheel_wheel,
                                     default_operating_mode=default_operating_mode_std)

    ar06e = ModelLine.objects.create(name='AR06E', brand=brand_ARH,
                                     default_output_type=default_motion_type_Q,
                                     default_ip=ip67,
                                     default_body_coating=body_std,
                                     default_exd=no_exd,
                                     default_blinker=default_blinker_std,
                                     default_end_switches=default_switches_spdt,
                                     default_way_switches=default_switches_none,
                                     default_torque_switches=default_switches_none,
                                     default_temperature=default_temperature_std,
                                     default_digital_protocol_support=default_digital_protocol_support_std,
                                     default_control_unit_installed=default_control_unit_installed_std,
                                     default_hand_wheel=default_hand_wheel_hex,
                                     default_operating_mode=default_operating_mode_std)


class Migration(migrations.Migration):
    dependencies = [
        ('electric_actuators', '0001_initial'),
        ('params', '0002_add_params_initial_data'),
        ('producers', '0002_producers_add_initial_data'),
    ]

    operations = [
        migrations.RunPython(model_line_create_initial_data),
    ]
