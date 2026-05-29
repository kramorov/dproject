# gearbox/catalog/views_filters.py
"""
GET /api/gearbox/filters/ — filter options for FilterSidebar.

Uses BaseFilterOptionsView with GEARBOX_CONFIG.
"""
from rest_framework.permissions import AllowAny
from core.views import BaseFilterOptionsView
from gearbox.catalog.config import GEARBOX_CONFIG


class GearboxFilterOptionsView(BaseFilterOptionsView):
    permission_classes = [AllowAny]
    catalog_config = GEARBOX_CONFIG
