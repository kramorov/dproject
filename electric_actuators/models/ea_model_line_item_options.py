# electric_actuators/models/ea_model_line_item_options.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List , Optional , Tuple , Any , Dict , Union
from django.core.exceptions import ValidationError

from core.models import StructuredDataMixin
from electric_actuators.models.ea_model_line_item import ElectricActuatorModelLineItem
from options.models import BaseThroughOptionNoDefault

import logging

from params.models import PowerSupplies

logger = logging.getLogger(__name__)


class ElectricPowerSupplyOption(BaseThroughOptionNoDefault) :
    """Опции напряжения питания для модели в серии электроприводов"""
    """
        through-модель для температурных опций
        Наследует от BaseThroughOptionNoDefault (нет напряжения питания по дефолту и добавляет температурные поля
        """
    model_line_item = models.ForeignKey(
                                    ElectricActuatorModelLineItem ,
                                    on_delete=models.CASCADE ,
                                    related_name='model_line_item_power_supply_option' ,
                                    verbose_name=_("Модель") ,
                                    help_text=_('Модель в серии электроприводов'))
    power_supply = models.ForeignKey(PowerSupplies ,
                                     related_name='electric_actuator_data_model_power_supply' , null=False ,
                                     on_delete=models.CASCADE ,
                                     verbose_name=_("Напряжение") ,
                                     help_text=_('Напряжение питания модели'))

    time_to_open = models.DecimalField(max_digits=5 , decimal_places=3 , blank=True , null=True ,
                                       default=0 ,
                                       verbose_name=_('Время поворота на 90°') ,
                                       help_text=_('Время поворота на 90°, сек'))
    rotation_speed = models.DecimalField(max_digits=3 , decimal_places=0 , blank=True , null=True ,
                                         default=0 ,
                                         verbose_name=_('Скорость') ,
                                         help_text=_('Скорость, об/мин'))
    torque_min = models.DecimalField(max_digits=5 , decimal_places=0 ,
                                     default=0 ,
                                     verbose_name=_('Мин.усилие') ,
                                     help_text=_('Минимальное усилие'))
    torque_max = models.DecimalField(max_digits=5 , decimal_places=0 ,
                                     default=0 ,
                                     verbose_name=_('Макс.усилие') ,
                                     help_text=_('Максимальное усилие'))
    motor_current_rated = models.DecimalField(max_digits=6 , decimal_places=2 , blank=True , null=True ,
                                              default=0 ,
                                              verbose_name=_('Ток ном,А') ,
                                              help_text=_('Номинальный ток двигателя'))

    motor_current_starting = models.DecimalField(max_digits=6 , decimal_places=2 , blank=True , null=True ,
                                                 default=0 ,
                                                 verbose_name=_('Ток пуск,А') ,
                                                 help_text=_('Пусковой ток двигателя'))
    motor_power = models.DecimalField(max_digits=6 , decimal_places=2 , blank=True , null=True ,
                                      default=0 ,
                                      verbose_name=_('Мощн,кВт') ,
                                      help_text=_('Мощность двигателя, кВт'))
    class Meta :
        verbose_name = _("Опция напряжения питания для модели в серии электроприводов")
        verbose_name_plural = _("Опции напряжения питания для модели в серии электроприводов")
        ordering = ['sorting_order']
        # unique_together = ['model_line' , 'encoding']

    @classmethod
    def _get_parent_field_name(cls) :
        return 'model_line'
