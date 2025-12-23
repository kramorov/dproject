# cable_glands/models/cg_body.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union

from core.models import StructuredDataMixin

class CableGlandBody(StructuredDataMixin, models.Model):
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
    model_line = models.ForeignKey(
        'CableGlandModelLine',
        blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_("Серия"),
        related_name='cg_body_model_line', help_text=_('Серия модели корпуса кабельного ввода'))

    metal_sleeve = models.ManyToManyField(
        'MetalSleeve',
        blank=True,
        related_name='metal_sleeve_cg_model_body',
        verbose_name=_("Металлорукав"),
        help_text=_('Металлорукава, подходящие для этого корпуса'))

    cable_diameter_inner_min = models.DecimalField(max_digits = 5, decimal_places =1, default=0, blank=True, null=True,
                                                   verbose_name=_("Кабель мин"),
                                                        help_text='Минимальный диаметр обжимаемого кабеля')
    cable_diameter_inner_max = models.DecimalField(max_digits = 5, decimal_places =1, default=0, blank=True, null=True,
                                                   verbose_name=_("Кабель макс"),
                                                        help_text='Максимальный диаметр обжимаемого кабеля')
    metal_sleeve_inner = models.DecimalField(max_digits = 5, decimal_places =1, default=0, blank=True, null=True,
                                             verbose_name=_("МР внутр"),
                                                           help_text='Внутренний диаметр металлорукава)')
    metal_sleeve_outer = models.DecimalField(max_digits = 5, decimal_places =1, default=0, blank=True, null=True,
                                            verbose_name=_("МР внеш"),
                                                           help_text='Внешний диаметр металлорукава')
    total_lenght = models.DecimalField(max_digits = 5, decimal_places =1, default=0, blank=True, null=True, verbose_name=_("Длина,мм"),
                                               help_text='Общая длина, мм')
    thread_lenght = models.DecimalField(max_digits = 5, decimal_places =1, default=0, blank=True, null=True, verbose_name=_("Резьба,мм"),
                                                help_text='Длина резьбы,мм')
    weight =models.DecimalField(max_digits = 5, decimal_places =3, default=0, blank=True, null=True, verbose_name=_("Вес,кг"),
                                                help_text='Вес,кг')

    class Meta:
        verbose_name = _("Корпус кабельного ввода")
        verbose_name_plural = _("Корпуса кабельных вводов")
        ordering = ['sorting_order']

    @property
    def metal_sleeve_display(self):
        """Отображает металлорукава через разделитель /"""
        metal_sleeves = self.metal_sleeve.all()
        if metal_sleeves:
            return " / ".join([str(metal_sleeve) for metal_sleeve in metal_sleeves])
        return "-"
