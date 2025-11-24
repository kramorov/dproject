import uuid
from datetime import datetime

from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.utils.timezone import now

# from client_request.models import ClientRequestLine, ClientRequest
from electric_actuators.models import CableGlandHolesSet
from producers.models import Brands, Producer
from params.models import PowerSupplies , ExdOption , BodyCoatingOption , BlinkerOption , SwitchesParameters , \
    EnvTempParameters , IpOption , MeasureUnits , \
    DigitalProtocolsSupportOption , ControlUnitInstalledOption , ActuatorGearboxOutputType , HandWheelInstalledOption , \
    OperatingModeOption , StemShapes , StemSize , MountingPlateTypes , ThreadSize , CertVariety , CertData , \
    MechanicalIndicatorInstalledOption , ControlUnitLocationOption , ControlUnitTypeOption , SafetyPositionOption , \
    ValveTypes , ClimaticConditions

VALVE_DATA_STEM_TYPES = [
    ('Выдвижной', 'Выдвижной шток'),  # ('AC', 'Постоянный ток')
    ('НЕвыдвижной', 'Невыдвижной шток'),  # ('DC', 'Переменный ток')
]

class AbstractValveModel(models.Model):
    valve_model_dn = models.PositiveIntegerField(blank=True, null=True, help_text='Dn арматуры')
    valve_model_pn = models.PositiveIntegerField(blank=True, null=True, help_text='Dn арматуры')
    valve_model_pn_measure_unit = models.ForeignKey(MeasureUnits, related_name='%(class)s_pn_measure_unit', blank=True,
                                                    null=True,
                                                    on_delete=models.SET_NULL, help_text='Единица измерения Pn')
    valve_model_pn_delta = models.PositiveIntegerField(blank=True, null=True, help_text='Перепад Dn арматуры')
    valve_model_pn_delta_measure_unit = models.ForeignKey(MeasureUnits, related_name='%(class)s_pn_delta_measure_unit',
                                                          blank=True, null=True,
                                                          on_delete=models.SET_NULL,
                                                          help_text='Единица измерения перепада Pn')
    valve_model_torque_to_open = models.DecimalField(max_digits=5, decimal_places=0, help_text='Усилие на открытие')
    valve_model_torque_to_close = models.DecimalField(max_digits=5, decimal_places=0, help_text='Усилие на открытие')
    valve_model_rotations_to_open = models.DecimalField(max_digits=5, decimal_places=1,
                                                        help_text='Число оборотов на открытие')
    valve_model_stem_size = models.ForeignKey(StemSize, related_name='%(class)s', blank=True,
                                              null=True,
                                              on_delete=models.SET_NULL, help_text='Размер штока модели арматуры')

    valve_model_mounting_plate = models.ManyToManyField(MountingPlateTypes, blank=True,
                                                        related_name='%(class)s',
                                                        help_text='Монтажная площадка модели арматуры')
    valve_type = models.ForeignKey(ValveTypes, related_name='%(class)s_valve_type', blank=True, null=True,
                                   on_delete=models.SET_NULL, help_text='Тип арматуры ')
    valve_stem_retract_type = models.CharField(max_length=30, choices=VALVE_DATA_STEM_TYPES, default='НЕвыдвижной')

    class Meta:
        abstract = True


class AbstractActuatorModelBodyMixin(models.Model):
    mounting_plate = models.ManyToManyField(MountingPlateTypes, blank=True,
                                            related_name='%(class)s',
                                            help_text='Монтажная площадка')
    stem_shape = models.ForeignKey(StemShapes, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='%(class)s', help_text='Тип отверстия под шток арматуры')
    stem_size = models.ForeignKey(StemSize, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='%(class)s', help_text='Размер отверстия под шток арматуры')

    class Meta:
        abstract = True


class AbstractActuatorModelBodyMaxStemMixin(models.Model):
    max_stem_height = models.PositiveIntegerField(blank=True, null=True,
                                                  help_text='Глубина отверстия под шток арматуры')
    max_stem_diameter = models.PositiveIntegerField(blank=True, null=True, help_text='Максимальный диаметр отверстия '
                                                                                     'под шток арматуры')

    class Meta:
        abstract = True


class AbstractElectricActuatorCableGlandMixin(models.Model):
    default_cable_glands_holes = \
        models.ForeignKey(CableGlandHolesSet, null=True, blank=True,
                          related_name='%(class)s',
                          on_delete=models.SET_NULL,
                          help_text='Стандартные отверстия под кабельные вводы')
    allowed_cable_glands_holes = \
        models.ManyToManyField(CableGlandHolesSet, blank=True,
                               related_name='%(class)s',
                               help_text='Возможные для выбора варианты отверстий под кабельные вводы для корпуса ('
                                         'можно выбрать несколько)')
    text_description = models.CharField(max_length=500, blank=True, null=True, help_text='Описание типа корпуса')

    class Meta:
        abstract = True


class AbstractActuatorMixin(AbstractActuatorModelBodyMixin):
    safety_position = models.ForeignKey(SafetyPositionOption,
                                        related_name='%(class)s',
                                        null=True, \
                                        blank=True, on_delete=models.SET_NULL,
                                        help_text='Положение безопасности привода')
    time_to_open = models.PositiveIntegerField(blank=True, null=True, help_text='Время поворота')
    time_to_open_measure_unit = models.ForeignKey(MeasureUnits, related_name='time_to_open_measure_unit_%(class)s',
                                                  null=True, blank=True,
                                                  on_delete=models.SET_NULL,
                                                  help_text='Ед.изм. времени поворота')
    rotations_to_open = models.PositiveIntegerField(blank=True, null=True,
                                                    help_text='Скорость')
    rotations_to_open_measure_unit = models.ForeignKey(MeasureUnits,
                                                       related_name='rotations_to_open_measure_unit_%(class)s',
                                                       null=True, \
                                                       blank=True, on_delete=models.SET_NULL,
                                                       help_text='Ед.изм. времени поворота')
    rotations_angle = models.PositiveIntegerField(blank=True, null=True,
                                                  help_text='Угол поворота')
    ip = models.ForeignKey(IpOption, related_name='%(class)s', blank=True, null=True,
                           on_delete=models.SET_NULL, help_text='Степень IP')
    body_coating = models.ForeignKey(BodyCoatingOption, related_name='%(class)s', blank=True,
                                     null=True,
                                     on_delete=models.SET_NULL, help_text='Покрытие корпуса')
    exd = models.ForeignKey(ExdOption, related_name='%(class)s', blank=True, null=True,
                            on_delete=models.SET_NULL, help_text='Степень exd')
    output_type = models.ForeignKey(ActuatorGearboxOutputType, related_name='%(class)s', blank=True,
                                    null=True,
                                    on_delete=models.SET_NULL, help_text='Вид привода')
    temperature = models.ForeignKey(EnvTempParameters, related_name='%(class)s', blank=True,
                                    null=True, on_delete=models.SET_NULL, help_text='Температурное исполнение')
    climatic_conditions =models.ForeignKey(ClimaticConditions, related_name='%(class)s', blank=True,
                                    null=True, on_delete=models.SET_NULL, help_text='Климатическое исполнение')

    mechanical_indicator = \
        models.ForeignKey(MechanicalIndicatorInstalledOption, blank=True, null=True,
                          related_name='%(class)s',
                          on_delete=models.SET_NULL,
                          help_text='Установленный механический индикатор')

    hand_wheel = models.ForeignKey(HandWheelInstalledOption, related_name='%(class)s', blank=True,
                                   null=True, on_delete=models.SET_NULL, help_text='Ручной дублер')

    operating_mode = models.ForeignKey(OperatingModeOption, related_name='%(class)s', blank=True,
                                       null=True, on_delete=models.SET_NULL, help_text='Режим работы')

    class Meta:
        abstract = True


class AbstractElectricActuator(AbstractActuatorMixin):
    cable_glands_holes = models.ForeignKey(CableGlandHolesSet, related_name='%(class)s', \
                                           on_delete=models.SET_NULL, null=True, blank=True, \
                                           help_text='Отверстия под кабельные вводы')
    blinker = models.ForeignKey(BlinkerOption, related_name='%(class)s', blank=True, null=True,
                                on_delete=models.SET_NULL, help_text='Блинкер')
    end_switches = models.ForeignKey(SwitchesParameters, related_name='%(class)s_end_switches', blank=True,
                                     null=True,
                                     on_delete=models.SET_NULL, help_text='Концевые выключатели')
    way_switches = models.ForeignKey(SwitchesParameters, related_name='%(class)s_way_switches', blank=True,
                                     null=True, on_delete=models.SET_NULL, help_text='Путевые выключатели')
    torque_switches = models.ForeignKey(SwitchesParameters, related_name='%(class)s_torque_switches', blank=True,
                                        null=True, on_delete=models.SET_NULL, help_text='Ограничители момента')
    output_type = models.ForeignKey(ActuatorGearboxOutputType, related_name='%(class)s', blank=True,
                                    null=True,
                                    on_delete=models.SET_NULL, help_text='Вид привода')
    digital_protocol_support = models.ForeignKey(DigitalProtocolsSupportOption,
                                                 related_name='%(class)s', blank=True,
                                                 null=True, on_delete=models.SET_NULL, \
                                                 help_text='Поддержка цифровых протоколов')
    control_unit_type = models.ForeignKey(ControlUnitTypeOption,
                                          related_name='%(class)s', blank=True,
                                          null=True, on_delete=models.SET_NULL, help_text='Тип блока управления')
    control_unit_installed = models.ForeignKey(ControlUnitInstalledOption,
                                               related_name='%(class)s', blank=True,
                                               null=True, on_delete=models.SET_NULL, help_text='Блок управления')
    control_unit_location = models.ForeignKey(ControlUnitLocationOption,
                                              related_name='%(class)s',
                                              blank=True,
                                              null=True, on_delete=models.SET_NULL,
                                              help_text='Размещение блока управления')
    operating_mode = models.ForeignKey(OperatingModeOption, related_name='%(class)s', blank=True,
                                       null=True, on_delete=models.SET_NULL, help_text='Режим работы электропривода')

    class Meta:
        abstract = True


# Базовый миксин, который добавляет поле created_at
class CreatedAtMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        abstract = True


# Миксин, который добавляет поле updated_at и наследует CreatedAtMixin
class UpdatedAtMixin(models.Model):
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        abstract = True
