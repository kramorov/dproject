# pneumatic_actuators/models/pa_basic_model_item.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import pre_save , post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from pneumatic_actuators.models.pa_body import PneumaticActuatorBody
from pneumatic_actuators.models.pa_model_line import PneumaticActuatorModelLine
from pneumatic_actuators.models.pa_params import PneumaticActuatorVariety


class PneumaticActuatorBasicModelItem(models.Model) :
    """
    Список базовых моделей с привязкой к body
    Указывается - DA или SR.
    Позволяет ограничить список моделей, присвоить уникальное название модели в серии
    Нужно в-основном, чтобы сделать маппинг китайских моделей в русские
    У китайцев могут быть свои непонятные наименования, у наших совсем другие.
    Конкретное изделие с уникальной кодировкой формируется из выбранных опций
        LT, количество пружин...
        допустимые опции указываются в model_line
    """
    name = models.CharField(max_length=200 ,
                            verbose_name=_("Название") ,
                            help_text=_('Название базовой модели привода'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код базовой модели модели"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание базовой модели привода'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))
    model_line = models.ForeignKey(PneumaticActuatorModelLine , on_delete=models.PROTECT ,
                                   verbose_name=_("Серия"),
                                   related_name='basic_model_pneumatic_model_line' , help_text=_('Серия приводов'))
    pneumatic_actuator_actuator_variety = \
        models.ForeignKey(PneumaticActuatorVariety , blank=True , null=True ,
                               related_name='basic_model_pneumatic_actuator_variety' ,
                               on_delete=models.SET_NULL ,
                               verbose_name=_("DA/SR") ,
                               help_text=_('Тип приводов - DA/SR'))

    body = models.ForeignKey(PneumaticActuatorBody , blank=True , null=True ,
                          related_name='basic_model_body' ,
                          on_delete=models.SET_NULL ,
                          verbose_name=_("Корпус") ,
                          help_text=_('Модель корпуса'))
    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Название базовой модели привода')
        verbose_name_plural = _('Названия базовых моделей приводов')

    def __str__(self) :
        return self.name