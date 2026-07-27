# pneumatic_fittings/catalog/views_engineer_filters.py
"""
GET /api/pneumatic-fittings/engineer/filters/ — filter options for EngineerSelection.
"""
from core.access import catalog_permission_classes
from core.views import BaseFilterOptionsView
from pneumatic_fittings.catalog.config import PNEUMATIC_FITTINGS_CONFIG


class PneumaticFittingsEngineerFilterOptionsView(BaseFilterOptionsView):
    permission_classes = catalog_permission_classes()
    
    catalog_config = PNEUMATIC_FITTINGS_CONFIG
    default_scope = 'engineer'
