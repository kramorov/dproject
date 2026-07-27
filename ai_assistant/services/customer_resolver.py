"""Customer resolver by request source (web_form, email, api)."""
import logging
from typing import Optional

from django.core.cache import cache

logger = logging.getLogger(__name__)

ANONYMOUS_CODE = "anonymous_web"


def resolve_customer(source="web_form", email="", api_key=""):
    """Resolve ProjectCustomer by request source.

    web_form → anonymous_web (system customer)
    email    → ProjectCustomer by sender email
    api      → CustomerApiKey.lookup()

    Returns ProjectCustomer or None.
    """
    if source == "api" and api_key:
        return _resolve_by_api_key(api_key)
    if source == "email" and email:
        return _resolve_by_email(email)
    return _get_anonymous()


def _get_anonymous():
    """Return system customer 'anonymous_web' (cached by id)."""
    from project_customers.models import ProjectCustomer

    customer_id = cache.get(f"customer_{ANONYMOUS_CODE}")
    if customer_id:
        try:
            return ProjectCustomer.objects.get(id=customer_id)
        except ProjectCustomer.DoesNotExist:
            cache.delete(f"customer_{ANONYMOUS_CODE}")

    customer = ProjectCustomer.objects.filter(
        name__startswith="Неавторизованный", is_active=True
    ).first()

    if customer:
        cache.set(f"customer_{ANONYMOUS_CODE}", customer.id, timeout=3600)
        return customer

    logger.error("System customer 'anonymous_web' not found — run migration 0014")
    return None


def _resolve_by_email(email):
    """Find ProjectCustomer by email (exact match, case-insensitive)."""
    from project_customers.models import ProjectCustomer
    customer = ProjectCustomer.objects.filter(email__iexact=email, is_active=True).first()
    if customer:
        return customer
    from project_customers.models import CustomerEmail
    ce = CustomerEmail.objects.filter(
        email__iexact=email, is_active=True, customer__is_active=True,
    ).select_related("customer").first()
    return ce.customer if ce else None


def _resolve_by_api_key(raw_key):
    """Resolve via CustomerApiKey.lookup()."""
    from project_customers.models import CustomerApiKey
    key = CustomerApiKey.lookup(raw_key)
    return key.customer if key else None
