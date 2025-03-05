# migrations/000X_auto_add_initial_data.py
from django.db import migrations


# power_supplies_add_initial_data, exd_add_initial_data, ip_add_initial_data, body_coating_add_initial_data, \
# blinker_add_initial_data, switches_add_initial_data, env_temp_add_initial_data, \
# digital_protocol_support_option_add_initial_data, control_unit_installed_option_add_initial_data, \
# actuator_gearbox_types_add_initial_data, actuator_gearbox_combination_types_add_initial_data, \
# valve_types_add_initial_data


def get_this_app_name():
    return 'params'


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
    this_model.objects.get_or_create(symbolic_code='STD', min_temp=-20, max_temp=70,
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
    this_model.objects.get_or_create(symbolic_code='POTE',
                                     text_description='Потенциометр, омическая обратная свзяь 0-1кОм')
    this_model.objects.get_or_create(symbolic_code='TR',
                                     text_description='Трансмиттер, обратная связь 4-20мА')
    this_model.objects.get_or_create(symbolic_code='POSI',
                                     text_description='Позиционер, упр.сигнал 4-20мА, обр.связь 4-20мА')
    this_model.objects.get_or_create(symbolic_code='INT_O',
                                     text_description='INT/O')
    this_model.objects.get_or_create(symbolic_code='INT_L',
                                     text_description='INT/L')
    this_model.objects.get_or_create(symbolic_code='INT_N',
                                     text_description='INT/N')
    this_model.objects.get_or_create(symbolic_code='TR10',
                                     text_description='Трансмиттер, обратная связь 0-10В')
    this_model.objects.get_or_create(symbolic_code='POSI10',
                                     text_description='Позиционер, упр.сигнал 0-10В, обр.связь 0-10В')


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

    this_model.objects.get_or_create(symbolic_code='Q', electric_actuator_type='Q', gearbox_type='NO',
                                     pneumatic_actuator_type='NO', text_description='Четвертьоборотный электропривод')

    this_model.objects.get_or_create(symbolic_code='M', electric_actuator_type='Q', gearbox_type='Q',
                                     pneumatic_actuator_type='NO',
                                     text_description='Многооборотный электропривод с четвертьоборотным редуктором')

    this_model.objects.get_or_create(symbolic_code='Q', electric_actuator_type='NO', gearbox_type='NO',
                                     pneumatic_actuator_type='Q', text_description='Четвертьоборотный пневмопривод')

    this_model.objects.get_or_create(symbolic_code='M', electric_actuator_type='M', gearbox_type='Q',
                                     pneumatic_actuator_type='NO', text_description='Многооборотный электропривод')

    this_model.objects.get_or_create(symbolic_code='M', electric_actuator_type='M', gearbox_type='M',
                                     pneumatic_actuator_type='Q',
                                     text_description='Многооборотный электропривод с многооборотным редуктором')

    this_model.objects.get_or_create(symbolic_code='L', electric_actuator_type='L', gearbox_type='NO',
                                     pneumatic_actuator_type='NO', text_description='Линейный электропривод')

    this_model.objects.get_or_create(symbolic_code='L', electric_actuator_type='M', gearbox_type='L',
                                     pneumatic_actuator_type='NO',
                                     text_description='Многооборотный электропривод с линейным модулем')

    this_model.objects.get_or_create(symbolic_code='L', electric_actuator_type='NO', gearbox_type='NO',
                                     pneumatic_actuator_type='L',
                                     text_description='Линейный пневмопривод')


def valve_types_add_initial_data(apps, schema_editor):
    this_model = apps.get_model(get_this_app_name(), 'ValveTypes')
    this_model.objects.get_or_create(
        symbolic_code='КШ',
        actuator_gearbox_combinations='Q',
        text_description='Кран шаровый')
    this_model.objects.get_or_create(
        symbolic_code='ЗД',
        actuator_gearbox_combinations='Q',
        text_description='Затвор дисковый')
    this_model.objects.get_or_create(
        symbolic_code='ЗК',
        actuator_gearbox_combinations='M|L',
        text_description='Задвижка клиновая')
    this_model.objects.get_or_create(
        symbolic_code='ЗШ',
        actuator_gearbox_combinations='M|L',
        text_description='Задвижка шиберная')
    this_model.objects.get_or_create(
        symbolic_code='КК',
        actuator_gearbox_combinations='L',
        text_description='Клапан')


def op_modes_add_initial_data(apps, schema_editor):
    this_model = apps.get_model(get_this_app_name(), 'OperatingModeOption')
    this_model.objects.get_or_create(symbolic_code='S2 - 15мин',
                                     text_description='S2 - 15 минут (открыть=закрыть)')
    this_model.objects.get_or_create(symbolic_code='S4 - 25%',
                                     text_description='S4 - 25% (регурирование)')
    this_model.objects.get_or_create(symbolic_code='S2-15мин/S4-25%',
                                     text_description='S2 - 15 минут (открыть=закрыть),S4 - 25% (регурирование)')


def hw_option_add_initial_data(apps, schema_editor):
    this_model = apps.get_model(get_this_app_name(), 'HandWheelInstalledOption')
    this_model.objects.get_or_create(symbolic_code='NONE', encoding='',
                                     text_description='Ручной дублер в виде шестигранника')
    this_model.objects.get_or_create(symbolic_code='HW opt', encoding='HW',
                                     text_description='Ручной дублер в виде штурвала')
    this_model.objects.get_or_create(symbolic_code='HW',
                                     text_description='Ручной дублер в виде штурвала')


def mounting_plates_add_initial_data(apps, schema_editor):
    this_model = apps.get_model(get_this_app_name(), 'MountingPlateTypes')
    this_model.objects.get_or_create(symbolic_code='F03')
    this_model.objects.get_or_create(symbolic_code='F05')
    this_model.objects.get_or_create(symbolic_code='F07')
    this_model.objects.get_or_create(symbolic_code='F10')
    this_model.objects.get_or_create(symbolic_code='F12')
    this_model.objects.get_or_create(symbolic_code='F14')
    this_model.objects.get_or_create(symbolic_code='F16')
    this_model.objects.get_or_create(symbolic_code='F03')
    this_model.objects.get_or_create(symbolic_code='ГОСТ А')
    this_model.objects.get_or_create(symbolic_code='ГОСТ Б')
    this_model.objects.get_or_create(symbolic_code='ГОСТ В')
    this_model.objects.get_or_create(symbolic_code='ГОСТ Г')
    this_model.objects.get_or_create(symbolic_code='ГОСТ Д')


def stem_shapes_add_initial_data(apps, schema_editor):
    this_model = apps.get_model(get_this_app_name(), 'StemShapes')
    this_model.objects.get_or_create(symbolic_code='SQ',
                                     text_description='Квадрат')
    this_model.objects.get_or_create(symbolic_code='D',
                                     text_description='Вал со шпонкой')
    this_model.objects.get_or_create(symbolic_code='DD',
                                     text_description='Double D (DD)')
    this_model.objects.get_or_create(symbolic_code='LH',
                                     text_description='Левая резьба')
    this_model.objects.get_or_create(symbolic_code='*',
                                     text_description='По заказу, макс.диам.')


def stem_size_add_initial_data(apps, schema_editor):
    StemShapes = apps.get_model('params', 'ActuatorGearboxOutputType')
    type_sq = StemShapes.objects.filter(symbolic_code='SQ').first()
    type_d = StemShapes.objects.filter(symbolic_code='D').first()
    type_any = StemShapes.objects.filter(symbolic_code='*').first()
    type_lh = StemShapes.objects.filter(symbolic_code='LH').first()

    this_model = apps.get_model(get_this_app_name(), 'StemSize')
    this_model.objects.get_or_create(symbolic_code='SQ09', stem_type=type_sq, stem_diameter=9,
                                     text_description='09x09')
    this_model.objects.get_or_create(symbolic_code='SQ11', stem_type=type_sq, stem_diameter=11,
                                     text_description='11x11')
    this_model.objects.get_or_create(symbolic_code='SQ14', stem_type=type_sq, stem_diameter=14,
                                     text_description='14x14')
    this_model.objects.get_or_create(symbolic_code='SQ17', stem_type=type_sq, stem_diameter=17,
                                     text_description='17x17')
    this_model.objects.get_or_create(symbolic_code='SQ19', stem_type=type_sq, stem_diameter=19,
                                     text_description='19x19')
    this_model.objects.get_or_create(symbolic_code='SQ27', stem_type=type_sq, stem_diameter=27,
                                     text_description='27x27')
    this_model.objects.get_or_create(symbolic_code='D20x6', stem_type=type_d, stem_diameter=20,
                                     chunk_x=6, chunk_y=6, chunk_z=0,
                                     text_description='20x6')
    this_model.objects.get_or_create(symbolic_code='D30x8', stem_type=type_d, stem_diameter=30,
                                     chunk_x=8, chunk_y=8, chunk_z=0,
                                     text_description='30x8')
    this_model.objects.get_or_create(symbolic_code='D32x10', stem_type=type_d, stem_diameter=32,
                                     chunk_x=10, chunk_y=10, chunk_z=0,
                                     text_description='32x10')
    this_model.objects.get_or_create(symbolic_code='D36x10', stem_type=type_d, stem_diameter=36,
                                     chunk_x=10, chunk_y=10, chunk_z=0,
                                     text_description='36x10')
    this_model.objects.get_or_create(symbolic_code='D40x12', stem_type=type_d, stem_diameter=40,
                                     chunk_x=12, chunk_y=12, chunk_z=0,
                                     text_description='D40x12')
    this_model.objects.get_or_create(symbolic_code='*28', stem_type=type_any, stem_diameter=28,
                                     text_description='вал макс. 28')
    this_model.objects.get_or_create(symbolic_code='*40', stem_type=type_any, stem_diameter=40,
                                     text_description='вал макс. 40')
    this_model.objects.get_or_create(symbolic_code='*55', stem_type=type_any, stem_diameter=55,
                                     text_description='вал макс. 55')
    this_model.objects.get_or_create(symbolic_code='*28', stem_type=type_any, stem_diameter=28,
                                     text_description='вал макс. 28')
    this_model.objects.get_or_create(symbolic_code='Tr20x4LH', stem_type=type_lh, stem_diameter=20, thread_pitch=4,
                                     text_description='Tr20x4LH')
    this_model.objects.get_or_create(symbolic_code='Tr28x5LH', stem_type=type_lh, stem_diameter=28, thread_pitch=5,
                                     text_description='Tr28x5LH')
    this_model.objects.get_or_create(symbolic_code='Tr32x6LH', stem_type=type_lh, stem_diameter=32, thread_pitch=6,
                                     text_description='Tr32x6LH')
    this_model.objects.get_or_create(symbolic_code='Tr40x6LH', stem_type=type_lh, stem_diameter=40, thread_pitch=6,
                                     text_description='Tr40x6LH')
    this_model.objects.get_or_create(symbolic_code='Tr50x8LH', stem_type=type_lh, stem_diameter=50, thread_pitch=8,
                                     text_description='Tr50x8LH')
    this_model.objects.get_or_create(symbolic_code='Tr60x8LH', stem_type=type_lh, stem_diameter=60, thread_pitch=8,
                                     text_description='Tr60x8LH')
    this_model.objects.get_or_create(symbolic_code='Tr70x10LH', stem_type=type_lh, stem_diameter=70, thread_pitch=10,
                                     text_description='Tr70x10LH')
    this_model.objects.get_or_create(symbolic_code='Tr80x10LH', stem_type=type_lh, stem_diameter=80, thread_pitch=10,
                                     text_description='Tr80x10LH')
    this_model.objects.get_or_create(symbolic_code='Tr100x24LH', stem_type=type_lh, stem_diameter=100, thread_pitch=24,
                                     text_description='Tr100x24LH')


def thread_types_add_initial_data(apps, schema_editor):
    this_model = apps.get_model(get_this_app_name(), 'ThreadTypes')
    this_model.objects.get_or_create(symbolic_code='NPT', text_description='NPT')
    this_model.objects.get_or_create(symbolic_code='G', text_description='G')
    this_model.objects.get_or_create(symbolic_code='M', text_description='M')


def measure_units_add_initial_data(apps, schema_editor):
    this_model = apps.get_model(get_this_app_name(), 'MeasureUnits')
    this_model.objects.get_or_create(symbolic_code='inch', measure_type='length', symbolic_description='"',
                                     text_description='дюйм')
    this_model.objects.get_or_create(symbolic_code='mm', measure_type='length', symbolic_description='мм',
                                     text_description='миллиметр')
    this_model.objects.get_or_create(symbolic_code='sm', measure_type='length', symbolic_description='см',
                                     text_description='сантиметр')
    this_model.objects.get_or_create(symbolic_code='m', measure_type='length', symbolic_description='м',
                                     text_description='метр')
    this_model.objects.get_or_create(symbolic_code='kg', measure_type='weight', symbolic_description='кг',
                                     text_description='килограмм')
    this_model.objects.get_or_create(symbolic_code='g', measure_type='weight', symbolic_description='г',
                                     text_description='грамм')
    this_model.objects.get_or_create(symbolic_code='nm', measure_type='torque', symbolic_description='Нм',
                                     text_description='Ньютон на метр')
    this_model.objects.get_or_create(symbolic_code='n', measure_type='torque', symbolic_description='Н',
                                     text_description='Ньютон')
    this_model.objects.get_or_create(symbolic_code='bar', measure_type='pressure', symbolic_description='бар',
                                     text_description='бар')
    this_model.objects.get_or_create(symbolic_code='mpa', measure_type='pressure', symbolic_description='МПа',
                                     text_description='Мегапаскаль')
    this_model.objects.get_or_create(symbolic_code='kgsm', measure_type='pressure', symbolic_description='кг/см2',
                                     text_description='Килограмм на см2')
    this_model.objects.get_or_create(symbolic_code='sm2', measure_type='square', symbolic_description='см2',
                                     text_description='Кв.сантиметр')
    this_model.objects.get_or_create(symbolic_code='m2', measure_type='square', symbolic_description='м2',
                                     text_description='Кв.метр')
    this_model.objects.get_or_create(symbolic_code='sqi', measure_type='square', symbolic_description='in2',
                                     text_description='Кв.дюйм')
    this_model.objects.get_or_create(symbolic_code='m3', measure_type='volume', symbolic_description='м3',
                                     text_description='метр куб.')
    this_model.objects.get_or_create(symbolic_code='obmin', measure_type='speed', symbolic_description='об/мин',
                                     text_description='Оборотов в минуту')
    this_model.objects.get_or_create(symbolic_code='grc', measure_type='temperature', symbolic_description='°C',
                                     text_description='Градусы Цельсия')
    this_model.objects.get_or_create(symbolic_code='grf', measure_type='temperature', symbolic_description='°F',
                                     text_description='Градусы Фаренгейт')
    this_model.objects.get_or_create(symbolic_code='mhz', measure_type='Частота', symbolic_description='МГц',
                                     text_description='Мегагерц')
    this_model.objects.get_or_create(symbolic_code='watt', measure_type='power', symbolic_description='Вт',
                                     text_description='Ватт')
    this_model.objects.get_or_create(symbolic_code='kwatt', measure_type='power', symbolic_description='кВт',
                                     text_description='Киловатт')
    this_model.objects.get_or_create(symbolic_code='sec', measure_type='time', symbolic_description='с',
                                     text_description='Секунд')
    this_model.objects.get_or_create(symbolic_code='min', measure_type='time', symbolic_description='мин',
                                     text_description='Минут')
    this_model.objects.get_or_create(symbolic_code='hour', measure_type='time', symbolic_description='час',
                                     text_description='Час')


def thread_size_add_initial_data(apps, schema_editor):
    ThreadTypes = apps.get_model('params', 'ThreadTypes')
    type_npt = ThreadTypes.objects.filter(symbolic_code='NPT').first()
    type_g = ThreadTypes.objects.filter(symbolic_code='G').first()
    type_m = ThreadTypes.objects.filter(symbolic_code='M').first()

    MeasureUnits = apps.get_model('params', 'MeasureUnits')
    units_inch = ThreadTypes.objects.filter(symbolic_code='inch').first()
    units_mm = ThreadTypes.objects.filter(symbolic_code='mm').first()

    this_model = apps.get_model(get_this_app_name(), 'ThreadSize')
    this_model.objects.get_or_create(symbolic_code='NPT_1_4', thread_type=type_npt, thread_diameter=1. / 4.,
                                     measure_units=units_inch,
                                     text_description='NPT 1/4')
    this_model.objects.get_or_create(symbolic_code='NPT_1_2', thread_type=type_npt, thread_diameter=1. / 2.,
                                     measure_units=units_inch,
                                     text_description='NPT 1/2')
    this_model.objects.get_or_create(symbolic_code='NPT_3_4', thread_type=type_npt, thread_diameter=3. / 4.,
                                     measure_units=units_inch,
                                     text_description='NPT 3/4')
    this_model.objects.get_or_create(symbolic_code='NPT_1', thread_type=type_npt, thread_diameter=1.,
                                     measure_units=units_inch,
                                     text_description='NPT 1')
    this_model.objects.get_or_create(symbolic_code='NPT_1_1_4', thread_type=type_npt, thread_diameter=1.+1. / 4.,
                                     measure_units=units_inch,
                                     text_description='NPT 11/4')
    this_model.objects.get_or_create(symbolic_code='NPT_1_1_2', thread_type=type_npt, thread_diameter=1.+1. / 2.,
                                     measure_units=units_inch,
                                     text_description='NPT 11/2')
    this_model.objects.get_or_create(symbolic_code='NPT_2', thread_type=type_npt, thread_diameter=2.,
                                     measure_units=units_inch,
                                     text_description='NPT 2')
    # -------------------- G -----------------------------
    this_model.objects.get_or_create(symbolic_code='G_1_4', thread_type=type_g, thread_diameter=1. / 4.,
                                     measure_units=units_inch,
                                     text_description='G 1/4')
    this_model.objects.get_or_create(symbolic_code='G_1_2', thread_type=type_g, thread_diameter=1. / 2.,
                                     measure_units=units_inch,
                                     text_description='G 1/2')
    this_model.objects.get_or_create(symbolic_code='G_3_4', thread_type=type_g, thread_diameter=3. / 4.,
                                     measure_units=units_inch,
                                     text_description='G 3/4')
    this_model.objects.get_or_create(symbolic_code='G_1', thread_type=type_g, thread_diameter=1.,
                                     measure_units=units_inch,
                                     text_description='G 1')
    this_model.objects.get_or_create(symbolic_code='G_1_1_4', thread_type=type_g, thread_diameter=1.+1. / 4.,
                                     measure_units=units_inch,
                                     text_description='G 11/4')
    this_model.objects.get_or_create(symbolic_code='G_1_1_2', thread_type=type_g, thread_diameter=1.+1. / 2.,
                                     measure_units=units_inch,
                                     text_description='G 11/2')
    this_model.objects.get_or_create(symbolic_code='G_2', thread_type=type_g, thread_diameter=2.,
                                     measure_units=units_inch,
                                     text_description='G 2')
    # -------------------- M -----------------------------
    this_model.objects.get_or_create(symbolic_code='M_20_1.5', thread_type=type_m, thread_diameter= 20,
                                     thread_pitch= 1. / 5.,
                                     measure_units=units_mm,
                                     text_description='M20x1.5')
    this_model.objects.get_or_create(symbolic_code='M_25_1.5', thread_type=type_m, thread_diameter= 25,
                                     thread_pitch= 1. / 5.,
                                     measure_units=units_mm,
                                     text_description='M25x1.5')


class Migration(migrations.Migration):
    dependencies = [
        # Укажите зависимости для вашей миграции, например:
        ('params', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(power_supplies_add_initial_data),
        migrations.RunPython(op_modes_add_initial_data),
        migrations.RunPython(hw_option_add_initial_data),
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
        migrations.RunPython(measure_units_add_initial_data),
        migrations.RunPython(mounting_plates_add_initial_data),
        migrations.RunPython(stem_shapes_add_initial_data),
        migrations.RunPython(stem_size_add_initial_data),
        migrations.RunPython(thread_types_add_initial_data),
        migrations.RunPython(thread_size_add_initial_data),
    ]
