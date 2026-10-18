# electric_actuators/models/ea_options.py
"""
Through-модели опций уровня model_line.

Каждая модель связывает серию (ElectricActuatorModelLine) с конкретной
reference-опцией из params, храня encoding, is_default и sorting_order.

Опции этого уровня едины для всех model_line_item в серии
(не зависят от напряжения и DN).

Модели:
    ElectricTemperatureOption      — климатическое исполнение (+обогрев привода)
    ElectricIpOption               — IP
    ElectricExdOption              — взрывозащита
    ElectricBodyCoatingOption      — покрытие корпуса
    ElectricBodyColorOption        — цвет корпуса
    ElectricHandWheelOption        — ручной дублёр
    ElectricTurnAngleOption        — угол поворота
    CableGlandHolesSetBodyOption   — кабельные вводы (привязаны к ModelBody)

Сигнальные опции (переключатели/БУ/блинкер/индикатор/режим) переехали в
матрицу EaSignalMatrixEntry — фаза 7.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union
from options.models import (
    BaseTemperatureThroughOption, BaseBodyCoatingThroughOption,
    BaseIpThroughOption, BaseHandWheelThroughOption, BaseTurnAngleThroughOption,
    BaseThroughOption, BaseSafetyPositionThroughOption,
    BaseColorThroughOption, BaseM2MExdThroughOption, CableGlandHolesSetThroughOption
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
    """Температурные опции для электроприводов.

    Плоская шкала (обогреватель привода — свойство строки):
    STD→NO_HEATER (стандарт); LT/VLT — парами «источник питания обогрева»
    (SEPARATE_LINE — стандарт, MOTOR_CIRCUIT — опция). Код `code` — для
    обмена матрицей (xlsx) и ext-кода; `heater_supply` — откуда питается
    обогреватель привода.
    """
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='temperature_options',
        verbose_name=_("Серия электроприводов")
    )
    code = models.CharField(
        max_length=20, blank=True, default='',
        verbose_name=_("Код исполнения"),
        help_text=_("STD/LT/VLT — для обмена xlsx и расширенного кода")
    )
    heater_supply = models.ForeignKey(
        'params.ActuatorHeaterSupply',
        on_delete=models.PROTECT, null=True, blank=True,
        related_name='temperature_options',
        verbose_name=_("Питание обогрева"),
        help_text=_("Обогреватель привода: NO_HEATER для стандарта, "
                    "SEPARATE_LINE/MOTOR_CIRCUIT для LT/VLT")
    )

    class Meta:
        verbose_name = _("Температурная опция электропривода")
        verbose_name_plural = _("Температурные опции электроприводов")
        ordering = ['is_default', 'sorting_order']
        # unique_together = ['model_line', '','encoding']

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




class ElectricExdOption(BaseM2MExdThroughOption):
    """Опции взрывозащиты для электроприводов.

    Одна строка = одна КОДИРОВКА (опция выбора), внутри — M2M видов взрывозащиты
    (params.ExdOption). Аналог CableGlandExdOption/PosiExdOption.
    """
    model_line = models.ForeignKey(
        'ElectricActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='exd_options',
        verbose_name=_("Серия электроприводов")
    )

    class Meta:
        verbose_name = _("Опция взрывозащиты электропривода")
        verbose_name_plural = _("Опции взрывозащиты электроприводов")
        ordering = ['is_default', 'sorting_order']

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
