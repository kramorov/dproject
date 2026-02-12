# price/admin/__init__.py
from .exchange_rate import ExchangeRateAdmin
from .currency import CurrencyAdmin, PriceVariety, PriceHistory

__all__ = ['ExchangeRateAdmin','CurrencyAdmin','PriceVariety','PriceHistory']