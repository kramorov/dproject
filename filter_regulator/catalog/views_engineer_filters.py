# filter_regulator/catalog/views_engineer_filters.py
"""
GET /api/filter-regulator/engineer/filters/ — filter options for EngineerSelection.

Uses BaseFilterOptionsView with FILTER_REGULATOR_CONFIG + default_scope='engineer'.
"""
from rest_framework.permissions import AllowAny
from core.views import BaseFilterOptionsView
from filter_regulator.catalog.config import FILTER_REGULATOR_CONFIG


class FilterRegulatorEngineerFilterOptionsView(BaseFilterOptionsView):
    permission_classes = [AllowAny]
    catalog_config = FILTER_REGULATOR_CONFIG
    default_scope = 'engineer'
