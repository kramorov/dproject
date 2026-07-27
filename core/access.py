"""
core/access.py — Centralized catalog access control.

Single entry point for all catalog API endpoints. Controls:
  1. HTTP-level access (permission_classes)
  2. Data-level visibility (brand/series filtering)

Usage in catalog views:
    from core.access import catalog_permission_classes, apply_catalog_visibility

    class MyCatalogView(APIView):
        permission_classes = catalog_permission_classes()

        def get(self, request):
            qs = config.get_scoped_queryset()
            qs = apply_catalog_visibility(request, qs)
            ...

Design (access.md §1):
  - API-keys    → X-Api-Key header → AccessPermission → request.customer
  - Login/pass  → Django session    → SectionAccessPermission → request.user profile
  - Anonymous   → no restrictions (for now)

Future (access.md §7):
  - request.customer.visible_brands    → filter(model_line__brand_id__in=[...])
  - request.customer.visible_sections  → check section access
  - CustomerApiKey.brand_filters       → further narrowing
  - CustomerAppAccess                  → org-level ceiling
"""

from rest_framework.permissions import AllowAny


def catalog_permission_classes():
    """
    Permission classes for catalog API endpoints.

    Currently: AllowAny — all catalog data is public.
    Future:    Add AccessPermission for API-key auth + optional SectionAccessPermission.
    """
    return [AllowAny]


def apply_catalog_visibility(request, queryset):
    """
    Restrict queryset to equipment visible to the current requester.

    Args:
        request:    DRF Request object
        queryset:   Django QuerySet (pre-scoped, pre-select_related)

    Returns:
        Filtered QuerySet (currently unchanged — stub).

    Future implementation:
        customer = getattr(request, 'customer', None)
        if customer is None:
            return queryset  # anonymous: full catalog

        # Brand filtering from organization settings
        visible_brands = customer.visible_brands.all()
        if visible_brands.exists():
            queryset = queryset.filter(model_line__brand__in=visible_brands)

        # API-key brand_filters (further narrowing)
        api_key = getattr(request, 'api_key', None)
        if api_key and api_key.brand_filters:
            app_code = _resolve_app_code(queryset.model)
            brand_ids = api_key.brand_filters.get(app_code)
            if brand_ids and brand_ids != 'all':
                queryset = queryset.filter(model_line__brand_id__in=brand_ids)

        return queryset
    """
    return queryset
