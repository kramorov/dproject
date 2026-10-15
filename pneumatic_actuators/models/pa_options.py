# pneumatic_actuators/models/pa_options.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union

from options.models import BaseTemperatureThroughOption, BaseThroughOption, \
    BaseIpThroughOption, BasePneumaticConnectionThroughOption, BaseSafetyPositionThroughOption, \
    BaseSpringsQtyThroughOption, BaseHandWheelThroughOption, BaseM2MExdThroughOption, \
    BaseColorThroughOption
from params.models import IpOption
from materials.models import MaterialGeneral
from core.utils.localization import localized_name, pick_i18n


class PneumaticManualOverrideOption(BaseHandWheelThroughOption):
    """Опции ручного дублера для пневмоприводов (на уровне модели в серии)."""
    sync_name_i18n = False
    model_line_item = models.ForeignKey(
        'PneumaticActuatorModelLineItem',
        on_delete=models.CASCADE,
        related_name='manual_override_options',
        verbose_name=_("Модель в серии")
    )
    mo_weight = models.DecimalField(max_digits=6 , decimal_places=2 ,
                                        default=0 , blank=True , null=True ,
                                        verbose_name=_("Вес ручного дублера") ,
                                        help_text=_(
                                            'Вес ручного дублера, кг.'))
    class Meta:
        verbose_name = _("Тип установленного ручного дублера")
        verbose_name_plural = _("Типы установленного ручного дублера пневмоприводов")
        ordering = ['is_default', 'sorting_order']  # ← ИСПРАВИТЬ СОРТИРОВКУ
        unique_together = ['model_line_item', 'encoding']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        """Явно указываем имя родительского поля"""
        return 'model_line_item'

    @classmethod
    def get_for_select(cls , model_line_id: Optional[int] = None ,
                       model_line_item_id: Optional[int] = None ,
                       active_only: bool = True) -> List[Dict] :
        """Получить опции ручного дублера."""
        queryset = cls.objects.all()

        if active_only :
            queryset = queryset.filter(is_active=True)

        if model_line_item_id :
            queryset = queryset.filter(model_line_item_id=model_line_item_id)
        elif model_line_id :
            from pneumatic_actuators.models import PneumaticActuatorModelLineItem
            item_ids = PneumaticActuatorModelLineItem.objects.filter(
                model_line_id=model_line_id
            ).values_list('id', flat=True)
            queryset = queryset.filter(model_line_item_id__in=item_ids)

        return [{'id' : obj.id , 'name' : str(obj) , 'code' : obj.encoding} for obj in queryset]

    @property
    def get_display_name(self):
        return self.hand_wheel_option.name

    def __str__(self):
        return f"{self.hand_wheel_option.name} (Стандарт)" if self.is_default else f"{self.hand_wheel_option.name} (Опция)"

    def _localized_base_name(self, locale=None):
        ref = self.hand_wheel_option
        return self._strip_option_suffix(localized_name(ref, locale)) if ref else ''

class PneumaticTemperatureOption(BaseTemperatureThroughOption):
    """Температурные опции для пневмоприводов"""
    sync_name_i18n = False
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
    sync_name_i18n = False
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

    def _localized_base_name(self, locale=None):
        ref = self.ip_option
        return self._strip_option_suffix(localized_name(ref, locale)) if ref else ''

    @classmethod
    def get_model_line_for_IP(cls, ip_option_id: Optional[int] = None,
                              active_only: bool = True) -> List[Dict]:
        """
        Получить список опций IP с рангом >= заданного.
        Возвращает опции с их encoding и информацией о серии приводов.

        Args:
            ip_option_id: ID выбранной опции IP
            active_only: только активные опции

        Returns:
            List[Dict]: список опций IP, у которых rank >= rank выбранной опции
            [
                {
                    'id': int,  # ID опции (PneumaticIpOption)
                    'encoding': str,  # Кодировка из through модели
                    'is_default': bool,
                    'sorting_order': int,
                    'ip_rank': int,  # Ранг из IpOption
                    'ip_option': {
                        'id': int,
                        'name': str,
                        'code': str,
                        'ip_rank': int
                    },
                    'model_line': {
                        'id': int,
                        'name': str,
                        'code': str
                    }
                },
                ...
            ]
        """
        queryset = cls.objects.select_related('ip_option', 'model_line')

        if active_only:
            queryset = queryset.filter(is_active=True)

        if ip_option_id:
            try:
                # Получаем выбранную опцию IP и её ранг
                ip_option_needed = IpOption.objects.get(id=ip_option_id)
                needed_rank = ip_option_needed.ip_rank

                # Фильтруем опции с rank >= нужного
                queryset = queryset.filter(ip_option__ip_rank__gte=needed_rank)
            except IpOption.DoesNotExist:
                return []

        # Формируем результат
        result = []
        for obj in queryset:
            result.append({
                'id': obj.id,
                'encoding': obj.encoding,  # Из BaseThroughOptionNoDefault
                'is_default': obj.is_default if hasattr(obj, 'is_default') else False,
                'sorting_order': obj.sorting_order,
                'ip_rank': obj.ip_option.ip_rank,
                'ip_option': {
                    'id': obj.ip_option.id,
                    'name': obj.ip_option.name,
                    'code': obj.ip_option.code,
                    'ip_rank': obj.ip_option.ip_rank
                },
                'model_line': {
                    'id': obj.model_line.id,
                    'name': obj.model_line.name,
                    'code': obj.model_line.code if hasattr(obj.model_line, 'code') else ''
                }
            })

        # Сортируем по рангу (от большего к меньшему)
        result.sort(key=lambda x: x['ip_rank'], reverse=True)

        return result

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

class PneumaticExdOption(BaseM2MExdThroughOption):
    """Опции взрывозащиты для пневмоприводов.

    Одна строка = одна КОДИРОВКА (опция выбора), внутри — M2M видов взрывозащиты
    (params.ExdOption). Аналог CableGlandExdOption/PosiExdOption.
    """
    sync_name_i18n = False
    model_line = models.ForeignKey(
        'PneumaticActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='exd_options',
        verbose_name=_("Серия пневмоприводов")
    )

    class Meta:
        verbose_name = _("Опция взрывозащиты пневмопривода")
        verbose_name_plural = _("Опции взрывозащиты пневмоприводов")
        ordering = ['is_default', 'sorting_order']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        return 'model_line'

    def __str__(self):
        if self.pk is None:
            return f"{self.encoding or '—'} (удалено)"
        short = self.get_exd_short_list or '—'
        return f"{short} (Стандарт)" if self.is_default else f"{short} (Опция)"

    @classmethod
    def get_for_select(cls , model_line_id: Optional[int] = None ,
                       model_line_item_id: Optional[int] = None ,
                       active_only: bool = True) -> List[Dict] :
        """Получить опции взрывозащиты (строки с кодировкой + виды Ex в M2M)"""
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

        return [
            {
                'id' : obj.id ,
                'name' : str(obj) ,
                'code' : obj.encoding ,
                'exd_variety_ids' : list(obj.exd_options.values_list('id' , flat=True)) ,
            }
            for obj in queryset.prefetch_related('exd_options')
        ]

class PneumaticBodyDesignOption(BaseThroughOption):
    """Исполнение корпуса (материал/покрытие) для пневмоприводов"""
    sync_name_i18n = False
    model_line = models.ForeignKey(
        'PneumaticActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='body_design_options',
        verbose_name=_("Серия пневмоприводов")
    )
    body_material = models.ForeignKey(
        MaterialGeneral,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='pa_body_design_materials',
        verbose_name=_("Материал корпуса")
    )
    body_coating = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Покрытие корпуса")
    )
    body_coating_option = models.ForeignKey(
        'params.BodyCoatingOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='pa_body_design_coatings',
        verbose_name=_("Опция покрытия корпуса (справочник)")
    )

    class Meta:
        verbose_name = _("Исполнение корпуса пневмопривода")
        verbose_name_plural = _("Исполнения корпуса пневмоприводов")
        ordering = ['is_default', 'sorting_order']
        unique_together = ['model_line', 'encoding']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        return 'model_line'

    @classmethod
    def create_default_option(cls , parent_obj) :
        """Создать стандартное исполнение корпуса (покрытие по умолчанию из справочника)"""
        from django.apps import apps
        BodyCoatingOption = apps.get_model('params' , 'BodyCoatingOption')
        std_coating = None
        for code in ('STD' , 'STANDARD' , 'DEFAULT') :
            std_coating = BodyCoatingOption.objects.filter(code=code , is_active=True).first()
            if std_coating :
                break
        if not std_coating :
            std_coating = BodyCoatingOption.objects.filter(is_active=True).first()

        parent_field = cls._get_parent_field_name()
        return cls.objects.create(
            **{parent_field : parent_obj} ,
            body_material=None ,
            body_coating=(dict(std_coating.name_i18n) if std_coating and std_coating.name_i18n
                          else ({'ru': std_coating.name} if std_coating else {})) ,
            body_coating_option=std_coating ,
            encoding=std_coating.code if std_coating else '' ,
            description='Стандартное исполнение корпуса' ,
            is_default=True ,
            sorting_order=0 ,
            is_active=True
        )

    def get_display_name(self, locale=None) :
        parts = []
        if self.body_material :
            parts.append(localized_name(self.body_material, locale))
        # body_coating_option (справочник) — источник истины; legacy body_coating
        # (JSON) используем только как fallback, если FK не заполнен.
        if self.body_coating_option :
            coating = localized_name(self.body_coating_option, locale)
        elif self.body_coating :
            coating = pick_i18n(self.body_coating, locale) or ''
        else :
            coating = ''
        if coating :
            parts.append(coating)
        base = ', '.join(parts) if parts else 'Не указано'
        if self.encoding and self.encoding.strip() :
            base = f"{self.encoding} ({base})"
        return f"{base} (Стандарт)" if self.is_default else f"{base} (Опция)"

    def __str__(self):
        return self.get_display_name()

    def _localized_base_name(self, locale=None):
        # get_display_name(locale) локализует материал/покрытие через справочники,
        # но всегда добавляет RU-суффикс — снимаем его, суффикс добавит localized_name().
        return self._strip_option_suffix(self.get_display_name(locale))


class PneumaticBodyColorOption(BaseColorThroughOption):
    """Цвет корпуса для пневмоприводов (отдельная through-опция)"""
    sync_name_i18n = False
    model_line = models.ForeignKey(
        'PneumaticActuatorModelLine',
        on_delete=models.CASCADE,
        related_name='body_color_options',
        verbose_name=_("Серия пневмоприводов")
    )

    class Meta:
        verbose_name = _("Цвет корпуса пневмопривода")
        verbose_name_plural = _("Цвета корпуса пневмоприводов")
        ordering = ['is_default', 'sorting_order']
        unique_together = ['model_line', 'encoding']

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str]:
        return 'model_line'

    @classmethod
    def create_default_option(cls, parent_obj):
        """Создать стандартный цвет (по умолчанию из справочника BodyColor)."""
        from django.apps import apps
        BodyColor = apps.get_model('params', 'BodyColor')
        std_color = BodyColor.objects.filter(code='STD', is_active=True).first() or \
            BodyColor.objects.filter(is_active=True).first()
        if not std_color:
            return None
        parent_field = cls._get_parent_field_name()
        return cls.objects.create(
            **{parent_field: parent_obj},
            color_option=std_color,
            encoding='',
            description='Стандартный цвет корпуса',
            is_default=True,
            sorting_order=0,
            is_active=True
        )

    @classmethod
    def get_for_select(cls, model_line_id: Optional[int] = None,
                       model_line_item_id: Optional[int] = None,
                       active_only: bool = True) -> List[Dict]:
        """Получить опции цвета корпуса."""
        queryset = cls.objects.all()
        if active_only:
            queryset = queryset.filter(is_active=True)
        if model_line_id:
            queryset = queryset.filter(model_line_id=model_line_id)
        return [{'id': obj.id, 'name': str(obj), 'code': obj.encoding} for obj in queryset]

    def _localized_base_name(self, locale=None):
        ref = self.color_option
        return self._strip_option_suffix(localized_name(ref, locale)) if ref else ''


class PneumaticSafetyPositionOption(BaseSafetyPositionThroughOption):
    """Опции покрытия корпуса для пневмоприводов"""
    sync_name_i18n = False
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
        return f"{self.safety_position.name} (Стандарт)" if self.is_default else f"{self.safety_position.name} (Опция)"

    def _localized_base_name(self, locale=None):
        ref = self.safety_position
        return self._strip_option_suffix(localized_name(ref, locale)) if ref else ''

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
    sync_name_i18n = False
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
        return f"{self.springs_qty.name} (Стандарт)" if self.is_default else f"{self.springs_qty.name} (Опция)"

    def _localized_base_name(self, locale=None):
        ref = self.springs_qty
        return self._strip_option_suffix(localized_name(ref, locale)) if ref else ''
    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        return 'model_line_item'

