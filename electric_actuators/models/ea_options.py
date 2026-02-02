#electric_actuators/models/ea_options.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union

from options.models import BaseTemperatureThroughOption, BaseExdThroughOption, BaseBodyCoatingThroughOption, \
    BaseIpThroughOption, BaseSafetyPositionThroughOption, \
    BaseSpringsQtyThroughOption, BaseHandWheelThroughOption, BaseTurnAngleThroughOption, BasePowerSupplyThroughOption, \
    BaseBlinkerThroughOption, BaseControlUnitInstalledThroughOption, BaseWaySwitchesThroughOption
from params.models import PowerSupplies

"""
Опции корпуса:
    резьба КВ и их количество
    End_switches type (mechanical, electronic) qty (SPDT/DPDT)
    Torque switch - type (mechanical, electronic) qty (SPDT/DPDT)
Опции model_line:
    ElectricTurnAngleOption угол поворота (90-180-270), точность регулировки +-
    ElectricHandWheelOption - вид ручного дублера
    ElectricTemperatureOption - LT
    ElectricIpOption - IP
    ElectricExdOption - Ex
    ElectricBodyCoatingOption - Опции покрытия корпуса для электроприводов
    QC быстросъемное соединение
    ElectricWaySwitchesOption MID	Опция 3х позиционный (по доп.концевикам) - Путевые выключатели SwitchesParameters
    ElectricPowerSupplyOption PowerSupply 
    ElectricControlUnitInstalledOption  Control Unit (POSI, TR, INT...)
    ElectricBlinkerOption  Блинкер BlinkerOption
    
"""

class ElectricTurnAngleOption(BaseTurnAngleThroughOption):
    """Температурные опции для электроприводов"""
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='turn_angle_options',
        verbose_name=_("Серия электроприводов")
    )

    class Meta:
        verbose_name = _('Угол поворота ЭП')
        verbose_name_plural = _("Углы поворота электроприводов")
        ordering = ['is_default', 'sorting_order']  # ← ИСПРАВИТЬ СОРТИРОВКУ
        unique_together = ['model_line', 'encoding']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        """Явно указываем имя родительского поля"""
        return 'model_line'

    @property
    def get_display_name(self):
        return self.get_display_name()

class ElectricHandWheelOption(BaseHandWheelThroughOption):
    """Температурные опции для электроприводов"""
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='hand_wheel_options',
        verbose_name=_("Серия электроприводов")
    )

    class Meta:
        verbose_name = _("Тип установленного ручного дублера")
        verbose_name_plural = _("Типы установленного ручного дублера электроприводов")
        ordering = ['is_default', 'sorting_order']  # ← ИСПРАВИТЬ СОРТИРОВКУ
        unique_together = ['model_line', 'encoding']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        """Явно указываем имя родительского поля"""
        return 'model_line'

    @property
    def get_display_name(self):
        return self.hand_wheel_option.name

    def __str__(self):
        return f"{self.hand_wheel_option.name} (Стандарт)" if self.is_default else f"{self.hand_wheel_option.name} (Опция)"

class ElectricTemperatureOption(BaseTemperatureThroughOption):
    """Температурные опции для электроприводов"""
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='temperature_options',
        verbose_name=_("Серия электроприводов")
    )

    class Meta:
        verbose_name = _("Температурная опция электропривода")
        verbose_name_plural = _("Температурные опции электроприводов")
        ordering = ['is_default', 'sorting_order']  # ← ИСПРАВИТЬ СОРТИРОВКУ
        unique_together = ['model_line', 'encoding']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        """Явно указываем имя родительского поля"""
        return 'model_line'

    def __str__(self):
        return self.get_display_name()  # ← ИСПОЛЬЗОВАТЬ БАЗОВЫЙ МЕТОД

class ElectricBlinkerOption(BaseBlinkerThroughOption):
    """Опции напряжения питания для электроприводов"""
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='blinker_options',
        verbose_name=_("Серия электроприводов")
    )

    class Meta:
        verbose_name = _("Опция наличия блинкера электропривода")
        verbose_name_plural = _("Опции блинкера электроприводов")
        ordering = ['sorting_order']
        unique_together = ['model_line', 'blinker_option']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        return 'model_line'

    def __str__(self):
        return f"{self.blinker_option.name} (Стандарт)" if self.is_default else f"{self.blinker_option.name} (Опция)"

class ElectricPowerSupplyOption(BasePowerSupplyThroughOption):
    """Опции напряжения питания для электроприводов"""
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='power_supply_options',
        verbose_name=_("Серия электроприводов")
    )

    class Meta:
        verbose_name = _("Опция напряжения питания")
        verbose_name_plural = _("Опции напряжения питания электроприводов")
        ordering = ['sorting_order']
        unique_together = ['model_line', 'power_supply']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        return 'model_line'

    def __str__(self):
        return f"{self.power_supply.name}"

class ElectricIpOption(BaseIpThroughOption):
    """Опции IP для электроприводов"""
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='ip_options',
        verbose_name=_("Серия электроприводов")
    )

    class Meta:
        verbose_name = _("Опция IP электропривода")
        verbose_name_plural = _("Опции IP электроприводов")
        ordering = ['ip_option__ip_rank', 'sorting_order']
        unique_together = ['model_line', 'ip_option']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        return 'model_line'

    def __str__(self):
        return f"{self.ip_option.name} (Стандарт)" if self.is_default else f"{self.ip_option.name} (Опция)"

class ElectricExdOption(BaseExdThroughOption):
    """Опции взрывозащиты для электроприводов"""
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='exd_options',
        verbose_name=_("Серия электроприводов")
    )

    class Meta:
        verbose_name = _("Опция взрывозащиты электропривода")
        verbose_name_plural = _("Опции взрывозащиты электроприводов")
        ordering = ['exd_option__sorting_order', 'sorting_order']
        unique_together = ['model_line', 'exd_option']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        return 'model_line'

    def __str__(self):
        return f"{self.exd_option.name} (Стандарт)" if self.is_default else f"{self.exd_option.name} (Опция)"

class ElectricWaySwitchesOption(BaseWaySwitchesThroughOption):
    """Опции взрывозащиты для электроприводов"""
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='way_switches_options',
        verbose_name=_("Серия электроприводов")
    )

    class Meta:
        verbose_name = _("Опция путевые выключатели электропривода")
        verbose_name_plural = _("Опции взрывозащиты электроприводов")
        ordering = ['sorting_order']
        unique_together = ['model_line', 'way_switches_option']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        return 'model_line'

    def __str__(self):
        return f"{self.way_switches_option.name} (Стандарт)" if self.is_default else f"{self.way_switches_option.name} (Опция)"

class ElectricBodyCoatingOption(BaseBodyCoatingThroughOption):
    """Опции покрытия корпуса для электроприводов"""
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='body_coating_options',
        verbose_name=_("Серия электроприводов")
    )

    class Meta:
        verbose_name = _("Опция покрытия корпуса электропривода")
        verbose_name_plural = _("Опции покрытия корпуса электроприводов")
        ordering = ['body_coating_option__sorting_order', 'sorting_order']
        unique_together = ['model_line', 'body_coating_option']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        return 'model_line'
    def __str__(self):
        # ИСПРАВЛЕНО: используем is_default вместо default_option
        return f"{self.body_coating_option.name} (Стандарт)" if self.is_default else f"{self.body_coating_option.name} (Опция)"

class ElectricControlUnitInstalledOption(BaseControlUnitInstalledThroughOption):
    """Опции покрытия корпуса для электроприводов"""
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='control_unit_options',
        verbose_name=_("Серия электроприводов")
    )

    class Meta:
        verbose_name = _("Опция блока управления электропривода")
        verbose_name_plural = _("Опции блока управления электроприводов")
        ordering = ['sorting_order']
        unique_together = ['model_line', 'control_unit_option']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        return 'model_line'
    def __str__(self):
        # ИСПРАВЛЕНО: используем is_default вместо default_option
        return f"{self.control_unit_option.name} (Стандарт)" if self.is_default else f"{self.control_unit_option.name} (Опция)"

# class ElectricSafetyPositionOption(BaseSafetyPositionThroughOption):
#     """Опции покрытия корпуса для электроприводов"""
#     model_line_item = models.ForeignKey(
#         'ElectricActuatorModelLineItem',
#         on_delete=models.CASCADE,
#         related_name='safety_position_option_model_line_item',
#         verbose_name=_("Положение безопасности")
#     )
#
#     class Meta:
#         verbose_name = _("Положение безопасности модели электропривода")
#         verbose_name_plural = _("Положения безопасности моделей электроприводов")
#         ordering = ['sorting_order']
#         unique_together = ['model_line_item', 'safety_position']
#
#     @classmethod
#     def _get_parent_field_name(cls) -> Optional[str] :
#         return 'model_line_item'
#     def __str__(self):
#         return f"{self.safety_position.name}"



