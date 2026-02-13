# price/models/currency.py
from django.utils.timezone import now  # <-- ДОБАВИТЬ ИМПОРТ
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

    def get_converted_prices(self):
        """
        Возвращает словарь с конвертированными ценами
        """
        from django.utils.timezone import now
        from price.models import ExchangeRate

        source_currency = self.currency.code if self.currency else 'RUB'
        price_date = self.price_date or now().date()
        today = now().date()

        # Получаем курсы на дату цены и на сегодня
        rates_price_date = {}
        rates_today = {}

        for code in ['USD', 'EUR', 'CNY']:
            rate_price = ExchangeRate.get_or_fetch_rate(code, price_date)
            rate_today = ExchangeRate.get_or_fetch_rate(code, today)

            if rate_price:
                rates_price_date[code] = float(rate_price.rate_per_one)
            if rate_today:
                rates_today[code] = float(rate_today.rate_per_one)

        rates_price_date['RUB'] = 1.0
        rates_today['RUB'] = 1.0

        # Определяем базовую цену и валюту для расчетов
        if source_currency == 'RUB':
            # Если цена в рублях - конвертируем в USD на дату цены
            usd_rate_price = rates_price_date.get('USD', 0)
            if usd_rate_price and usd_rate_price > 0:
                base_price = float(self.price) / usd_rate_price  # RUB → USD
                base_currency = 'USD'
                base_date = price_date
            else:
                # Если нет курса USD, оставляем RUB как базу
                base_price = float(self.price)
                base_currency = 'RUB'
                base_date = price_date
        else:
            # Если цена в твердой валюте - она и есть базовая
            base_price = float(self.price)
            base_currency = source_currency
            base_date = price_date

        # Формируем результат
        result = {
            'original': {
                'price': float(self.price),
                'currency': source_currency,
                'date': price_date.strftime('%d.%m.%Y'),
                'description': self.description,
            },
            'base': {
                'price': round(base_price, 2),
                'currency': base_currency,
                'date': base_date.strftime('%d.%m.%Y'),
            },
            'converted': [],
            'rates_on_date': rates_price_date,
            'rates_today': rates_today,
        }

        all_currencies = ['RUB', 'USD', 'EUR', 'CNY']

        for currency in all_currencies:
            rate_price_date = rates_price_date.get(currency, 0)
            rate_today = rates_today.get(currency, 0)

            item = {
                'currency': currency,
                'rate_price_date': round(rate_price_date, 4) if rate_price_date else None,
                'rate_today': round(rate_today, 4) if rate_today else None,
                'is_original': currency == source_currency,
            }

            # ЦЕНА НА ДАТУ ЗАПИСИ
            if currency == source_currency:
                # Исходная валюта
                item['price_on_date'] = round(float(self.price), 2)
            else:
                # Пересчет от базовой цены (USD или исходной твердой валюты)
                if base_currency == 'RUB':
                    # База в RUB - конвертируем в другие валюты
                    if rate_price_date and rate_price_date > 0:
                        converted = base_price / rate_price_date
                        item['price_on_date'] = round(converted, 2)
                    else:
                        item['price_on_date'] = None
                else:
                    # База в твердой валюте (USD/EUR)
                    if currency == 'RUB':
                        # В RUB: base_price * курс базовой валюты
                        base_rate = rates_price_date.get(base_currency, 0)
                        if base_rate and base_rate > 0:
                            converted = base_price * base_rate
                            item['price_on_date'] = round(converted, 2)
                        else:
                            item['price_on_date'] = None
                    else:
                        # В другую твердую валюту: кросс-курс через RUB
                        base_rate = rates_price_date.get(base_currency, 0)
                        target_rate = rates_price_date.get(currency, 0)
                        if base_rate and base_rate > 0 and target_rate and target_rate > 0:
                            # Сначала в RUB, потом в целевую валюту
                            price_in_rub = base_price * base_rate
                            converted = price_in_rub / target_rate
                            item['price_on_date'] = round(converted, 2)
                        else:
                            item['price_on_date'] = None

            # ЦЕНА НА СЕГОДНЯ (всегда от базовой цены USD)
            if currency == base_currency:
                # Базовая валюта не меняется
                item['price_today'] = round(base_price, 2)
            elif currency == 'RUB':
                # RUB = базовая цена * курс базовой валюты сегодня
                base_rate_today = rates_today.get(base_currency, 0)
                if base_rate_today and base_rate_today > 0:
                    item['price_today'] = round(base_price * base_rate_today, 2)
                else:
                    item['price_today'] = None
            else:
                # Другие валюты: кросс-курс от базовой через RUB
                base_rate_today = rates_today.get(base_currency, 0)
                target_rate_today = rates_today.get(currency, 0)
                if base_rate_today and base_rate_today > 0 and target_rate_today and target_rate_today > 0:
                    # Сначала в RUB, потом в целевую валюту
                    price_in_rub = base_price * base_rate_today
                    converted = price_in_rub / target_rate_today
                    item['price_today'] = round(converted, 2)
                else:
                    item['price_today'] = None

            result['converted'].append(item)

        # Сортируем: RUB, USD, EUR, CNY
        currency_order = {'RUB': 1, 'USD': 2, 'EUR': 3, 'CNY': 4}
        result['converted'].sort(key=lambda x: currency_order.get(x['currency'], 99))

        return result
    def save(self, *args, **kwargs):
        """
        Переопределяем save для автоматической простановки даты
        """
        from django.utils.timezone import now

        # Если дата цены не указана - ставим текущую
        if not self.price_date:
            self.price_date = now().date()

        super().save(*args, **kwargs)

    actions = ['copy_price']

    def create_copy(self, new_date=None):
        """
        Создает копию текущей цены
        Возвращает новый объект PriceHistory
        """
        copy = PriceHistory(
            name=f"{self.name} (Копия)",
            code=self.code,
            price_variety=self.price_variety,
            price=self.price,
            currency=self.currency,
            description=self.description,
            sorting_order=self.sorting_order,
            is_active=self.is_active,
        )

        # Если указана новая дата - используем её, иначе сработает save()
        if new_date:
            copy.price_date = new_date

        copy.save()
        return copy