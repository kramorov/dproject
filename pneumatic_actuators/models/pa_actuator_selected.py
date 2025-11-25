# pneumatic_actuators/models/pa_actual_actuator.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import pre_save , post_save
from django.dispatch import receiver
from typing import List, Optional, Tuple, Any, Dict, Union
from django.core.exceptions import ValidationError


from params.models import MountingPlateTypes , StemShapes , StemSize , ActuatorGearboxOutputType , IpOption , \
    BodyCoatingOption , ExdOption , EnvTempParameters , HandWheelInstalledOption
from pneumatic_actuators.models import PneumaticActuatorBody , PneumaticActuatorModelLineItem
from pneumatic_actuators.models.pa_params import PneumaticActuatorVariety, PneumaticActuatorConstructionVariety

from producers.models import Brands
import logging

logger = logging.getLogger(__name__)

class PneumaticActuatorSelected(models.Model) :
    """
    Выбранный из списка моделей привод
    с выбранными опциями.
    """
    name = models.CharField(max_length=200 ,
                            verbose_name=_("Название") ,
                            help_text=_('Название привода - формируется автоматически'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код привода - формируется автоматически"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание привода - формируется автоматически'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    selected_model = models.ForeignKey(PneumaticActuatorModelLineItem , null=True,
                              related_name='selected_pneumatic_actuator_model_line_item' ,
                              on_delete=models.SET_NULL,  # Сохранит привод, но установит selected_model в NULL
                              verbose_name=_('Модель'),
                              help_text=_('Модель пневмопривода'))
    # Выбранные опции
    selected_safety_position = models.ForeignKey(
        'PneumaticSafetyPositionOption' ,
        on_delete=models.SET_NULL ,
        null=True , blank=True ,
        verbose_name=_("Выбранное положение безопасности") ,
        help_text=_('Выбранное положение безопасности привода')
    )

    selected_springs_qty = models.ForeignKey(
        'PneumaticSpringsQtyOption' ,
        on_delete=models.SET_NULL ,
        null=True , blank=True ,
        verbose_name=_("Выбранное количество пружин") ,
        help_text=_('Выбранное количество пружин привода')
    )

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Выбранный пневмопривод')
        verbose_name_plural = _('Выбранные пневмоприводы')

    def __str__(self) :
        return self.name

    def save(self , *args , **kwargs) :
        """Используем сервис для генерации данных"""
        from pneumatic_actuators.services.option_service import OptionService

        if self.selected_model :

            generated_data = OptionService.generate_actuator_data(
                model_id=self.selected_model.id ,
                safety_option_id=self.selected_safety_position.id if self.selected_safety_position else None ,
                springs_option_id=self.selected_springs_qty.id if self.selected_springs_qty else None
            )

            self.name = generated_data['name']
            self.code = generated_data['code']
            self.description = generated_data['description']

        super().save(*args , **kwargs)



    @property
    def available_safety_positions(self) :
        """Доступные положения безопасности для выбранной модели"""
        from pneumatic_actuators.models.pa_options import PneumaticSafetyPositionOption
        if not self.selected_model :
            return PneumaticSafetyPositionOption.objects.none()
        return PneumaticSafetyPositionOption.objects.filter(
            model_line_item=self.selected_model ,
            is_active=True
        ).select_related('safety_position')

    @property
    def available_springs_qty(self) :
        """Доступные количества пружин для выбранной модели"""
        from pneumatic_actuators.models.pa_options import PneumaticSpringsQtyOption
        if not self.selected_model :
            return PneumaticSpringsQtyOption.objects.none()
        return PneumaticSpringsQtyOption.objects.filter(
            model_line_item=self.selected_model ,
            is_active=True
        ).select_related('springs_qty')

    def get_selected_options_display(self) :
        """Текстовое представление выбранных опций"""
        options = []
        if self.selected_safety_position :
            options.append(f"Положение: {self.selected_safety_position.safety_position.name}")
        if self.selected_springs_qty :
            options.append(f"Пружины: {self.selected_springs_qty.springs_qty.name}")
        return "; ".join(options) if options else "Опции не выбраны"