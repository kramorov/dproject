#electric_actuators/models/ea_model_line.py
from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.utils.translation import gettext_lazy as _
from typing import List , Optional , Tuple , Any , Dict , Union
from django.core.exceptions import ValidationError

from cert_doc.models import AbstractCertRelation
from core.models import StructuredDataMixin

from producers.models import Brands
from params.models import ExdOption, BodyCoatingOption, BlinkerOption, SwitchesParameters, \
    EnvTempParameters, IpOption, ControlUnitInstalledOption, ActuatorGearboxOutputType, HandWheelInstalledOption, \
    OperatingModeOption, CertData, \
    MechanicalIndicatorInstalledOption


class ElectricActuatorModelLine(StructuredDataMixin , models.Model) :
    """
    Серия электроприводов - объединяет в себе общие для всех моделей серии свойства
    и доступные опции
    Опции корпуса:

        резьба КВ и их количество
        End_switches type (mechanical, electronic) qty (SPDT/DPDT)
        Torque switch - type (mechanical, electronic) qty (SPDT/DPDT)
    Опции model_line:
        угол поворота (90-180-270)
        LT
        IP
        Ex
        QC быстросъемное соединение
        MID	Опция 3х позиционный (по доп.концевикам) - Путевые выключатели
        PowerSupply
        Control Unit (POSI, TR, INT...)
    """
    name = models.CharField(max_length=200 ,
                            verbose_name=_("Название") ,
                            help_text=_('Название серии'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код серии приводов"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание модели корпуса привода'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))
    model_item_code_template = models.CharField(max_length=500 , blank=True , null=True ,
                                                verbose_name=_("Шаблон артикула") ,
                                                help_text=_('Шаблон артикула для конкретной модели серии'))
    brand = models.ForeignKey(Brands , blank=True , null=True ,
                              related_name='electric_model_line_brand' ,
                              on_delete=models.SET_NULL ,
                              help_text='Бренд производителя')
    default_output_type = \
        models.ForeignKey(ActuatorGearboxOutputType , blank=True , null=True ,
                          related_name='electric_model_line_default_output_type' ,
                          on_delete=models.SET_NULL ,
                          help_text=_('Тип работы серии приводов'))


    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Серия моделей электроприводов')
        verbose_name_plural = _('Серии моделей электроприводов')

    def __str__(self) :
        return self.name

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

    certificates = GenericRelation(CertData)

    def __str__(self):
        return self.name

