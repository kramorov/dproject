# solenoid_valves/catalog/views_filters.py
"""
GET /api/solenoid-valves/filters/ — filter options for FilterSidebar.
"""
from rest_framework.permissions import AllowAny
from core.views import BaseFilterOptionsView
from solenoid_valves.catalog.config import SOLENOID_VALVES_CONFIG


class SolenoidValvesFilterOptionsView(BaseFilterOptionsView):
    permission_classes = [AllowAny]
    catalog_config = SOLENOID_VALVES_CONFIG
