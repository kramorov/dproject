"""Cached permission lookups to avoid repeated DB queries."""
from functools import lru_cache


@lru_cache(maxsize=1)
def get_anonymous_group():
    """
    Return anonymous_users SystemGroup or None.

    Cached until clear_permission_cache() is called.
    Call clear_permission_cache() after any SystemGroup save.
    """
    from project_customers.models import SystemGroup
    try:
        return SystemGroup.objects.get(code='anonymous_users')
    except SystemGroup.DoesNotExist:
        return None


def clear_permission_cache():
    """Invalidate all permission caches."""
    get_anonymous_group.cache_clear()
