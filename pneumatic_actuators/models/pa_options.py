# pneumatic_actuators/models/pa_options.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union

from options.models import BaseTemperatureThroughOption , BaseExdThroughOption , BaseBodyCoatingThroughOption , \
    BaseIpThroughOption , BasePneumaticConnectionThroughOption , BaseSafetyPositionThroughOption , \
    BaseSpringsQtyThroughOption


class PneumaticTemperatureOption(BaseTemperatureThroughOption):
    """Температурные опции для пневмоприводов"""
    model_line = models.ForeignKey(
        'PneumaticActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='temperature_options',
        verbose_name=_("Серия пневмоприводов")
    )

    class Meta:
        verbose_name = _("Температурная опция пневмопривода")
        verbose_name_plural = _("Температурные опции пневмоприводов")
        ordering = ['is_default', 'sorting_order']  # ← ИСПРАВИТЬ СОРТИРОВКУ
        unique_together = ['model_line', 'encoding']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        """Явно указываем имя родительского поля"""
        return 'model_line'

    def __str__(self):
        return self.get_display_name()  # ← ИСПОЛЬЗОВАТЬ БАЗОВЫЙ МЕТОД


class PneumaticIpOption(BaseIpThroughOption):
    """Опции IP для пневмоприводов"""
    model_line = models.ForeignKey(
        'PneumaticActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='ip_options',
        verbose_name=_("Серия пневмоприводов")
    )

    class Meta:
        verbose_name = _("Опция IP пневмопривода")
        verbose_name_plural = _("Опции IP пневмоприводов")
        ordering = ['ip_option__ip_rank', 'sorting_order']
        unique_together = ['model_line', 'ip_option']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        return 'model_line'

    def __str__(self):
        name_str = f"{self.ip_option.name} (Стандарт)" if self.default_option else f"{self.ip_option.name} (Опц.исполнение)"
        return name_str

class PneumaticExdOption(BaseExdThroughOption):
    """Опции взрывозащиты для пневмоприводов"""
    model_line = models.ForeignKey(
        'PneumaticActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='exd_options',
        verbose_name=_("Серия пневмоприводов")
    )

    class Meta:
        verbose_name = _("Опция взрывозащиты пневмопривода")
        verbose_name_plural = _("Опции взрывозащиты пневмоприводов")
        ordering = ['exd_option__sorting_order', 'sorting_order']
        unique_together = ['model_line', 'exd_option']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        return 'model_line'

    def __str__(self):
        name_str= f"{self.exd_option.name} (Стандарт)" if self.default_option else f"{self.exd_option.name} (Опц.исполнение)"
        return name_str

class PneumaticBodyCoatingOption(BaseBodyCoatingThroughOption):
    """Опции покрытия корпуса для пневмоприводов"""
    model_line = models.ForeignKey(
        'PneumaticActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='body_coating_options',
        verbose_name=_("Серия пневмоприводов")
    )

    class Meta:
        verbose_name = _("Опция покрытия корпуса пневмопривода")
        verbose_name_plural = _("Опции покрытия корпуса пневмоприводов")
        ordering = ['body_coating_option__sorting_order', 'sorting_order']
        unique_together = ['model_line', 'body_coating_option']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        return 'model_line'
    def __str__(self):
        name_str = f"{self.body_coating_option.name} (Стандарт)" if self.default_option else f"{self.body_coating_option.name} (Опц.исполнение)"
        return name_str

class PneumaticSafetyPositionOption(BaseSafetyPositionThroughOption):
    """Опции покрытия корпуса для пневмоприводов"""
    model_line_item = models.ForeignKey(
        'PneumaticActuatorModelLineItem',
        on_delete=models.CASCADE,
        related_name='safety_position_option_model_line_item',
        verbose_name=_("Положение безопасности")
    )

    class Meta:
        verbose_name = _("Положение безопасности модели пневмопривода")
        verbose_name_plural = _("Положения безопасности моделей пневмоприводов")
        ordering = ['sorting_order']
        unique_together = ['model_line_item', 'safety_position']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        return 'model_line_item'
    def __str__(self):
        return f"{self.safety_position.name}"

class PneumaticSpringsQtyOption(BaseSpringsQtyThroughOption):
    """Опции покрытия корпуса для пневмоприводов"""
    model_line_item = models.ForeignKey(
        'PneumaticActuatorModelLineItem',
        on_delete=models.CASCADE,
        related_name='springs_qty_option_model_line_item',
        verbose_name=_("Количество пружин")
    )

    class Meta:
        verbose_name = _("Количество пружин модели пневмопривода")
        verbose_name_plural = _("Количество пружин моделей пневмоприводов")
        ordering = ['sorting_order']
        unique_together = ['model_line_item', 'springs_qty']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        return 'model_line_item'
    def __str__(self):
        return f"{self.springs_qty.name}"
