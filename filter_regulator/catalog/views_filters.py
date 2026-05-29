# filter_regulator/catalog/views_filters.py
"""
GET /api/filter-regulator/filters/ — filter options for FilterSidebar.
"""
from rest_framework.permissions import AllowAny
from core.views import BaseFilterOptionsView
from filter_regulator.catalog.config import FILTER_REGULATOR_CONFIG


class FilterRegulatorFilterOptionsView(BaseFilterOptionsView):
    permission_classes = [AllowAny]
    catalog_config = FILTER_REGULATOR_CONFIG
