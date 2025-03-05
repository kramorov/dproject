# models.py
from datetime import datetime

from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.utils.timezone import now

from producers.models import Brands, Producer
from params.models import PowerSupplies, ExdOption, BodyCoatingOption, BlinkerOption, SwitchesParameters, \
    EnvTempParameters, IpOption, MeasureUnits, \
    DigitalProtocolsSupportOption, ControlUnitInstalledOption, ActuatorGearboxOutputType, HandWheelInstalledOption, \
    OperatingModeOption, StemShapes, StemSize, MountingPlateTypes, ThreadSize, CertificateType, Certificate, \
    MechanicalIndicatorInstalledOption


class CableGlandHolesSet(models.Model):
    name = models.CharField(max_length=20, blank=True, \
                            help_text='Название варианта набора отверстий под КВ')
    cg1 = models.ForeignKey(ThreadSize, related_name='cable_gland1', blank=True, null=True, on_delete=models.SET_NULL,
                            verbose_name='Отверстие под КВ1')
    cg2 = models.ForeignKey(ThreadSize, related_name='cable_gland2', blank=True, null=True, on_delete=models.SET_NULL,
                            verbose_name='Отверстие под КВ2')
    cg3 = models.ForeignKey(ThreadSize, related_name='cable_gland3', blank=True, null=True, on_delete=models.SET_NULL,
                            verbose_name='Отверстие под КВ3')
    cg4 = models.ForeignKey(ThreadSize, related_name='cable_gland4', blank=True, null=True, on_delete=models.SET_NULL,
                            verbose_name='Отверстие под КВ4')
    text_description = models.CharField(max_length=200, blank=True, \
                                        help_text='Текстовое описание набора отверстий под КВ')

    def __str__(self):
        return self.text_description


class ModelLine(models.Model):
    name = models.CharField(max_length=20, help_text='Название серии')
    brand = \
        models.ForeignKey(Brands, blank=True, null=True,
                          related_name='model_line_brand',
                          on_delete=models.SET_NULL,
                          help_text='Бренд производителя')
    default_output_type = \
        models.ForeignKey(ActuatorGearboxOutputType, blank=True, null=True,
                          related_name='default_output_type',
                          on_delete=models.SET_NULL,
                          help_text='Тип работы серии приводов')

    default_ip = \
        models.ForeignKey(IpOption, blank=True, null=True,
                          related_name='default_ip_option',
                          on_delete=models.SET_NULL,
                          help_text='Стандартное исполнение степени защиты IP для серии')
    allowed_ip = \
        models.ManyToManyField(IpOption, blank=True, default=1,
                               related_name='ea_model_line_allowed_ip',
                               help_text='Возможные для выбора степени защиты IP для серии (можно выбрать '
                                         'несколько)')

    default_body_coating = \
        models.ForeignKey(BodyCoatingOption, blank=True, null=True,
                          related_name='default_body_coating',
                          on_delete=models.SET_NULL,
                          help_text='Стандартное исполнение покрытия корпуса для серии')
    allowed_body_coating = \
        models.ManyToManyField(BodyCoatingOption, blank=True, default=1,
                               related_name='ea_model_line_allowed_body_coating',
                               help_text='Возможные для выбора покрытия корпуса для серии (можно выбрать несколько)')

    default_exd = \
        models.ForeignKey(ExdOption, blank=True, null=True,
                          related_name='default_exd_option',
                          on_delete=models.SET_NULL,
                          help_text='Стандартное исполнение степени взрывозащиты для серии')
    allowed_exd = \
        models.ManyToManyField(ExdOption, blank=True, default=1,
                               related_name='ea_model_line_allowed_exd',
                               help_text='Возможные для выбора степени взрывозащиты для серии (можно '
                                         'выбрать несколько)')

    default_blinker = \
        models.ForeignKey(BlinkerOption, blank=True, null=True,
                          related_name='default_blinker_option',
                          on_delete=models.SET_NULL,
                          help_text='Стандартное исполнение блинкера для серии')

    default_end_switches = \
        models.ForeignKey(SwitchesParameters, blank=True, null=True,
                          related_name='default_end_switches',
                          on_delete=models.SET_NULL,
                          help_text='Стандартное исполнение путевых выключателей для серии')
    allowed_end_switches = \
        models.ManyToManyField(SwitchesParameters, blank=True, default=1,
                               related_name='ea_model_line_allowed_end_switches',
                               help_text='Возможные для выбора исполнения путевых выключателей для '
                                         'серии (можно выбрать несколько)')
    default_way_switches = \
        models.ForeignKey(SwitchesParameters, blank=True, null=True,
                          related_name='default_way_switches',
                          on_delete=models.SET_NULL,
                          help_text='Стандартное исполнение конечных выключателей для серии')
    allowed_way_switches = \
        models.ManyToManyField(SwitchesParameters, blank=True, default=1,
                               related_name='ea_model_line_allowed_way_switches',
                               help_text='Возможные для выбора исполнения конечных выключателей '
                                         'для серии (можно выбрать несколько)')
    default_torque_switches = models.ForeignKey(SwitchesParameters, blank=True, null=True,
                                                related_name='default_torque_switches',
                                                on_delete=models.SET_NULL,
                                                help_text='Стандартное исполнение ограничителей момента для серии')
    allowed_torque_switches = models.ManyToManyField(SwitchesParameters, blank=True, default=1,
                                                     related_name='ea_model_line_allowed_torque_switches',
                                                     help_text='Возможные для выбора исполнения ограничителей момента '
                                                               'для серии (можно выбрать несколько)')

    default_temperature = models.ForeignKey(EnvTempParameters, blank=True, null=True,
                                            related_name='default_temperature',
                                            on_delete=models.SET_NULL,
                                            help_text='Стандартное температурное исполнения для серии')
    allowed_temperature = \
        models.ManyToManyField(EnvTempParameters, blank=True, default=1,
                               related_name='ea_model_line_allowed_temperature',
                               help_text='Возможные для выбора температурные исполнения для серии ('
                                         'можно выбрать несколько)')

    default_control_unit_installed = \
        models.ForeignKey(ControlUnitInstalledOption, blank=True, null=True,
                          related_name='default_control_unit_installed',
                          on_delete=models.SET_NULL,
                          help_text='Стандартно установленный блок управления для серии')
    allowed_control_unit_installed = \
        models.ManyToManyField(ControlUnitInstalledOption, blank=True, default=1,
                               related_name='ea_model_line_allowed_control_unit_installed',
                               help_text='Возможные для выбора блоки управления для серии (можно выбрать несколько)')

    default_hand_wheel = \
        models.ForeignKey(HandWheelInstalledOption, blank=True, null=True,
                          related_name='default_hand_wheel',
                          on_delete=models.SET_NULL,
                          help_text='Стандартно установленный ручной дублер для серии')

    allowed_hand_wheel = \
        models.ManyToManyField(HandWheelInstalledOption, blank=True, default=1,
                               related_name='ea_model_line_allowed_hand_wheel',
                               help_text='Возможные для выбора ручные дублеры для серии (можно выбрать несколько)')

    default_mechanical_indicator = \
        models.ForeignKey(MechanicalIndicatorInstalledOption, blank=True, null=True,
                          related_name='default_mechanical_indicator',
                          on_delete=models.SET_NULL,
                          help_text='Стандартно установленный механический индикатор для серии')

    allowed_mechanical_indicator = \
        models.ManyToManyField(MechanicalIndicatorInstalledOption, blank=True, default=1,
                               related_name='ea_model_line_allowed_mechanical_indicator',
                               help_text='Возможные для выбора варианты установки механического индикатора для серии '
                                         '(можно выбрать несколько)')
    default_operating_mode = \
        models.ForeignKey(OperatingModeOption, blank=True, null=True,
                          related_name='default_operating_mode',
                          on_delete=models.SET_NULL,
                          help_text='Стандартный режим работы двигателя для серии')
    allowed_operating_mode = \
        models.ManyToManyField(OperatingModeOption, blank=True, default=1,
                               related_name='ea_model_line_allowed_operating_mode',
                               help_text='Возможные для выбора режимы работы двигателя для серии (можно выбрать '
                                         'несколько)')

    certificates = GenericRelation(Certificate)

    def __str__(self):
        return self.name


class ModelBody(models.Model):
    name = models.CharField(max_length=200, verbose_name='Текстовое название типа корпуса')
    model_line = models.ForeignKey(ModelLine, on_delete=models.PROTECT,
                                   related_name='model_body_model_line', help_text='Серия приводов')
    default_cable_glands_holes = \
        models.ForeignKey(CableGlandHolesSet, null=True, blank=True,
                          related_name='model_body_default_cable_glands_holes',
                          on_delete=models.SET_NULL,
                          help_text='Стандартные отверстия под кабельные вводы')
    allowed_cable_glands_holes = \
        models.ManyToManyField(CableGlandHolesSet, blank=True,
                               related_name='model_body_allowed_cable_glands_holes',
                               help_text='Возможные для выбора варианты отверстий под кабельные вводы для корпуса ('
                                         'можно выбрать несколько)')
    mounting_plate = models.ManyToManyField(MountingPlateTypes, blank=True,
                                            related_name='model_body_cable_mounting_plate',
                                            help_text='Монтажная площадка')
    stem_shape = models.ForeignKey(StemShapes, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='model_body_stem_shape', help_text='Тип отверстия под шток арматуры')
    stem_size = models.ForeignKey(StemSize, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='model_body_stem_size', help_text='Размер отверстия под шток арматуры')
    max_stem_height = models.PositiveIntegerField(blank=True, null=True,
                                                  help_text='Глубина отверстия под шток арматуры')
    max_stem_diameter = models.PositiveIntegerField(blank=True, null=True, help_text='Максимальный диаметр отверстия '
                                                                                     'под шток арматуры')
    text_description = models.CharField(max_length=500, blank=True, null=True, help_text='Описание типа корпуса')

    def __str__(self):
        return self.name


class ElectricActuatorData(models.Model):
    name = models.CharField(max_length=30, help_text='Название модели / корпуса')
    model_line = models.ForeignKey(ModelLine, related_name='electric_actuator_data_model_line', null=True, \
                                   on_delete=models.PROTECT, help_text='Серия модели')
    model_body = models.ForeignKey(ModelBody, related_name='electric_actuator_data_model_body', null=True, \
                                   on_delete=models.SET_NULL, help_text='Корпус модели')
    voltage = models.ForeignKey(PowerSupplies, related_name='electric_actuator_data_model_voltage', null=True, \
                                on_delete=models.SET_NULL, help_text='Напряжение питания модели')
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text='Вес модели')
    time_to_open = models.DecimalField(max_digits=3, decimal_places=0, blank=True, null=True,
                                       help_text='Время поворота на 90°')
    time_to_open_measure_unit = models.ForeignKey(MeasureUnits, related_name='electric_actuator_data_time_to_open',
                                                  null=True, \
                                                  blank=True, on_delete=models.SET_NULL,
                                                  help_text='Ед.изм. времени поворота на 90°')
    rotation_speed = models.DecimalField(max_digits=3, decimal_places=0, blank=True, null=True, help_text='Скорость')
    rotation_speed_measure_unit = models.ForeignKey(MeasureUnits, related_name='electric_actuator_data_rotation_speed',
                                                    null=True, \
                                                    blank=True, on_delete=models.SET_NULL,
                                                    help_text='Ед.изм. скорости привода')
    torque_min = models.DecimalField(max_digits=5, decimal_places=0, help_text='Минимальное усилие')
    torque_max = models.DecimalField(max_digits=5, decimal_places=0, help_text='Максимальное усилие')

    motor_power = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, \
                                      help_text='Мощность двигателя')
    motor_power_measure_unit = models.ForeignKey(MeasureUnits, related_name='electric_actuator_data_power', null=True, \
                                                 blank=True, on_delete=models.SET_NULL,
                                                 help_text='Ед.изм. мощности двигателя')
    motor_current_rated = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, \
                                              help_text='Номинальный ток двигателя')
    motor_current_rated_measure_unit = models.ForeignKey(MeasureUnits,
                                                         related_name='electric_actuator_data_current_rated',
                                                         null=True, \
                                                         blank=True, on_delete=models.SET_NULL,
                                                         help_text='Ед.изм. номинального тока двигателя')
    motor_current_starting = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, \
                                                 help_text='Пусковой ток двигателя')
    motor_current_starting_measure_unit = models.ForeignKey(MeasureUnits,
                                                            related_name='electric_actuator_data_current_starting',
                                                            null=True, \
                                                            blank=True, on_delete=models.SET_NULL,
                                                            help_text='Ед.изм. пускового тока двигателя')

    def __str__(self):
        return self.name


class WiringDiagram(models.Model):
    name = models.CharField(max_length=30, help_text='Название схемы подключения по чертежу')
    applies_to_model_lines = models.ForeignKey(ModelLine,
                                               on_delete=models.CASCADE,
                                               related_name='wiring_diagrams_applies_to_model_lines')
    applies_to_models = models.ManyToManyField(ElectricActuatorData, related_name='wiring_diagrams_applies_to_models')
    voltage = models.ForeignKey(PowerSupplies, on_delete=models.CASCADE, related_name='wiring_diagrams_voltage')
    cu = models.ForeignKey(ControlUnitInstalledOption,
                           on_delete=models.CASCADE,
                           related_name='wiring_diagrams_control_units')
    text_description = models.CharField(max_length=200, blank=True, null=True, \
                                        help_text='Описание схемы подключения - к каким приводам и к какому '
                                                  'напряжению относится')

    def __str__(self):
        return self.text_description


def sort_data(data):
    sorted_data = sorted(data, key=lambda x: (x['section'], x['order']))
    return sorted_data


class ActualActuator(models.Model):
    def get_full_description(self):
        data = [
            {'param_name': 'name',
             'param_text': 'Полное название модели привода с опциями и исполнением', 'param_value': self.name},
            {'param_name': 'actual_model', 'param_text': 'Базовая модель',
             'param_value': self.actual_model},
            {'param_name': 'actual_time_to_open', 'param_text': 'Время поворота',
             'param_value': self.actual_time_to_open},
            {'param_name': 'actual_time_to_open_measure_unit',
             'param_text': 'Ед.изм. времени поворота', 'param_value': self.actual_time_to_open_measure_unit},
            {'param_name': 'actual_rotations_to_open', 'param_text': 'Скорость',
             'param_value': self.actual_rotations_to_open},
            {'param_name': 'actual_rotations_to_open_measure_unit',
             'param_text': 'Ед.изм. скорости поворота', 'param_value': self.actual_rotations_to_open_measure_unit},
            {'param_name': 'actual_mounting_plate', 'param_text': 'Монтажная площадка',
             'param_value': self.actual_mounting_plate},
            {'param_name': 'actual_stem_shape',
             'param_text': 'Тип отверстия под шток арматуры', 'param_value': self.actual_stem_shape},
            {'param_name': 'actual_stem_size',
             'param_text': 'Размер отверстия под шток арматуры', 'param_value': self.actual_stem_size},
            {'param_name': 'actual_cable_glands_holes',
             'param_text': 'Отверстия под кабельные вводы',
             'param_value': self.actual_cable_glands_holes.text_description},
            {'param_name': 'actual_wiring_diagram', 'param_text': 'Схема подключения',
             'param_value': self.actual_wiring_diagram},
            {'param_name': 'actual_ip', 'param_text': 'IP', 'param_value': self.actual_ip},
            {'param_name': 'actual_body_coating', 'param_text': 'Покрытие корпуса',
             'param_value': self.actual_body_coating},
            {'param_name': 'actual_exd', 'param_text': 'exd', 'param_value': self.actual_exd},
            {'param_name': 'actual_blinker', 'param_text': 'Блинкер',
             'param_value': self.actual_blinker},
            {'param_name': 'actual_end_switches', 'param_text': 'Концевые выключатели',
             'param_value': self.actual_end_switches},
            {'param_name': 'actual_way_switches', 'param_text': 'Путевые выключатели',
             'param_value': self.actual_way_switches},
            {'param_name': 'actual_torque_switches', 'param_text': 'Ограничители момента',
             'param_value': self.actual_torque_switches},
            {'param_name': 'actual_output_type', 'param_text': 'Вид привода',
             'param_value': self.actual_output_type},
            {'param_name': 'actual_temperature', 'param_text': 'Температурное исполнение',
             'param_value': self.actual_temperature},
            {'param_name': 'actual_digital_protocol_support',
             'param_text': 'Поддержка цифровых протоколов', 'param_value': self.actual_digital_protocol_support},
            {'param_name': 'actual_control_unit_installed', 'param_text': 'Блок управления',
             'param_value': self.actual_control_unit_installed},
            {'param_name': 'actual_hand_wheel', 'param_text': 'Ручной дублер',
             'param_value': self.actual_hand_wheel},
            {'param_name': 'actual_operating_mode', 'param_text': 'Режим работы',
             'param_value': self.actual_operating_mode}
        ]
        return data

    def make_actual_name(self):
        actual_model_var = self.actual_model
        actual_model_line_var = actual_model_var.model_line
        actual_model_body_var = actual_model_var.model_body
        name_str = actual_model_var.name + '.'
        if self.actual_temperature != actual_model_line_var.default_temperature:
            name_str = name_str + '.' + self.actual_temperature.symbolic_code
        if self.actual_ip != actual_model_line_var.default_ip:
            name_str = name_str + '.' + self.actual_ip.symbolic_code
        if self.actual_hand_wheel != actual_model_line_var.default_hand_wheel:
            name_str = name_str + '.' + self.actual_hand_wheel.symbolic_code
        if self.actual_control_unit_installed != actual_model_line_var.default_control_unit_installed:
            name_str = name_str + '.' + self.default_control_unit_installed.symbolic_code
        # if self.actual_digital_protocol_support != self.actual_model.model_line.default_control_unit_installed:
        #     name_str = name_str + '.' + self.actual_digital_protocol_support.symbolic_code
        name_str = name_str + '.' + self.actual_model.voltage.symbolic_code
        if self.actual_exd != actual_model_line_var.default_exd:
            name_str = name_str + '.' + self.actual_exd.symbolic_code

        make_options_str = ''
        if self.actual_body_coating != actual_model_line_var.default_body_coating:
            make_options_str = make_options_str + 'Покрытие корпуса:' + self.actual_body_coating.symbolic_code
        # if self.actual_mounting_plate != self.actual_model.model_body.mounting_plate:
        #     make_options_str = make_options_str + '; Монтажная площадка:' + self.actual_mounting_plate.symbolic_code
        if self.actual_stem_shape != self.actual_model.model_body.stem_shape:
            make_options_str = make_options_str + '; Тип штока:' + self.actual_stem_shape.symbolic_code
        if self.actual_stem_size != self.actual_model.model_body.stem_size:
            make_options_str = make_options_str + '; Размер штока:' + self.actual_stem_size.symbolic_code
        if self.actual_cable_glands_holes != self.actual_model.model_body.default_cable_glands_holes:
            make_options_str = make_options_str + '; Размер штока:' + self.actual_cable_glands_holes.name

        if len(make_options_str) > 0:
            name_str = name_str + 'Вариант исполнения: ' + make_options_str

        self.name = name_str

    # def init(self, new_model):
    #     self.actual_model = new_model
    #     self.actual_time_to_open = self.actual_model.time_to_open
    #     self.actual_time_to_open_measure_unit = self.actual_model.time_to_open_measure_unit
    #     self.actual_rotations_to_open = self.actual_model.rotation_speed
    #     self.actual_rotations_to_open_measure_unit = self.actual_model.rotation_speed_measure_unit
    #     self.actual_mounting_plate = self.actual_model.model_body.mounting_plate
    #     self.actual_stem_shape = self.actual_model.model_body.stem_shape
    #     self.actual_stem_size = self.actual_model.model_body.stem_size
    #     self.actual_cable_glands_holes = self.actual_model.model_body.cable_glands_holes
    #     self.actual_wiring_diagram = self.actual_model.wiring_diagrams
    #     self.actual_ip = self.actual_model.model_body.default_ip
    #     self.actual_exd = self.actual_model.model_body.default_body_coating
    #     self.actual_blinker = self.actual_model.model_body.default_blinker
    #     self.actual_end_switches = self.actual_model.model_body.default_end_switches
    #     self.actual_way_switches = self.actual_model.model_body.default_way_switches
    #     self.actual_torque_switches = self.actual_model.model_body.default_torque_switches
    #     self.actual_output_type = self.actual_model.model_body.default_output_type
    #     self.actual_temperature = self.actual_model.model_body.default_temperature
    #     self.actual_digital_protocol_support = self.actual_model.model_body.default_digital_protocol_support
    #     self.actual_control_unit_installed = self.actual_model.model_body.default_control_unit_installed
    #     self.actual_hand_wheel = self.actual_model.model_body.default_hand_wheel
    #     self.actual_operating_mode = self.actual_model.model_body.default_operating_mode
    #     self.actual_mechanical_indicator = self.actual_model.model_body.default_mechanical_indicator

    def set_actual_time_to_open(self, new_time_to_open):
        self.actual_time_to_open = new_time_to_open

    def set_actual_time_to_open_measure_unit(self, new_time_to_open_measure_unit):
        self.actual_time_to_open_measure_unit = new_time_to_open_measure_unit

    def set_actual_rotations_to_open(self, new_rotation_speed):
        self.actual_rotations_to_open = new_rotation_speed

    def set_actual_rotations_to_open_measure_unit(self, new_rotation_speed_measure_unit):
        self.actual_rotations_to_open_measure_unit = new_rotation_speed_measure_unit

    def set_actual_mounting_plate(self, new_mounting_plate):
        self.actual_mounting_plate = new_mounting_plate
        self.make_actual_name()

    def set_actual_stem_shape(self, new_stem_shape):
        self.actual_stem_shape = new_stem_shape
        self.make_actual_name()

    def set_actual_stem_size(self, new_stem_size):
        self.actual_stem_size = new_stem_size
        self.make_actual_name()

    def set_actual_cable_glands_holes(self, new_cable_glands_holes):
        self.actual_cable_glands_holes = new_cable_glands_holes
        self.make_actual_name()

    def set_actual_wiring_diagram(self, new_wiring_diagrams):
        self.actual_wiring_diagram = new_wiring_diagrams

    def set_actual_ip(self, new_ip):
        self.actual_ip = new_ip
        self.make_actual_name()

    def set_actual_exd(self, new_exd):
        self.actual_exd = new_exd
        self.make_actual_name()

    def set_actual_blinker(self, new_blinker):
        self.actual_blinker = new_blinker

    def set_actual_end_switches(self, new_end_switches):
        self.set_actual_end_switches = new_end_switches

    def set_actual_way_switches(self, new_way_switches):
        self.actual_way_switches = new_way_switches

    def set_actual_torque_switches(self, new_torque_switches):
        self.actual_torque_switches = new_torque_switches
        self.make_actual_name()

    def set_actual_output_type(self, new_output_type):
        self.actual_output_type = new_output_type

    def set_actual_temperature(self, new_temperature):
        self.actual_temperature = new_temperature
        self.make_actual_name()

    def set_actual_digital_protocol_support(self, new_digital_protocol_support):
        self.actual_digital_protocol_support = new_digital_protocol_support
        self.make_actual_name()

    def set_actual_control_unit_installed(self, new_control_unit_installed):
        self.actual_control_unit_installed = new_control_unit_installed
        self.make_actual_name()

    def set_actual_hand_wheel(self, new_hand_wheel):
        self.actual_hand_wheel = new_hand_wheel
        self.make_actual_name()

    def set_actual_body_coating(self, new_body_coating):
        self.actual_body_coating = new_body_coating
        self.make_actual_name()

    def set_actual_operating_mode(self, new_operating_mode):
        self.actual_operating_mode = new_operating_mode

    def set_actual_mechanical_indicator(self, new_mechanical_indicator):
        self.actual_mechanical_indicator = new_mechanical_indicator

    def get_name_for_new_actuator(self):
        return 'Проект от ' + datetime.now()

    # Определение полей:
    PROJECT_STATUS = [
        ('Draft', 'Проект'),  # ('AC', 'Постоянный ток')
        ('Approved', 'Утвержден'),  # ('DC', 'Переменный ток')
    ]
    status = models.CharField(max_length=10, choices=PROJECT_STATUS, default='Draft')
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    date_updated = models.DateTimeField(default=now, editable=False)
    name = models.CharField(max_length=200, default='Проект',
                            help_text='Полное название модели привода с опциями и исполнением')
    actual_model = \
        models.ForeignKey(ElectricActuatorData, null=True,
                          related_name='actual_model', \
                          on_delete=models.SET_NULL, help_text='Базовая модель')
    actual_time_to_open = models.PositiveIntegerField(blank=True, null=True, help_text='Время поворота')
    actual_time_to_open_measure_unit = models.ForeignKey(MeasureUnits, related_name='actual_actuator_data_time_to_open',
                                                         null=True, blank=True,
                                                         on_delete=models.SET_NULL,
                                                         help_text='Ед.изм. времени поворота')
    actual_rotations_to_open = models.PositiveIntegerField(blank=True, null=True,
                                                           help_text='Скорость')
    actual_rotations_to_open_measure_unit = models.ForeignKey(MeasureUnits,
                                                              related_name='actual_rotations_to_open_measure_unit',
                                                              null=True, \
                                                              blank=True, on_delete=models.SET_NULL,
                                                              help_text='Ед.изм. времени поворота')
    actual_mounting_plate = models.ManyToManyField(MountingPlateTypes, blank=True,
                                            related_name='actual_mounting_plate',
                                            help_text='Монтажная площадка')
    actual_stem_shape = models.ForeignKey(StemShapes, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='actual_stem_shape', help_text='Тип отверстия под шток арматуры')
    actual_stem_size = models.ForeignKey(StemSize, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='actual_stem_size',
                                         help_text='Размер отверстия под шток арматуры')
    actual_cable_glands_holes = models.ForeignKey(CableGlandHolesSet, related_name='actual_cable_glands_holes', \
                                                  on_delete=models.SET_NULL, null=True, blank=True, \
                                                  help_text='Отверстия под кабельные вводы')

    actual_wiring_diagram = models.ForeignKey(WiringDiagram, related_name='actual_wiring_diagram', \
                                              on_delete=models.SET_NULL, null=True, blank=True, \
                                              help_text='Схема подключения')
    actual_ip = models.ForeignKey(IpOption, related_name='actual_ip', blank=True, null=True,
                                  on_delete=models.SET_NULL, help_text='Степень IP')
    actual_body_coating = models.ForeignKey(BodyCoatingOption, related_name='actual_body_coating', blank=True,
                                            null=True,
                                            on_delete=models.SET_NULL, help_text='Покрытие корпуса')
    actual_exd = models.ForeignKey(ExdOption, related_name='actual_exd', blank=True, null=True,
                                   on_delete=models.SET_NULL, help_text='Степень exd')
    actual_blinker = models.ForeignKey(BlinkerOption, related_name='actual_blinker', blank=True, null=True,
                                       on_delete=models.SET_NULL, help_text='Блинкер')
    actual_end_switches = models.ForeignKey(SwitchesParameters, related_name='actual_end_switches', blank=True,
                                            null=True,
                                            on_delete=models.SET_NULL, help_text='Концевые выключатели')
    actual_way_switches = models.ForeignKey(SwitchesParameters, related_name='actual_way_switches', blank=True,
                                            null=True, on_delete=models.SET_NULL, help_text='Путевые выключатели')
    actual_torque_switches = models.ForeignKey(SwitchesParameters, related_name='actual_torque_switches', blank=True,
                                               null=True, on_delete=models.SET_NULL, help_text='Ограничители момента')
    actual_output_type = models.ForeignKey(ActuatorGearboxOutputType, related_name='actual_output_type', blank=True,
                                           null=True,
                                           on_delete=models.SET_NULL, help_text='Вид привода')
    actual_temperature = models.ForeignKey(EnvTempParameters, related_name='actual_output_type', blank=True,
                                           null=True, on_delete=models.SET_NULL, help_text='Температурное исполнение')

    actual_digital_protocol_support = models.ForeignKey(DigitalProtocolsSupportOption,
                                                        related_name='actual_digital_protocol_support', blank=True,
                                                        null=True, on_delete=models.SET_NULL, \
                                                        help_text='Поддержка цифровых протоколов')
    actual_control_unit_installed = models.ForeignKey(ControlUnitInstalledOption,
                                                      related_name='actual_control_unit_installed', blank=True,
                                                      null=True, on_delete=models.SET_NULL, help_text='Блок управления')
    actual_mechanical_indicator = \
        models.ForeignKey(MechanicalIndicatorInstalledOption, blank=True, null=True,
                          related_name='actual_mechanical_indicator',
                          on_delete=models.SET_NULL,
                          help_text='Установленный механический индикатор')

    actual_hand_wheel = models.ForeignKey(HandWheelInstalledOption, related_name='actual_hand_wheel', blank=True,
                                          null=True, on_delete=models.SET_NULL, help_text='Ручной дублер')

    actual_operating_mode = models.ForeignKey(OperatingModeOption, related_name='actual_operating_mode', blank=True,
                                              null=True, on_delete=models.SET_NULL, help_text='Режим работы')
    text_description = models.CharField(max_length=1000, \
                                        blank=True, null=True, \
                                        help_text='Полное описание привода с опциями и вариантами исполнения')
    #
    # @classmethod
    # def save_actuator(cls, actuator):
    #     # Вызов функции для установки name перед сохранением
    #     actuator.make_actual_name()
    #
    #     # Если статус 'Approved', то проверяем наличие аналогичной записи
    #     if actuator.status == 'Approved':
    #         # Составляем фильтр для сравнения всех полей (кроме дат)
    #         filters = {
    #             'actual_model': actuator.actual_model,
    #             'actual_temperature': actuator.actual_temperature,
    #             'actual_ip': actuator.actual_ip,
    #             'actual_hand_wheel': actuator.actual_hand_wheel,
    #             'actual_control_unit_installed': actuator.actual_control_unit_installed,
    #             'actual_digital_protocol_support': actuator.actual_digital_protocol_support,
    #             'actual_exd': actuator.actual_exd,
    #             'actual_mounting_plate': actuator.actual_mounting_plate,
    #             'actual_stem_shape': actuator.actual_stem_shape,
    #             'actual_stem_size': actuator.actual_stem_size,
    #             'actual_cable_glands_holes': actuator.actual_cable_glands_holes,
    #             'actual_wiring_diagram': actuator.actual_wiring_diagram,
    #             'actual_blinker': actuator.actual_blinker,
    #             'actual_end_switches': actuator.actual_end_switches,
    #             'actual_way_switches': actuator.actual_way_switches,
    #             'actual_torque_switches': actuator.actual_torque_switches,
    #             'actual_output_type': actuator.actual_output_type,
    #             'actual_temperature': actuator.actual_temperature,
    #             'actual_control_unit_installed': actuator.actual_control_unit_installed,
    #             'actual_hand_wheel': actuator.actual_hand_wheel,
    #             'actual_operating_mode': actuator.actual_operating_mode,
    #             'text_description': actuator.text_description
    #         }
    #
    #         # Ищем аналогичную запись
    #         existing_record = cls.objects.filter(**filters).first()
    #
    #         if existing_record:
    #             return existing_record.id  # Возвращаем id существующей записи
    #
    #     # Если не нашли аналогичной записи или статус не 'Approved', сохраняем новый объект
    #     actuator.save()
    #     return actuator.id  # Возвращаем id новой записи
    #
    # def save(self, *args, **kwargs):
    #     # Вызов метода save_actuator для обработки записи
    #     actuator_id = self.save_actuator(self)
    #     return actuator_id

    def __str__(self):
        return self.name

