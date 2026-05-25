# price/services/currency_converter.py
"""
Конвертация цен на лету через ExchangeRate.

Используется вьюхами каталога для пересчёта цены из валюты хранения
в валюту клиента (из CustomerSettings.default_currency).
"""
from decimal import Decimal
from datetime import date

from price.models import ExchangeRate


def convert_price(price_value: Decimal, from_currency_code: str,
                  to_currency_code: str, target_date: date = None) -> Decimal:
    """
    Пересчитать цену из одной валюты в другую через RUB.

    Все курсы в ExchangeRate — к RUB. Алгоритм:
      from → RUB (делим на курс from)
      RUB → to   (умножаем на курс to)

    Если валюты совпадают или курс не найден — возвращает исходную цену.
    """
    if not price_value or from_currency_code == to_currency_code:
        return price_value or Decimal('0')

    target_date = target_date or date.today()

    # Получаем оба курса к RUB
    rate_from = _get_rate(from_currency_code, target_date)
    rate_to = _get_rate(to_currency_code, target_date)

    if not rate_from:
        return price_value

    # from → RUB
    rub = price_value * rate_from

    # RUB → to
    if rate_to:
        return (rub / rate_to).quantize(Decimal('0.01'))

    # Если to_currency — RUB, то уже в рублях
    if to_currency_code == 'RUB':
        return rub.quantize(Decimal('0.01'))

    return price_value


def _get_rate(currency_code: str, target_date: date) -> Decimal:
    """
    Получить курс валюты к RUB на дату.

    Для RUB курс = 1.
    """
    if currency_code == 'RUB':
        return Decimal('1')

    rate_obj = ExchangeRate.objects.filter(
        currency=currency_code,
        date__lte=target_date,
    ).order_by('-date').first()

    if rate_obj:
        return rate_obj.rate_per_one

    return None


def get_display_price(sku_code: str, default_currency_code: str = 'RUB') -> dict:
    """
    Получить цену для отображения в каталоге.

    Ищет актуальную цену SKU (is_current=True), конвертирует в валюту клиента.

    Возвращает:
        {'price': '1250.00', 'currency': 'RUB', 'symbol': '₽'}
        или None, если цена не найдена.
    """
    from price.models import PriceHistory, PriceVariety, Currency

    # Берём первый активный вид цены (обычно РРЦ)
    variety = PriceVariety.objects.filter(is_active=True).first()
    if not variety or not sku_code:
        return None

    price_record = PriceHistory.objects.filter(
        sku__code=sku_code,
        price_variety=variety,
        is_current=True,
        is_active=True,
    ).select_related('currency').first()

    if not price_record:
        return None

    from_currency = price_record.currency.code if price_record.currency else 'USD'

    # Конвертируем
    converted = convert_price(
        price_record.price,
        from_currency,
        default_currency_code,
    )

    # Символ валюты
    to_currency = Currency.objects.filter(code=default_currency_code).first()
    symbol = to_currency.symbol if to_currency else default_currency_code

    return {
        'price': str(converted),
        'currency': default_currency_code,
        'symbol': symbol,
    }


def get_bulk_prices(sku_codes: list, default_currency_code: str = 'RUB') -> dict:
    """
    Массовый запрос цен для списка SKU.

    Возвращает: {sku_code: {price, currency, symbol}, ...}
    """
    from price.models import PriceHistory, PriceVariety

    if not sku_codes:
        return {}

    variety = PriceVariety.objects.filter(is_active=True).first()
    if not variety:
        return {}

    records = PriceHistory.objects.filter(
        sku__code__in=sku_codes,
        price_variety=variety,
        is_current=True,
        is_active=True,
    ).select_related('currency', 'sku')

    result = {}
    for rec in records:
        from_currency = rec.currency.code if rec.currency else 'USD'
        converted = convert_price(rec.price, from_currency, default_currency_code)
        result[rec.sku.code] = {
            'price': str(converted),
            'currency': default_currency_code,
            'symbol': _get_symbol(default_currency_code),
        }
    return result


def _get_symbol(currency_code: str) -> str:
    from price.models import Currency
    c = Currency.objects.filter(code=currency_code).first()
    return c.symbol if c else currency_code
