# cable_glands/models/cg_model_line.py

from django.db import models
from django.utils.translation import gettext_lazy as _
# from typing import List, Optional, Tuple, Any, Dict, Union

from core.models import StructuredDataMixin
from producers.models import Brands

from params.models import IpOption, ExdOption


class CableGlandModelLine(StructuredDataMixin, models.Model):
    """
    Description - Описание Кабельные вводы для всех типов гибкого кабеля круглого сечения, осна-
                    щенные фитингом с трубной резьбой
    """
    name = models.CharField(max_length=200,
                            verbose_name=_("Название"),
                            help_text=_('Название серии кабельных вводов'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код серии кабельных вводов"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание модели корпуса КВ'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))


    brand = models.ForeignKey(Brands, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_("Бренд"),
                              related_name='cable_gland_brand', help_text=_('Бренд (производитель) кабельных вводов'))
    cable_gland_type = models.ForeignKey(
        'CableGlandItemType',
        blank=True, null=True, on_delete=models.SET_NULL,
        verbose_name=_("Тип"),
        related_name='cable_gland_type', help_text=_('Тип КВ'))
    ip = models.ManyToManyField(IpOption, blank=True, default=1, related_name='cable_gland_model_line_ip',
                                verbose_name=_("IP"),
                                help_text=_('Степень защиты IP (можно выбрать несколько)'))
    exd = models.ManyToManyField(ExdOption, blank=True, default=1, verbose_name=_("Взрывозащита"),
                                 related_name='cable_gland_model_line_exd', help_text=_('Тип взрывозащиты'))
    for_armored_cable = models.BooleanField(blank=True, null=True, verbose_name=_("Бронированный кабель"),
                                            help_text=_('Для бронированного кабеля'))
    for_metal_sleeve_cable = models.BooleanField(blank=True, null=True, verbose_name=_("Металлорукав"),
                                                 help_text=_('Для кабеля в металлорукаве'))
    for_pipelines_cable = models.BooleanField(blank=True, null=True, verbose_name=_("Трубопровод"),
                                              help_text=_('Для кабеля в трубопроводе'))
    thread_external = models.BooleanField(blank=True, null=True, verbose_name=_("Наружная резьба"),
                                          help_text=_('Наружная резьба для внешнего присоединения'))
    thread_internal = models.BooleanField(blank=True, null=True, verbose_name=_("Внутренняя резьба"),
                                          help_text=_('Внутренняя резьба для внешнего присоединения'))
    temp_min = models.SmallIntegerField(blank=True, null=True, verbose_name=_("Темп.мин"),
                                        help_text=_('Минимальная температура окружающей среды'))
    temp_max = models.SmallIntegerField(blank=True, null=True, verbose_name=_("Темп.макс"),
                                        help_text=_('Максимальная температура окружающей среды'))
    gost = models.CharField(max_length=1000, blank=True, null=True, verbose_name=_("ГОСТ"),
                            help_text=_('Соответствие ГОСТ, ТУ, другим стандартам - перечень'))

    def get_full_description(self):
        result_table = []
        # result_table.extend([
        #     {'param_name': 'description',
        #      'param_text': 'Описание', 'param_value': '' + self.description + ' Производитель:' + self.brand.name},
        #     {'param_name': 'ip',
        #      'param_text': 'Исполнение IP', 'param_value': \
        #          ' / '.join([ip.code for ip in sorted(self.ip.all(), key=lambda ip: ip.code)])},
        #     {'param_name': 'exd',
        #      'param_text': 'Взрывозащита', 'param_value': ' / '.join(
        #         [exd.description for exd in sorted(self.exd.all(), key=lambda exd: exd.description)])},
        #     {'param_name': 'gost',
        #      'param_text': 'Соответствие ГОСТ, ТУ, другим стандартам', 'param_value': self.gost},
        # ])
        return result_table

    class Meta:
        verbose_name = _("Серия кабельных вводов")
        verbose_name_plural = _("Серии кабельных вводов")
        ordering = ['sorting_order']

    def __str__(self):
        return self.code
