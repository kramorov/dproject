# cable_glands/catalog/views_filters.py
"""
GET /api/cable-glands/filters/ — опции фильтров для FilterSidebar.
"""
from rest_framework.permissions import AllowAny
from core.views import BaseFilterOptionsView
from cable_glands.catalog.config import CABLE_GLAND_CONFIG


class CableGlandFilterOptionsView(BaseFilterOptionsView):
    permission_classes = [AllowAny]
    catalog_config = CABLE_GLAND_CONFIG
