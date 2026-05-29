# pa_controls/catalog/views_filters.py
"""
GET /api/pa-controls/filters/ — filter options for FilterSidebar.
"""
from rest_framework.permissions import AllowAny
from core.views import BaseFilterOptionsView
from pa_controls.catalog.config import LIMIT_SWITCH_CONFIG


class LimitSwitchBoxFilterOptionsView(BaseFilterOptionsView):
    permission_classes = [AllowAny]
    catalog_config = LIMIT_SWITCH_CONFIG
