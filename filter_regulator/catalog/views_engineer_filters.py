# filter_regulator/catalog/views_engineer_filters.py
"""
GET /api/filter-regulator/engineer/filters/ — filter options for EngineerSelection.

Uses BaseFilterOptionsView with FILTER_REGULATOR_CONFIG + default_scope='engineer'.
"""
from core.access import catalog_permission_classes
from core.views import BaseFilterOptionsView
from filter_regulator.catalog.config import FILTER_REGULATOR_CONFIG


class FilterRegulatorEngineerFilterOptionsView(BaseFilterOptionsView):
    permission_classes = catalog_permission_classes()
    
    catalog_config = FILTER_REGULATOR_CONFIG
    default_scope = 'engineer'
