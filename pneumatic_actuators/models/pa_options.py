# pneumatic_actuators/models/pa_options.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union

from options.models import BaseTemperatureThroughOption, BaseExdThroughOption, BaseBodyCoatingThroughOption, \
    BaseIpThroughOption, BasePneumaticConnectionThroughOption, BaseSafetyPositionThroughOption, \
    BaseSpringsQtyThroughOption, BaseHandWheelThroughOption


class PneumaticHandWheelOption(BaseHandWheelThroughOption):
    """Температурные опции для пневмоприводов"""
    model_line = models.ForeignKey(
        'PneumaticActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='hand_wheel_options',
        verbose_name=_("Серия пневмоприводов")
    )

    class Meta:
        verbose_name = _("Тип установленного ручного дублера")
        verbose_name_plural = _("Типы установленного ручного дублерапневмоприводов")
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
        return self.hand_wheel_option.name

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
    def get_or_create_default(cls , parent_obj) :
        """
        Получить дефолтную опцию положения безопасности у родительского объекта

        Args:
            parent_obj: PneumaticActuatorModelLineItem

        Returns:
            Дефолтная опция или None
        """
        parent_field = cls._get_parent_field_name()
        if not parent_field :
            return None

        # ВАЖНО: НЕ создаем опцию, если ее нет - просто возвращаем существующую дефолтную
        # Гарантируем, что дефолтная опция существует через ensure_default_exists
        # cls.ensure_default_exists(parent_obj)

        # Ищем дефолтную опцию у родительского объекта
        default_option = cls.objects.filter(
            **{parent_field : parent_obj , 'is_default' : True , 'is_active' : True}
        ).first()

        # Если дефолтной нет, берем первую активную
        if not default_option :
            default_option = cls.objects.filter(
                **{parent_field : parent_obj , 'is_active' : True}
            ).first()

            if default_option :
                # Делаем ее дефолтной
                default_option.is_default = True
                default_option.save()

        return default_option

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
    def get_or_create_default(cls , parent_obj) :
        """
        Получить дефолтную опцию количества пружин у родительского объекта

        Args:
            parent_obj: PneumaticActuatorModelLineItem

        Returns:
            Дефолтная опция или None
        """
        parent_field = cls._get_parent_field_name()
        if not parent_field :
            return None

        # ВАЖНО: НЕ создаем опцию, если ее нет - просто возвращаем существующую дефолтную
        # Гарантируем, что дефолтная опция существует через ensure_default_exists
        # cls.ensure_default_exists(parent_obj)

        # Ищем дефолтную опцию у родительского объекта
        default_option = cls.objects.filter(
            **{parent_field : parent_obj , 'is_default' : True , 'is_active' : True}
        ).first()

        # Если дефолтной нет, берем первую активную
        if not default_option :
            default_option = cls.objects.filter(
                **{parent_field : parent_obj , 'is_active' : True}
            ).first()

            if default_option :
                # Делаем ее дефолтной
                default_option.is_default = True
                default_option.save()

        return default_option

    def __str__(self) :
        return f"{self.springs_qty.name}"
    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        return 'model_line_item'
    def __str__(self):
        return f"{self.springs_qty.name}"
