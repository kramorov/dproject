# pneumatic_fittings/catalog/views_filters.py
"""
GET /api/pneumatic-fittings/filters/ — filter options for FilterSidebar.
"""
from rest_framework.permissions import AllowAny
from core.views import BaseFilterOptionsView
from pneumatic_fittings.catalog.config import PNEUMATIC_FITTINGS_CONFIG


class PneumaticFittingsFilterOptionsView(BaseFilterOptionsView):
    permission_classes = [AllowAny]
    catalog_config = PNEUMATIC_FITTINGS_CONFIG
