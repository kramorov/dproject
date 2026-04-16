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
        verbose_name_plural = _("Типы установленного ручного дублера пневмоприводов")
        ordering = ['is_default', 'sorting_order']  # ← ИСПРАВИТЬ СОРТИРОВКУ
        unique_together = ['model_line', 'encoding']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        """Явно указываем имя родительского поля"""
        return 'model_line'

    @classmethod
    def get_for_select(cls , model_line_id: Optional[int] = None ,
                       model_line_item_id: Optional[int] = None ,
                       active_only: bool = True) -> List[Dict] :
        """Получить опции ручного дублера"""
        queryset = cls.objects.all()

        if active_only :
            queryset = queryset.filter(is_active=True)

        if model_line_id :
            queryset = queryset.filter(model_line_id=model_line_id)

        # Если передан model_line_item_id, получаем model_line через него
        if model_line_item_id :
            from pneumatic_actuators.models import PneumaticActuatorModelLineItem
            try :
                model_line_item = PneumaticActuatorModelLineItem.objects.select_related(
                    'model_line'
                ).get(id=model_line_item_id)
                if model_line_item.model_line :
                    queryset = queryset.filter(model_line_id=model_line_item.model_line.id)
            except PneumaticActuatorModelLineItem.DoesNotExist :
                pass

        return [{'id' : obj.id , 'name' : str(obj) , 'code' : obj.encoding} for obj in queryset]

    @property
    def get_display_name(self):
        return self.hand_wheel_option.name

    def __str__(self):
        return f"{self.hand_wheel_option.name} (Стандарт)" if self.is_default else f"{self.hand_wheel_option.name} (Опция)"

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
        return f"{self.ip_option.name} (Стандарт)" if self.is_default else f"{self.ip_option.name} (Опция)"

    @classmethod
    def get_for_select(cls , model_line_id: Optional[int] = None ,
                       model_line_item_id: Optional[int] = None ,
                       active_only: bool = True) -> List[Dict] :
        """Получить опции IP защиты"""
        queryset = cls.objects.all()

        if active_only :
            queryset = queryset.filter(is_active=True)

        if model_line_id :
            queryset = queryset.filter(model_line_id=model_line_id)

        if model_line_item_id :
            from pneumatic_actuators.models import PneumaticActuatorModelLineItem
            try :
                model_line_item = PneumaticActuatorModelLineItem.objects.select_related(
                    'model_line'
                ).get(id=model_line_item_id)
                if model_line_item.model_line :
                    queryset = queryset.filter(model_line_id=model_line_item.model_line.id)
            except PneumaticActuatorModelLineItem.DoesNotExist :
                pass

        return [{'id' : obj.id , 'name' : str(obj) , 'code' : obj.encoding} for obj in queryset]

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
        return f"{self.exd_option.name} (Стандарт)" if self.is_default else f"{self.exd_option.name} (Опция)"

    @classmethod
    def get_for_select(cls , model_line_id: Optional[int] = None ,
                       model_line_item_id: Optional[int] = None ,
                       active_only: bool = True) -> List[Dict] :
        """Получить опции взрывозащиты"""
        queryset = cls.objects.all()

        if active_only :
            queryset = queryset.filter(is_active=True)

        if model_line_id :
            queryset = queryset.filter(model_line_id=model_line_id)

        if model_line_item_id :
            from pneumatic_actuators.models import PneumaticActuatorModelLineItem
            try :
                model_line_item = PneumaticActuatorModelLineItem.objects.select_related(
                    'model_line'
                ).get(id=model_line_item_id)
                if model_line_item.model_line :
                    queryset = queryset.filter(model_line_id=model_line_item.model_line.id)
            except PneumaticActuatorModelLineItem.DoesNotExist :
                pass

        return [{'id' : obj.id , 'name' : str(obj) , 'code' : obj.encoding} for obj in queryset]

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
        # ИСПРАВЛЕНО: используем is_default вместо default_option
        return f"{self.body_coating_option.name} (Стандарт)" if self.is_default else f"{self.body_coating_option.name} (Опция)"

    @classmethod
    def get_for_select(cls , model_line_id: Optional[int] = None ,
                       model_line_item_id: Optional[int] = None ,
                       active_only: bool = True) -> List[Dict] :
        """Получить опции покрытия корпуса"""
        queryset = cls.objects.all()

        if active_only :
            queryset = queryset.filter(is_active=True)

        if model_line_id :
            queryset = queryset.filter(model_line_id=model_line_id)

        if model_line_item_id :
            from pneumatic_actuators.models import PneumaticActuatorModelLineItem
            try :
                model_line_item = PneumaticActuatorModelLineItem.objects.select_related(
                    'model_line'
                ).get(id=model_line_item_id)
                if model_line_item.model_line :
                    queryset = queryset.filter(model_line_id=model_line_item.model_line.id)
            except PneumaticActuatorModelLineItem.DoesNotExist :
                pass

        return [{'id' : obj.id , 'name' : str(obj) , 'code' : obj.encoding} for obj in queryset]

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

    @classmethod
    def get_for_select(cls , model_line_id=None , model_line_item_id=None ,
                       model_line_item_ids=None , active_only=True) :
        """
        Получить опции положения безопасности

        Args:
            model_line_id: ID серии моделей
            model_line_item_id: ID конкретной модели
            model_line_item_ids: список ID моделей
            active_only: только активные
        """
        from pneumatic_actuators.models import PneumaticActuatorModelLineItem

        # Приоритет: model_line_item_id > model_line_item_ids > model_line_id

        if model_line_item_id :
            queryset = cls.objects.filter(model_line_item_id=model_line_item_id)

        elif model_line_item_ids :
            queryset = cls.objects.filter(model_line_item_id__in=model_line_item_ids)

        elif model_line_id :
            model_line_item_ids = PneumaticActuatorModelLineItem.objects.filter(
                model_line_id=model_line_id
            ).values_list('id' , flat=True)
            queryset = cls.objects.filter(model_line_item_id__in=model_line_item_ids)

        else :
            from params.models import SafetyPositionOption
            queryset = SafetyPositionOption.objects.all()

            if active_only :
                queryset = queryset.filter(is_active=True)

            return [{'id' : obj.id , 'name' : obj.name , 'code' : obj.code} for obj in queryset]

        if active_only :
            queryset = queryset.filter(is_active=True)

        return [{'id' : obj.id , 'name' : str(obj) , 'code' : obj.encoding} for obj in queryset]

    @classmethod
    def get_for_model_line(cls , model_line_id: int , active_only: bool = True) -> List[Dict] :
        """Получить опции для всех моделей в серии"""
        from pneumatic_actuators.models import PneumaticActuatorModelLineItem

        model_line_item_ids = PneumaticActuatorModelLineItem.objects.filter(
            model_line_id=model_line_id
        ).values_list('id' , flat=True)

        queryset = cls.objects.filter(model_line_item_id__in=model_line_item_ids)
        if active_only :
            queryset = queryset.filter(is_active=True)
        return [{'id' : obj.id , 'name' : str(obj) , 'code' : obj.encoding} for obj in queryset]

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

    def __str__(self) :
        return f"{self.springs_qty.name}"
    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        return 'model_line_item'

