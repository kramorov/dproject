# cable_glands/models/cg_body.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union

from core.models import StructuredDataMixin
from core.models.mixins import CopyMixin
from producers.models import Brands
from params.models import ThreadSizeThroughOption


class CableGlandBody(CopyMixin, StructuredDataMixin, models.Model):
    """Корпус кабельного ввода — геометрия под диапазон обжимаемого кабеля.

    Справочник «размерных» корпусов: диапазон обжимаемого кабеля
    (cable_diameter_inner_min/max), длина резьбы (thread_lenght), бренд
    (brand). Варианты доступных резьб задаются через-моделью
    CableGlandThreadOption (FK cable_gland_body, unique по thread_size).

    Используется «моделью в серии» (CableGlandModelLineItem.body); артикулы
    CableGland получают диаметры и варианты резьб транзитом через неё.

    CopyMixin._copy_custom_relations при копировании корпуса дублирует и его
    опции резьбы (CableGlandThreadOption).
    """
    name = models.CharField(max_length=200,
                            verbose_name=_("Название"),
                            help_text=_('Название модели корпуса кабельного ввода'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код модели корпуса кабельного ввода"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание модели корпуса КВ'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    brand = models.ForeignKey(Brands, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_("Бренд"),
                              related_name='cable_gland_brand', help_text=_('Бренд (производитель) кабельных вводов'))

    cable_diameter_inner_min = models.DecimalField(max_digits = 5, decimal_places =1, default=0, blank=True, null=True,
                                                   verbose_name=_("Кабель мин"),
                                                        help_text='Минимальный диаметр обжимаемого кабеля')
    cable_diameter_inner_max = models.DecimalField(max_digits = 5, decimal_places =1, default=0, blank=True, null=True,
                                                   verbose_name=_("Кабель макс"),
                                                        help_text='Максимальный диаметр обжимаемого кабеля')

    # total_lenght = models.DecimalField(max_digits = 5, decimal_places =1, default=0, blank=True, null=True, verbose_name=_("Длина,мм"),
    #                                            help_text='Общая длина, мм')
    thread_lenght = models.DecimalField(max_digits = 5, decimal_places =1, default=0, blank=True, null=True, verbose_name=_("Резьба,мм"),
                                                help_text='Длина резьбы,мм')


    class Meta:
        verbose_name = _("Корпус кабельного ввода")
        verbose_name_plural = _("Корпуса кабельных вводов")
        ordering = ['sorting_order']

    def __str__(self):
        return self.name

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        return 'cable_gland_body'

    def _copy_custom_relations(self, new_copy):
        """Копия корпуса дублирует и его опции резьбы (CableGlandThreadOption)."""
        from .cg_thread_option import CableGlandThreadOption
        for src in CableGlandThreadOption.objects.filter(cable_gland_body_id=self.pk):
            dst = CableGlandThreadOption()
            for field in src._meta.fields:
                if field.name in ('id', 'cable_gland_body'):
                    continue
                setattr(dst, field.name, getattr(src, field.name))
            dst.cable_gland_body = new_copy
            dst.save()



class CableGlandMetalSleeveBody(CopyMixin, StructuredDataMixin, models.Model):
    """Устройство подключения металлорукава к кабельному вводу (крепление МР).

    Определяет совместимость с металлорукавом: внутренний и внешний диаметры
    (metal_sleeve_inner / metal_sleeve_outer) и набор совместимых типов
    металлорукава (M2M MetalSleeve), плюс бренд.

    Используется «моделью в серии» (CableGlandModelLineItem.metal_sleeve_body)
    для исполнений «кабель в металлорукаве» (у серии флаг
    for_metal_sleeve_cable). Свойство metal_sleeve_display отдаёт список
    металлорукавов через разделитель.
    """
    name = models.CharField(max_length=200,
                            verbose_name=_("Название"),
                            help_text=_('Название модели устройства для подключения металлорукава'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код модели устройства для подключения металлорукава"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание модели устройства для подключения металлорукава'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    brand = models.ForeignKey(Brands, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_("Бренд"),
                              related_name='cg_metal_sleeve_body_brand',
                              help_text=_('Бренд (производитель) кабельных вводов'))

    metal_sleeve_inner = models.DecimalField(max_digits = 5, decimal_places =1, default=0, blank=True, null=True,
                                             verbose_name=_("МР внутр"),
                                                           help_text='Внутренний диаметр металлорукава)')
    metal_sleeve_outer = models.DecimalField(max_digits = 5, decimal_places =1, default=0, blank=True, null=True,
                                            verbose_name=_("МР внеш"),
                                                           help_text='Внешний диаметр металлорукава')
    metal_sleeve = models.ManyToManyField(
        'MetalSleeve',
        blank=True,
        verbose_name=_("Металлорукав"),
        help_text=_('Металлорукава, подходящие для этого корпуса'))

    class Meta:
        verbose_name = _("Устройство для подключения металлорукава")
        verbose_name_plural = _("Устройства для подключения металлорукава")
        ordering = ['sorting_order']

    def __str__(self):
        return self.name

    @property
    def metal_sleeve_display(self):
        """Отображает металлорукава через разделитель /"""
        metal_sleeves = self.metal_sleeve.all()
        if metal_sleeves:
            return " / ".join([str(metal_sleeve) for metal_sleeve in metal_sleeves])
        return "-"
