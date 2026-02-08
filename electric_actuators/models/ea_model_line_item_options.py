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


    motor_current_rated = models.DecimalField(max_digits=6 , decimal_places=2 , blank=True , null=True ,
                                              default=0 ,
                                              verbose_name=_('Ток ном,А') ,
                                              help_text=_('Номинальный ток двигателя'))

    motor_current_starting = models.DecimalField(max_digits=6 , decimal_places=2 , blank=True , null=True ,
                                                 default=0 ,
                                                 verbose_name=_('Ток пуск,А') ,
                                                 help_text=_('Пусковой ток двигателя'))
    motor_power = models.DecimalField(max_digits=7 , decimal_places=3 , blank=True , null=True ,
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

    def clean(self) :
        """Валидация перед сохранением"""
        errors = {}

        # Проверка обязательных полей
        if not self.model_line_item :
            errors['model_line_item'] = _('Необходимо указать модель в серии')

        if not self.power_supply :
            errors['power_supply'] = _('Необходимо указать напряжение питания')

        # Валидация числовых полей
        if self.motor_current_rated is not None and self.motor_current_rated < 0 :
            errors['motor_current_rated'] = _('Ток не может быть отрицательным')

        if self.motor_current_starting is not None and self.motor_current_starting < 0 :
            errors['motor_current_starting'] = _('Пусковой ток не может быть отрицательным')

        if self.motor_power is not None and self.motor_power < 0 :
            errors['motor_power'] = _('Мощность не может быть отрицательной')

        # Проверка логики: пусковой ток должен быть больше или равен номинальному
        if (self.motor_current_starting is not None and
                self.motor_current_rated is not None and
                self.motor_current_starting < self.motor_current_rated) :
            errors['motor_current_starting'] = _(
                'Пусковой ток должен быть больше или равен номинальному току'
            )

        # Проверка на дубликаты (если уникальность не задана через unique_together)
        # if self.pk is None :  # Только для новых записей
        #     existing = ElectricPowerSupplyOption.objects.filter(
        #         model_line_item=self.model_line_item ,
        #         power_supply=self.power_supply
        #     ).exists()
        #
        #     if existing :
        #         errors['__all__'] = _(
        #             f'Опция с напряжением "{self.power_supply}" '
        #             f'уже существует для модели "{self.model_line_item}"'
        #         )

        if errors :
            raise ValidationError(errors)

    def save(self , *args , **kwargs) :
        """Сохранение с установкой encoding и валидацией"""

        # Автоматически устанавливаем encoding из имени power_supply
        if self.power_supply and self.model_line_item and self.encoding :
            self.encoding = str(self.power_supply.encoding)

        # Если encoding слишком длинный, обрезаем его
        if self.encoding and len(self.encoding) > 50 :
            self.encoding = self.encoding[:50]

        # Выполняем валидацию
        self.full_clean()

        # Сохраняем объект
        super().save(*args , **kwargs)

    def __str__(self) :
        """Строковое представление"""
        if self.model_line_item and self.power_supply :
            return f"{self.model_line_item.name} - {self.power_supply.name}"
        return super().__str__()
