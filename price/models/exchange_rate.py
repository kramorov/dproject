# price/models/exchange_rate.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
import requests
import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import Dict, Optional
import logging

from core.models import StructuredDataMixin

logger = logging.getLogger(__name__)


class ExchangeRate(StructuredDataMixin, models.Model):
    """
    Курсы валют к RUB на дату
    """
    CURRENCY_CHOICES = [
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('CNY', 'CNY'),  # YAN = CNY
    ]

    currency = models.CharField(
        _('валюта'),
        max_length=3,
        choices=CURRENCY_CHOICES,
        db_index=True
    )
    date = models.DateField(
        _('дата курса'),
        db_index=True
    )
    rate = models.DecimalField(
        _('курс'),
        max_digits=12,
        decimal_places=4,
        help_text=_('Сколько RUB за 1 единицу валюты')
    )
    nominal = models.PositiveIntegerField(
        _('номинал'),
        default=1,
        help_text=_('Количество единиц валюты (обычно 1 или 100)')
    )
    created_at = models.DateTimeField(
        _('дата создания'),
        auto_now_add=True,
        null=True  # временно, если уже есть данные
    )
    updated_at = models.DateTimeField(
        _('дата обновления'),
        auto_now=True,
        null=True  # временно, если уже есть данные
    )
    class Meta:
        verbose_name = _('Курс валюты')
        verbose_name_plural = _('Курсы валют')
        ordering = ['-date', 'currency']
        unique_together = ['currency', 'date']  # Одна запись на валюту/дату

    def __str__(self):
        return f"{self.currency} → RUB: {self.rate} на {self.date}"

    @property
    def rate_per_one(self) -> Decimal:
        """Курс за 1 единицу валюты"""
        return self.rate / self.nominal


