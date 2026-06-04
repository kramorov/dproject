# solenoid_valves/catalog/views_engineer_filters.py
"""
GET /api/solenoid-valves/engineer/filters/ — filter options for EngineerSelection.
"""
from rest_framework.permissions import AllowAny
from core.views import BaseFilterOptionsView
from solenoid_valves.catalog.config import SOLENOID_VALVES_CONFIG


class SolenoidValvesEngineerFilterOptionsView(BaseFilterOptionsView):
    permission_classes = [AllowAny]
    catalog_config = SOLENOID_VALVES_CONFIG
    default_scope = 'engineer'
