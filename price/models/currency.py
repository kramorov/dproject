# price/models/currency.py

from django.db import models
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from typing import List, Optional, Tuple, Any, Dict, Union
from decimal import Decimal
from django.core.exceptions import ValidationError
import re
from tabulate import tabulate

import logging
from django.utils.html import format_html

from core.models import StructuredDataMixin
from electric_actuators.models import ElectricActuatorModelLineItem, CableGlandHolesSet, ElectricSafetyPositionOption
from params.models import MountingPlateTypes, StemShapes, StemSize

logger = logging.getLogger(__name__)


class Currency(StructuredDataMixin, models.Model):
    name = models.CharField(max_length=50 ,
                            verbose_name=_("Название") ,
                            help_text=_('Название валюты'))
    code = models.CharField(
        _("Код"),
        max_length=3,  # ISO 4217 — 3 символа
        unique=True,
        help_text=_("ISO 4217 код валюты (RUB, USD, EUR)")
    )
    symbol = models.CharField(
        _('символ'),
        max_length=10,
        blank=True,
        help_text=_('₽, $, €, ¥ и т.д.')
    )
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание валюты'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Тип валюты')
        verbose_name_plural = _('Типы валюты')

    def __str__(self):
        return f"{self.name}"

class PriceVariety(StructuredDataMixin, models.Model):
    name = models.CharField(max_length=50 ,
                            verbose_name=_("Название") ,
                            help_text=_('Название вида цен'))
    code = models.CharField(max_length=20 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код вида цен"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание вида цен'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Вид цены')
        verbose_name_plural = _('Виды цен')

    def __str__(self):
        return f"{self.name}"

class PriceHistory(StructuredDataMixin, models.Model):
    name = models.CharField(max_length=100 ,
                            verbose_name=_("Название товара") ,
                            help_text=_('Название текст'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код товара (необязательно"))
    price_variety = models.ForeignKey(
        PriceVariety,
        verbose_name=_("Тип цены"),
        on_delete=models.PROTECT
    )
    price = models.DecimalField(
        _('Цена'),
        max_digits=12,
        decimal_places=2
    )
    currency = models.ForeignKey(
        Currency,
        verbose_name=_("Валюта"),
        on_delete=models.PROTECT
    )

    description = models.TextField(blank=True ,null=True,
                                   verbose_name=_("Комментарий") ,
                                   help_text=_('Комментарий к цене'))
    price_date = models.DateField(blank=True ,null=True,
                                   verbose_name=_("Дата цены") ,
                                   help_text=_('Дата, на которую зафиксирована цена'))

    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Цены')
        verbose_name_plural = _('Известные цены')

    def __str__(self):
        return f"{self.name} - {self.currency.symbol if self.currency else ''}{self.price}"