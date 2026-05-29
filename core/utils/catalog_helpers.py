# core/utils/catalog_helpers.py
"""
Shared utilities for catalog views — avoid code duplication across catalogs.
"""
from project_customers.utils import get_current_customer_user


def get_currency_code(request) -> str:
    """Extract currency code from customer settings, default RUB."""
    try:
        user = get_current_customer_user(request)
        if user and hasattr(user, 'customer'):
            settings = getattr(user.customer, 'settings', None)
            if settings and settings.default_currency:
                return settings.default_currency.code
    except Exception:
        pass
    return 'RUB'
