# cable_glands/models/cg_dicts.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union

class CableGlandItemType(models.Model):
    text_description = models.CharField(max_length=200)
    name = models.CharField(max_length=255,
                            verbose_name=_("Название"),
                            help_text=_('Название типа КВ'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа КВ"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа КВ'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    class Meta:
        verbose_name = _("Тип кабельного ввода")
        verbose_name_plural = _("Типы кабельных вводов")
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class CableGlandBodyMaterial( models.Model):
    text_description = models.CharField(max_length=200)
    name = models.CharField(max_length=50,
                            verbose_name=_("Название"),
                            help_text=_('Название материала корпуса КВ'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код материала корпуса КВ"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание материала корпуса КВ'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    class Meta:
        verbose_name = _("Тип материала корпуса кабельного ввода")
        verbose_name_plural = _("Типы материала корпуса кабельных вводов")
        ordering = ['sorting_order']

    def __str__(self):
        return self.name