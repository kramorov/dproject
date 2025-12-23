# cable_glands/models/metal_sleeve.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union


class MetalSleeve( models.Model):
    name = models.CharField(max_length=200,
                            verbose_name=_("Название"),
                            help_text=_('Название металлорукава'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код металлорукава"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание металлорукава'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    class Meta:
        verbose_name = _("Тип и диаметр металлорукава")
        verbose_name_plural = _("Типы и диаметры металлорукавов")
        ordering = ['sorting_order']

    def create_copy(self , name_suffix=None , code_suffix=None) :
        """Создает копию модели со всеми связанными данными"""
        if name_suffix is None :
            name_suffix = _(" (Копия)")
        if code_suffix is None :
            code_suffix = _(" (Копия)")
        # Создаем новый объект с теми же данными
        copy = MetalSleeve(
            name=f"{self.name}{name_suffix}" if self.name else "Копия",
            code=f"{self.code}{code_suffix}" if self.code else "Копия",
            description=self.description,
            sorting_order=self.sorting_order,
            is_active=self.is_active,

        )
        copy.save()
        return copy

    def __str__(self):
        return self.name