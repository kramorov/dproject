# pneumatic_fittings/catalog/views_engineer_filters.py
"""
GET /api/pneumatic-fittings/engineer/filters/ — filter options for EngineerSelection.
"""
from project_customers.permissions import SectionAccessPermission
from core.views import BaseFilterOptionsView
from pneumatic_fittings.catalog.config import PNEUMATIC_FITTINGS_CONFIG


class PneumaticFittingsEngineerFilterOptionsView(BaseFilterOptionsView):
    permission_classes = [SectionAccessPermission]
    required_section = 'configurator'
    catalog_config = PNEUMATIC_FITTINGS_CONFIG
    default_scope = 'engineer'
