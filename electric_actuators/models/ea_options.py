# electric_actuators/models/ea_options.py - ИСПРАВЛЕННЫЙ:

from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union
from options.models import (
    BaseTemperatureThroughOption, BaseExdThroughOption, BaseBodyCoatingThroughOption,
    BaseIpThroughOption, BaseHandWheelThroughOption, BaseTurnAngleThroughOption,
    BaseBlinkerThroughOption, BaseControlUnitInstalledThroughOption,
    BaseWaySwitchesThroughOption,
    BaseOperatingModeThroughOption,
    BaseMechanicalIndicatorThroughOption, BaseThroughOption, BaseSafetyPositionThroughOption,
    BaseColorThroughOption, BaseEndSwitchesThroughOption, BaseTorqueSwitchesThroughOption,
    CableGlandHolesSetThroughOption
)



class ElectricHandWheelOption(BaseHandWheelThroughOption):
    """Ручной дублер для электроприводов"""
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='hand_wheel_options',
        verbose_name=_("Серия электроприводов")
    )

    class Meta:
        verbose_name = _("Тип установленного ручного дублера")
        verbose_name_plural = _("Типы установленного ручного дублера электроприводов")
        ordering = ['is_default', 'sorting_order']
        unique_together = ['model_line', 'hand_wheel_option', 'encoding']

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line'


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
        ordering = ['is_default', 'sorting_order']
        # unique_together = ['model_line', '','encoding']

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line'


class ElectricBlinkerOption(BaseBlinkerThroughOption):
    """Опции блинкера для электроприводов"""
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
    def _get_parent_field_name(cls):
        return 'model_line'


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
    def _get_parent_field_name(cls):
        return 'model_line'




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
    def _get_parent_field_name(cls):
        return 'model_line'

class ElectricBodyColorOption(BaseColorThroughOption):
    """Опции взрывозащиты для электроприводов"""
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='body_color_options',
        verbose_name=_("Серия электроприводов")
    )

    class Meta:
        verbose_name = _("Опция цвета корпуса электропривода")
        verbose_name_plural = _("Опции цвета корпуса электроприводов")
        ordering = ['sorting_order']
        unique_together = ['model_line', 'color_option']

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line'

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
    def _get_parent_field_name(cls):
        return 'model_line'


class ElectricControlUnitInstalledOption(BaseControlUnitInstalledThroughOption):
    """Опции блока управления для электроприводов"""
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
    def _get_parent_field_name(cls):
        return 'model_line'


class ElectricOperatingModeOption(BaseOperatingModeThroughOption):
    """Опции режима работы двигателя для электроприводов"""
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='operating_mode_options',
        verbose_name=_("Серия электроприводов")
    )

    class Meta:
        verbose_name = _("Опция режима работы двигателя электропривода")
        verbose_name_plural = _("Опции режима работы двигателя электроприводов")
        ordering = ['sorting_order']
        unique_together = ['model_line', 'operating_mode_option']

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line'


class ElectricMechanicalIndicatorOption(BaseMechanicalIndicatorThroughOption):
    """Опции механического индикатора для электроприводов"""
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='mechanical_indicator_options',
        verbose_name=_("Серия электроприводов")
    )

    class Meta:
        verbose_name = _("Опция механического индикатора электропривода")
        verbose_name_plural = _("Опции механического индикатора электроприводов")
        ordering = ['sorting_order']
        unique_together = ['model_line', 'mechanical_indicator_option']

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line'


class CableGlandHolesSetBodyOption(CableGlandHolesSetThroughOption):
    """Модель для сквозных опций CableGlandHolesSet"""

    model_body = models.ForeignKey(
        'ElectricActuatorBody',
        on_delete=models.CASCADE,
        related_name='cg_set_options_through',
        verbose_name=_("Модель корпуса")
    )

    @classmethod
    def _get_parent_field_name(cls) :
        return 'model_body'

class ElectricTurnAngleOption(BaseTurnAngleThroughOption):
    """Угол поворота для электроприводов"""
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='turn_angle_options',
        verbose_name=_("Серия электроприводов")
    )

    class Meta:
        verbose_name = _('Угол поворота ЭП')
        verbose_name_plural = _("Углы поворота электроприводов")
        ordering = ['is_default', 'sorting_order']
        # unique_together = ['model_line', 'encoding']

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line'

class ElectricWaySwitchesOption(BaseWaySwitchesThroughOption):
    """Опции путевых выключателей для электроприводов
        привязан к ModelLineItem"""
    model_line_item = models.ForeignKey(
        'ElectricActuatorModelLineItem',
        on_delete=models.CASCADE,
        related_name='way_switches_options',
        help_text=_("Модель в серии электроприводов"),
        verbose_name=_('Модель')
    )

    class Meta:
        verbose_name = _("Опция путевые выключатели электропривода")
        verbose_name_plural = _("Опции путевых выключателей электроприводов")
        ordering = ['sorting_order']
        # unique_together = ['model_line_item', 'way_switches_option']

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line_item'

class ElectricEndSwitchesOption(BaseEndSwitchesThroughOption):
    """Опции концевых выключателей для электроприводов, привязан к ModelLineItem"""
    model_line_item = models.ForeignKey(
        'ElectricActuatorModelLineItem',
        on_delete=models.CASCADE,
        related_name='end_switches_options',
        help_text=_("Модель в серии электроприводов"),
        verbose_name=_('Модель')
    )

    class Meta:
        verbose_name = _("Опция конечные выключатели электропривода")
        verbose_name_plural = _("Опции конечных выключателей электроприводов")
        ordering = ['sorting_order']
        # unique_together = ['model_line_item', 'way_switches_option']

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line_item'

class ElectricTorqueSwitchesOption(BaseTorqueSwitchesThroughOption):
    """Опции моментных выключателей для электроприводов, привязан к ModelLineItem"""
    model_line_item = models.ForeignKey(
        'ElectricActuatorModelLineItem',
        on_delete=models.CASCADE,
        related_name='torque_switches_options',
        help_text=_("Модель в серии электроприводов"),
        verbose_name=_('Модель')
    )

    class Meta:
        verbose_name = _("Опция моментные выключатели электропривода")
        verbose_name_plural = _("Опции моментных выключателей электроприводов")
        ordering = ['sorting_order']
        # unique_together = ['model_line_item', 'way_switches_option']

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line_item'
