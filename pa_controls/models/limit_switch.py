# pa_controls/models/limit_switch.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from typing import List, Optional, Tuple, Any, Dict, Union

import logging

from core.models import StructuredDataMixin
from electric_actuators.models import CableGlandHolesSet
from materials.models import MaterialGeneral, MaterialSpecified
# from pa_controls.models import PaControlMountingStandard
from producers.models import Brands, Producer

logger = logging.getLogger(__name__)

from params.models import IpOption, ExdOption


# ============================================================
# БЛОК КОНЦЕВЫХ ВЫКЛЮЧАТЕЛЕЙ (Limit Switch Box)
# ============================================================

class LimitSwitchSensorVariety(models.Model):
    """Тип сенсора концевого выключателя (механический, индуктивный, магнитный, пневматический)"""
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название типа сенсора БКВ")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа сенсора БКВ"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа сенсораа БКВ'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = _("Тип сенсора БКВ")
        verbose_name_plural = _("Типы сенсоров БКВ")

    def __str__(self):
        return self.name

    @classmethod
    def get_choices(cls):
        """
        Возвращает список кортежей для использования в выпадающем списке
        Returns: [(id, name), ...] или [(0, "— Выберите —"), (id, name), ...]
        """
        choices = cls.objects.filter(is_active=True).order_by('sorting_order', 'name')
        return [(item.id, item.name) for item in choices]

    @classmethod
    def get_select_choices(cls, include_empty=True):
        """
        Возвращает список кортежей с пустым значением для selectbox
        Args:
            include_empty: добавить ли пустой вариант "-- Выберите --"
        Returns: [(0, "— Выберите —"), (id, name), ...] или [(id, name), ...]
        """
        choices = cls.get_choices()

        if include_empty:
            return [(0, "— Выберите —")] + choices

        return choices

    @classmethod
    def get_choice_by_id(cls, choice_id):
        """ Получить название по ID """
        if not choice_id:
            return None

        try:
            item = cls.objects.get(id=choice_id, is_active=True)
            return item.name
        except cls.DoesNotExist:
            return None


class LimitSwitchOutput(models.Model):
    """Тип выходного сигнала БКВ """
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название типа выходного сигнала БКВ")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа выходного сигнала БКВ"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа выходного сигнала БКВ'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    contact_form = models.CharField(
        max_length=10, null=True, blank=True,
        choices=[
            ('SPST', 'SPST'), ('SPDT', 'SPDT'),
            ('DPST', 'DPST'), ('DPDT', 'DPDT'),
        ],
        verbose_name=_("Форма контактов")
    )

    wire_count = models.PositiveSmallIntegerField(default=2, verbose_name=_("Количество проводов"))

    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Параметры"),
        help_text=_("signal_type, resistance, range и т.д.")
    )

    class Meta:
        verbose_name = _("Тип выхода БКВ")
        verbose_name_plural = _("Типы выходов БКВ")
        ordering = ['sorting_order', 'name']

    def __str__(self):
        if self.contact_form:
            return f"{self.name} ({self.contact_form}, {self.wire_count}пр)"
        return self.name or self.code

    @classmethod
    def get_choices(cls):
        """Возвращает список кортежей для выпадающего списка"""
        choices = cls.objects.filter(is_active=True).order_by('sorting_order', 'name')
        return [(item.id, str(item)) for item in choices]

    @classmethod
    def get_select_choices(cls, include_empty=True, empty_label="— Выберите —"):
        """Возвращает список с пустым значением для selectbox"""
        choices = cls.get_choices()

        if include_empty:
            return [(0, empty_label)] + choices

        return choices

    @classmethod
    def get_choice_by_id(cls, choice_id):
        """Получить название по ID"""
        try:
            item = cls.objects.get(id=choice_id, is_active=True)
            return str(item)
        except cls.DoesNotExist:
            return None


class LimitSwitchModelLine(StructuredDataMixin, models.Model):
    """
    Серия БКВ
    """

    name = models.CharField(max_length=200,
                            verbose_name=_("Название"),
                            help_text=_('Текстовое название серии БКВ'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код клапана"))

    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание серии БКВ'))
    name_template = models.TextField(blank=True, null=True,
                                     verbose_name=_("Шаблон названия"),
                                     help_text=_('Шаблон для текстового названия БКВ'))
    description_template = models.TextField(blank=True, null=True,
                                            verbose_name=_("Шаблон описания"),
                                            help_text=_('Шаблон для описания БКВ'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    producer = models.ForeignKey(Producer, related_name='limit_switch_model_line_producer', blank=True,
                                 null=True,
                                 on_delete=models.SET_NULL,
                                 help_text=_('Производитель БКВ'),
                                 verbose_name=_("Производитель"))
    brand = models.ForeignKey(Brands, related_name='limit_switch_model_line_brand', blank=True, null=True,
                              on_delete=models.SET_NULL,
                              help_text=_('Бренд БКВ'),
                              verbose_name=_("Бренд"))
    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Параметры"),
        help_text=_("signal_type, resistance, range и т.д.")
    )

    class Meta:
        ordering = ['sorting_order', 'code']
        verbose_name = _('Серия БКВ')
        verbose_name_plural = _('Серии БКВ')

    def __str__(self):
        return self.name


class LimitSwitchBox(StructuredDataMixin, models.Model):
    """Модель блока концевых выключателей (каталог)
    points: int,
        1 точка - один датчик (обычно только на закрыто)
        2 точки - два датчика (на открыто и на закрыто) - самый распространенный вариант
        3 точки - три датчика (открыто, закрыто, промежуточное положение)
        4 точки - четыре датчика (два промежуточных положения + концевые)
    """
    name = models.TextField(
        verbose_name=_("Название"),
        help_text=_('Текстовое название БКВ'))
    code = models.CharField(max_length=150, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код БКВ"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание БКВ'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    model_line = models.ForeignKey(LimitSwitchModelLine, related_name='limit_switch_box_model_line', blank=True,
                                   null=True,
                                   on_delete=models.SET_NULL,
                                   help_text=_('Серия БКВ'),
                                   verbose_name=_("Серия"))

    # Характеристики
    sensor_variety = models.ForeignKey(
        LimitSwitchSensorVariety, on_delete=models.SET_NULL, null=True,
        help_text=_('Тип сенсора'),
        verbose_name=_("Тип сенсора")
    )
    output_type = models.ForeignKey(
        LimitSwitchOutput, on_delete=models.SET_NULL, null=True,
        related_name='limit_switch_box_sensor_variety',
        help_text=_('Тип выходного сигнала'),
        verbose_name=_("Выходной сигнал")
    )
    points = models.IntegerField(default=2,
                                 verbose_name=_("Количество датчиков"),
                                 help_text=_("Количество точек переключения (датчиков)")
                                 )
    ip = models.ForeignKey(IpOption, on_delete=models.SET_NULL, null=True,
                           related_name='limit_switch_box_ip',
                           help_text=_('Степень защиты IP'),
                           verbose_name=_("IP")
                           )
    exd = models.ForeignKey(ExdOption, on_delete=models.SET_NULL, null=True,
                            related_name='limit_switch_box_exd',
                            help_text=_('Степень Exd'),
                            verbose_name=_("Exd")
                            )
    work_temp_min = models.IntegerField(
        null=True, blank=True, default=-40,
        help_text=_('Минимальная рабочая температура, °С'),
        verbose_name=_('Т раб.мин, °С')
    )
    work_temp_max = models.IntegerField(
        null=True, blank=True, default=120,
        help_text=_('Максимальная рабочая температура, °С'),
        verbose_name=_('Т раб.макс, °С'))

    # Материалы
    body_material = models.ForeignKey(MaterialGeneral, related_name='limit_switch_box_body_material',
                                      blank=True,
                                      null=True,
                                      on_delete=models.SET_NULL,
                                      help_text=_('Корпус'),
                                      verbose_name=_('Тип материала корпуса'))
    body_material_specified = models.ForeignKey(MaterialSpecified,
                                                related_name='limit_switch_box_body_material_specified',
                                                blank=True, null=True,
                                                on_delete=models.SET_NULL,
                                                help_text=_('Материал корпуса арматуры'),
                                                verbose_name=_('Материал корпуса'))
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True,
                                 null=True, help_text=_('Вес'),
                                 verbose_name=_("Вес, кг"))
    cable_glands_holes = \
        models.ManyToManyField(CableGlandHolesSet,  blank=True,
                               related_name='limit_switch_box_cable_glands_holes',
                                verbose_name=_("Отверстия КВ"),
                               help_text=_('Отверстия под кабельные вводы'))
    # Дополнительные характеристики
    is_pneumatic = models.BooleanField(default=False, verbose_name=_("Пневматический"))
    has_namur_interface = models.BooleanField(default=False, verbose_name=_("NAMUR интерфейс"))
    has_visual_indicator = models.BooleanField(default=False, verbose_name=_("Визуальный индикатор"))

    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Параметры"),
        help_text=_("signal_type, resistance, range и т.д.")
    )
    # Присоединительные размеры (Many-to-Many с монтажными стандартами)
    mounting_standards = models.ManyToManyField(
        'pa_controls.PaControlMountingStandard',
        blank=True,
        related_name='limit_switch_box_mounting',
        verbose_name=_("Стандарты присоединения"),
        help_text=_("Стандарты присоединения NAMUR, с которыми совместим БКВ")
    )

    class Meta:
        verbose_name = _("Блок концевых выключателей")
        verbose_name_plural = _("Блоки концевых выключателей")
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.name}"
