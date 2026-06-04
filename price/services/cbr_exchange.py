# price/services/cbr_exchange.py
from django.core.exceptions import ValidationError
from decimal import Decimal
import requests
import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import Dict, Optional
from django.utils.timezone import timedelta

from price.models.exchange_rate import ExchangeRate

import logging

from core.models import StructuredDataMixin

logger = logging.getLogger(__name__)

class CBRExchangeService:
    """Сервис для получения курсов валют от ЦБ РФ"""

    CBR_URL = "http://www.cbr.ru/scripts/XML_daily.asp"
    CURRENCY_MAP = {
        'USD': 'R01235',
        'EUR': 'R01239',
        'CNY': 'R01375',
    }

    @classmethod
    def fetch_and_save_rates(cls, target_date: Optional[date] = None) -> Dict[str, Decimal]:
        """Получить курсы от ЦБ и сохранить в БД."""
        if target_date is None:
            target_date = date.today()

        # Проверяем — есть ли уже курсы на эту дату в БД
        existing = ExchangeRate.objects.filter(date=target_date).count()
        if existing >= len(cls.CURRENCY_MAP):
            logger.info(
                "Курсы на %s уже есть в БД (%d записей), не запрашиваем ЦБ",
                target_date.strftime('%d.%m.%y'), existing
            )
            return dict(ExchangeRate.objects.filter(date=target_date).values_list('currency', 'rate_per_one'))

        url = cls.CBR_URL
        params = {'date_req': target_date.strftime('%d/%m/%Y')}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.encoding = 'windows-1251'
            response.raise_for_status()

            root = ET.fromstring(response.text)
            rates = {}

            for currency_code, cbr_id in cls.CURRENCY_MAP.items():
                valute = root.find(f"./Valute[@ID='{cbr_id}']")
                if valute is not None:
                    nominal = int(valute.find('Nominal').text)
                    rate = Decimal(valute.find('Value').text.replace(',', '.'))

                    ExchangeRate.objects.update_or_create(
                        currency=currency_code,
                        date=target_date,
                        defaults={
                            'rate': rate,
                            'nominal': nominal,
                        }
                    )
                    rates[currency_code] = rate / nominal

            logger.info("Курсы на %s сохранены: %s", target_date, rates)
            return rates

        except requests.RequestException as e:
            logger.error("Ошибка получения данных от ЦБ: %s", e)
            raise
        except ET.ParseError as e:
            logger.error("Ошибка парсинга XML: %s", e)
            raise
        except Exception as e:
            logger.error("Неожиданная ошибка: %s", e)
            raise

    @classmethod
    def get_rate_for_date(cls, currency: str, target_date: date) -> Optional[Decimal]:
        """Получить курс на конкретную дату (с кешированием в БД)."""
        try:
            rate = ExchangeRate.objects.get(currency=currency, date=target_date)
            return rate.rate_per_one
        except ExchangeRate.DoesNotExist:
            try:
                rates = cls.fetch_and_save_rates(target_date)
                return rates.get(currency)
            except Exception:
                return None

    @classmethod
    def update_rates_for_period(cls, start_date: date, end_date: date):
        """Обновить курсы за период (для бэкфиллинга)."""
        current = start_date
        while current <= end_date:
            try:
                cls.fetch_and_save_rates(current)
            except Exception as e:
                logger.warning("Не удалось загрузить курс на %s: %s", current, e)
            current += timedelta(days=1)
