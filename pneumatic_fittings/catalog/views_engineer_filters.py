# pneumatic_fittings/catalog/views_engineer_filters.py
"""
GET /api/pneumatic-fittings/engineer/filters/ — filter options for EngineerSelection.
"""
from rest_framework.permissions import AllowAny
from core.views import BaseFilterOptionsView
from pneumatic_fittings.catalog.config import PNEUMATIC_FITTINGS_CONFIG


class PneumaticFittingsEngineerFilterOptionsView(BaseFilterOptionsView):
    permission_classes = [AllowAny]
    catalog_config = PNEUMATIC_FITTINGS_CONFIG
    default_scope = 'engineer'
